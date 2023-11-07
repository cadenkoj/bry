import re
import requests
import humanize

import discord
from discord import app_commands as apc
from discord.ext import commands
from pymongo.collection import Collection

from _types import Ticket
from bot import Bot

TICKET_EMOJI = 'https://cdn.discordapp.com/emojis/1169397900183351378.webp?size=128'
LOADING_EMOJI = 'https://cdn.discordapp.com/emojis/1170402444627419146.gif?size=128'


class DynamicDelete(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r'category:(?P<category>[^:]+):channel:(?P<id>[0-9]+)',
):
    def __init__(self, channel_id: int, category: str) -> None:
        self.channel_id: int = channel_id
        self.category: str = category
        super().__init__(
            discord.ui.Button(
                label='Delete Ticket',
                style=discord.ButtonStyle.danger,
                emoji='\N{WASTEBASKET}',
                custom_id=f'category:{category}:channel:{channel_id}',
            )
        )

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        channel_id = int(match['id'])
        category = match['category']
        return cls(channel_id, category)

    async def callback(self, interaction: discord.Interaction[Bot]) -> None:
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(color=0x599ae0)

        embed.set_author(
            name=f"Deleting ticket...",
            icon_url=LOADING_EMOJI
        )

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon.url
        )

        await interaction.channel.send(embed=embed)

        category = interaction.channel.category
        channel = next((channel for channel in category.text_channels if channel.name == "📃・transcripts"), None)

        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(
            view_channel=False)}
        if not channel:
            await category.create_text_channel('📃・transcripts', overwrites=overwrites)

        params = {"channel_id": interaction.channel_id, "category": self.category}
        requests.get(f"http://api.railway.internal:8080/save", params)

        ticket_collection: Collection[Ticket] = interaction.client.database.get_collection("tickets")
        
        filter = {"channel_id": interaction.channel_id}
        ticket = ticket_collection.find_one_and_delete(filter)

        creator = interaction.guild.get_member(ticket['user_id'])

        embed = discord.Embed(color=0x599ae0)

        created_at = interaction.channel.created_at
        current_time = discord.utils.utcnow()
        duration = humanize.naturaldelta(current_time - created_at)

        embed.add_field(name="Server", value=interaction.guild, inline=True)
        embed.add_field(name="Ticket", value=interaction.channel.name, inline=True)
        embed.add_field(name="Category", value=self.category, inline=True)
        embed.add_field(name="Creator", value=f"{creator} (`{creator.id}`)", inline=True)
        embed.add_field(name="Closer", value=f"{interaction.user} (`{interaction.user.id}`)", inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)

        embed.set_author(name=f"Ticket Transcript", icon_url=TICKET_EMOJI)

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon.url
        )

        view = discord.ui.View()

        params = f"channel_id={interaction.channel_id}"
        transcript_url = f"https://api-production-ce8c.up.railway.app/view?{params}"
        download_url = f"https://api-production-ce8c.up.railway.app/download?{params}"

        view_transcript = discord.ui.Button(emoji="\N{PAGE FACING UP}", label="View Transcript", url=transcript_url, style=discord.ButtonStyle.link)
        download_transcript = discord.ui.Button(emoji="\N{LINK SYMBOL}", label="Download Transcript", url=download_url, style=discord.ButtonStyle.link)

        view.add_item(view_transcript)
        view.add_item(download_transcript)

        await channel.send(embed=embed, view=view)
        await interaction.channel.delete()


class DynamicToggle(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r'open:(?P<open>True|False):channel:(?P<id>[0-9]+)',
):
    def __init__(self, channel_id: int, open: bool = True) -> None:
        self.channel_id: int = channel_id
        self.open: bool = open
        super().__init__(
            discord.ui.Button(
                label=self.label,
                style=self.style,
                emoji=self.emoji,
                custom_id=f'open:{open}:channel:{channel_id}',
            )
        )

    @property
    def label(self) -> str:
        return 'Close Ticket' if self.open else 'Reopen Ticket'

    @property
    def style(self) -> discord.ButtonStyle:
        return discord.ButtonStyle.danger if self.open else discord.ButtonStyle.primary

    @property
    def emoji(self) -> str:
        return '\N{LOCK}' if self.open else '\N{OPEN LOCK}'

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        open = match['open'] == 'True'
        channel_id = int(match['id'])
        return cls(channel_id, open=open)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(color=0x599ae0)

        embed.set_author(
            name=f"Closing ticket..." if self.open else f"Reopening ticket...",
            icon_url=LOADING_EMOJI
        )

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon.url
        )

        message = await interaction.channel.send(embed=embed)

        overwrites = {
            **interaction.channel.overwrites,
            interaction.user: discord.PermissionOverwrite(view_channel=not self.open)
        }

        await interaction.channel.edit(overwrites=overwrites)

        embed = discord.Embed(
            color=0x599ae0,
            description=f"The ticket {interaction.channel.mention} has been {'closed' if self.open else 're-opened'} by {interaction.user.mention}."
        )

        embed.set_author(
            name=f"Ticket {'Closed' if self.open else 'Reopened'}",
            icon_url=TICKET_EMOJI
        )

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon.url
        )

        await message.edit(embed=embed)

        self.open = not self.open
        self.item.label = self.label
        self.item.style = self.style
        self.item.emoji = self.emoji
        self.custom_id = f'open:{self.open}:channel:{self.channel_id}'

        await interaction.message.edit(view=self.view)


