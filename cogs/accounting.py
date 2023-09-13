from typing import List, Optional
import discord
from discord import app_commands as apc
from discord.ext import commands, tasks

from bot import Bot


class Accounting(commands.Cog):
    """Commands for accounting stock and payment logs."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.update_channels.start()

    payment = [
        apc.Choice(name="PayPal", value="paypal_email"),
        apc.Choice(name="Cash App", value="cashapp_tag"),
        apc.Choice(name="BTC", value="btc_address"),
        apc.Choice(name="LTC", value="ltc_address"),
        apc.Choice(name="ETH", value="eth_address"),
    ]

    @apc.command()
    @apc.guild_only()
    @apc.choices(payment=payment)
    async def log(
        self,
        interaction: discord.Interaction,
        customer: discord.User,
        username: str,
        item: str,
        payment: apc.Choice[str],
        info: str,
    ) -> None:
        """Logs a sale and updates channel info.

        Parameters
        ___________
        customer: discord.User
            The user who bought the item.
        username: str
            The Roblox username of the user.
        item: app_commands.Choice[str]
            The item that was bought.
        payment: app_commands.Choice[str]
            The payment method used.
        info: str
            The payment info provided."""
        name, display_price = item.split("$")

        if interaction.user.get_role(1146357576389378198) is None:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if display_price == "0":
            await interaction.response.send_message("This item is out of stock.", ephemeral=True)
            return

        await interaction.response.defer()

        customer_role = interaction.guild.get_role(1145959140594810933)
        log_channel = self.bot.get_channel(1151322058941267968)

        log_collection = self.bot.database.get_collection("logs")
        stock_collection = self.bot.database.get_collection("stock")

        filter = {"item": name}
        update = {"$inc": {"quantity": -1}}

        doc = stock_collection.find_one(filter)
        stock_collection.update_one(filter, update, upsert=True)
        raw_price = doc["price"]

        body = {
            "user_id": customer.id,
            "username": username,
            "item": {"name": name, "price": raw_price},
        }

        body[payment.value] = info
        log_collection.insert_one(body)

        log_embed = discord.Embed(
            color=0x77ABFC,
            description=f"{customer.mention} (`{customer.id}`) has bought **{name}** for **${display_price}**.",
        )

        log_embed.set_author(name=customer, icon_url=customer.display_avatar.url)
        log_embed.add_field(name=f"__Username__", value=username, inline=True)
        log_embed.add_field(name=f"__{payment.name}__", value=info, inline=True)

        chat_embed = discord.Embed(
            color=0x77ABFC,
            description=f"""**__Info__**
Item → {name}
Price → ${display_price}
Payment Method → {payment.name}
            """,
        )

        chat_embed.set_footer(text=info)

        await customer.add_roles(customer_role)
        await log_channel.send(embed=log_embed)
        await interaction.followup.send(embed=chat_embed)

    @apc.command()
    @apc.guild_only()
    async def stock(self, interaction: discord.Interaction) -> None:
        """Displays the curent available stock."""
        if interaction.user.get_role(1146357576389378198) is None:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        stock_collection = self.bot.database.get_collection("stock")
        stock = stock_collection.find({})

        stock_items = []
        for doc in stock:
            item = doc["item"]
            price = doc["price"]
            quantity = doc["quantity"]

            display_item = f"**{item}** (${price})"

            if quantity < 1:
                display_item = f"~~{display_item}~~ — **Out of Stock**"
            else:
                display_item = f"{display_item} — **{quantity}x**"

            stock_items.append(f"- {display_item}")

        display_stock = "\n".join(stock_items)
        stock_embed = discord.Embed(color=0x77ABFC, description=f"**__Stock__**\n{display_stock}")

        await interaction.response.send_message(embed=stock_embed)

    @apc.command()
    @apc.guild_only()
    async def restock(self, interaction: discord.Interaction, item: str, quantity: int) -> None:
        """Updates the a stock amount.

        Parameters
        ___________
        item: app_commands.Choice[str]
            The item that was restocked.
        quantity: app_commands.Choice[str]
            The amount that was restocked"""
        name, display_price = item.split("$")

        is_seller = interaction.user.get_role(1145959138602524672) is not None
        is_exclusive = interaction.user.get_role(1146357576389378198) is not None
        if not is_seller and not is_exclusive:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        stock_collection = self.bot.database.get_collection("stock")

        filter = {"item": name}
        update = {"$inc": {"quantity": quantity}}

        doc = stock_collection.find_one(filter)

        if doc is None:
            await interaction.response.send_message("This item does not exist.", ephemeral=True)
            return

        stock_collection.update_one(filter, update, upsert=True)

        price = doc["price"]
        combined_quantity = doc["quantity"] + quantity

        restock_embed = discord.Embed(
            color=0x77ABFC,
            description=f"Restocked **{name}** with **{quantity}x** → {combined_quantity} Total",
            timestamp=discord.utils.utcnow(),
        )

        restock_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
        restock_embed.set_footer(text=f"${price:,}")

        await interaction.response.send_message(embed=restock_embed)

    @apc.command()
    @apc.guild_only()
    async def additem(self, interaction: discord.Interaction, name: str, price: int, quantity: int) -> None:
        """Adds an item to the stock list.

        Parameters
        ___________
        name: str
            The name of the new item.
        price: int
            The price of the item.
        quantity: int
            The amount of the item in stock."""
        is_seller = interaction.user.get_role(1145959138602524672) is not None
        is_exclusive = interaction.user.get_role(1146357576389378198) is not None
        if not is_seller and not is_exclusive:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        stock_collection = self.bot.database.get_collection("stock")

        if stock_collection.find_one({"item": name}):
            await interaction.response.send_message("This item already exists.", ephemeral=True)
            return

        stock_collection.insert_one({"item": name, "price": price, "quantity": quantity})

        add_item_embed = discord.Embed(
            color=0x77ABFC,
            description=f"Added **{quantity}x** **{name}** to the stock for **${price:,}**.",
            timestamp=discord.utils.utcnow(),
        )

        add_item_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=add_item_embed)

    @apc.command()
    @apc.guild_only()
    async def updateitem(
        self,
        interaction: discord.Interaction,
        item: str,
        name: Optional[str],
        price: Optional[int],
    ) -> None:
        """Updates an item in the stock list.

        Parameters
        ___________
        item: str
            The name of the item to update.
        name: Optional[str]
            The new name of the item.
        price: Optional[int]
            The new price of the item."""
        old_name, old_price = item.split("$")

        is_seller = interaction.user.get_role(1145959138602524672) is not None
        is_exclusive = interaction.user.get_role(1146357576389378198) is not None
        if not is_seller and not is_exclusive:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        stock_collection = self.bot.database.get_collection("stock")

        if not stock_collection.find_one({"item": old_name}):
            await interaction.response.send_message("This item does not exist.", ephemeral=True)
            return

        filter = {"item": old_name}
        update = {}

        if name is not None:
            update["item"] = name

        if price is not None:
            update["price"] = price

        if not update:
            await interaction.response.send_message("You must provide a new name or price.", ephemeral=True)
            return

        stock_collection.update_one(filter, {"$set": update})

        update_item_embed = discord.Embed(
            color=0x77ABFC,
            description=f"""
