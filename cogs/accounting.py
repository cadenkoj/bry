from typing import List
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

    item = [
        apc.Choice(name="Golden Age DB", value="350"),
        apc.Choice(name="Golden Age Rev", value="250"),
        apc.Choice(name="Golden Age Tanto", value="115"),
        apc.Choice(name="Golden Age Set", value="715"),
        apc.Choice(name="Web Hero II", value="100"),
        apc.Choice(name="Web Hero III", value="125"),
        apc.Choice(name="Web Hero Set", value="225"),
        apc.Choice(name="Galaxy Rev", value="55"),
        apc.Choice(name="Galaxy DB", value="55"),
        apc.Choice(name="Galaxy Tac", value="35"),
        apc.Choice(name="Galaxy Set", value="145"),
        apc.Choice(name="Matrix Rev", value="30"),
        apc.Choice(name="Matrix DB", value="30"),
        apc.Choice(name="Matrix Set", value="60"),
        apc.Choice(name="Luck Rev", value="40"),
        apc.Choice(name="Luck DB", value="35"),
        apc.Choice(name="Luck Set", value="75"),
        apc.Choice(name="Inferno Rev", value="35"),
        apc.Choice(name="Inferno DB", value="30"),
        apc.Choice(name="Inferno Set", value="65"),
        apc.Choice(name="RGB Knife", value="1700"),
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
        name, price_str = item.split("-")
        price = int(price_str)

        customer_role = interaction.guild.get_role(1150962653536198779)

        if interaction.user.get_role(1143177702954782860) is None:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer()

        log_channel = self.bot.get_channel(1150604259398787152)
        log_collection = self.bot.database.get_collection("logs")

        body = {
            "user_id": customer.id,
            "username": username,
            "item": {"name": name, "price": price},
        }

        body[payment.value] = info
        log_collection.insert_one(body)

        log_embed = discord.Embed(
            color=0x77ABFC,
            description=f"{customer.mention} (`{customer.id}`) has bought **{name}** for **${price:,}**.",
        )

        log_embed.set_author(name=customer, icon_url=customer.display_avatar.url)
        log_embed.add_field(name=f"__Username__", value=username, inline=True)
        log_embed.add_field(name=f"__{payment.name}__", value=info, inline=True)

        chat_embed = discord.Embed(
            color=0x77ABFC,
            description=f"""**__Info__**
Item → {name}
Price → {price}
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
        stock_collection = self.bot.database.get_collection("stock")
        stock = stock_collection.find_one({})

        display_stock = "\n".join(f"{v['item']} ({v['quantity']}x)" for v in stock)

        stock_embed = discord.Embed(
            color=0x77ABFC,
            description=f"**__Stock__**\n{display_stock}x",
        )

        await interaction.response.send_message(embed=stock_embed)

    @apc.command()
    @apc.guild_only()
    @apc.choices(item=item)
    async def restock(self, interaction: discord.Interaction, item: apc.Choice[str], amount: int) -> None:
        """Updates the stock.

        Parameters
        ___________
        item: app_commands.Choice[str]
            The item that was restocked.
        amount: app_commands.Choice[str]
            The amount that was restocked"""

        stock_collection = self.bot.database.get_collection("stock")

        filter = {"item": item}
        update = {"$inc": {"quantity": amount}}

        stock_collection.update_one(filter, update, upsert=True)

        restock_embed = discord.Embed(
            color=0x77ABFC,
            description=f"Restocked **{item}** with **{amount}x**.",
            timestamp=discord.utils.utcnow(),
        )

        restock_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)

    @log.autocomplete("item")
    async def stock_autocompletion(self, interaction: discord.Interaction, current: str) -> List[apc.Choice[str]]:
        data = []

        stock_collection = self.bot.database.get_collection("stock")
        stock = stock_collection.find({})

        for stock_doc in stock:
            item = stock_doc["item"]
            price = stock_doc["price"]
            quantity = stock_doc["quantity"]

            if current.lower() in item.lower():
                data.append(apc.Choice(name=f"{item} (x{quantity})", value=f"{item}-{price}"))

        return data

    @tasks.loop(minutes=10)
    async def update_channels(self) -> None:
        earned_channel = self.bot.get_channel(1150924551576879127)
        sales_channel = self.bot.get_channel(1150924530819289159)

        log_collection = self.bot.database.get_collection("logs")
        logs = log_collection.find({})

        starting_sales = 99

        combined_earnings = sum([log["item"]["price"] for log in logs])
        combined_sales = starting_sales + log_collection.count_documents({})

        await earned_channel.edit(name=f"Earned: ${combined_earnings:,}")
        await sales_channel.edit(name=f"Sales: {combined_sales:,}")
