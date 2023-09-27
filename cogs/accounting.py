from typing import Optional

import discord
from bson import ObjectId
from discord import app_commands as apc
from discord.ext import commands, tasks
from pymongo.collection import Collection

from _types import Log, Stock
from bot import Bot

OWNER_IDS = [525189552986521613, 1092543812527738911, 997958244452544582]


class Accounting(commands.Cog):
    """Commands for accounting stock and payment logs."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.update_channels.start()
        self.update_stock_embed.start()

    methods = [
        apc.Choice(name="PayPal", value="paypal_email"),
        apc.Choice(name="Cash App", value="cashapp_tag"),
        apc.Choice(name="Venmo", value="venmo_username"),
        apc.Choice(name="Stripe", value="stripe_email"),
        apc.Choice(name="BTC", value="btc_address"),
        apc.Choice(name="LTC", value="ltc_address"),
        apc.Choice(name="ETH", value="eth_address"),
    ]

    log = apc.Group(name="log", description="Manages a purchase log.")
    item = apc.Group(name="item", description="Manages a stock item.")

    @log.command()
    @apc.guild_only()
    @apc.choices(method=methods)
    async def create(
        self,
        interaction: discord.Interaction,
        customer: discord.Member,
        username: str,
        method: apc.Choice[str],
        info: str,
        item1: str,
        item2: Optional[str],
        item3: Optional[str],
        item4: Optional[str],
        item5: Optional[str],
    ) -> None:
        """Logs a sale and updates channel info.

        Parameters
        ___________
        customer: discord.Member
            The member who bought the item.
        username: str
            The Roblox username of the user.
        method: app_commands.Choice[str]
            The payment method used.
        info: str
            The payment info provided.
        item1: str
            Item 1
        item2: Optional[str]
            Item 2
        item3: Optional[str]
            Item 3
        item4: Optional[str]
            Item 4
        item5: Optional[str]
            Item 5"""

        is_support = interaction.user.get_role(1145965467207467049)
        if not is_support:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer()

        customer_role = interaction.guild.get_role(1145959140594810933)
        log_channel = self.bot.get_channel(1151322058941267968)

        log_collection: Collection[Log] = self.bot.database.get_collection("logs")
        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")

        combined_items = [item1, item2, item3, item4, item5]
        item_ids: list[str] = [item for item in combined_items if item is not None]

        total_price = 0
        item_names: list[str] = []

        invalid_items: list[str] = []
        out_of_stock: list[str] = []

        for item in item_ids:
            stock_item = stock_collection.find_one({"_id": ObjectId(item)})

            if stock_item is None:
                invalid_items.append(item)
                continue

            name = stock_item["name"]
            price = stock_item["price"]
            quantity = stock_item["quantity"]

            if quantity < 1:
                out_of_stock.append(name)
                continue

            total_price += price
            item_names.append(name)

            stock_collection.update_one(stock_item, {"$inc": {"quantity": -1}})

            log = Log(user_id=customer.id, username=username, item=stock_item)
            log[method.value] = info

            log_collection.insert_one(log)

        user_logs = log_collection.find({"user_id": customer.id})
        log_count = log_collection.count_documents({"user_id": customer.id})
        total_spent = sum([log["item"]["price"] for log in user_logs])

        if total_price >= 100:
            valued_role = interaction.guild.get_role(1156319778810646579)
            await customer.add_roles(valued_role)

        if total_spent >= 250:
            vip_role = interaction.guild.get_role(1145959139432992829)
            await customer.add_roles(vip_role)

        if total_spent >= 500:
            high_value_role = interaction.guild.get_role(1156319772640817242)
            await customer.add_roles(high_value_role)

        if total_spent >= 1000:
            notable_role = interaction.guild.get_role(1145959137453285416)
            await customer.add_roles(notable_role)

        log_embed = discord.Embed(
            color=0x77ABFC,
            description=f"{customer.mention} (`{customer.id}`) purchased **{'**, **'.join(item_names)}** for **${total_price:,}**.",
        )

        log_embed.set_author(name=f"{customer}", icon_url=f"{customer.display_avatar.url}")
        log_embed.add_field(name=f"__Username__", value=username, inline=True)
        log_embed.add_field(name=f"__{method.name}__", value=info, inline=True)
        log_embed.add_field(name=f"__Total Spent__", value=f"${total_spent:,}", inline=True)
        log_embed.set_footer(text=f"Transaction #{log_count}")

        chat_embed = discord.Embed(
            color=0x77ABFC,
            description=f"""**__Info__**
