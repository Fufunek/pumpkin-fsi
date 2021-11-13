import json
import re
from typing import Dict, Optional, List

import discord
from discord.ext import commands, tasks

from core import check, i18n, logger, utils

_ = i18n.Translator("modules/meme").translate
guild_log = logger.Guild.logger()

FISH_REGEX = r"^je [cč]erstv[aá]"
UH_OH_REGEX = r"^uh oh"
HUG_REGEX = r"<:peepoHug:897172785250594816>"


class Triggers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.fish_cache = 0
        self.cleanup.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        """User interactions"""
        # Ignore DMs
        if not isinstance(message.channel, discord.TextChannel):
            return

        if re.match(FISH_REGEX, message.content, flags=re.IGNORECASE):
            await self._fish_reaction(message)
        elif re.match(UH_OH_REGEX, message.content, flags=re.IGNORECASE):
            await self._uhoh_reaction(message)
        elif re.match(HUG_REGEX, message.content, flags=re.IGNORECASE):
            await self._hug_reaction(message)

    async def _fish_reaction(self, message):
        if self.fish_cache < 4:
            self.fish_cache += 1
            await message.channel.send("Není čerstvá!")

    async def _uhoh_reaction(self, message):
        if message.author.bot:
            return
        await message.channel.send("Uh oh")

    async def _hug_reaction(self, message):
        if message.author.bot:
            return
        await message.channel.send("<:peepoHug:897172785250594816>")

    @tasks.loop(seconds=30.0)
    async def cleanup(self):
        if self.fish_cache > 0:
            self.fish_cache -= 1


def setup(bot) -> None:
    bot.add_cog(Triggers(bot))
