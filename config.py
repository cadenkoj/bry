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
    owner_ids = [1174402623965769881, 230897007001075712, 997958244452544582]
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
                shop=bot.get_channel(1151344325893046293),
                updates=bot.get_channel(1166520967745511454),
                boosts=bot.get_channel(1148450041732804648),
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
        guild = bot.get_guild(1123001792775590053)

        return BotConfig(
            channels=ChannelConfig(
                sales=bot.get_channel(1174443203500445786),
                earnings=bot.get_channel(1174443221498200075),
                purchases=bot.get_channel(1174443476998430901),
                logs=bot.get_channel(1174879358498918471),
                modlogs=bot.get_channel(1174878230147248148),
                shop=bot.get_channel(1174443381078900816),
                updates=bot.get_channel(1174443394051874910),
                boosts=bot.get_channel(1148450041732804648),
            ),
            roles=RolesConfig(
                staff=guild.get_role(1174443576550248599),
                customer=guild.get_role(1174443664223764582),
                tier1=guild.get_role(1174443686717825045),
                tier2=guild.get_role(1174443747115794593),
                tier3=guild.get_role(1174443765100982373),
                tier4=guild.get_role(1174443786118627360),
                tier5=guild.get_role(1174443799443931316),
            ),
        )
