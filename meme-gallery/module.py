from typing import List, Set

import discord
from discord.ext import commands

from pie import utils, check, i18n
from pie.utils.objects import ConfirmView, ScrollableEmbed

from io import BytesIO

_ = i18n.Translator("modules/fsi").translate

class MemeGallery(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # # HELPER FUNCTIONS
    # def _create_embeds(ctx, title: str, description: str) -> List[discord.Embed]:
    #     elements = []
    #     """Create embed for member list.
    #     Args:
    #         ctx: Command context.
    #         option: Item's title.
    #         description: list of items.
    #     Returns: :class:`discord.Embed` information embed
    #     """

    
    #     page = utils.discord.create_embed(
    #         author=ctx.author,
    #         title=title,
    #         description="\n".join(description[i : i + chunk_size]),
    #     )

    #     elements.append(page)

    #     return elements

    # def _get_intersection(role_base: str, role_remove: str) -> Set[discord.Member]:
    #     base_members = set(role_base.members)
    #     remove_members = set(role_remove.members)

    #     role_intersection = base_members & remove_members
    #     return role_intersection

    # MAIN
    @commands.guild_only()
    @commands.group(name="memegallery")
    @check.acl2(check.ACLevel.MOD)
    async def memegallery_(self, ctx):
        """
        Preview and remove selected roles from members with specified based role.
        """
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.MOD)
    @memegallery_.command(name="spusteni")
    async def memegallery_execute(
        self, ctx,
    ):
        """
        Execute command to remove selected role from members with base role.
        """

        REACTION_LIMIT = 1
        TARGET_CHANNEL_ID = 992161562389381281

        target_channel = self.bot.get_channel(TARGET_CHANNEL_ID)
        if not target_channel:
            await ctx.reply("Nemohu najít cílový kanál.")
            return

        async for message in ctx.channel.history(limit=100):
            total_reactions = sum(reaction.count for reaction in message.reactions)
            if total_reactions >= REACTION_LIMIT:
                # Sestavení informací o reakcích
                reactions_str = " ".join([f"{str(reaction)} {reaction.count}x" for reaction in message.reactions if reaction.count >= REACTION_LIMIT])

                # Vytvoření a odeslání embedu s informacemi a obrázkem
                embed = discord.Embed(color=discord.Color.blue())
                embed.title = "Odkaz na originál"
                embed.url = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
                embed.add_field(name="Autor", value=message.author.display_name, inline=True)
                embed.add_field(name="Počet reakcí", value=reactions_str, inline=True)

                # Přílohy se odesílají podle typu
                image_sent = False
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'gif']):
                        # Přílohu obrázku přidáme do embedu
                        embed.set_image(url=attachment.url)
                        image_sent = True

                # Odeslání embedu s obrázkem
                if image_sent:
                    await target_channel.send(embed=embed)

                # Odeslání videa samostatně
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['mp4', 'mov', 'webm']):
                        # Pokud byl obrázek již odeslán v embedu, video pošleme samostatně
                        if not image_sent:
                            # Odeslání embedu bez obrázku, pokud ještě nebyl odeslán
                            await target_channel.send(embed=embed)
                            image_sent = True  # Zabráníme opakovanému odeslání embedu
                        await target_channel.send(attachment.url)

async def setup(bot) -> None:
    await bot.add_cog(MemeGallery(bot))