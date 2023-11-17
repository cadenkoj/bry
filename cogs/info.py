from discord import app_commands as apc
from discord.ext import commands

from bot import Bot

class Info(commands.Cog):
    """Commands for getting information."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def pn(self, ctx: commands.Context):
        await ctx.send(f"This is for digital goods. I have already received what I paid for. I will not chargeback under any circumstance. I am fully aware that making any attempt to chargeback this payment is considered fraud and against the seller's policy.")

    @commands.command()
    async def ps(self, ctx: commands.Context):
        is_staff = self.bot.config.roles.staff in ctx.author.roles
        if not is_staff:
            raise Exception("You do not have permission to use this command.")

        await ctx.send("https://www.roblox.com/games/2788229376/1M-CODEs-Da-Hood?privateServerLinkCode=83706208461702631056500770002026")

    @commands.command()
    async def ltc(self, ctx: commands.Context):
        await ctx.send("```LTX2cZ9DoFR2gErZdCaaLA1ovFzdNsfTmH```")

    @commands.command()
    async def btc(self, ctx: commands.Context):
        await ctx.send("```bc1qcza9p80drr8wzvdpn0vzegpsglmkvgsmmukuxe```")

    @commands.command()
    async def eth(self, ctx: commands.Context):
        await ctx.send("```0x7462F240169b7411fDC83C607e5C13fbcBC7E988```")

async def setup(bot: Bot):
    await bot.add_cog(Info(bot))