**__Info__**
Item → {name}
Price → ${price:,}
            """,
            timestamp=discord.utils.utcnow(),
        )

        update_item_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=update_item_embed)

    @apc.command()
    @apc.guild_only()
    async def delitem(self, interaction: discord.Interaction, item: str) -> None:
        """Removes an item from the stock list.

        Parameters
        ___________
        item: str
            The name of the item to remove."""
        name, display_price = item.split("$")

        is_seller = interaction.user.get_role(1145959138602524672) is not None
        is_exclusive = interaction.user.get_role(1146357576389378198) is not None
        if not is_seller and not is_exclusive:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        stock_collection = self.bot.database.get_collection("stock")

        if not stock_collection.find_one({"item": name}):
            await interaction.response.send_message("This item does not exist.", ephemeral=True)
            return

        stock_collection.delete_one({"item": name})

        remove_item_embed = discord.Embed(
            color=0x77ABFC,
            description=f"Removed **{name}** from the stock.",
            timestamp=discord.utils.utcnow(),
        )

        remove_item_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
        remove_item_embed.set_footer(text=f"${display_price}")

        await interaction.response.send_message(embed=remove_item_embed)

    @log.autocomplete("item")
    @restock.autocomplete("item")
    @updateitem.autocomplete("item")
    @delitem.autocomplete("item")
    async def stock_autocompletion(self, interaction: discord.Interaction, current: str) -> List[apc.Choice[str]]:
        data = []

        stock_collection = self.bot.database.get_collection("stock")
        stock = stock_collection.find({})

        for doc in stock:
            item = doc["item"]
            price = doc["price"]
            quantity = doc["quantity"]

            if current.lower() in item.lower():
                display_item = f"{item} (${price})"
                if quantity < 1:
                    data.append(apc.Choice(name=f"{display_item} — Out of Stock", value=f"{item}$0"))
                else:
                    data.append(apc.Choice(name=f"{display_item} — {quantity}x", value=f"{item}${price:,}"))

        return data

    @tasks.loop(minutes=10)
    async def update_channels(self) -> None:
        earned_channel = self.bot.get_channel(1146378858451435540)
        sales_channel = self.bot.get_channel(1146378711088775219)

        log_collection = self.bot.database.get_collection("logs")
        logs = log_collection.find({})

        # Don't touch!
        starting_sales = 100

        combined_earnings = sum([log["item"]["price"] for log in logs])
        combined_sales = starting_sales + log_collection.count_documents({})

        await earned_channel.edit(name=f"Earned: ${combined_earnings:,}")
        await sales_channel.edit(name=f"Sales: {combined_sales:,}")
