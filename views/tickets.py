import asyncio
import re
from collections import defaultdict
import chat_exporter

import discord
import humanize
import requests
from pymongo.collection import Collection

from _types import Stock, Ticket
from bot import Bot
from constants import *
from utils import calc_discount, save_transcript, split_list


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
        is_staff = interaction.client.config.roles.staff in interaction.user.roles
        if not is_staff:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        embed = discord.Embed(color=0x599ae0)

        embed.set_author(
            name=f"Deleting ticket...",
            icon_url=ICONS.loading
        )

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon
        )

        await interaction.channel.send(embed=embed)

        category = interaction.channel.category
        channel = next((channel for channel in category.text_channels if channel.name == "transcripts"), None)

        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False)}
        if not channel:
            channel = await category.create_text_channel('transcripts', overwrites=overwrites)

        ticket_collection: Collection[Ticket] = interaction.client.database.get_collection("tickets")
        
        filter = {"channel_id": interaction.channel_id}
        update = {"$set": {"open": False}}
        ticket = ticket_collection.find_one_and_update(filter, update)

        if ticket == None:
            await interaction.followup.send("This ticket has already been closed.", ephemeral=True)
            return

        creator_name = ticket["username"]
        creator_id = ticket["user_id"]

        embed = discord.Embed(color=0x599ae0)

        created_at = interaction.channel.created_at
        current_time = discord.utils.utcnow()
        duration = humanize.naturaldelta(current_time - created_at)

        embed.add_field(name="Server", value=interaction.guild, inline=True)
        embed.add_field(name="Ticket", value=interaction.channel.name, inline=True)
        embed.add_field(name="Category", value=self.category, inline=True)
        embed.add_field(name="Creator", value=f"{creator_name} (`{creator_id}`)", inline=True)
        embed.add_field(name="Closer", value=f"{interaction.user} (`{interaction.user.id}`)", inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)

        embed.set_author(name=f"Ticket Transcript", icon_url=ICONS.ticket)

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon
        )

        view = discord.ui.View()

        params = f"channel_id={interaction.channel_id}"
        transcript_url = f"https://bry.up.railway.app/view?{params}"

        view_transcript = discord.ui.Button(emoji="\N{PAGE FACING UP}", label="View Transcript", url=transcript_url, style=discord.ButtonStyle.link)
        view.add_item(view_transcript)
        
        file = await save_transcript(interaction.channel)

        await channel.send(embed=embed, view=view, file=file)
        await asyncio.sleep(2)
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

    async def callback(self, interaction: discord.Interaction[Bot]) -> None:
        await interaction.response.defer(ephemeral=True)

        is_staff = interaction.client.config.roles.staff in interaction.user.roles
        if not is_staff:
            await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)
            return

        embed = discord.Embed(color=0x599ae0)

        embed.set_author(
            name=f"Closing ticket..." if self.open else f"Reopening ticket...",
            icon_url=ICONS.loading
        )

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon
        )

        message = await interaction.channel.send(embed=embed)

        ticket_collection: Collection[Ticket] = interaction.client.database.get_collection("tickets")

        filter = {"channel_id": interaction.channel_id}
        ticket = ticket_collection.find_one(filter)

        if ticket == None:
            await interaction.followup.send("This ticket has already been closed.", ephemeral=True)
            return

        creator_name = ticket["username"]
        creator_id = ticket["user_id"]

        creator = interaction.guild.get_member(creator_id)
        overwrites = interaction.channel.overwrites

        if creator:
            overwrites[creator] = discord.PermissionOverwrite(view_channel=not self.open)

        await interaction.channel.edit(overwrites=overwrites)

        embed = discord.Embed(
            color=0x599ae0,
            description=f"The ticket {interaction.channel.mention} has been {'closed' if self.open else 're-opened'} by {interaction.user.mention}."
        )

        embed.set_author(
            name=f"Ticket {'Closed' if self.open else 'Reopened'}",
            icon_url=ICONS.ticket
        )

        embed.set_footer(
            text=interaction.guild,
            icon_url=interaction.guild.icon
        )

        await message.edit(embed=embed)

        self.open = not self.open
        self.item.label = self.label
        self.item.style = self.style
        self.item.emoji = self.emoji
        self.custom_id = f'open:{self.open}:channel:{self.channel_id}'

        await interaction.message.edit(view=self.view)

        ticket_id = interaction.channel.name[-4:]
        short_name = creator_name[:5]
        status = "ticket" if self.open else "closed"
        
        name = f'{status}-{short_name}-{ticket_id}'
        await interaction.channel.edit(name=name)


class ManageView(discord.ui.View):
    def __init__(self, channel_id: int, category: str):
        self.category = category
        super().__init__(timeout=None)
        self.add_item(DynamicDelete(channel_id, category))
        self.add_item(DynamicToggle(channel_id))


