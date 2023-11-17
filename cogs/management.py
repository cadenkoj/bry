from typing import Optional
import discord
from discord import app_commands as apc
from discord.ext import commands

from bot import Bot

class Management(commands.Cog):
    """Commands for managing the server."""

    def __init__(self, bot: Bot):
        self.bot = bot

    invite = apc.Group(name="invite", description="Commands for managing invites.")

    @apc.command()
    @apc.guild_only()
    async def invites(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Check how many invites a member has.

        Parameters
        ----------
        member : discord.Member
            The member to check invites for.
        """

        if member == None:
           member = interaction.user
           start_text = "You have"
        else:
            start_text = f"{member.mention} has"

        total_invites = 0
        for invite in await interaction.guild.invites():
            if invite.inviter == member:
                total_invites += invite.uses

        await interaction.response.send_message(f"{start_text} **{total_invites}** invites.", ephemeral=True)
    
    @invite.command()
    @apc.guild_only()
    @apc.default_permissions(manage_guild=True)
    async def purge(self, interaction: discord.Interaction):
        """Clear all invites for the server."""

        await interaction.response.defer(ephemeral=True)

        for invite in await interaction.guild.invites():
            await invite.delete(reason=f"{interaction.user}: Purge")

        await interaction.followup.send("Purged all invites.", ephemeral=True)

async def setup(bot: Bot):
    await bot.add_cog(Management(bot))