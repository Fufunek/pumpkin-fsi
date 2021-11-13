import json
import re
from typing import Dict, Optional, List

import discord
from discord.ext import commands, tasks

from core import check, i18n, logger, utils

_ = i18n.Translator("modules/fsi").translate
guild_log = logger.Guild.logger()

FISH_REGEX = r"^je [cč]erstv[aá]"
UH_OH_REGEX = r"^uh oh"
HUG_REGEX = r"<:peepoHug:897172785250594816>"


class FSI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.fish_cache = 0
        self.cleanup.start()

    @commands.command(aliases=["divocak", "jako"])
    async def slovakize(self, ctx, *, message: str = None):
        """Slovakize message"""
        if message is None:
            text = "Moc kratky text brasko!"
        else:
            text = utils.Text.sanitise(
                self._slovakize(message), limit=1900, escape=False
            )
        await ctx.send(
            f"**{utils.Text.sanitise(ctx.author.display_name)}**\n>>> " + text
        )

        await utils.Discord.delete_message(ctx.message)

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

    # HELPER FUNCTIONS

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

    def _slovakize(self, text: str) -> str:
        text = text.replace(".", "").replace("?", "").replace("!", "").replace(",", "")
        words = text.split()

        for idx, word in enumerate(words):
            if len(word) < 3:
                continue

            if word.lower() in ["som", "ako"]:
                continue

            if word.lower() == "jako":
                words[idx] = word + "oou"
                continue

            if not word[-1].isalpha():
                continue
            if word[-1] == "e":
                continue
            elif word[-1] == "o":
                words[idx] = word + "s"
                continue
            elif word[-1] in ["a", "i", "u", "y"]:
                words[idx] = word[:-1] + "os"
                continue

            words[idx] = word + "os"

        text = " ".join(words) + " šak povedz ty ne"
        return text

    @tasks.loop(seconds=30.0)
    async def cleanup(self):
        if self.fish_cache > 0:
            self.fish_cache -= 1


def setup(bot) -> None:
    bot.add_cog(FSI(bot))
