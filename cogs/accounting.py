import locale
from typing import Optional
from bson import ObjectId

import discord
from discord import app_commands as apc
from discord.ext import commands, tasks
import pymongo
from pymongo.collection import Collection
import locale

from _types import Log, Stock
from bot import Bot
from utils import parse_cash_app_receipt, write_to_ws
from constants import *
from views.payment import PaymentButtons

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
price_fmt = lambda price: locale.currency(price, grouping=True)

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

    cash = apc.Group(name="cash", description="Cash App")
    item = apc.Group(name="item", description="Manages stock items.")
    log = apc.Group(name="log", description="Manages purchase logs.")

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
        discount: Optional[float] = 0.0,
        item2: Optional[str] = None,
        item3: Optional[str] = None,
        item4: Optional[str] = None,
        item5: Optional[str] = None,
    ) -> None:
        """Logs a sale and updates channel info.

        Parameters
        ___________
        customer : discord.Member
            The member who bought the item.
        username : str
            The Roblox username of the user.
        method : app_commands.Choice[str]
            The payment method used.
        info : str
            The customer's payment info.
        item1 : str
            Item 1
        discount : Optional[float]
            The discount applied to the full purchase.
        item2 : Optional[str]
            Item 2
        item3 : Optional[str]
            Item 3
        item4 : Optional[str]
            Item 4
        item5 : Optional[str]
            Item 5
        """

        await interaction.response.defer()

        is_staff = self.bot.config.roles.staff in interaction.user.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        items = [stock_collection.find_one({"_id": ObjectId(item_id)}) for item_id in [item1, item2, item3, item4, item5] if item_id != None]

        purchase_log = await self.log_purchase(
            customer=customer,
            username=username,
            method=method,
            info=info,
            items=items,
            discount=discount
        )
            
        embed = discord.Embed(
            color=0x599ae0,
            description=f"View the purchase log here: {purchase_log.jump_url}"
        )
        
        embed.set_author(
            name=f"Payment Completed",
            icon_url=ICONS.ticket
        )

        await interaction.followup.send(embed=embed)

    @commands.hybrid()
    @commands.guild_only()
    async def stock(self, ctx: commands.Context) -> None:
        """Displays the curent available stock."""

        is_staff = self.bot.config.roles.staff in ctx.author.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")

        stock_embed = discord.Embed(color=0x77ABFC, title="Stock")
        for stock_item in stock_collection.find({"name": {"$regex": "Set$"}}).sort("name"):
            name = stock_item["name"]
            price = stock_item["price"]

            stock_embed.add_field(name=f"{name} (${price:,})", value="")
        stock_embed.add_field(name="Miscellaneous", value="")

        for stock_item in stock_collection.find({"name": {"$not": {"$regex": "Set$"}}}).sort("price", pymongo.DESCENDING):
            name = stock_item["name"]
            price = stock_item["price"]
            quantity = stock_item["quantity"]

            set_name, _ = name.rsplit(" ", 1)
            i, field = next(((i, field) for (i, field) in enumerate(stock_embed.fields) if field.name.rsplit(" ", 1)[0] == f"{set_name} Set"), (-1, stock_embed.fields[-1]))

            field.value += f"\n- {name} - ${price:,} "

            if quantity >= 1:
                field.value += f"`{quantity}x`"
            else:
                field.value += "`\N{CROSS MARK}`"
            
            stock_embed.set_field_at(i, name=field.name, value=field.value, inline=False)

        if not stock_embed.fields[-1].value:
            stock_embed.remove_field(-1)

        await ctx.send(embed=stock_embed)

    @apc.command()
    @apc.guild_only()
    async def restock(self, interaction: discord.Interaction, item: str, quantity: int) -> None:
        """Updates the a stock amount.

        Parameters
        ___________
        item : app_commands.Choice[str]
            The item that was restocked.
        quantity : app_commands.Choice[str]
            The amount that was restocked
        """

        is_staff = self.bot.config.roles.staff in interaction.user.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"_id": ObjectId(item)})

        if stock_item is None:
            raise commands.BadArgument("This item does not exist.")

        await interaction.response.defer()

        name = stock_item["name"]
        price = stock_item["price"]
        combined_quantity = stock_item["quantity"] + quantity

        stock_collection.update_one(stock_item, {"$inc": {"quantity": quantity}})

        restock_embed = discord.Embed(
            color=0x77ABFC,
            description=f"Restocked **{name}** by **{quantity}x** ({combined_quantity} Total)",
            timestamp=discord.utils.utcnow(),
        )

        restock_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
        restock_embed.set_footer(text=f"${price:,}")

        await interaction.followup.send(embed=restock_embed)

    @apc.command()
    @apc.guild_only()
    async def clearstock(self, interaction: discord.Interaction) -> None:
        """Clears the stock list."""

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock = stock_collection.find()

        for stock_item in stock:
            stock_collection.update_one(stock_item, {"$set": {"quantity": 0}})

        await interaction.response.send_message("Cleared the stock.", ephemeral=True)

    @apc.command()
    @apc.guild_only()
    async def fillstock(self, interaction: discord.Interaction, amount: int) -> None:
        """Fills the stock list.

        Parameters
        ___________
        amount : int
            The amount to fill the stock with.
        """

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock = stock_collection.find()

        for stock_item in stock:
            stock_collection.update_one(stock_item, {"$set": {"quantity": amount}})

        await interaction.response.send_message(f"Filled the stock with **{amount}x** per item.", ephemeral=True)

    @item.command()
    @apc.guild_only()
    async def add(self, interaction: discord.Interaction, name: str, price: int, quantity: int) -> None:
        """Adds an item to the stock list.

        Parameters
        ___________
        name : str
            The name of the new item.
        price : int
            The price of the item.
        quantity : int
            The amount of the item in stock.
        """

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"name": name})

        if stock_item is not None:
            raise commands.BadArgument("This item already exists.")

        stock_item = Stock(name=name, price=price, quantity=quantity)
        stock_collection.insert_one(stock_item)

        item_embed = discord.Embed(
            color=0x77ABFC,
            title=f"Added {name}",
            timestamp=discord.utils.utcnow(),
        )

        item_embed.add_field(name="Name", value=f"```{name}```", inline=True)
        item_embed.add_field(name="Price", value=f"```${price:,}```", inline=True)
        item_embed.add_field(name="In Stock", value=f"```{quantity}```", inline=True)

        await interaction.response.send_message(embed=item_embed)

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
        item : str
            The name of the item to update.
        name : Optional[str]
            The new name of the item.
        price : Optional[int]
            The new price of the item.
        quantity : Optional[int]
            The new amount of the item.
        """

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"_id": ObjectId(item)})

        if stock_item is None:
            raise commands.BadArgument("This item does not exist.")

        if any([name, price, quantity]) is False:
            raise commands.BadArgument("You must specify at least one attribute to update.")
        
        old_name = stock_item["name"]
        old_price = stock_item["price"]
        old_quantity = stock_item["quantity"]
        
        new_item = stock_item.copy()

        item_embed = discord.Embed(
            color=0x77ABFC,
            title=f"Updated {old_name}",
            timestamp=discord.utils.utcnow(),
        )

        item_embed.add_field(name="Name", value=f"```{name or old_name}```", inline=True)
        item_embed.add_field(name="Price", value=f"```${price or old_price:,}```", inline=True)
        item_embed.add_field(name="In Stock", value=f"```{quantity or old_quantity}```", inline=True)

        if price is not None:
            new_item["price"] = price

            if old_price != price:
                updates_channel = self.bot.config.channels.updates

                price_icon = "📈" if price > old_price else "📉"
                price_embed = discord.Embed(
                    color=0x77ABFC,
                    title=f"{price_icon} Price Updated",
                    description=f"**{new_item['name']}** has been updated from **${old_price:,}** to **${price:,}**.",
                )

                await updates_channel.send(content="<@&1167290712220504064>", embed=price_embed)

        if quantity is not None:
            new_item["quantity"] = quantity

        stock_collection.update_one(stock_item, {"$set": new_item})

        await interaction.response.send_message(embed=item_embed)

    @item.command()
    @apc.guild_only()
    async def delete(self, interaction: discord.Interaction, item: str) -> None:
        """Removes an item from the stock list.

        Parameters
        ___________
        item : str
            The name of the item to remove.
        """

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"_id": ObjectId(item)})

        if stock_item is None:
            raise commands.BadArgument("This item does not exist.")

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

    @cash.command()
    @apc.guild_only()
    async def app(
        self,
        interaction: discord.Interaction,
        item1: str,
        discount: Optional[float] = 0.0,
        item2: Optional[str] = None,
        item3: Optional[str] = None,
        item4: Optional[str] = None,
        item5: Optional[str] = None,
    ) -> None:
        """Sends the Cash App payment panel.
        
        Parameters
        ___________
        item1 : str
            Item 1
        discount : Optional[float]
            The discount applied to the full purchase.
        item2 : Optional[str]
            Item 2
        item3 : Optional[str]
            Item 3
        item4 : Optional[str]
            Item 4
        item5 : Optional[str]
            Item 5
        """

        await interaction.response.defer()

        is_staff = self.bot.config.roles.staff in interaction.user.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        embed = discord.Embed(
            color=0x00c853,
            title="Cash App",
            description="<:BS_CashApp:1146371930228801566> Make sure to send with **Cash Balance** and **include the note** in your payment. After you're done, click the button below.",
        )

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        items = [stock_collection.find_one({"_id": ObjectId(item_id)}) for item_id in [item1, item2, item3, item4, item5] if item_id != None]
        
        total = self.calc_total(items, discount)
        amount_due = locale.currency(total, grouping=True)

        embed.add_field(name='Cashtag', value='```$ehxpulse```', inline=True)
        embed.add_field(name='Amount', value=f'```{amount_due}```', inline=True)
        embed.add_field(name='Note', value=f'```gift```', inline=True)
        embed.set_thumbnail(url='https://cash.app/qr/$ehxpulse')
        embed.set_image(url="https://cdn.discordapp.com/attachments/1150184910640918629/1174187738765992038/pay-image.png")

        view = PaymentButtons()
        
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        
        await view.wait()

        customer = view.modal.interaction.user
        username = view.modal.username.value
        web_receipt = view.modal.web_receipt.value

        info, success = await parse_cash_app_receipt(web_receipt)

        await view.modal.interaction.delete_original_response()

        if success is False:
            raise Exception(info)
        
        received = float(info.replace('$', ''))

        if received < total:
            raise Exception(f"You did not pay the full amount. You paid **{info}** but the total is **{amount_due}**.")
        
        purchase_log = await self.log_purchase(
            customer=customer,
            username=username,
            method=apc.Choice(name="Cash App", value="cashapp_receipt"),
            info=web_receipt,
            items=items,
            discount=discount
        )

        embed = discord.Embed(
            color=0x599ae0,
            description=f"View the purchase log here: {purchase_log.jump_url}"
        )
        
        embed.set_author(
            name=f"Payment Received",
            icon_url=ICONS.ticket
        )

        await message.reply(embed=embed)

    def calc_total(self, items: list[Stock], discount: Optional[float] = 0.0) -> float:
        """Calculates the total price of a purchase."""

        total_price = -abs(discount)

        for item in items:
            price = item["price"]
            quantity = item["quantity"]

            if quantity >= 1:
                total_price += price

        return total_price

    async def log_purchase(
        self,
        customer: discord.Member,
        username: str,
        method: apc.Choice[str],
        info: str,
        items: list[Stock],
        discount: Optional[float] = 0.0
    ) -> tuple[float, discord.Message]:
        """Logs a purchase and updates channel info."""

        log_collection: Collection[Log] = self.bot.database.get_collection("logs")
        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        log_channel = self.bot.config.channels.purchases
    
        total = self.calc_total(items, discount)

        item_names: list[str] = []
        for item in items:
            name = item["name"]
            price = item["price"]

            stock_collection.update_one(item, {"$inc": {"quantity": -1}})

            log = Log(user_id=customer.id, username=username, item=item)
            log[method.value] = info

            item_names.append(name)
            log_collection.insert_one(log)

            itemized_discount = discount / len(items)
            total -= itemized_discount
            
            try:
                write_to_ws(username, customer.id, name, price - itemized_discount)
                reaction = '\N{WHITE HEAVY CHECK MARK}'
            except Exception:
                reaction = '\N{CROSS MARK}'

        log_count = log_collection.count_documents({"user_id": customer.id})
        user_logs = log_collection.find({"user_id": customer.id})
        total_spent = sum([log["item"]["price"] for log in user_logs])

        discount_tag = f" (-{price_fmt(discount)})" if discount > 0 else ""

        log_embed = discord.Embed(
            color=0x77ABFC,
            description=f"{customer.mention} (`{customer.id}`) purchased **{'**, **'.join(item_names)}** for **{price_fmt(total)}**{discount_tag}.",
        )

        if method.value == "cashapp_receipt":
            info = f"[Web Receipt]({info})"

        log_embed.set_author(name=f"{customer}", icon_url=f"{customer.display_avatar.url}")
        log_embed.add_field(name=f"__Username__", value=username, inline=True)
        log_embed.add_field(name=f"__{method.name}__", value=info, inline=True)
        log_embed.add_field(name=f"__Total Spent__", value=f"{price_fmt(total)}", inline=True)
        log_embed.set_footer(text=f"Transaction #{log_count}")

        customer_role = self.bot.config.roles.customer
        await customer.add_roles(customer_role)

        tier_role = None
        if total_spent >= 100:
            tier_role = self.bot.config.roles.tier1
        if total_spent >= 250:
            tier_role = self.bot.config.roles.tier2
        if total_spent >= 500:
            tier_role = self.bot.config.roles.tier3
        if total_spent >= 1000:
            tier_role = self.bot.config.roles.tier4
        if total_spent >= 1500:
            tier_role = self.bot.config.roles.tier5

        if tier_role:
            await customer.add_roles(tier_role, reason=f"Spent ${total_spent:,}")

        message = await log_channel.send(embed=log_embed)
        await message.add_reaction(reaction)
        return message
        
    # Cash App
    @app.autocomplete("item1")
    @app.autocomplete("item2")
    @app.autocomplete("item3")
    @app.autocomplete("item4")
    @app.autocomplete("item5")
    # Logs
    @create.autocomplete("item1")
    @create.autocomplete("item2")
    @create.autocomplete("item3")
    @create.autocomplete("item4")
    @create.autocomplete("item5")
    # Stock
    @restock.autocomplete("item")
    # Updates
    @update.autocomplete("item")
    @delete.autocomplete("item")
    async def stock_autocompletion(self, interaction: discord.Interaction, current: str) -> list[apc.Choice[str]]:
        """Autocompletes stock items."""

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

    @tasks.loop(minutes=10)
    async def update_channels(self) -> None:
        """Updates the sales and earnings channels."""

        sales_channel = self.bot.config.channels.sales
        earnings_channel = self.bot.config.channels.earnings

        log_collection: Collection[Log] = self.bot.database.get_collection("logs")
        logs = log_collection.find()

        # Don't touch!
        starting_sales = 99

        combined_sales = starting_sales + log_collection.count_documents({})
        combined_earnings = sum([log["item"]["price"] for log in logs])

        await sales_channel.edit(name=f"Sales: {combined_sales:,}")
        await earnings_channel.edit(name=f"Earned: ${combined_earnings:,}")

    @tasks.loop(minutes=10)
    async def update_stock_embed(self) -> None:
        """Updates the stock embed."""

        stock_channel = self.bot.config.channels.shop

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")

        stock_embed = discord.Embed(color=0x77ABFC, title="Stock", timestamp=discord.utils.utcnow())
        stock_embed.set_footer(text="Last Updated")
        
        for stock_item in stock_collection.find({"name": {"$regex": "Set$"}}).sort("name"):
            name = stock_item["name"]
            price = stock_item["price"]

            stock_embed.add_field(name=f"{name} (${price})", value="")
        stock_embed.add_field(name="Miscellaneous", value="")

        for stock_item in stock_collection.find({"name": {"$not": {"$regex": "Set$"}}}).sort("price", pymongo.DESCENDING):
            name = stock_item["name"]
            price = stock_item["price"]
            quantity = stock_item["quantity"]

            set_name, _ = name.rsplit(" ", 1)
            i, field = next(((i, field) for (i, field) in enumerate(stock_embed.fields) if field.name.rsplit(" ", 1)[0] == f"{set_name} Set"), (-1, stock_embed.fields[-1]))

            field.value += f"\n- {name} - ${price:,} "

            if quantity >= 1:
                field.value += f"`{quantity}x`"
            else:
                field.value += "`\N{CROSS MARK}`"
        
            stock_embed.set_field_at(i, name=field.name, value=field.value, inline=False)

        if not stock_embed.fields[-1].value:
            stock_embed.remove_field(-1)

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
        """Waits for the bot to be ready."""
        await self.bot.wait_until_ready()


async def setup(bot: Bot):
    await bot.add_cog(Accounting(bot))
