from typing import Collection

import discord
from discord import ui

from _types import Log
from bot import Bot
from constants import *

class ConfirmationView(discord.ui.View):
    """Confirmation view for info commands."""

    def __init__(self, replacement: discord.ui.Item):
        super().__init__(timeout=None)
        self.replacement = replacement

    @discord.ui.button(label="I understand", style=discord.ButtonStyle.secondary)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Confirm an info command."""
        await interaction.response.defer()

        self.clear_items()
        self.add_item(self.replacement)

        await interaction.message.edit(view=self)
        self.stop()

async def setup(bot: Bot):
    pass