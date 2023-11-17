import os
import re
from typing import Optional
from urllib.parse import urlparse

import discord
from discord import app_commands as apc
from discord.ext import commands
import requests

from bot import Bot

def clean_emoji(name: str, id: int) -> str:
    clean_name = ''.join(x if x.isalnum() else '' for x in name)
    
    if len(clean_name) < 2:
        return str(id)
    
    return clean_name[:32]

class Emoji(commands.Cog):
    """Commands for handling emojis."""

    def __init__(self, bot: Bot):
        self.bot = bot

    emoji = apc.Group(name="emoji", description="Manage emojis.")

    @emoji.command()
    @apc.guild_only()
    @apc.default_permissions(manage_emojis=True)
    async def copy(self, interaction: discord.Interaction, emojis: str, name: Optional[str] = None) -> None:
        """Copy emojis from another server.
        
        Parameters
        ----------
        emojis : str
            The emojis to add.
        name : Optional[str]
            The name to give the emoji.
        """

        pattern = re.compile(r'<(?P<tag>a?):(?P<name>[a-zA-Z0-9_]+):(?P<id>[0-9]+)>')
        matches = pattern.finditer(emojis)

        added: list[discord.Emoji] = []
        for match in matches:
            name = name or match.group('name')
            animated = match.group('tag') == 'a'
            id = match.group('id')

            emoji = discord.PartialEmoji(name=name, animated=animated, id=id)
            res = requests.get(emoji.url, stream=True)

            emoji = await interaction.guild.create_custom_emoji(name=name, image=res.content)
            added.append(emoji)

        if added:
            mentions = ' '.join([str(emoji) for emoji in added])
            await interaction.response.send_message(f'Successfully added: {mentions}', ephemeral=True)
        else:
            await interaction.response.send_message('No emojis were added', ephemeral=True)

    @emoji.command()
    @apc.guild_only()
    @apc.default_permissions(manage_emojis=True)
    async def upload(self, interaction: discord.Interaction, file: discord.Attachment, name: Optional[str] = None) -> None:
        """Upload an emoji.
        
        Parameters
        ----------
        emoji : discord.Attachment
            The emoji to upload.
        name : Optional[str]
            The name to give the emoji.
        """

        filename = file.filename.split('.')[0]

        name = name or clean_emoji(filename, file.id)
        image = await file.read()

        emoji = await interaction.guild.create_custom_emoji(name=name, image=image)

        await interaction.response.send_message(f'Successfully added: {emoji}', ephemeral=True)

    @emoji.command()
    @apc.guild_only()
    @apc.default_permissions(manage_emojis=True)
    async def link(self, interaction: discord.Interaction, url: str, name: Optional[str] = None) -> None:
        """Add emoji by url.

        Parameters
        ----------
        url : str
            The url to the emoji.
        name : Optional[str]
            The name to give the emoji.
        """

        res = requests.get(url, stream=True)
        res.raise_for_status()

        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)

        name = name or clean_emoji(filename, 'unnamed_emoji')
        image = res.content

        emoji = await interaction.guild.create_custom_emoji(name=name, image=image)

        await interaction.response.send_message(f'Successfully added: {emoji}', ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Emoji(bot))