import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import fetch_images_sync, ImageView


class ImageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="image", description="画像を検索します")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(query="検索するキーワード")
    async def image_search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        images = await asyncio.to_thread(fetch_images_sync, query)

        if not images:
            await interaction.followup.send(
                "画像が見つからなかったか、取得に失敗しました。時間をおいて再試行してください。"
            )
            return

        view = ImageView(query, images, interaction.user.id)
        embed = discord.Embed(title=f"検索結果: {query}")
        embed.set_image(url=images[0])
        embed.set_footer(text=f"1 / {len(images)}")

        await interaction.followup.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(ImageCog(bot))
