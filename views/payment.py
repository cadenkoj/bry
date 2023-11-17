from typing import Collection

import discord
from discord import ui

from _types import Log
from bot import Bot
from constants import *

class PaymentButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.payment_method = None
        self.modal = CashAppModal()

        url = 'https://cash.app/$ehxpulse'
        self._children.insert(0, discord.ui.Button(label='Cash App', url=url))

    @discord.ui.button(label='Done', style=discord.ButtonStyle.secondary)
    async def finished(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()

        button.disabled = True
        await interaction.message.edit(view=self)

        self.stop()

class CashAppModal(ui.Modal, title="Cash App"):
    interaction: discord.Interaction
    username = ui.TextInput(label="Roblox Username", placeholder="John_Doe")
    web_receipt = ui.TextInput(label="Web Receipt", placeholder="https://cash.app/payments/xxx/receipt")

    async def on_submit(self, interaction: discord.Interaction[Bot]):
        self.interaction = interaction

        log_collection: Collection[Log] = interaction.client.database.get_collection("logs")

        if log_collection.find_one({"web_receipt": self.web_receipt.value}):
            raise ValueError("This receipt has already been submitted.")
        
        embed = discord.Embed(color=0x599ae0)

        embed.set_author(
            name=f"Verifying Transaction",
            icon_url=ICONS.loading
        )

        await interaction.response.send_message(embed=embed)
        self.stop()

async def setup(bot: Bot):
    pass