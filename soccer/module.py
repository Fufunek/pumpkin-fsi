from __future__ import annotations

from typing import Union

import nextcord

from nextcord import TextChannel, Thread, DMChannel, GroupChannel, PartialMessageable
from nextcord.ext import commands

from pie import logger, i18n, utils, database

_ = i18n.Translator("modules/fsi").translate

config = database.config.Config.get()

guild_log = logger.Guild.logger()
bot_log = logger.Bot.logger()


class Soccer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.history_limit = 200

        self.soccer_channels = [935158870937071626]  # TODO REWORK
        
        self.ignored_threads = [939848150825447424]

        self.embed_cache = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if not self._is_soccer_channel(message.channel):
            return

        await self._check_message(message)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: nextcord.RawMessageUpdateEvent):
        before = payload.cached_message
        after = await utils.discord.get_message(
            self.bot, payload.guild_id, payload.channel_id, payload.message_id
        )

        if not after:
            return

        if after.author.bot:
            return

        if not self._is_soccer_channel(after.channel):
            return

        if before:
            word_before = self._get_word(before)
            word_after = self._get_word(after)

            if word_before == word_after:
                return

        await self._check_message(after)

    @commands.Cog.listener()
    async def on_message_delete(self, message: nextcord.Message):
        if message.author.bot:
            return

        if not self._is_soccer_channel(message.channel):
            return

        await self._delete_report(message)

    async def _check_message(self, message: nextcord.Message):
        if not len(message.content):
            return

        if message.content.startswith("*") or message.content.startswith(config.prefix):
            return

        word = self._get_word(message)

        history = message.channel.history(limit=self.history_limit)

        async for history_message in history:
            if history_message.author.bot:
                continue

            if history_message.id == message.id:
                continue

            history_word = self._get_word(history_message)

            if history_word == word:
                await self._report_repost(message, history_message, word)
                return

        await self._delete_report(message)

    async def _delete_report(self, message):
        if message.id in self.embed_cache:
            message = self.embed_cache[message.id]
            try:
                await message.delete()
            except nextcord.errors.HTTPException:
                pass

            self.embed_cache.pop(message.id)
            return

        messages = await message.channel.history(
            after=message, limit=3, oldest_first=True
        )
        for report in messages:
            if not report.author.bot:
                continue
            if len(report.embeds) != 1 or type(report.embeds[0].footer.text) != str:
                continue
            if str(message.id) != report.embeds[0].footer.text.split(" | ")[1]:
                continue

            try:
                await report.delete()
            except nextcord.errors.HTTPException:
                pass

            return

    async def _report_repost(
        self, message: nextcord.Message, history_message: nextcord.Message, word: str
    ):
        gtx = i18n.TranslationContext(message.guild.id, message.author.id)

        embed = utils.discord.create_embed(
            author=message.author,
            title=_(gtx, "The judge's whistle"),
            color=nextcord.Colour.yellow(),
            description=_(
                gtx, "Word **{word}** was already used in last {limit} messages!"
            ).format(word=word, limit=self.history_limit),
        )

        embed.add_field(
            name=_(gtx, "Previously used:"),
            value=history_message.jump_url,
        )

        embed.set_footer(text=f"{message.author.id} | {message.id}")

        report = await message.reply(embed=embed)
        self.embed_cache[message.id] = report

    def _is_soccer_channel(
        self,
        channel: Union[
            TextChannel, Thread, DMChannel, GroupChannel, PartialMessageable
        ],
    ) -> bool:
        if not isinstance(channel, nextcord.Thread):
            return False
            
        if channel.id in self.ignored_threads:
            return False
        
        if not channel.guild:
            return False

        if channel.parent.id not in self.soccer_channels:
            return False

        return True

    def _get_word(self, message: nextcord.Message) -> str:
        text = message.content
        text = text.split()

        if len(text) < 1:
            return None

        text = text[0]

        text = text.replace("|", "").replace("`", "").replace("*", "")

        return text.lower()


def setup(bot) -> None:
    bot.add_cog(Soccer(bot))
