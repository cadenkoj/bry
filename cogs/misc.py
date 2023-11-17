from typing import Optional

import discord
from discord.ext import commands

from bot import Bot

class Misc(commands.Cog):
    """Miscellaneous commands."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["av"])
    async def avatar(self, ctx: commands.Context, *, user: Optional[discord.User] = None):
        """Get the avatar of a user.
        
        Parameters
        ----------
        user : Optional[discord.User]
            The user to get the avatar of.
        """

        if user is None:
            user = ctx.author._user

        avatar_embed = discord.Embed(
            color=0x99b4e1,
            description=f"**[{user.display_name}'s avatar]({user.display_avatar.url})**",
            timestamp=discord.utils.utcnow(),
        )

        avatar_embed.set_image(url=user.display_avatar.url)
        avatar_embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)

        await ctx.reply(embed=avatar_embed, mention_author=False)

    @commands.hybrid_command()
    async def banner(self, ctx: commands.Context, *, user: Optional[discord.User] = None):
        """Get the banner of a user.
        
        Parameters
        ----------
        user : Optional[discord.User]
            The user to get the banner of.
        """

        if user is None:
            user = ctx.author._user

        if user.banner is None:
            raise commands.BadArgument(f"{user.display_name} does not have a banner.")

        banner_embed  = discord.Embed(
            color=0x99b4e1,
            description=f"**[{user.display_name}'s banner]({user.banner.url})**",
            timestamp=discord.utils.utcnow(),
        )

        banner_embed.set_image(url=user.banner.url)
        banner_embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)

        await ctx.reply(embed=banner_embed , mention_author=False)

async def setup(bot: Bot) -> None:
    await bot.add_cog(Misc(bot))