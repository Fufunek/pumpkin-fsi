import datetime
import hashlib
import inspect

from discord.ext import commands, tasks

from pie import logger, utils

guild_log = logger.Guild.logger()
bot_log = logger.Bot.logger()


class Patcher(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.date_check = "16572801b42921d1f9f9b1279dc75dba"
        self.datetime_check = "23af3078e84e9f0dfbef619dfde789b4"

        self.patch.start()

    @tasks.loop(seconds=10.0, count=1)
    async def patch(self):
        date_source = inspect.getsource(utils.time.format_date)
        date_hash = hashlib.md5(date_source.encode()).hexdigest()

        log = f"Original date function hash is {date_hash}."

        if date_hash == self.date_check:
            print(log + " Hash matches. Patching.")
            utils.time.format_date = Patcher.fix_format_date
        else:
            print(log + " Hash does not match!")
            await bot_log.error(
                None, None, "Hash for function 'utils.time.format_date' does not match!"
            )

        datetime_source = inspect.getsource(utils.time.format_datetime)
        datetime_hash = hashlib.md5(datetime_source.encode()).hexdigest()

        log = f"Original datetime function hash is {datetime_hash}."

        if datetime_hash == self.datetime_check:
            print(log + " Hash matches. Patching.")
            utils.time.format_datetime = Patcher.fix_format_datetime
        else:
            print(log + " Hash does not match!")
            await bot_log.error(
                None,
                None,
                "Hash for function 'utils.time.format_datetime' does not match!",
            )

    @patch.before_loop
    async def before_patch(self):
        """Ensures that bot is ready before doing any
        patches.
        """
        print("Waiting for bot being ready to fix some deFEKTs")
        await self.bot.wait_until_ready()

    @staticmethod
    def fix_format_date(timestamp: datetime.datetime) -> str:
        """Convert timestamp to date."""
        return timestamp.strftime("%d-%m-%Y ")

    @staticmethod
    def fix_format_datetime(timestamp: datetime.datetime) -> str:
        """Convert timestamp to date and time."""
        return timestamp.strftime("%d-%m-%Y %H:%M:%S")


async def setup(bot) -> None:
    await bot.add_cog(Patcher(bot))