class ManageView(discord.ui.View):
    def __init__(self, channel_id: int, category: str):
        self.category = category
        super().__init__(timeout=None)
        self.add_item(DynamicDelete(channel_id, category))
        self.add_item(DynamicToggle(channel_id))


class CreationModal(discord.ui.Modal):
    def __init__(self, category: str, input: discord.ui.TextInput):
        self.category = category
        self.input = input
        super().__init__(title=f'{category} Ticket')
        self.add_item(input)

    async def on_submit(self, interaction: discord.Interaction[Bot]):
        await interaction.response.defer(ephemeral=True)

        support_roles = await self.get_support_roles(interaction)

        category_name = f"{self.category} Tickets"
        category = next((category for category in interaction.guild.categories if category.name == category_name), None)

        ticket_collection: Collection[Ticket] = interaction.client.database.get_collection("tickets")

        ticket_id = str(ticket_collection.count_documents({}))

        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False)}
        user_overwrites = {**overwrites, interaction.user: discord.PermissionOverwrite(view_channel=True)}
        channel = await category.create_text_channel(f'ticket-{interaction.user.name[:5]}-{ticket_id.rjust(4, "0")}', overwrites=user_overwrites)

        if not category:
            category = await interaction.guild.create_category(category_name)
            await category.create_text_channel('📃・transcripts', overwrites=overwrites)

        for role in support_roles:
            overwrite = {role: discord.PermissionOverwrite(view_channel=True)}
            await channel.edit(overwrites=overwrite)
            
        body = {"user_id": interaction.user.id, "channel_id": channel.id}
        update = {"$set": body}
        ticket_collection.update_one(body, update, upsert=True)

        embed = discord.Embed(
            color=0x599ae0,
            description=f"""
Welcome, {interaction.user.mention}!
Support will be with you shortly. 

**Reason** → {self.input.value}
""",
        )

        embed.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        embed.set_author(
            name=f"Ticket #{ticket_id} ({self.category})",
            icon_url=TICKET_EMOJI
        )

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon.url
        )

        view = ManageView(channel.id, self.category)
        mentions = " ".join([r.mention for r in support_roles])

        message = await channel.send(f"{interaction.user.mention} {mentions}", embed=embed, view=view)

        await message.pin()

    async def get_support_roles(self, interaction: discord.Interaction) -> tuple[discord.Role]:
        support_roles = []
        for role_id in [1146375334170730548, 1145965467207467049, 1145959138602524672]:
            role = interaction.guild.get_role(role_id)
            support_roles.append(role.mention)
        return tuple(support_roles)


class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="\N{MONEY WITH WINGS}", label="Purchase", style=discord.ButtonStyle.primary, custom_id="purchase_ticket")
    async def purchase_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        info = discord.ui.TextInput(
            label='Enter info for your purchase',
            placeholder='e.g. Golden Age Tanto (PayPal)',
        )

        await interaction.response.send_modal(CreationModal('Purchase', info))

    @discord.ui.button(emoji="\N{handshake}", label="Support", style=discord.ButtonStyle.primary, custom_id="support_ticket")
    async def support_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        info = discord.ui.TextInput(
            label='Enter reason for your support',
            placeholder='e.g. I need help with my purchase',
        )

        await interaction.response.send_modal(CreationModal('Support', info))


class Support(commands.Cog):
    """Commands for handling support tickets."""

    def __init__(self, bot: Bot):
        self.bot = bot

    ticket = apc.Group(name="ticket", description="Manage a support ticket.")

    @ticket.command()
    @apc.guild_only()
    async def panel(self, interaction: discord.Interaction) -> None:
        """Sends the support panel."""

        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            color=0x599ae0,
            title="Support Panel",
            description="Click a button below to create a support ticket."
        )

        view = PanelView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.delete_original_response()


async def setup(bot: Bot):
    bot.add_view(PanelView())
    bot.add_dynamic_items(DynamicDelete)
    bot.add_dynamic_items(DynamicToggle)
    await bot.add_cog(Support(bot))
