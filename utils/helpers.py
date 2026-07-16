import asyncio
from typing import List

import discord
from PIL import Image, ImageDraw
from ddgs import DDGS


def parse_time_to_seconds(time_str: str) -> float:
    time_str = time_str.strip()
    parts = time_str.split(':')

    try:
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError("無効な時間フォーマットです")
    except ValueError:
        raise ValueError("時間の値が数値ではありません")


def fetch_images_sync(query: str) -> List[str]:
    try:
        results = DDGS().images(query, max_results=15)
        if not results:
            return []
        return [item.get("thumbnail") or item.get("image") for item in results]
    except Exception as e:
        print(f"Image Search Error: {e}")
        return []


class ImageView(discord.ui.View):

    def __init__(self, query: str, images: list, user_id: int):
        super().__init__(timeout=600)
        self.query = query
        self.images = images
        self.user_id = user_id
        self.index = 0

    async def update_message(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"検索結果: {self.query}")
        embed.set_image(url=self.images[self.index])
        embed.set_footer(text=f"{self.index + 1} / {len(self.images)}")

        try:
            await interaction.edit_original_response(embed=embed, view=self)
        except discord.errors.NotFound:
            pass
        except Exception as e:
            print(f"Edit failed: {e}")

    @discord.ui.button(label="前へ", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("他の人の検索結果は操作できません。", ephemeral=True)
            return

        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            return

        self.index = (self.index - 1) % len(self.images)
        await self.update_message(interaction)

    @discord.ui.button(label="次へ", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("他の人の検索結果は操作できません。", ephemeral=True)
            return

        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            return

        self.index = (self.index + 1) % len(self.images)
        await self.update_message(interaction)
