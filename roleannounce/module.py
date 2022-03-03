from __future__ import annotations

import nextcord
from nextcord.ext import commands

from pie import i18n, logger, utils

guild_log = logger.Guild.logger()
_ = i18n.Translator("modules/fsi").translate


class RoleAnnounce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.info_channel = {}
        self.teacher_channel = {}
        self.teacher_role = {}
        self.mute_role = {}

        self.info_channel[633740398174404608] = 907602423617556490  # TODO - dynamic
        self.teacher_channel[633740398174404608] = 760600713763356742  # TODO
        self.teacher_role[633740398174404608] = 892455004915499129
        self.mute_role[633740398174404608] = 896832583906787419

    @commands.Cog.listener()
    async def on_member_update(self, before: nextcord.Member, after: nextcord.Member):
        was_boosting = self._is_boosting(before)
        is_boosting = self._is_boosting(after)

        if was_boosting and not is_boosting:
            embed = await self._get_booster_embed(before, after, False)
            channel_id = self.info_channel[after.guild.id]
        elif not was_boosting and is_boosting:
            embed = await self._get_booster_embed(before, after, True)
            channel_id = self.info_channel[after.guild.id]
        else:
            was_muted = before.get_role(self.mute_role[before.guild.id]) is not None
            if was_muted:
                return
            
            was_teacher = (
                before.get_role(self.teacher_role[before.guild.id]) is not None
            )
            is_teacher = after.get_role(self.teacher_role[before.guild.id]) is not None

            if was_teacher:
                return

            if is_teacher:
                channel_id = self.teacher_channel[after.guild.id]
                embed = await self._get_teacher_embed(before, after)
            else:
                return

        if not channel_id:
            return

        channel = after.guild.get_channel_or_thread(channel_id)

        if not channel:
            await guild_log.warning(
                after,
                after.guild,
                f"Can't send role info into channel #{channel_id} - not found!",
            )
            return

        await channel.send(embed=embed)

    async def _get_booster_embed(
        self, before: nextcord.Member, after: nextcord.Member, boosted: bool
    ) -> nextcord.Embed:

        utx = i18n.TranslationContext(after.guild.id, None)

        title = (
            _(utx, "Member added boost!")
            if boosted
            else _(utx, "Member removed boost!")
        )
        embed = utils.discord.create_embed(
            author=self.bot.user,
            title=title,
            color=nextcord.Colour.gold() if boosted else nextcord.Colour.dark_gray(),
        )

        embed.add_field(name=_(utx, "Member name"), value=after.display_name)

        avatar_url: str = after.display_avatar.replace(size=256).url
        embed.set_thumbnail(url=avatar_url)

        return embed

    async def _get_teacher_embed(
        self, before: nextcord.Member, after: nextcord.Member
    ) -> nextcord.Embed:

        utx = i18n.TranslationContext(after.guild.id, None)
        embed = utils.discord.create_embed(
            author=self.bot.user,
            title=_(utx, "New teacher!"),
            color=nextcord.Colour.red(),
        )
        embed.add_field(name=_(utx, "Member name"), value=after.display_name)
        avatar_url: str = after.display_avatar.replace(size=256).url
        embed.set_thumbnail(url=avatar_url)

        return embed

    def _is_boosting(self, member: nextcord.Member) -> bool:
        for role in member.roles:
            if role.is_premium_subscriber():
                return True

        return False


def setup(bot) -> None:
    bot.add_cog(RoleAnnounce(bot))
