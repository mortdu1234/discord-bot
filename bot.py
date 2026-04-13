import discord
from discord.ext import commands
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PTERODACTYL_URL = os.getenv("PTERODACTYL_URL")       # ex: https://panel.tondomaine.com
PTERODACTYL_API_KEY = os.getenv("PTERODACTYL_API_KEY") # Client API Key

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─── Helpers API Pterodactyl ──────────────────────────────────────────────────

def ptero_headers():
    return {
        "Authorization": f"Bearer {PTERODACTYL_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

async def get_all_servers():
    """Retourne la liste de tous les serveurs accessibles par le compte."""
    url = f"{PTERODACTYL_URL}/api/client"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=ptero_headers()) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("data", [])

async def find_server(name: str):
    """Cherche un serveur par nom (insensible à la casse)."""
    servers = await get_all_servers()
    if servers is None:
        return None, "Impossible de contacter le panel Pterodactyl."
    name_lower = name.lower()
    for server in servers:
        attr = server["attributes"]
        if attr["name"].lower() == name_lower:
            return attr, None
    return None, f"Aucun serveur trouvé avec le nom **{name}**."

async def get_server_resources(identifier: str):
    """Retourne les ressources (état, RAM, CPU) d'un serveur."""
    url = f"{PTERODACTYL_URL}/api/client/servers/{identifier}/resources"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=ptero_headers()) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("attributes", {})

async def send_power_action(identifier: str, action: str):
    """Envoie une action de puissance : start, stop, restart, kill."""
    url = f"{PTERODACTYL_URL}/api/client/servers/{identifier}/power"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=ptero_headers(), json={"signal": action}) as resp:
            return resp.status == 204

# ─── Commandes Discord ────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user} (ID: {bot.user.id})")
    await bot.tree.sync()

@bot.command(name="status")
async def status(ctx, *, server_name: str = None):
    """!status [NomDuServeur] — Affiche le statut d'un serveur Minecraft."""
    if not server_name:
        await ctx.send("❌ Usage : `!status [NomDuServeur]`")
        return

    async with ctx.typing():
        attr, error = await find_server(server_name)
        if error:
            embed = discord.Embed(title="❌ Serveur introuvable", description=error, color=0xe74c3c)
            await ctx.send(embed=embed)
            return

        identifier = attr["identifier"]
        resources = await get_server_resources(identifier)

        if resources is None:
            await ctx.send("❌ Impossible de récupérer les ressources du serveur.")
            return

        state = resources.get("current_state", "unknown")
        stats = resources.get("resources", {})

        # Couleur et emoji selon l'état
        state_info = {
            "running":  ("🟢", "En ligne",   0x2ecc71),
            "starting": ("🟡", "Démarrage",  0xf39c12),
            "stopping": ("🟠", "Arrêt",      0xe67e22),
            "offline":  ("🔴", "Hors ligne", 0xe74c3c),
        }
        emoji, label, color = state_info.get(state, ("⚪", state.capitalize(), 0x95a5a6))

        ram_mb   = stats.get("memory_absolute", 0) / 1024 / 1024
        ram_lim  = attr.get("limits", {}).get("memory", 0)
        cpu_pct  = stats.get("cpu_absolute", 0)
        disk_mb  = stats.get("disk_absolute", 0) / 1024 / 1024
        disk_lim = attr.get("limits", {}).get("disk", 0)
        uptime_s = stats.get("uptime", 0) // 1000
        uptime_fmt = f"{uptime_s // 3600}h {(uptime_s % 3600) // 60}m {uptime_s % 60}s" if uptime_s else "—"

        embed = discord.Embed(
            title=f"{emoji} {attr['name']}",
            description=f"**État :** {label}",
            color=color
        )
        embed.add_field(name="🖥️ RAM",    value=f"`{ram_mb:.0f} MB` / `{ram_lim} MB`", inline=True)
        embed.add_field(name="⚙️ CPU",    value=f"`{cpu_pct:.1f}%`",                    inline=True)
        embed.add_field(name="💾 Disque", value=f"`{disk_mb:.0f} MB` / `{disk_lim} MB`",inline=True)
        embed.add_field(name="⏱️ Uptime", value=f"`{uptime_fmt}`",                       inline=True)
        embed.add_field(name="🔑 ID",     value=f"`{identifier}`",                       inline=True)
        embed.set_footer(text=f"Pterodactyl • {attr['node']}" if 'node' in attr else "Pterodactyl")

        view = ServerControlView(identifier, attr["name"], state)
        await ctx.send(embed=embed, view=view)


@bot.command(name="servers")
async def list_servers(ctx):
    """!servers — Liste tous les serveurs disponibles."""
    async with ctx.typing():
        servers = await get_all_servers()
        if not servers:
            await ctx.send("❌ Aucun serveur trouvé ou panel inaccessible.")
            return

        embed = discord.Embed(title="📋 Serveurs Minecraft", color=0x3498db)
        for s in servers:
            a = s["attributes"]
            embed.add_field(
                name=a["name"],
                value=f"ID: `{a['identifier']}` | Nœud: `{a.get('node', '?')}`",
                inline=False
            )
        await ctx.send(embed=embed)


# ─── Vue avec boutons de contrôle ────────────────────────────────────────────

class ServerControlView(discord.ui.View):
    def __init__(self, identifier: str, server_name: str, current_state: str):
        super().__init__(timeout=120)
        self.identifier = identifier
        self.server_name = server_name

        # Bouton Start : visible seulement si le serveur est offline
        if current_state in ("offline", "stopping"):
            self.add_item(PowerButton("▶️ Démarrer", "start",   discord.ButtonStyle.success,  identifier))
        if current_state == "running":
            self.add_item(PowerButton("🔁 Redémarrer", "restart", discord.ButtonStyle.primary,  identifier))
            self.add_item(PowerButton("⏹️ Arrêter",   "stop",    discord.ButtonStyle.danger,   identifier))


class PowerButton(discord.ui.Button):
    def __init__(self, label: str, action: str, style: discord.ButtonStyle, identifier: str):
        super().__init__(label=label, style=style)
        self.action = action
        self.identifier = identifier

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        success = await send_power_action(self.identifier, self.action)
        if success:
            labels = {"start": "démarrage", "stop": "arrêt", "restart": "redémarrage"}
            await interaction.followup.send(
                f"✅ Commande de **{labels.get(self.action, self.action)}** envoyée avec succès !"
            )
        else:
            await interaction.followup.send("❌ Échec de l'envoi de la commande.")
        # Désactiver les boutons après usage
        for item in self.view.children:
            item.disabled = True
        await interaction.message.edit(view=self.view)


# ─── Lancement ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)