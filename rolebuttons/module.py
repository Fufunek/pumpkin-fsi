import nextcord
from nextcord.ext import commands, tasks

from typing import Dict, List, Optional, Union

from pie import i18n, logger, utils, check
from pie.utils.objects import ConfirmView

from .objects import RBViewUI
from .database import RBView, RestrictionType, RBOption, RBItem, DiscordType, RBMessage
from .utils import RBUtils as rbutils

_ = i18n.Translator("modules/fsi").translate
guild_log = logger.Guild.logger()
bot_log = logger.Bot.logger()


class RoleButtons(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.views = {}

        self.load_views.start()

    def cog_unload(self):
        self._unload_views()

    # HELPER FUNCTIONS
    def _unload_views(self):
        """Unload all views. It's used in reload commands
        or when unloading / reloading module.
        """
        for id, view in self.views.items():
            view.stop()

        self.views = {}

    @tasks.loop(seconds=10.0, count=1)
    async def load_views(self):
        """Task used to load all view as persistent.
        It has count=1 so it runs only once after called.
        Also using before_loop it ensures this is run only
        after bot is ready.
        """
        self.views = {}

        views = RBView.get_all()

        for view in views:
            view_ui = RBViewUI(self.bot, view)
            self.views[view.idx] = view_ui
            self.bot.add_view(view_ui)

            for message in view.messages:
                dc_message = await utils.discord.get_message(
                    self.bot, view.guild_id, message.channel_id, message.message_id
                )
                if dc_message:
                    await dc_message.edit(view=view_ui)

        print("All RoleButtons persistent views loaded.")

    @load_views.before_loop
    async def before_load(self):
        """Ensures that bot is ready before loading any
        persitant view.
        """
        print("Loading RoleButtons persistent views. Waiting for bot being ready.")
        await self.bot.wait_until_ready()

    def _get_item_embed(self, ctx, option: RBOption, item: RBItem) -> nextcord.Embed:
        """Create information embed for item.

        Args:
            ctx: Command context
            option: Item's parent DB object.
            item: RBItem for information

        Returns: :class:`nextcord.Embed` information embed
        """
        embed = utils.discord.create_embed(
            author=ctx.author, title=_(ctx, "Item information")
        )

        role, channel = rbutils.process_items(item, ctx.guild)

        item = role + channel

        if len(item) != 1:
            name = "({id})".format(id=item.discord_id)
        else:
            name = item.mention

        embed.add_field(name=_(ctx, "ID"), value=str.item.discord_id)
        embed.add_field(name=_(ctx, "Option ID"), value=option.idx)
        embed.add_field(name=_(ctx, "Name"), value=name)
        embed.add_field(name=_(ctx, "Type"), value=name.__class__.__name__)

        return embed

    async def _get_view_embed(self, ctx, view) -> nextcord.Embed:
        """Create information embed for View.

        Args:
            ctx: Command context
            view: View DB object.

        Returns: :class:`nextcord.Embed` information embed
        """

        embed = utils.discord.create_embed(
            author=ctx.author, title=_(ctx, "View informations")
        )

        embed.add_field(name=_(ctx, "ID"), value=str(view.idx), inline=True)
        embed.add_field(
            name=_(ctx, "Unique (only one role)"),
            value=_(ctx, "Yes") if view.unique else _(ctx, "No"),
            inline=True,
        )

        embed.add_field(
            name=_(ctx, "Messages"),
            value="\n".join(
                [
                    f"({message.message_id}, {message.channel_id})"
                    for message in view.messages
                ]
            )
            if view.messages
            else "-",
            inline=True,
        )

        roles = await self._get_view_roles(ctx, view)

        allowed_roles = ", ".join(roles[RestrictionType.ALLOW])
        disallowed_roles = ", ".join(roles[RestrictionType.ALLOW])

        embed.add_field(
            name=_(ctx, "Allowed roles"),
            value=allowed_roles if len(allowed_roles) != 0 else _(ctx, "All"),
            inline=True,
        )

        embed.add_field(
            name=_(ctx, "Disallowed roles"),
            value=disallowed_roles if len(disallowed_roles) != 0 else _(ctx, "None"),
            inline=True,
        )

        options = await self._get_option_names(ctx, view)

        embed.add_field(
            name=_(ctx, "Options"),
            value="\n".join(options) if options else "-",
            inline=True,
        )

        return embed

    async def _get_option_embed(self, ctx, option) -> nextcord.Embed:
        """Create information embed for option.

        Args:
            ctx: Command context
            option: Item's parent DB object.

        Returns: :class:`nextcord.Embed` information embed
        """
        embed = utils.discord.create_embed(
            author=ctx.author, title=_(ctx, "Option informations")
        )

        embed.add_field(name=_(ctx, "ID"), value=str(option.idx), inline=True)
        embed.add_field(name=_(ctx, "View ID"), value=str(option.view_id), inline=True)
        embed.add_field(
            name=_(ctx, "Label"),
            value=option.label,
            inline=True,
        )
        embed.add_field(
            name=_(ctx, "Emoji"),
            value=rbutils.emoji_decode(self.bot, option.emoji),
            inline=True,
        )
        embed.add_field(
            name=_(ctx, "Description"),
            value=option.description,
            inline=True,
        )

        items = await self._get_item_names(ctx.guild, option)

        embed.add_field(
            name=_(ctx, "Items"),
            value=", ".join(sorted(items)) if items else "-",
            inline=True,
        )

        return embed

    async def _get_view_roles(self, ctx, view: RBView) -> Dict[RestrictionType, str]:
        """Create dict where key is RestrictionType and values are lists
        of strings representing role names.

        Args:
            ctx: Command context
            view: View DB object

        Returns: :class:`nextcord.Embed` information embed
        """
        roles = {}
        roles[RestrictionType.ALLOW] = []
        roles[RestrictionType.DISALLOW] = []

        for restriction in view.restrictions:
            role = ctx.guild.get_role(restriction.role_id)

            if role is None:
                name = "(restriction.role_id)"
            else:
                name = role.name

            roles[role.type].append(name)

        return roles

    async def _get_option_names(self, ctx, view) -> List[str]:
        options = []

        for option in view.options:
            options.append("({id}) {label}".format(id=option.idx, label=option.label))

        return options

    async def _get_item_names(self, guild: nextcord.Guild, option: RBOption) -> str:
        items = []
        for item in option.items:
            if item.discord_type == DiscordType.ROLE:
                role = guild.get_role(item.discord_id)
                if not role:
                    items.append("(\\@{id})".format(id=item.discord_id))
                else:
                    items.append(role.mention)
            else:
                channel = guild.get_channel(item.discord_id)
                if not channel or not isinstance(channel, nextcord.abc.GuildChannel):
                    items.append("(\\#{id})".format(id=item.discord_id))
                else:
                    items.append(channel.mention)

        return items

    # COMMANDS

    @commands.check(check.acl)
    @commands.group(name="rolebuttons")
    async def rolebuttons_(self, ctx):
        await utils.discord.send_help(ctx)

    @commands.check(check.acl)
    @rolebuttons_.command(name="reload")
    async def rolebuttons_reload(self, ctx):
        """Reload all Views and re-attach them
        to their messages.
        """
        self._unload_views()
        self.load_views.start()

    @commands.check(check.acl)
    @rolebuttons_.command(name="create")
    async def rolebuttons_create(self, ctx, unique: bool):
        """Create RoleButtons View.

        When adding roles and channels, unique RoleButtons View
        will remove all other roles and channels from other options
        before adding selected option's roles and channels.

        Args:
            unique: Changes RoleButtons View behavior
        """
        view = RBView.create(ctx.guild, unique)
        if view:
            await ctx.reply(
                _(ctx, "RoleButtons View created with ID {id}").format(id=view.idx)
            )
        else:
            await ctx.reply(_(ctx, "Could not create RoleButtons View."))

    @commands.check(check.acl)
    @rolebuttons_.command(name="list")
    async def rolebuttons_list(self, ctx):
        """Get list of Views"""
        views = RBView.get_all(ctx.guild)
        tables = utils.text.create_table(
            views,
            {
                "idx": _(ctx, "ID"),
                "unique": _(ctx, "Unique"),
            },
        )
        for table in tables:
            await ctx.send("```" + table + "```")

    @commands.check(check.acl)
    @rolebuttons_.command(name="delete")
    async def rolebuttons_delete(self, ctx, view_id: int):
        """Delete View. Has to be confirmed.

        Args:
            view_id: ID of View.
        """
        view = RBView.get(ctx.guild, view_id)
        if view is None:
            await ctx.reply(_(ctx, "View with ID {id} not found.").format(id=view_id))
            return

        embed = await self._get_view_embed(ctx, view)
        embed.title = _(ctx, "Do you want to delete this view?")

        view = ConfirmView(ctx, embed)
        value = await view.send()

        if value is None:
            await ctx.send(_(ctx, "Deleting timed out."))
        elif value:
            view_ui = self.views.pop(view.id, None)
            if view_ui is not None:
                view_ui.stop()
            view.delete()
            view.save()
            await ctx.send(_(ctx, "View ID {id} deleted.").format(id=id))
        else:
            await ctx.send(_(ctx, "Deleting aborted."))

    @commands.check(check.acl)
    @rolebuttons_.command(name="info")
    async def rolebuttons_info(self, ctx, view_id: int):
        """Shows RoleButtons View information.

        Args:
            view_id: ID of View.
        """
        view = RBView.get(ctx.guild, view_id)
        if view is None:
            await ctx.reply(_(ctx, "View with ID {id} not found.").format(id=view_id))
            return

        embed = await self._get_view_embed(ctx, view)

        await ctx.send(embed=embed)

    @commands.check(check.acl)
    @rolebuttons_.group(name="option")
    async def rolebuttons_option_(self, ctx):
        await utils.discord.send_help(ctx)

    @commands.check(check.acl)
    @rolebuttons_option_.command(name="list")
    async def rolebuttons_option_list(self, ctx, view_id: int):
        """Shows list of View's Options

        Args:
            view_id: ID of View.
        """
        view = RBView.get(ctx.guild, view_id)
        if view is None:
            await ctx.reply(_(ctx, "View with ID {id} not found.").format(id=view_id))
            return

        tables = utils.text.create_table(
            view.options,
            {
                "idx": _(ctx, "ID"),
                "label": _(ctx, "Label"),
            },
        )
        for table in tables:
            await ctx.send("```" + table + "```")

    @commands.check(check.acl)
    @rolebuttons_option_.command(name="info")
    async def rolebuttons_option_info(self, ctx, option_id: int):
        """Shows RoleButtons View's Option information.

        Args:
            option_id: ID of Option.
        """
        option = RBOption.get(ctx.guild, option_id)
        if option is None:
            await ctx.reply(
                _(ctx, "Option with ID {id} not found.").format(id=option_id)
            )
            return

        embed = await self._get_option_embed(ctx, option)

        await ctx.send(embed=embed)

    @commands.check(check.acl)
    @rolebuttons_option_.command(name="add")
    async def rolebuttons_option_add(
        self,
        ctx,
        view_id: int,
        label: str,
        emoji: Optional[Union[nextcord.PartialEmoji, str]],
        *,
        description: Optional[str] = None,
    ):
        """Add option to View

        Args:
            view_id: ID of View.
            label: Option's label
            emoji: Option's emoji
            description: Option's description
        """
        view = RBView.get(ctx.guild, view_id)
        if view is None:
            await ctx.reply(_(ctx, "View with ID {id} not found.").format(id=view_id))
            return

        if emoji == "" or emoji == "None":
            emoji = None

        option = RBOption(
            view_id=view_id,
            label=label,
            description=description,
            emoji=rbutils.emoji_encode(self.bot, emoji) if emoji is not None else None,
        )

        view.add_option(option)

        await ctx.send(_(ctx, "Option added with ID {id}.").format(id=option.idx))

    @commands.check(check.acl)
    @rolebuttons_option_.command(name="remove")
    async def rolebuttons_option_remove(self, ctx, option_id):
        """Delete option. Has to be confirmed.

        Args:
            option_d: ID of option.
        """
        option = RBOption.get(ctx.guild, option_id)
        if option is None:
            await ctx.reply(
                _(ctx, "Option with ID {id} not found.").format(id=option_id)
            )
            return

        embed = await self._get_option_embed(ctx, option)
        embed.title = _(ctx, "Do you want to delete this option?")

        view = ConfirmView(ctx, embed)
        value = await view.send()

        if value is None:
            await ctx.send(_(ctx, "Deleting timed out."))
        elif value:
            option.delete()
            await ctx.send(_(ctx, "Option with ID {id} deleted.").format(id=option_id))
        else:
            await ctx.send(_(ctx, "Deleting aborted."))

    @commands.check(check.acl)
    @rolebuttons_.group(name="item")
    async def rolebuttons_item_(self, ctx):
        await utils.discord.send_help(ctx)

    @commands.check(check.acl)
    @rolebuttons_item_.command(name="add")
    async def rolebuttons_item_add(
        self,
        ctx,
        option_id: int,
        dc_item: Union[nextcord.Role, nextcord.abc.GuildChannel],
    ):
        """Add role or channel to option.

        Channel can be TextChannel, VoiceChannel, Stage or Category.

        Args:
            option_id: ID of Option
            dc_item: Mentioned Role or Channel.
        """
        option = RBOption.get(ctx.guild, option_id)
        if option is None:
            await ctx.reply(
                _(ctx, "Option with ID {id} not found.").format(id=option_id)
            )
            return

        type = (
            DiscordType.ROLE
            if isinstance(dc_item, nextcord.Role)
            else DiscordType.CHANNEL
        )

        item = RBItem(discord_id=dc_item.id, discord_type=type)

        option.add_item(item)

        await ctx.send(
            _(ctx, "Item {name} added to Option ID {id}").format(
                name=dc_item.name, id=option_id
            )
        )

    @commands.check(check.acl)
    @rolebuttons_item_.command(name="list")
    async def rolebuttons_item_list(self, ctx, option_id: int):
        """List Option's items."""
        option = RBOption.get(ctx.guild, option_id)
        if option is None:
            await ctx.reply(
                _(ctx, "Option with ID {id} not found.").format(id=option_id)
            )
            return

        roles, channels = await rbutils.process_items(option.items, ctx.guild)

        items = []

        for item in roles + channels:
            dummy = ItemDummy()
            dummy.id = item.id
            dummy.name = item.name
            dummy.type = item.__class__.__name__
            items.append(dummy)

        tables = utils.text.create_table(
            items,
            {
                "id": _(ctx, "ID"),
                "name": _(ctx, "Name"),
                "type": _(ctx, "Type"),
            },
        )
        for table in tables:
            await ctx.send("```" + table + "```")

    @commands.check(check.acl)
    @rolebuttons_item_.command(name="delete")
    async def rolebuttons_item_remove(
        self,
        ctx,
        option_id: int,
        dc_item: Union[nextcord.Role, nextcord.abc.GuildChannel, int],
    ):
        """Delete Option's items. Has to be confirmed."""
        option = RBOption.get(ctx.guild, option_id)
        if option is None:
            await ctx.reply(
                _(ctx, "Option with ID {id} not found.").format(id=dc_item.id)
            )
            return

        if isinstance(dc_item, int):  # THIS SHOULD BE MOVED INTO CORE -> UTILS
            role = nextcord.utils.get(ctx.guild.roles, id=dc_item)
            if role:
                dc_item = role
            else:
                channel = nextcord.utils.get(ctx.guild.channels, id=dc_item)
                if channel is not None:
                    dc_item = channel

        items = [item for item in option.items if item.discord_id == dc_item.id]

        if len(items) != 1:
            await ctx.reply(
                _(ctx, "Item {name} in Option ID {id} not found.").format(
                    name=dc_item.name, id=option_id
                )
            )
            return

        item = items[0]

        embed = self._get_item_embed(ctx, option, item)
        embed.title = _(ctx, "Do you want to delete this item?")

        view = ConfirmView(ctx, embed)
        value = await view.send()

        if value is None:
            await ctx.send(_(ctx, "Deleting timed out."))
        elif value:
            item.delete()
            await ctx.send(_(ctx, "Item {name} deleted.").format(name=dc_item.name))
        else:
            await ctx.send(_(ctx, "Deleting aborted."))

    @commands.check(check.acl)
    @rolebuttons_.group(name="set")
    async def rolebuttons_set_(self, ctx):
        await utils.discord.send_help(ctx)

    @commands.check(check.acl)
    @rolebuttons_.command(name="unique")
    async def rolebuttons_set_unique(self, ctx, view_id: int, unique: bool):
        """Changes View's unique attribute.

        When adding roles and channels, unique RoleButtons View
        will remove all other roles and channels from other options
        before adding selected option's roles and channels.

        """
        view = RBView.get(ctx.guild, view_id)
        if view is None:
            await ctx.reply(_(ctx, "View with ID {id} not found.").format(id=view_id))
            return

        view.unique = unique
        view.save()

        await ctx.reply(
            _(ctx, "View with ID {id} changed to {type}").format(
                id=view_id, type=_(ctx, "unique") if unique else _(ctx, "non-unique")
            )
        )

    @commands.check(check.acl)
    @rolebuttons_.group(name="message")
    async def rolebuttons_message_(self, ctx):
        await utils.discord.send_help(ctx)

    @commands.check(check.acl)
    @rolebuttons_message_.command(name="attach")
    async def rolebuttons_message_attach(
        self, ctx, channel_id: int, message_id: int, view_id: int
    ):
        """Attach View to Discord's Message.

        The Message must exist in provided channel
        and also it must be sent by bot.

        Args:
            channel_id: ID of channel, if 0 it uses actual channel
            message_id: ID of message
            view_id: ID of View
        """
        if channel_id == 0:
            channel_id = ctx.channel.id

        view = self.views[view_id]

        if view.view.guild_id != ctx.guild.id:
            ctx.reply(_(ctx, "View with ID {id} not found.").format(id=view_id))
            return

        message = await utils.discord.get_message(
            self.bot, ctx.guild.id, channel_id, message_id
        )

        if message is None:
            ctx.reply(_(ctx, "Message with ID {id} not found.").format(id=message_id))
            return

        if message.author != self.bot.user:
            ctx.reply(_(ctx, "Message author must be bot."))
            return

        view.view.add_message(message)
        await message.edit(view=view)

        await ctx.reply(
            _(ctx, "View with ID {view_id} attached to message {message_id}").format(
                view_id=view.view.idx, message_id=message.id
            )
        )

    @commands.check(check.acl)
    @rolebuttons_message_.command(name="detach")
    async def rolebuttons_message_dettach(self, ctx, message_id: int):
        """Detach View from Message.

        Args:
            message_id: Message ID
        """
        rbmessage = RBMessage.get(message_id)

        if rbmessage is None:
            await ctx.send(
                _(ctx, "Message with ID {id} has no RoleButtons View attached.").format(
                    id=message_id
                )
            )
            return

        message = await utils.discord.get_message(
            self.bot, ctx.guild.id, rbmessage.channel_id, message_id
        )

        view = rbmessage.rbview
        view.remove_message(rbmessage)

        if message is None:
            ctx.reply(
                _(
                    ctx, "Message with ID {id} not found on Discord. Detached anyway."
                ).format(id=message_id)
            )
            return

        await message.edit(view=None)

        ctx.reply(_(ctx, "Message with ID {id} detached.").format(id=message_id))


class ItemDummy:
    """
    Dummy class used for creatig item list.
    """

    pass


def setup(bot) -> None:
    bot.add_cog(RoleButtons(bot))