class PaymentDropdown(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.payment_method = None

    @discord.ui.select(placeholder='Select your payment method', options=[
        discord.SelectOption(label='Cash App', emoji='<:BS_CashApp:1146371930228801566>', description='Cash Balance'),
        discord.SelectOption(label='PayPal', emoji='<:BS_PayPal:1146371958024441886>', description='Friends & Family'),
        discord.SelectOption(label='Crypto', emoji='<:BS_Crypto:1146371947207335947>', description='LTC, BTC, ETH'),
        discord.SelectOption(label='Limited Items', emoji='<:BS_Sshf:1172691541366681681>', description='150k+ Value')
    ])
    async def select_payment(self, interaction: discord.Interaction, item: discord.ui.Select):
        self.payment_method = item.values[0]
        await interaction.response.defer(ephemeral=True)
        self.stop()


class CreationModal(discord.ui.Modal):
    def __init__(self, category: str, input: discord.ui.TextInput):
        self.category = category
        self.input = input
        super().__init__(title=f'{category} Ticket')
        self.add_item(input)

    async def on_submit(self, interaction: discord.Interaction[Bot]):
        await interaction.response.defer(ephemeral=True)
        await create_ticket(interaction, self.category, self.input.value)

async def create_ticket(interaction: discord.Interaction[Bot], category: str, reason: str, data: dict = None):
    category_name = f"{category} Tickets"
    category_channel = next((category for category in interaction.guild.categories if category.name == category_name), None)

    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.client.config.roles.staff: discord.PermissionOverwrite(view_channel=True),
    }

    if not category_channel:
        category_channel = await interaction.guild.create_category(category_name)
        await category_channel.create_text_channel('transcripts', overwrites=overwrites)
        
    ticket_collection: Collection[Ticket] = interaction.client.database.get_collection("tickets")
    ticket_count = ticket_collection.count_documents({})

    filter = {"user_id": interaction.user.id, "category": category, "open": True}
    open_ticket = ticket_collection.find_one(filter)

    if open_ticket:
        await interaction.followup.send(f"You already have an open ticket at <#{open_ticket['channel_id']}>.", ephemeral=True)
        return
    
    if category == "Purchase":
        view = PaymentDropdown()
        await interaction.edit_original_response(embed=None, view=view)
        await view.wait()

        payment_method = view.payment_method
        if payment_method == None:
            return

    ticket_id = str(ticket_count).rjust(4, "0")
    
    name = f'ticket-{interaction.user.name[:5]}-{ticket_id}'
    user_overwrites = {**overwrites, interaction.user: discord.PermissionOverwrite(view_channel=True)}
    channel = await category_channel.create_text_channel(name, overwrites=user_overwrites)

    embed = discord.Embed(
        color=0x599ae0,
        description=f"Your ticket has been created at {channel.mention}."
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

    update = {
        "$set": {
            "user_id": interaction.user.id,
            "channel_id": channel.id,
            "username": interaction.user.name,
            "category": category,
            "open": True,
        }
    }

    if category == "Purchase":
        update["$set"]["data"] = {
            "payment_method": payment_method,
            **data,
        }

    ticket_collection.update_one(filter, update, upsert=True)

    embed = discord.Embed(
        color=0x599ae0,
        description=f"""
Welcome, {interaction.user.mention}!
Support will be with you shortly.
Feel free to provide more info in the meantime.
"""
    )

    if category == "Purchase":
        embed.description += f"\n**Item(s):** {reason}"
    else:
        embed.description += f"\n**Reason:** {reason}"

    embed.set_thumbnail(
        url=interaction.user.display_avatar.url
    )

    embed.set_author(
        name=f"Ticket #{ticket_count} ({category})",
        icon_url=ICONS.ticket
    )

    embed.set_footer(
        text=interaction.guild,
        icon_url=interaction.guild.icon
    )

    if category == "Purchase":
        embed._footer["text"] += f" | Payment Method: {payment_method}"

    view = ManageView(channel.id, category)

    mention = interaction.client.config.roles.staff.mention
    message = await channel.send(f"{interaction.user.mention} {mention}", embed=embed, view=view)
    await message.pin()

class PurchaseDropdown(discord.ui.View):
    def __init__(self, bot: Bot):
        super().__init__(timeout=None)
        self.values = []
        self.sets = defaultdict(lambda: {"price": 0, "total_quantity": 0, "items": []})
        self.reason = ""
        self.subtotal = 0
        self.total = 0

        stock_collection = bot.database.get_collection("stock")

        for stock_item in stock_collection.find().sort("set"):
            set_name = stock_item.get("set", "")

            self.sets[set_name]["price"] += stock_item["price"]
            self.sets[set_name]["total_quantity"] += stock_item["quantity"]
            self.sets[set_name]["items"].append(stock_item)

        ordered_sets = list(self.sets.items())
        ordered_sets.append(ordered_sets.pop(0))

        options = []
        for set_name, data in ordered_sets:
            price = data["price"]
            total_quantity = data["total_quantity"]

            items: list[Stock] = sorted(data["items"], key=lambda x: x["price"])

            if total_quantity <= 0:
                continue

            if set_name != "":
                options.append(
                    discord.SelectOption(
                        label=f"{set_name} Set",
                        description=f"${price:,}",
                        value=f"{set_name} Set"
                    )
                )

            for item in items:
                objectId = item["_id"]
                name = item["name"]
                price = item["price"]
                quantity = item["quantity"]

                if quantity <= 0:
                    continue

                options.append(
                    discord.SelectOption(
                        label=f"{set_name} {name}",
                        description=f"${price:,} | {quantity} in stock",
                        value=str(objectId)
                    )
                )

        option_chunks = split_list(options, 25)
        for i, chunk in enumerate(option_chunks):
            select = discord.ui.Select(
                placeholder = "Select your items",
                custom_id=f"purchase-{i}",
                options=chunk
            )

            if i > 0:
                select.placeholder += " (continued)"

            select.callback = self.selection_callback
            self.add_item(select)

        checkout = discord.ui.Button(
            label="Checkout",
            style=discord.ButtonStyle.primary,
            custom_id="checkout"
        )

        checkout.callback = self.checkout_callback
        self.add_item(checkout)

    async def selection_callback(self, interaction: discord.Interaction):
        values = interaction.data["values"][0].rsplit(" ", 1)

        set_name = values[0]
        item = values[-1]

        if item == "Set":
            items = self.sets[set_name]["items"]
            self.values.extend([str(x["_id"]) for x in items])
        else:
            self.values.append(item)

        stock_collection: Collection[Stock] = interaction.client.database.get_collection("stock")
        stock_names = {str(item["_id"]): f"{item.get('set', '')} {item['name']}" for item in stock_collection.find()}
        stock_prices = {str(item["_id"]): f"{item['price']}" for item in stock_collection.find()}

        self.items = [stock_names[id] for id in self.values]
        self.reason = "\n- " + "\n- ".join(self.items)

        embed = discord.Embed(
            color=0x599ae0,
            title="Selected Items:",
            description=self.reason,
        )

        self.subtotal = sum(int(stock_prices[id]) for id in self.values)
        self.total = self.subtotal - calc_discount(self.subtotal, len(self.values))

        embed.set_footer(
            icon_url=interaction.guild.icon,
            text=f"Subtotal: ${self.subtotal:,}\nTotal: ${self.total:,}"
        )

        await interaction.response.edit_message(embed=embed, view=self)

    async def checkout_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        purchase_data = {
            "items": self.values,
            "subtotal": self.subtotal,
            "total": self.total,
        }
        await create_ticket(interaction, "Purchase", self.reason, purchase_data)

class PurchasePanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="\N{shopping bags}", label="Purchase", style=discord.ButtonStyle.primary, custom_id="purchase_ticket")
    async def purchase_ticket(self, interaction: discord.Interaction[Bot], button: discord.ui.Button):
        embed = discord.Embed(
            color=0x599ae0,
            description=f"Please select the items you'd like to purchase:"
        )

        await interaction.response.send_message(embed=embed, view=PurchaseDropdown(interaction.client), ephemeral=True)

    @discord.ui.button(emoji="\N{hourglass}", label="Exclusive", style=discord.ButtonStyle.primary, custom_id="exclusive_ticket")
    async def exclusive_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        info = discord.ui.TextInput(label='Enter info for your purchase', placeholder='e.g. 2050 VALORANT Points')
        await interaction.response.send_modal(CreationModal('Exclusive', info))

    @discord.ui.button(emoji="\N{money with wings}", label="Sell", style=discord.ButtonStyle.primary, custom_id="sell_ticket")
    async def sell_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        info = discord.ui.TextInput(label='Enter info for your sale', placeholder='e.g. Golden Age Tanto for $100')
        await interaction.response.send_modal(CreationModal('Sell', info))

    @discord.ui.button(emoji="<:dahoodcash:1200935989363871837>", label="DHC", style=discord.ButtonStyle.primary, custom_id="dhc_ticket")
    async def dhc_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        info = discord.ui.TextInput(label='Enter info for your purchase')
        await interaction.response.send_modal(CreationModal('DHC', info))

class SupportPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="\N{wrench}", label="Support", style=discord.ButtonStyle.primary, custom_id="support_ticket")
    async def support_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        info = discord.ui.TextInput(label='Enter reason for your support')
        await interaction.response.send_modal(CreationModal('Support', info))

    @discord.ui.button(emoji="\N{handshake}", label="Middleman", style=discord.ButtonStyle.primary, custom_id="mm_ticket")
    async def vbucks_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        info = discord.ui.TextInput(label='Enter reason for your support')
        await interaction.response.send_modal(CreationModal('Middleman', info))

    @discord.ui.button(emoji="\N{sleuth or spy}", label="Scam Report", style=discord.ButtonStyle.primary, custom_id="scam_ticket")
    async def scam_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        info = discord.ui.TextInput(label="Enter user you're reporting", placeholder="User ID/Username")
        await interaction.response.send_modal(CreationModal('Scam Report', info))

async def setup(bot: Bot):
    bot.add_view(PurchasePanel())
    bot.add_view(SupportPanel())
    bot.add_dynamic_items(DynamicDelete, DynamicToggle)
