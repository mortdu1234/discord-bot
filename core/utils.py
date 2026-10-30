"""Petites fonctions utilitaires réutilisables par tous les cogs."""
import discord
from discord.ext import commands


async def safe_delete(ctx: commands.Context) -> None:
    """Supprime le message de commande, sans planter si le bot n'a pas la permission."""
    try:
        await ctx.message.delete()
    except (discord.Forbidden, discord.NotFound):
        pass


def format_name_grid(names: list[str], per_row: int = 3) -> str:
    """['a','b','c','d'] -> '`a`  `b`  `c`\\n`d`' (pseudos triés, par lignes de 3)."""
    names = sorted(names)
    return "\n".join(
        "  ".join(f"`{n}`" for n in names[i:i + per_row])
        for i in range(0, len(names), per_row)
    )


def error_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(title=f"❌ {title}", description=description, color=0xE74C3C)