Items → {", ".join(item_names)}
Total Price → ${total_price:,}
Username → {username}
Payment Method → {method.name}
            """,
        )

        chat_embed.set_footer(text=info)

        error_embed = discord.Embed(
            color=0xE24C4B,
            description="**__Failed__**",
        )

        if invalid_items:
            error_embed.description += f"\nInvalid Items → {len(invalid_items)}"

        if out_of_stock:
            error_embed.description += f"\nOut of Stock → {', '.join(out_of_stock)}"

        embeds = [chat_embed]
        if invalid_items or out_of_stock:
            embeds.insert(0, error_embed)

        await customer.add_roles(customer_role)
        await log_channel.send(embed=log_embed)
        await interaction.followup.send(embeds=embeds)

    @apc.command()
    @apc.guild_only()
    async def stock(self, interaction: discord.Interaction) -> None:
        """Displays the curent available stock."""

        is_support = interaction.user.get_role(1145965467207467049)
        if not is_support:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")

        stock_items = []
        for stock_item in stock_collection.find().sort("name"):
            name = stock_item["name"]
            price = stock_item["price"]
            quantity = stock_item["quantity"]

            if quantity < 1:
                continue

            display_item = f"- **{name}** (${price:,}) — **{quantity}x**"
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

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"_id": ObjectId(item)})

        if stock_item is None:
            await interaction.response.send_message("This item does not exist.", ephemeral=True)
            return

        await interaction.response.defer()

        name = stock_item["name"]
        price = stock_item["price"]
        combined_quantity = stock_item["quantity"] + quantity

        stock_collection.update_one(stock_item, {"$inc": {"quantity": quantity}})

        restock_embed = discord.Embed(
            color=0x77ABFC,
            description=f"Restocked **{name}** with **{quantity}x** → {combined_quantity} Total",
            timestamp=discord.utils.utcnow(),
        )

        restock_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
        restock_embed.set_footer(text=f"${price:,}")

        await interaction.followup.send(embed=restock_embed)

    @item.command()
    @apc.guild_only()
    async def add(self, interaction: discord.Interaction, name: str, price: int, quantity: int) -> None:
        """Adds an item to the stock list.

        Parameters
        ___________
        name: str
            The name of the new item.
        price: int
            The price of the item.
        quantity: int
            The amount of the item in stock."""

        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"name": name})

        if stock_item is not None:
            await interaction.response.send_message("This item already exists.", ephemeral=True)
            return

        stock_item = Stock(name=name, price=price, quantity=quantity)
        stock_collection.insert_one(stock_item)

        add_item_embed = discord.Embed(
            color=0x77ABFC,
            description=f"Added **{quantity}x** **{name}** to the stock for **${price:,}**.",
            timestamp=discord.utils.utcnow(),
        )

        add_item_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=add_item_embed)

    @item.command()
    @apc.guild_only()
    async def update(
        self,
        interaction: discord.Interaction,
        item: str,
        name: Optional[str],
        price: Optional[int],
        quantity: Optional[int],
    ) -> None:
        """Updates an item in the stock list.

        Parameters
        ___________
        item: str
            The name of the item to update.
        name: Optional[str]
            The new name of the item.
        price: Optional[int]
            The new price of the item.
        quantity: Optional[int]
            The new amount of the item."""

        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"_id": ObjectId(item)})

        if stock_item is None:
            await interaction.response.send_message("This item does not exist.", ephemeral=True)
            return

        if any([name, price, quantity]) is False:
            await interaction.response.send_message("You must provide at least 1 field to update.", ephemeral=True)
            return

        updated_item = stock_item.copy()
        description = f"**__Info__**"

        if name is not None:
            updated_item["name"] = name
            description += f"\nName → {name}"

        if price is not None:
            updated_item["price"] = price
            description += f"\nPrice → ${price:,}"

        if quantity is not None:
            updated_item["quantity"] = quantity
            description += f"\nQuantity → {quantity}"

        stock_collection.update_one(stock_item, {"$set": updated_item})

        update_item_embed = discord.Embed(
            color=0x77ABFC,
            description=description,
            timestamp=discord.utils.utcnow(),
        )

        update_item_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=update_item_embed)

    @item.command()
    @apc.guild_only()
    async def delete(self, interaction: discord.Interaction, item: str) -> None:
        """Removes an item from the stock list.

        Parameters
        ___________
        item: str
            The name of the item to remove."""

        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"_id": ObjectId(item)})

        if stock_item is None:
            await interaction.response.send_message("This item does not exist.", ephemeral=True)
            return

        name = stock_item["name"]
        price = stock_item["price"]

        stock_collection.delete_one(stock_item)

        remove_item_embed = discord.Embed(
            color=0x77ABFC,
            description=f"Removed **{name}** from the stock.",
            timestamp=discord.utils.utcnow(),
        )

        remove_item_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
        remove_item_embed.set_footer(text=f"${price:,}")

        await interaction.response.send_message(embed=remove_item_embed)

    @create.autocomplete("item1")
    @create.autocomplete("item2")
    @create.autocomplete("item3")
    @create.autocomplete("item4")
    @create.autocomplete("item5")
    @restock.autocomplete("item")
    @update.autocomplete("item")
    @delete.autocomplete("item")
    async def stock_autocompletion(self, interaction: discord.Interaction, current: str) -> list[apc.Choice[str]]:
        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")

        data = []

        for stock_item in stock_collection.find().sort("name"):
            objectId = stock_item["_id"]
            item = stock_item["name"]
            price = stock_item["price"]
            quantity = stock_item["quantity"]

            if current.lower() in item.lower():
                display_item = f"{item} (${price})"
                if quantity < 1:
                    data.append(apc.Choice(name=f"{display_item} — Out of Stock", value=str(objectId)))
                else:
                    data.append(apc.Choice(name=f"{display_item} — {quantity}x", value=str(objectId)))

        return data[:25]

    # async def log_autocompletion(self, interaction: discord.Interaction, current: str) -> list[apc.Choice[str]]:
    #     log_collection: Collection[Log] = self.bot.database.get_collection("logs")

    #     data = []

    #     for log in log_collection.find().sort("username"):
    #         objectId = log["_id"]

    #         if "username" not in log:
    #             continue

    #         username = log["username"]
    #         item = log["item"]["name"]

    #         display_item = f"{username} — {item}"
    #         if current.lower() in display_item.lower():
    #             data.append(apc.Choice(name=display_item, value=str(objectId)))

    #     return data[:25]

    @tasks.loop(minutes=10)
    async def update_channels(self) -> None:
        earned_channel = self.bot.get_channel(1146378858451435540)
        sales_channel = self.bot.get_channel(1146378711088775219)

        log_collection: Collection[Log] = self.bot.database.get_collection("logs")
        logs = log_collection.find()

        # Don't touch!
        starting_sales = 99

        combined_earnings = sum([log["item"]["price"] for log in logs])
        combined_sales = starting_sales + log_collection.count_documents({})

        await earned_channel.edit(name=f"Earned: ${combined_earnings:,}")
        await sales_channel.edit(name=f"Sales: {combined_sales:,}")

    @tasks.loop(minutes=10)
    async def update_stock_embed(self) -> None:
        stock_channel = self.bot.get_channel(1151344325893046293)

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")

        stock_items = []
        for stock_item in stock_collection.find().sort("name"):
            name = stock_item["name"]
            price = stock_item["price"]
            quantity = stock_item["quantity"]

            if quantity < 1:
                continue

            display_item = f"- **{name}** (${price:,}) — **{quantity}x**"
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


async def setup(bot: Bot):
    await bot.add_cog(Accounting(bot))
