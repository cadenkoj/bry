import discord
from discord import app_commands as apc
from discord.ext import commands
from pymongo.collection import Collection

from _types import Ticket
from bot import Bot
from constants import *
from views.tickets import PanelView

class Support(commands.Cog):
    """Commands for handling support tickets."""

    def __init__(self, bot: Bot):
        self.bot = bot

    ticket = apc.Group(name="ticket", description="Ticket commands")
    purchase = apc.Group(name="purchase", description="Purchase commands")
    support = apc.Group(name="support", description="Support commands")

    @purchase.command()
    @apc.guild_only()
    @apc.default_permissions(manage_guild=True)
    async def panel(self, interaction: discord.Interaction) -> None:
        """Sends the ticket panel."""

        await interaction.response.defer(ephemeral=True)

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        embed = discord.Embed(
            color=0x599ae0,
            title="Payment Info",
            description="""
<:BS_CashApp:1146371930228801566> ▹ Cash App (Cash Balance)

<:BS_PayPal:1146371958024441886> ▹ PayPal (Friends & Family)

<:BS_Crypto:1146371947207335947> ▹ Crypto (LTC, BTC, ETH)

<:BS_Sshf:1172691541366681681> ▹ Limited Items (150k+ Value)
"""
        )

        embed.set_footer(text="Click a button below to create a ticket")

        view = PanelView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.delete_original_response()

    @support.command()
    @apc.guild_only()
    @apc.default_permissions(manage_guild=True)
    async def panel(self, interaction: discord.Interaction) -> None:
        """Sends the ticket panel."""

        await interaction.response.defer(ephemeral=True)

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        embed = discord.Embed(
            color=0x599ae0,
            title="Payment Info",
            description="""
<:BS_CashApp:1146371930228801566> ▹ Cash App (Cash Balance)

<:BS_PayPal:1146371958024441886> ▹ PayPal (Friends & Family)

<:BS_Crypto:1146371947207335947> ▹ Crypto (LTC, BTC, ETH)

<:BS_Sshf:1172691541366681681> ▹ Limited Items (150k+ Value)
"""
        )

        embed.set_footer(text="Click a button below to create a ticket")

        view = PanelView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.delete_original_response()

    @ticket.command()
    @apc.guild_only()
    async def rename(self, interaction: discord.Interaction, name: str) -> None:
        """Renames a support ticket.
        
        Parameters
        ----------
        name : str
            The new name for the ticket.
        """

        await interaction.response.defer()

        is_staff = self.bot.config.roles.staff in interaction.user.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        ticket_collection: Collection[Ticket] = interaction.client.database.get_collection("tickets")

        filter = {"channel_id": interaction.channel_id}
        ticket = ticket_collection.find_one(filter)

        if ticket == None:
            raise Exception("This channel is not a ticket.")

        await interaction.channel.edit(name=name)

        embed = discord.Embed(
            color=0x599ae0,
            description=f"The ticket {interaction.channel.mention} has been renamed by {interaction.user.mention}."
        )

        embed.set_author(
            name=f"Ticket Renamed",
            icon_url=ICONS.ticket
        )

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon
        )

        await interaction.followup.send(embed=embed)

    @ticket.command()
    @apc.guild_only()
    async def adduser(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """Adds a user to a support ticket.
        
        Parameters
        ----------
        user : discord.Member
            The user to add to the ticket.
        """

        await interaction.response.defer()

        is_staff = self.bot.config.roles.staff in interaction.user.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        ticket_collection: Collection[Ticket] = interaction.client.database.get_collection("tickets")

        filter = {"channel_id": interaction.channel_id}
        ticket = ticket_collection.find_one(filter)

        if ticket == None:
            raise Exception("This channel is not a ticket.")

        overwrites = interaction.channel.overwrites
        overwrites[user] = discord.PermissionOverwrite(view_channel=True)

        await interaction.channel.edit(overwrites=overwrites)

        embed = discord.Embed(
            color=0x599ae0,
            description=f"{user.mention} has been added to the ticket {interaction.channel.mention} by {interaction.user.mention}."
        )

        embed.set_author(
            name=f"Ticket User Added",
            icon_url=ICONS.ticket
        )

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon
        )

        await interaction.followup.send(embed=embed)

    @ticket.command()
    @apc.guild_only()
    async def removeuser(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """Removes a user from a support ticket.
        
        Parameters
        ----------
        user : discord.Member
            The user to remove from the ticket.
        """

        await interaction.response.defer()

        is_staff = self.bot.config.roles.staff in interaction.user.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        ticket_collection: Collection[Ticket] = interaction.client.database.get_collection("tickets")

        filter = {"channel_id": interaction.channel_id}
        ticket = ticket_collection.find_one(filter)

        if ticket == None:
            raise Exception("This channel is not a ticket.")

        overwrites = interaction.channel.overwrites
        overwrites[user] = discord.PermissionOverwrite(view_channel=False)

        await interaction.channel.edit(overwrites=overwrites)

        embed = discord.Embed(
            color=0x599ae0,
            description=f"{user.mention} has been removed from the ticket {interaction.channel.mention} by {interaction.user.mention}."
        )

        embed.set_author(
            name=f"Ticket User Removed",
            icon_url=ICONS.ticket
        )

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon
        )

        await interaction.followup.send(embed=embed)

async def setup(bot: Bot):
    await bot.add_cog(Support(bot))
