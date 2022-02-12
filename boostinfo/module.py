from __future__ import annotations

import nextcord
from nextcord.ext import commands

from pie import i18n, logger, utils

guild_log = logger.Guild.logger()
_ = i18n.Translator("modules/fsi").translate


class BoostInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.info_channel = {}

        self.info_channel[633740398174404608] = 907602423617556490  # TODO - dynamic

    @commands.Cog.listener()
    async def on_member_update(self, before: nextcord.Member, after: nextcord.Member):
        was_boosting = self._is_boosting(before)
        is_boosting = self._is_boosting(after)

        if was_boosting and not is_boosting:
            embed = await self._get_embed(before, after, False)
        elif not was_boosting and is_boosting:
            embed = await self._get_embed(before, after, True)
        else:
            return

        channel_id = self.info_channel(after.guild.id)
        if not channel_id:
            return

        channel = after.guild.get_channel_or_thread(channel_id)

        if not channel:
            guild_log.warning(
                after,
                after.guild,
                f"Can't send boost info into channel #{channel_id} - not found!",
            )
            return

        await channel.send(embed=embed)

    async def _get_embed(
        self, before: nextcord.Member, after: nextcord.Member, boosted: bool
    ) -> nextcord.Embed:

        utx = i18n.TranslationContext(after.guild.id, None)

        title = (
            _(utx, "Member added boost!")
            if boosted
            else _(utx, "Member removed boost!")
        )
        embed = utils.discord.create_embed(
            author=self.bot,
            title=title,
            color=nextcord.Colour.gold() if boosted else nextcord.Colour.dark_gray(),
        )

        avatar_url: str = after.display_avatar.replace(size=256).url
        embed.set_thumbnail(url=avatar_url)

        return embed

    def _is_boosting(member: nextcord.Member) -> bool:
        for role in member.roles:
            if role.is_premium_subscriber():
                return True

        return False


def setup(bot) -> None:
    bot.add_cog(BoostInfo(bot))
