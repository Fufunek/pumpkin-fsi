import tempfile

from typing import Union

import nextcord
from nextcord.ext import commands

from pie import i18n, logger, utils, check

_ = i18n.Translator("modules/sudo").translate
guild_log = logger.Guild.logger()


class Sudo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # HELPER FUNCTIONS
    async def _get_message(self, ctx, message: str):
        if message is not None:
            return message
        else:
            if len(ctx.message.attachments) != 1 or not ctx.message.attachments[
                0
            ].filename.lower().endswith("txt"):
                return None

            data_file = tempfile.TemporaryFile()
            await ctx.message.attachments[0].save(data_file)
            data_file.seek(0)

            return data_file.read().decode("utf-8")

    # COMMANDS

    @commands.check(check.acl)
    @commands.group(name="sudo")
    async def sudo_(self, ctx):
        """Do something as this bot."""
        await utils.discord.send_help(ctx)

    @commands.check(check.acl)
    @sudo_.group(name="message")
    async def sudo_message_(self, ctx):
        """Sends / edits message as this bot."""
        await utils.discord.send_help(ctx)

    @commands.check(check.acl)
    @sudo_message_.command(name="send")
    async def sudo_message_send(
        self,
        ctx,
        channel: Union[nextcord.TextChannel, nextcord.Thread],
        *,
        message: str = None
    ):
        """Sends message as this bot.

        Args:
            channel: Channel mention to send message
            message: Text message (can be ommited when uploading .txt file)
        """
        message = await self._get_message(ctx, message)
        if message is None:
            await ctx.reply(
                _(ctx, "You must write message as parameter or upload TXT file.")
            )
            return

        if len(message) > 2000:
            await ctx.reply(_(ctx, "Message must be shorter than 2000 characters."))
            return

        message = await channel.send(message)

        await utils.discord.delete_message(ctx.message)
        await ctx.send(
            _(ctx, "Your message was sent into channel {channel}").format(
                channel=channel.mention
            ),
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            "SUDO sent message with ID {} in channel #{}".format(
                message.id, message.channel.name
            ),
        )

    @commands.check(check.acl)
    @sudo_message_.command(name="edit")
    async def sudo_message_edit(
        self, ctx, channel_id: int, message_id: int, *, message: str = None
    ):
        """Edit bot message.

        Args:
            channel: Channel mention to send message, 0 if current channel
            message_id: ID of edited message
            message: Text message (can be ommited when uploading .txt file)
        """
        if channel_id == 0:
            channel_id = ctx.channel.id

        dc_message = await utils.discord.get_message(
            self.bot, ctx.guild.id, channel_id, message_id
        )

        if dc_message is None:
            ctx.reply(_(ctx, "Message with ID {id} not found.").format(id=message_id))

        message = await self._get_message(ctx, message)
        if message is None:
            await ctx.reply(
                _(ctx, "You must write message as parameter or upload TXT file.")
            )
            return

        if len(message) > 2000:
            await ctx.reply(_(ctx, "Message must be shorter than 2000 characters."))
            return

        await dc_message.edit(message)
        await utils.discord.delete_message(ctx.message)
        await ctx.send(
            _(ctx, "Your message {id} in channel {channel} was edited.").format(
                id=message_id, channel=dc_message.channel.mention
            ),
        )

        await guild_log.info(
            ctx.author,
            ctx.channel,
            "SUDO edited message with ID {} in channel #{}".format(
                message_id, dc_message.channel.name
            ),
        )

    @commands.check(check.acl)
    @sudo_message_.commands(name="download")
    async def sudo_message_download(self, ctx, channel_id: int, message_id: int):
        """Downloads message to file.

        Args:
            channel: Channel ID to send message, 0 if current channel
            message_id: ID of downloaded message
        """
        if channel_id == 0:
            channel_id = ctx.channel.id

        dc_message = await utils.discord.get_message(
            self.bot, ctx.guild.id, channel_id, message_id
        )

        if dc_message is None:
            ctx.reply(_(ctx, "Message with ID {id} not found.").format(id=message_id))

        file = tempfile.TemporaryFile(mode="w+")

        file.write(dc_message.content)

        filename = "message-{channel}-{message}.txt".format(
            channel=channel_id, message=dc_message.id
        )

        file.seek(0)
        await ctx.reply(
            _(ctx, "Message exported to TXT."),
            file=nextcord.File(fp=file, filename=filename),
        )
        file.close()

    @commands.check(check.acl)
    @sudo_message_.command(name="append")
    async def sudo_message_append(
        self, ctx, channel_id: int, message_id: int, *, message: str = None
    ):
        """Append to bot message.

        Args:
            channel: Channel ID to send message, 0 if current channel
            message_id: ID of edited message
            message: Appended text (can be ommited when uploading .txt file)
        """
        if channel_id == 0:
            channel_id = ctx.channel.id

        dc_message = await utils.discord.get_message(
            self.bot, ctx.guild.id, channel_id, message_id
        )

        if dc_message is None:
            ctx.reply(_(ctx, "Message with ID {id} not found.").format(id=message_id))

        message = await self._get_message(ctx, message)
        if message is None:
            await ctx.reply(
                _(ctx, "You must write message as parameter or upload TXT file.")
            )
            return

        message = dc_message.content + message

        if message is None:
            await ctx.reply(
                _(ctx, "You must write message as parameter or upload TXT file.")
            )
            return

        if len(message) > 2000:
            await ctx.reply(_(ctx, "Message must be shorter than 2000 characters."))
            return

        await dc_message.edit(message)
        await utils.discord.delete_message(ctx.message)
        await ctx.send(
            _(ctx, "Your message {id} in channel {channel} was edited.").format(
                id=message_id, channel=dc_message.channel.mention
            ),
        )

        await guild_log.info(
            ctx.author,
            ctx.channel,
            "SUDO edited message with ID {} in channel #{}".format(
                message_id, dc_message.channel.name
            ),
        )


def setup(bot) -> None:
    bot.add_cog(Sudo(bot))
