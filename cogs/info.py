import locale

import discord
from discord.ext import commands

from bot import Bot
from views.payment import ConfirmationView
from typing import Optional

from pymongo.collection import Collection

from _types import Log

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
price_fmt = lambda price: locale.currency(price, grouping=True)


class Info(commands.Cog):
    """Commands for getting information."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def ps(self, ctx: commands.Context):
        """Send the payment note."""

        embed = discord.Embed(
            color=0x77ABFC,
            description="""
1. Join the [private server here](https://www.roblox.com/games/2788229376/Da-Hood?privateServerLinkCode=32902013200534655990932210019492).

2. Go to bank and open up your trade menu.

3. Once the trade is complete, use the picture (if provided) sent by the seller for <#1141650778021441536>.
""",
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def ts(self, ctx: commands.Context, *, user: Optional[discord.User] = None):
        """Send the total amount spent for a user.

        Parameters
        ----------
        user : Optional[discord.User]
            The user to get the total spent of.
        """

        if user is None:
            user = ctx.author._user

        log_collection: Collection[Log] = self.bot.database.get_collection("logs")

        log_count = log_collection.count_documents({"user_id": user.id})
        user_logs = log_collection.find({"user_id": user.id})
        total_spent = sum([log["item"]["price"] for log in user_logs])

        embed = discord.Embed(
            color=0x77ABFC,
        )
        embed.add_field(
            name=f"__Total Spent__", value=f"{price_fmt(total_spent)}", inline=True
        )
        embed.add_field(name=f"__Transaction Count__", value=log_count, inline=True)
        embed.set_author(name=user, icon_url=user.display_avatar.url)

        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def ltc(self, ctx: commands.Context):
        """Send the LTC address."""

        await ctx.send("LTX2cZ9DoFR2gErZdCaaLA1ovFzdNsfTmH")

    @commands.hybrid_command()
    async def btc(self, ctx: commands.Context):
        """Send the BTC address."""

        await ctx.send("bc1qcza9p80drr8wzvdpn0vzegpsglmkvgsmmukuxe")

    @commands.hybrid_command()
    async def eth(self, ctx: commands.Context):
        """Send the ETH address."""

        await ctx.send("0x7462F240169b7411fDC83C607e5C13fbcBC7E988")

    @commands.hybrid_command()
    async def paypal(self, ctx: commands.Context, amount: int):
        """Send the PayPal info."""

        is_staff = self.bot.config.roles.staff in ctx.author.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")
        
        embed = discord.Embed(
            color=0x012169,
            title="PayPal",
            description=f"""
1. Set the amount as ${amount:,}.

2. Make the note "gift", click next, and then select Friends & Family.

3. Now go to your Transactions > ${amount:,} > Print Details > Take and send a screenshot

4. Once we confirm, ping us and send your PayPal email so we can find your payment.

5. Then send your Roblox name.

6. If you understand, click the button below.
""",
        )

        paypal_button = discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="PayPal",
            url=f"https://paypal.me/korrzkorrzz?country.x=DE&locale.x=en_US",
        )
        view = ConfirmationView(paypal_button)

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command()
    async def cashapp(self, ctx: commands.Context, amount: int):
        """Send the Cash App info."""

        is_staff = self.bot.config.roles.staff in ctx.author.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")
        
        embed = discord.Embed(
            color=0x00C853,
            title="Cash App",
            description=f"""
1. Send a screenshot of your Cash App balance and ping us. Then wait for us to confirm.

2. Once we confirm, send $1 to the Cash App below.

3. Now send the web receipt link, Transactions > ${amount - 1:,} > Web receipt > Copy link.

4. Then send your Roblox name & Cash Tag.

5. If you understand, click the button below.
""",
        )

        embed.set_image(
            url="https://media.discordapp.net/attachments/1203846919583957064/1217552769066729594/cachedImage.png?ex=66047161&is=65f1fc61&hm=810611d01eba3c1b704928242944b590b24bd9b9165327b9bb0fb92ae891f0f4&"
        )

        cashapp_button = discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="Cash App",
            url=f"https://cash.app/$nleft",
        )

        view = ConfirmationView(cashapp_button)
        await ctx.send(embed=embed, view=view)


async def setup(bot: Bot):
    await bot.add_cog(Info(bot))
