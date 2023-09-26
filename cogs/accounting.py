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
        self.update_stock_embed.start()

    payment = [
        apc.Choice(name="PayPal", value="paypal_email"),
        apc.Choice(name="Cash App", value="cashapp_tag"),
        apc.Choice(name="Venmo", value="venmo_username"),
        apc.Choice(name="Stripe", value="stripe_email"),
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
        customer: discord.Member,
        username: str,
        item: str,
        payment: apc.Choice[str],
        info: str,
    ) -> None:
        """Logs a sale and updates channel info.

        Parameters
        ___________
        customer: discord.Member
            The member who bought the item.
        username: str
            The Roblox username of the user.
        item: app_commands.Choice[str]
            The item that was bought.
        payment: app_commands.Choice[str]
            The payment method used.
        info: str
            The payment info provided."""

        is_support = interaction.user.get_role(1145965467207467049)
        if not is_support:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        try:
            name, display_price = item.split("$")
        except ValueError:
            await interaction.response.send_message("You must provide a valid item.", ephemeral=True)
            return

        if display_price == "0":
            await interaction.response.send_message("This item is out of stock.", ephemeral=True)
            return

        customer_role = interaction.guild.get_role(1145959140594810933)
        log_channel = self.bot.get_channel(1151322058941267968)

        log_collection = self.bot.database.get_collection("logs")
        stock_collection = self.bot.database.get_collection("stock")

        filter = {"item": name}
        update = {"$inc": {"quantity": -1}}

        doc = stock_collection.find_one(filter)

        if doc is None:
            await interaction.response.send_message("This item does not exist.", ephemeral=True)
            return

        await interaction.response.defer()

        stock_collection.update_one(filter, update)

        raw_price = doc["price"]

        body = {
            "user_id": customer.id,
            "username": username,
            "item": {"name": name, "price": raw_price},
        }

        body[payment.value] = info
        log_collection.insert_one(body)

        user_logs = log_collection.find({"user_id": customer.id})
        total_count = log_collection.count_documents({"user_id": customer.id})
        total_spent = sum([log["item"]["price"] for log in user_logs])

        if total_spent >= 250:
            vip_role = interaction.guild.get_role(1145959139432992829)
            await customer.add_roles(vip_role)

        if total_spent >= 1000:
            notable_role = interaction.guild.get_role(1145959137453285416)
            await customer.add_roles(notable_role)

        log_embed = discord.Embed(
            color=0x77ABFC,
            description=f"{customer.mention} (`{customer.id}`) purchased **{name}** for **${display_price}**.",
        )

        log_embed.set_author(name=f"{customer}", icon_url=f"{customer.display_avatar.url}")
        log_embed.add_field(name=f"__Username__", value=username, inline=True)
        log_embed.add_field(name=f"__{payment.name}__", value=info, inline=True)
        log_embed.add_field(name=f"__Total Spent__", value=f"${total_spent:,}", inline=True)
        log_embed.set_footer(text=f"Transaction #{total_count}")

        chat_embed = discord.Embed(
            color=0x77ABFC,
            description=f"""**__Info__**
Item → {name}
Price → ${display_price}
Username → {username}
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

        is_support = interaction.user.get_role(1145965467207467049)
        if not is_support:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        stock_collection = self.bot.database.get_collection("stock")
        stock = stock_collection.find().sort("item")

        stock_items = []
        for doc in stock:
            item = doc["item"]
            price = doc["price"]
            quantity = doc["quantity"]

            if quantity < 1:
                continue

            display_item = f"- **{item}** (${price}) — **{quantity}x**"
            stock_items.append(display_item)

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

        is_seller = interaction.user.get_role(1145959138602524672) is not None
        is_exclusive = interaction.user.get_role(1146357576389378198) is not None
        if not is_seller and not is_exclusive:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        try:
            name, display_price = item.split("$")
        except ValueError:
            await interaction.response.send_message("You must provide a valid item.", ephemeral=True)
            return

        stock_collection = self.bot.database.get_collection("stock")

        filter = {"item": name}
        update = {"$inc": {"quantity": quantity}}

        doc = stock_collection.find_one(filter)

        if doc is None:
            await interaction.response.send_message("This item does not exist.", ephemeral=True)
            return

        stock_collection.update_one(filter, update)

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

        is_owner = interaction.user.id == 525189552986521613 or interaction.user.id == 1092543812527738911 or interaction.user.id == 997958244452544582
        if not is_owner:
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

        is_owner = interaction.user.id == 525189552986521613 or interaction.user.id == 1092543812527738911 or interaction.user.id == 997958244452544582
        if not is_owner:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        try:
            old_name, old_price = item.split("$")
        except ValueError:
            await interaction.response.send_message("You must provide a valid item.", ephemeral=True)
            return

        stock_collection = self.bot.database.get_collection("stock")
        doc = stock_collection.find_one({"item": old_name})

        if doc is None:
            await interaction.response.send_message("This item does not exist.", ephemeral=True)
            return

        filter = {"item": old_name}
        description = f"**__Info__**"

        if name is not None:
            doc["item"] = name
            description += f"\nName → {name}"

        if price is not None:
            doc["price"] = price
            description += f"\nPrice → ${price:,}"

        stock_collection.update_one(filter, {"$set": doc})

        update_item_embed = discord.Embed(
            color=0x77ABFC,
            description=description,
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

        is_owner = interaction.user.id == 525189552986521613 or interaction.user.id == 1092543812527738911 or interaction.user.id == 997958244452544582
        if not is_owner:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        try:
            name, display_price = item.split("$")
        except ValueError:
            await interaction.response.send_message("You must provide a valid item.", ephemeral=True)
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
        stock = stock_collection.find().sort("item")

        for doc in stock:
            item = doc["item"]
            price = doc["price"]
            quantity = doc["quantity"]

            if current.lower() in item.lower():
                display_item = f"{item} (${price})"
                if quantity < 1:
                    data.append(apc.Choice(name=f"{display_item} — Out of Stock", value=f"{item}$0"))
                else:
                    data.append(
                        apc.Choice(
                            name=f"{display_item} — {quantity}x",
                            value=f"{item}${price:,}",
                        )
                    )

        return data[:25]

    @tasks.loop(minutes=10)
    async def update_channels(self) -> None:
        earned_channel = self.bot.get_channel(1146378858451435540)
        sales_channel = self.bot.get_channel(1146378711088775219)

        log_collection = self.bot.database.get_collection("logs")
        logs = log_collection.find()

        # Don't touch!
        starting_sales = 99

        combined_earnings = sum([log["item"]["price"] for log in logs])
        combined_sales = starting_sales + log_collection.count_documents()

        await earned_channel.edit(name=f"Earned: ${combined_earnings:,}")
        await sales_channel.edit(name=f"Sales: {combined_sales:,}")

    @tasks.loop(minutes=10)
    async def update_stock_embed(self) -> None:
        stock_channel = self.bot.get_channel(1151344325893046293)

        stock_collection = self.bot.database.get_collection("stock")
        stock = stock_collection.find().sort("item")

        stock_items = []
        for doc in stock:
            item = doc["item"]
            price = doc["price"]
            quantity = doc["quantity"]

            if quantity < 1:
                continue

            display_item = f"- **{item}** (${price}) — **{quantity}x**"
            stock_items.append(display_item)

        display_stock = "\n".join(stock_items)

        stock_embed = discord.Embed(
            color=0x77ABFC,
            description=f"**__Stock__**\n{display_stock}",
            timestamp=discord.utils.utcnow(),
        )

        stock_embed.set_footer(text="Last Updated")

        stock_message = None
        async for message in stock_channel.history():
            if message.author == message.guild.me:
                stock_message = message
                break

        if stock_message is None:
            await stock_channel.send(embed=stock_embed)
        else:
            await stock_message.edit(embed=stock_embed)

    @update_channels.before_loop
    @update_stock_embed.before_loop
    async def before_update(self) -> None:
        await self.bot.wait_until_ready()
