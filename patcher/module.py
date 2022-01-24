from nextcord.ext import commands, tasks

from pie import logger, check

guild_log = logger.Guild.logger()
bot_log = logger.Bot.logger()

ADD_ACL = ["gn", "selfunverify"]


class Patcher(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.patch.start()

    @tasks.loop(seconds=10.0, count=1)
    async def patch(self):
        out = "Patched commands: "
        for command in ADD_ACL:
            if await self._add_acl(command):
                out += f"`{command}` "

        await bot_log.info(
            None,
            None,
            out,
        )

    @patch.before_loop
    async def before_patch(self):
        """Ensures that bot is ready before doing any
        patches.
        """
        print("Waiting for bot being ready to fix some deFEKTs")
        await self.bot.wait_until_ready()

    async def _add_acl(self, command_name):
        command = self.bot.get_command(command_name)
        if command is None:
            await bot_log.error(
                None,
                None,
                f"Can't add ACL to command {command_name}. Command not found.",
            )
            return

        command.add_check(check.acl)
        return True


def setup(bot) -> None:
    bot.add_cog(Patcher(bot))
