from collections import defaultdict
from typing import Optional

import discord
from bson import ObjectId
from discord import app_commands as apc
from discord.ext import commands, tasks
from pymongo.collection import Collection

from _types import Log, Stock
from bot import Bot
from constants import *


class Accounting(commands.Cog):
    """Commands for accounting stock and payment logs."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.update_channels.start()
        self.update_stock_embed.start()

    item = apc.Group(name="item", description="Manages stock items")
    log = apc.Group(name="log", description="Manages logs")

    @log.command()
    @apc.guild_only()
    async def scam(
        self,
        interaction: discord.Interaction,
        username: str,
        user_id: str,
        reporter: discord.Member,
        reason: str,
        proof: discord.Attachment
    ) -> None:
        """Logs a scam report.

        Parameters
        ___________
        username : str
            The username of the scammer.
        user_id : str
            The user ID of the scammer.
        reporter : discord.Member
            The member who reported the scam.
        reason : str
            The reason for the scam report.
        proof : discord.Attachment
            The proof of the scam.
        """

        await interaction.response.defer()

        is_staff = self.bot.config.roles.staff in interaction.user.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        embed = discord.Embed(
            color=0xff4f4f,
            title="Scam Report",
            timestamp=discord.utils.utcnow(),
        )

        embed.add_field(name="Username", value=username, inline=True)
        embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
        embed.add_field(name="Reporter", value=reporter.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)

        embed.set_image(url=proof.url)
        embed.set_footer(text=interaction.guild.name, icon_url=interaction.guild.icon)
        
        scams_channel = self.bot.config.channels.scams
        message = await scams_channel.send(embed=embed)

        embed = discord.Embed(
            color=0x599ae0,
            description=f"View the scam log here: {message.jump_url}"
        )

        await interaction.followup.send(embed=embed)

    @commands.hybrid_command()
    @commands.guild_only()
    async def stock(self, ctx: commands.Context) -> None:
        """Displays the curent available stock."""

        await ctx.defer()

        is_staff = self.bot.config.roles.staff in ctx.author.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        stock_embed = self.create_stock_embed()
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

        await interaction.response.defer()

        is_staff = self.bot.config.roles.staff in interaction.user.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"_id": ObjectId(item)})

        if stock_item is None:
            raise commands.BadArgument("This item does not exist.")

        set = stock_item.get("set", "")
        name = stock_item["name"]
        price = stock_item["price"]
        combined_quantity = stock_item["quantity"] + quantity

        stock_collection.update_one(stock_item, {"$inc": {"quantity": quantity}})

        restock_embed = discord.Embed(
            color=0x77ABFC,
            description=f"Restocked **{set} {name}** by `{quantity}` ({combined_quantity} Total)",
            timestamp=discord.utils.utcnow(),
        )

        restock_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar)
        restock_embed.set_footer(text=f"${price:,}")

        await interaction.followup.send(embed=restock_embed)

    @apc.command()
    @apc.guild_only()
    async def clearstock(self, interaction: discord.Interaction) -> None:
        """Clears the stock list."""

        await interaction.response.defer()

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        for stock_item in stock_collection.find():
            stock_collection.update_one(stock_item, {"$set": {"quantity": 0}})

        await interaction.followup.send("Cleared the stock.", ephemeral=True)

    @apc.command()
    @apc.guild_only()
    async def fillstock(self, interaction: discord.Interaction, amount: int) -> None:
        """Fills the stock list.

        Parameters
        ___________
        amount : int
            The amount to fill the stock with.
        """

        await interaction.response.defer()

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        for stock_item in stock_collection.find():
            stock_collection.update_one(
                stock_item, {"$set": {"quantity": amount}})

        await interaction.followup.send(f"Filled the stock with `{amount}` per item.", ephemeral=True)

    @item.command()
    @apc.guild_only()
    async def add(self, interaction: discord.Interaction, name: str, price: int, quantity: int, set: Optional[str]) -> None:
        """Adds an item to the stock list.

        Parameters
        ___________
        name : str
            The name of the new item.
        price : int
            The price of the item.
        quantity : int
            The amount of the item in stock.
        set : Optional[str]
            The set the item belongs to.
        """

        await interaction.response.defer()

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"set": set, "name": name})

        if stock_item is not None:
            raise commands.BadArgument("This item already exists.")

        stock_item = Stock(set=set, name=name, price=price, quantity=quantity)
        stock_collection.insert_one(stock_item)

        item_embed = discord.Embed(
            color=0x77ABFC,
            title=f"Added {set} {name}",
            timestamp=discord.utils.utcnow(),
        )

        item_embed.add_field(name="Set", value=f"```{set}```", inline=True)
        item_embed.add_field(name="Name", value=f"```{name}```", inline=True)
        item_embed.add_field(name="Price", value=f"```${price:,}```", inline=True)
        item_embed.add_field(name="In Stock", value=f"```{quantity}```", inline=True)

        await interaction.followup.send(embed=item_embed)

    @item.command()
    @apc.guild_only()
    async def update(
        self,
        interaction: discord.Interaction,
        item: str,
        set: Optional[str],
        name: Optional[str],
        price: Optional[int],
        quantity: Optional[int],
    ) -> None:
        """Updates an item in the stock list.

        Parameters
        ___________
        item : str
            The name of the item to update.
        set : Optional[str]
            The new set of the item.
        name : Optional[str]
            The new name of the item.
        price : Optional[int]
            The new price of the item.
        quantity : Optional[int]
            The new amount of the item.
        """

        await interaction.response.defer()

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"_id": ObjectId(item)})

        if stock_item is None:
            raise commands.BadArgument("This item does not exist.")

        if any([name, price, quantity]) is False:
            raise commands.BadArgument("You must specify at least one attribute to update.")

        old_set = stock_item.get("set", "")
        old_name = stock_item["name"]
        old_price = stock_item["price"]
        old_quantity = stock_item["quantity"]

        new_item = stock_item.copy()

        item_embed = discord.Embed(
            color=0x77ABFC,
            title=f"Updated {old_name}",
            timestamp=discord.utils.utcnow(),
        )

        item_embed.add_field(name="Set", value=f"```{set or old_set}```", inline=True)
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
                    description=f"**{new_item['set']} {new_item['name']}** has been updated from **${old_price:,}** to **${price:,}**.",
                )

                await updates_channel.send(content="<@&1167290712220504064>", embed=price_embed)

        if quantity is not None:
            new_item["quantity"] = quantity

        stock_collection.update_one(stock_item, {"$set": new_item})
        await interaction.followup.send(embed=item_embed)

    @item.command()
    @apc.guild_only()
    async def delete(self, interaction: discord.Interaction, item: str) -> None:
        """Removes an item from the stock list.

        Parameters
        ___________
        item : str
            The name of the item to remove.
        """

        await interaction.response.defer()

        is_owner = interaction.user.id in self.bot.config.owner_ids
        if not is_owner:
            raise Exception("You do not have permission to use this command.")

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        stock_item = stock_collection.find_one({"_id": ObjectId(item)})

        if stock_item is None:
            raise commands.BadArgument("This item does not exist.")

        set = stock_item.get("set", "")
        name = stock_item["name"]
        price = stock_item["price"]

        stock_collection.delete_one(stock_item)

        remove_item_embed = discord.Embed(
            color=0x77ABFC,
            description=f"Removed **{set} {name}** from the stock.",
            timestamp=discord.utils.utcnow(),
        )

        remove_item_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar)
        remove_item_embed.set_footer(text=f"${price:,}")

        await interaction.followup.send(embed=remove_item_embed)

    def calc_total(self, items: list[Stock], discount: Optional[float] = 0.0) -> float:
        """Calculates the total price of a purchase."""

        total_price = -abs(discount)

        for item in items:
            total_price += item["price"]

        return total_price

    # Stock
    @restock.autocomplete("item")
    # Updates
    @update.autocomplete("item")
    @delete.autocomplete("item")
    async def stock_autocompletion(self, interaction: discord.Interaction, current: str) -> list[apc.Choice[str]]:
        """Autocompletes stock items."""

        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")

        choices = []
        for item in stock_collection.find().sort("name"):
            objectId = item["_id"]
            set_name = item.get("set", "")
            name = item["name"]
            price = item["price"]
            quantity = item["quantity"]

            if current.lower() in f"{set_name} {name}".strip().lower():
                display_item = f"{set_name} {name} (${price})"
                if quantity < 1:
                    choices.append(apc.Choice(name=f"{display_item} | Out of Stock", value=str(objectId)))
                else:
                    choices.append(apc.Choice(name=f"{display_item} | Stock: {quantity}", value=str(objectId)))

        return choices[:25]
            
    def create_stock_embed(self):
        stock_collection: Collection[Stock] = self.bot.database.get_collection("stock")
        sets = defaultdict(lambda: {"price": 0, "items": []})

        stock_embed = discord.Embed(color=0x77ABFC, title="Bry's Shop Stock", timestamp=discord.utils.utcnow())
        stock_embed.set_footer(text="Last Updated")
        
        for stock_item in stock_collection.find().sort("set"):
            set_name = stock_item.get("set") or "Other"
            price = stock_item["price"]

            sets[set_name]["price"] += price
            sets[set_name]["items"].append(stock_item)

        for set_name, data in sets.items():
            name = stock_item["name"]
            price = stock_item["price"]
            quantity = stock_item["quantity"]

            items: list[Stock] = data["items"]
            items.sort(key=lambda x: x["price"])

            field_value = ""
            for item in items:
                name = item["name"]
                price = item["price"]
                quantity = item["quantity"]

                field_template = f"` ${price:,} ` {name}"

                if quantity >= 1:
                    field_value += f"\n- {field_template} ` Stock: {quantity} `"
                else:
                    field_value += f"\n- {field_template} ` Out of Stock `"

            stock_embed.add_field(name=set_name, value=field_value, inline=False)

        stock_embed._fields.append(stock_embed._fields.pop(0))
        return stock_embed

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
        stock_embed = self.create_stock_embed()
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
