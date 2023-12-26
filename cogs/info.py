import discord
from discord.ext import commands

from bot import Bot
from views.payment import ConfirmationView


class Info(commands.Cog):
    """Commands for getting information."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def pn(self, ctx: commands.Context):
        """Send the payment note."""

        await ctx.send(
            f"This is for digital goods. I have already received what I paid for. I will not chargeback under any circumstance. I am fully aware that making any attempt to chargeback this payment is considered fraud and against the seller's policy."
        )

    @commands.hybrid_command()
    async def ps(self, ctx: commands.Context):
        """Send the private server."""

        is_staff = self.bot.config.roles.staff in ctx.author.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        await ctx.send(
            "https://www.roblox.com/games/2788229376/1M-CODEs-Da-Hood?privateServerLinkCode=08505190204121690811488497040441"
        )

    @commands.hybrid_command()
    async def ltc(self, ctx: commands.Context):
        """Send the LTC address."""

        await ctx.send("```LTX2cZ9DoFR2gErZdCaaLA1ovFzdNsfTmH```")

    @commands.hybrid_command()
    async def btc(self, ctx: commands.Context):
        """Send the BTC address."""

        await ctx.send("```bc1qcza9p80drr8wzvdpn0vzegpsglmkvgsmmukuxe```")

    @commands.hybrid_command()
    async def eth(self, ctx: commands.Context):
        """Send the ETH address."""

        await ctx.send("```0x7462F240169b7411fDC83C607e5C13fbcBC7E988```")

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

3. Take a screenshot of the details before sending the payment and wait for us to confirm.

4. Once we confirm, ping us and send your email so we can find your payment.
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
1. Send a screenshot of your Cash App balance, then wait for us to confirm.

2. Once we confirm, send $1 to the Cash App below. Once <@230897007001075712> accepts the payment, send ${amount - 1:,} with the note "gift".

3. After you've sent it, send the transaction's web receipt link.
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
