import discord
from discord.ext import commands

from bot import Bot
from views.payment import ConfirmationView


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
1. Join the [private server here](https://www.roblox.com/games/2788229376/1M-CODEs-Da-Hood?privateServerLinkCode=08505190204121690811488497040441).

2. Go to bank and open up your trade menu.

3. Once the trade is complete, use the picture (if provided) sent by the seller for <#1141650778021441536>.
""",
        )

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
            url=f"https://www.paypal.com/paypalme/hadialidani",
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

2. Once we confirm, send $1 to the Cash App below. After <@230897007001075712> accepts the payment, send ${amount - 1:,} with the note "gift".

3. Now send the web receipt link, Transactions > ${amount - 1:,} > Web receipt > Copy link.

4. Then send your Roblox name & Cash Tag.

5. If you understand, click the button below.
""",
        )

        embed.set_image(
            url="https://cdn.discordapp.com/attachments/1150184910640918629/1175260629939003452/pay_image.png"
        )
        cashapp_button = discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="Cash App",
            url=f"https://cash.app/$ehxpulse",
        )
        view = ConfirmationView(cashapp_button)

        await ctx.send(embed=embed, view=view)


async def setup(bot: Bot):
    await bot.add_cog(Info(bot))
