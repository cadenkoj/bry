from datetime import datetime, timedelta
from typing import Optional
import discord
from discord import app_commands as apc
from discord.ext import commands
import humanize

from bot import Bot
from constants import *
from utils import MemberLog, parse_human_duration

class Moderation(commands.Cog):
    """Commands for moderating the server."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, reason: Optional[str] = "No reason given"):
        """Ban a member from the server.
        
        Parameters
        ----------
        member : discord.Member
            The member to ban.
        reason : Optional[str]
            The reason for the ban.
        """
        
        if member == ctx.author:
            raise commands.BadArgument("You can't ban yourself.")
        if member == ctx.guild.owner or ctx.author.top_role <= member.top_role:
            raise commands.BadArgument("You can't ban this user.")

        try:
            await ctx.guild.fetch_ban(member)
            raise commands.BadArgument(f"{member.mention} is already banned.")
        except discord.NotFound:
            pass

        try:
            view = discord.ui.View()

            origin_button = discord.ui.Button(label=f"Sent From: {ctx.guild}", disabled=True)
            view.add_item(origin_button)

            await member.send(f"You have been banned: **{reason}**", view=view)
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        self.bot.action_cache.ban = MemberLog(member, ctx.author, reason)

        await ctx.guild.ban(member, reason=f"{ctx.author}: {reason}")

        ban_chat_embed = discord.Embed(
            color=0x99b4e1,
            description=f"{EMOJIS.check} {member.mention} has been banned: **{reason}**",
        )

        await ctx.reply(embed=ban_chat_embed)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user: discord.User, reason: Optional[str] = "No reason given"):
        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            raise commands.BadArgument(f"{user.mention} is not banned.")

        self.bot.action_cache.unban = MemberLog(user, ctx.author, reason)

        await ctx.guild.unban(user, reason=f"{ctx.author}: {reason}")

        unban_chat_embed = discord.Embed(
            color=0x99b4e1,
            description=f"{EMOJIS.check} {user.mention} has been unbanned: **{reason}**",
        )

        await ctx.reply(embed=unban_chat_embed)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, reason: Optional[str] = "No reason given"):
        if member == ctx.author:
            raise commands.BadArgument("You can't kick yourself.")
        if member == ctx.guild.owner or ctx.author.top_role <= member.top_role:
            raise commands.BadArgument("You can't kick this user.")

        try:
            view = discord.ui.View()

            origin_button = discord.ui.Button(label=f"Sent From: {ctx.guild}", disabled=True)
            view.add_item(origin_button)

            await member.send(f"You have been kicked: **{reason}**", view=view)
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        self.bot.action_cache.kick = MemberLog(member, ctx.author, reason)

        await ctx.guild.kick(member, reason=f"{ctx.author}: {reason}")

        kick_chat_embed = discord.Embed(
            color=0x99b4e1,
            description=f"{EMOJIS.check} {member.mention} has been kicked: **{reason}**",
        )

        await ctx.reply(embed=kick_chat_embed)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: str, reason: Optional[str] = "No reason given"):
        mute_duration = parse_human_duration(duration)
        max_duration = timedelta(days=28)

        if mute_duration >= max_duration:
            raise commands.BadArgument(f"Duration must be less than {max_duration.days} days.")
        if member == ctx.author:
            raise commands.BadArgument("You can't mute yourself.")
        if member == ctx.guild.owner or ctx.author.top_role <= member.top_role:
            raise commands.BadArgument("You can't mute this user.")
        if member.is_timed_out():
            raise commands.BadArgument(f"{member.mention} is already muted.")

        human_time = humanize.naturaldelta(mute_duration)

        try:
            view = discord.ui.View()

            origin_button = discord.ui.Button(label=f"Sent From: {ctx.guild}", disabled=True)
            view.add_item(origin_button)

            await member.send(f"You have been muted for **{human_time}**: **{reason}**", view=view)
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        self.bot.action_cache.mute = MemberLog(member, ctx.author, reason)

        await member.timeout(mute_duration, reason=f"{ctx.author}: {reason}")

        mute_chat_embed = discord.Embed(
            color=0x99b4e1,
            description=f"{EMOJIS.check} {member.mention} has been muted for **{human_time}**: **{reason}**",
        )

        await ctx.reply(embed=mute_chat_embed)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member, reason: Optional[str] = "No reason given"):
        if member == ctx.author:
            raise commands.BadArgument("You can't unmute yourself.")
        if member == ctx.guild.owner or ctx.author.top_role <= member.top_role:
            raise commands.BadArgument("You can't unmute this user.")
        if not member.is_timed_out():
            raise commands.BadArgument(f"{member.mention} is not muted.")

        try:
            view = discord.ui.View()

            origin_button = discord.ui.Button(label=f"Sent From: {ctx.guild}", disabled=True)
            view.add_item(origin_button)

            await member.send(f"You have been unmuted: **{reason}**", view=view)
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        self.bot.action_cache.unmute = MemberLog(member, ctx.author, reason)

        await member.timeout(None, reason=f"{ctx.author}: {reason}")

        unmute_chat_embed = discord.Embed(
            color=0x99b4e1,
            description=f"{EMOJIS.check} {member.mention} has been unmuted: **{reason}**",
        )

        await ctx.reply(embed=unmute_chat_embed)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int):
        await ctx.defer()

        if amount < 1:
            raise commands.BadArgument("Amount must be greater than 0.")
        if amount > 100:
            raise commands.BadArgument("Amount must be less than 100.")

        await ctx.channel.purge(limit=amount + 1)

        purge_chat_embed = discord.Embed(
            color=0x99b4e1,
            description=f"{EMOJIS.check} **{amount}** messages have been purged.",
        )

        await ctx.channel.send(embed=purge_chat_embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, member: discord.Member):
        cache = self.bot.action_cache.ban

        if cache and member == cache.user:
            moderator = cache.moderator
            reason = cache.reason

            cache.ban = None
        else:
            entries = [entry async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban)]
            entry = entries[0]

            if entry.target != member:
                return

            moderator = entry.user
            reason = entry.reason or "No reason given"

        embed = discord.Embed(
            color=0x99b4e1,
            description=f"{member.mention} has been **banned**.",
            timestamp=discord.utils.utcnow(),
        )

        mod_info = moderator.mention if moderator else "Unknown"

        embed.set_author(icon_url=member.display_avatar.url, name=f"{member} ({member.id})")
        embed.add_field(name="Moderator", value=mod_info, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)

        channel = self.bot.config.channels.modlogs

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        cache = self.bot.action_cache.unban

        if cache and user == cache.user:
            moderator = cache.moderator
            reason = cache.reason

            cache.unban = None
        else:
            entries = [entry async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban)]
            entry = entries[0]

            if entry.target != user:
                return
            
            moderator = entry.user
            reason = entry.reason or "No reason given"

        embed = discord.Embed(
            color=0x99b4e1,
            description=f"{user.mention} has been **unbanned**.",
            timestamp=discord.utils.utcnow(),
        )

        mod_info = moderator.mention if moderator else "Unknown"

        embed.set_author(icon_url=user.display_avatar.url, name=f"{user} ({user.id})")
        embed.add_field(name="Moderator", value=mod_info, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)

        channel = self.bot.config.channels.modlogs

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        cache = self.bot.action_cache.kick

        if cache and member == cache.user:
            moderator = cache.moderator
            reason = cache.reason

            cache.kick = None
        else:
            entries = [entry async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick)]
            entry = entries[0]

            if entry.target != member:
                return

            moderator = entry.user
            reason = entry.reason or "No reason given"

        embed = discord.Embed(
            color=0x99b4e1,
            description=f"{member.mention} has been **kicked**.",
            timestamp=discord.utils.utcnow(),
        )

        mod_info = moderator.mention if moderator else "Unknown"

        embed.set_author(icon_url=member.display_avatar.url, name=f"{member} ({member.id})")
        embed.add_field(name="Moderator", value=mod_info, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)

        channel = self.bot.config.channels.modlogs

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        mute_cache = self.bot.action_cache.mute
        unmute_cache = self.bot.action_cache.unmute
    
        if mute_cache and after == mute_cache.user:
            moderator = mute_cache.moderator
            reason = mute_cache.reason

            action = "muted"
            mute_cache.mute = None
        elif unmute_cache and after == unmute_cache.user:
            moderator = unmute_cache.moderator
            reason = unmute_cache.reason

            action = "unmuted"
            unmute_cache.unmute = None
        else:
            return

        embed = discord.Embed(
            color=0x99b4e1,
            description=f"{after.mention} has been **{action}**.",
            timestamp=discord.utils.utcnow(),
        )

        mod_info = moderator.mention if moderator else "Unknown"

        embed.set_author(icon_url=after.display_avatar.url, name=f"{after} ({after.id})")
        embed.add_field(name="Moderator", value=mod_info, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)

        channel = self.bot.config.channels.modlogs

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        embed = discord.Embed(
            color=0x99b4e1,
            description=f"**Message sent by {message.author.mention} deleted in {message.channel.mention}**",
            timestamp=discord.utils.utcnow(),
        )

        embed.set_author(icon_url=message.author.display_avatar.url, name=f"{message.author} ({message.author.id})")
        embed.add_field(name="Content", value=message.content, inline=False)

        channel = self.bot.config.channels.logs

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return

        embed = discord.Embed(
            color=0x99b4e1,
            description=f"**Message sent by {before.author.mention} edited in {before.channel.mention}**",
            timestamp=discord.utils.utcnow(),
        )

        embed.set_author(icon_url=before.author.display_avatar.url, name=f"{before.author} ({before.author.id})")
        embed.add_field(name="Before", value=before.content, inline=True)
        embed.add_field(name="After", value=after.content, inline=True)

        channel = self.bot.config.channels.logs

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        embed = discord.Embed(
            color=0x99b4e1,
            description=f"**Channel created:** #{channel.name} ({channel.id})",
            timestamp=discord.utils.utcnow(),
        )

        channel = self.bot.config.channels.logs

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        embed = discord.Embed(
            color=0x99b4e1,
            description=f"**Channel deleted:** #{channel.name} ({channel.id})",
            timestamp=discord.utils.utcnow(),
        )

        channel = self.bot.config.channels.logs

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        embed = discord.Embed(
            color=0x99b4e1,
            description=f"**Role created:** {role.name} ({role.id})",
            timestamp=discord.utils.utcnow(),
        )

        channel = self.bot.config.channels.logs

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        embed = discord.Embed(
            color=0x99b4e1,
            description=f"**Role deleted:** {role.name} ({role.id})",
            timestamp=discord.utils.utcnow(),
        )

        channel = self.bot.config.channels.logs

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        embed = discord.Embed(
            color=0x99b4e1,
            description=f"**Role updated:** {after.name} ({after.id})",
            timestamp=discord.utils.utcnow(),
        )

        if before.name != after.name:
            embed.add_field(
                name="Name",
                value=f"{before.name} → {after.name}",
                inline=True,
            )

        if before.hoist != after.hoist:
            embed.add_field(
                name="Hoisted",
                value=f"{'Yes' if before.hoist else 'No'} → {'Yes' if after.hoist else 'No'}",
                inline=True,
            )

        if before.color != after.color:
            embed.add_field(
                name="Color",
                value=f"{before.color} → {after.color}",
                inline=True,
            )

        if embed.fields:
            channel = self.bot.config.channels.logs

            await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):   
        embed = discord.Embed(
            color=0x99b4e1,
            description=f"**Guild updated:** {after.name}",
            timestamp=discord.utils.utcnow(),
        )

        if before.name != after.name:
            embed.add_field(
                name="Name",
                value=f"{before.name} → {after.name}",
                inline=True,
            )

        if before.owner != after.owner:
            embed.add_field(
                name="Owner",
                value=f"{before.owner} → {after.owner}",
                inline=True,
            )

        if before.verification_level != after.verification_level:
            embed.add_field(
                name="Verification Level",
                value=f"{before.verification_level.name.capitalize()} → {after.verification_level.name.capitalize()}",
                inline=True,
            )

        
        if before.vanity_url != after.vanity_url:
            embed.add_field(
                name="Vanity URL",
                value=f"{before.vanity_url} → {after.vanity_url}",
                inline=True,
            )

        channel = self.bot.config.channels.logs

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.type != discord.MessageType.premium_guild_subscription:
            return
        
        member = message.author

        embed = discord.Embed(
            color=0x99b4e1,
            title="Thanks for Boosting!",
            description=f"**{member}**, thank you for boosting! To reward you for your kindness, we're offering you some special perks!\n\n- Weekly DH Cash Drops\n- $5 off on orders < $100 and $10 off on orders > $100",
            timestamp=discord.utils.utcnow(),
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Rewards will last until your Boost expires", icon_url=member.display_avatar.url)

        channel = self.bot.config.channels.boosts

        await channel.send(embed=embed, content=message.author.mention)


async def setup(bot: Bot):
    await bot.add_cog(Moderation(bot))
