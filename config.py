from dataclasses import dataclass

from discord import Role, TextChannel, VoiceChannel

from bot import Bot
from constants import *


@dataclass
class ChannelConfig:
    sales: VoiceChannel
    earnings: VoiceChannel
    purchases: TextChannel
    logs: TextChannel
    modlogs: TextChannel
    shop: TextChannel
    updates: TextChannel
    boosts: TextChannel
    scams: TextChannel


@dataclass
class RolesConfig:
    staff: Role
    customer: Role
    tier1: Role
    tier2: Role
    tier3: Role
    tier4: Role
    tier5: Role


@dataclass
class BotConfig:
    owner_ids = [1201776746555527198, 230897007001075712, 997958244452544582, 1070544585228570685]
    channels: ChannelConfig
    roles: RolesConfig


def get_config(bot: Bot):
    if IS_PROD:
        guild = bot.get_guild(1141650741111558245)

        return BotConfig(
            channels=ChannelConfig(
                sales=bot.get_channel(1146378711088775219),
                earnings=bot.get_channel(1146378858451435540),
                purchases=bot.get_channel(1151322058941267968),
                logs=bot.get_channel(1148454686945443851),
                modlogs=bot.get_channel(1148446938157563914),
                shop=bot.get_channel(1213588818628968528),
                updates=bot.get_channel(1213588854041215016),
                boosts=bot.get_channel(1213583947154333756),
                scams=bot.get_channel(1214008347863552050),
            ),
            roles=RolesConfig(
                staff=guild.get_role(1146375334170730548),
                customer=guild.get_role(1145959140594810933),
                tier1=guild.get_role(1156319778810646579),
                tier2=guild.get_role(1145959139432992829),
                tier3=guild.get_role(1156319772640817242),
                tier4=guild.get_role(1145959137453285416),
                tier5=guild.get_role(1156320181895827537),
            ),
        )
    else:
        guild = bot.get_guild(1203846918724395008)

        return BotConfig(
            channels=ChannelConfig(
                sales=bot.get_channel(1203847431477927936),
                earnings=bot.get_channel(1203847446971809792),
                purchases=bot.get_channel(1203847411437543474),
                logs=bot.get_channel(1203847411437543474),
                modlogs=bot.get_channel(1203847411437543474),
                shop=bot.get_channel(1203847411437543474),
                updates=bot.get_channel(1203847411437543474),
                boosts=bot.get_channel(1203847411437543474),
                scams=bot.get_channel(1203847411437543474),
            ),
            roles=RolesConfig(
                staff=guild.get_role(1203847285633720350),
                customer=guild.get_role(1203847285633720350),
                tier1=guild.get_role(1203847285633720350),
                tier2=guild.get_role(1203847285633720350),
                tier3=guild.get_role(1203847285633720350),
                tier4=guild.get_role(1203847285633720350),
                tier5=guild.get_role(1203847285633720350),
            ),
        )
