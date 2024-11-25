import os
from dataclasses import dataclass


@dataclass
class Icons:
    check = "https://cdn.discordapp.com/emojis/1144037334657019925.webp?size=128"
    error = "https://cdn.discordapp.com/emojis/1145220217836933130.webp?size=128"
    loading = "https://cdn.discordapp.com/emojis/1170402444627419146.gif?size=128"
    ticket = "https://cdn.discordapp.com/emojis/1169397900183351378.webp?size=128"


@dataclass
class Emojis:
    check = "<:Check:1144037334657019925>"
    error = "<:Error:1145220217836933130>"
    loading = "<a:Loading:1170402444627419146>"
    ticket = "<:Ticket:1169397900183351378>"


IS_PROD = os.getenv("ENV") == "prod"

ICONS = Icons()
EMOJIS = Emojis()
