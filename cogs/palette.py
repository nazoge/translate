import io
import random

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw


class PaletteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="palette", description="ランダムなカラーパレットを生成します")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def random_palette(self, interaction: discord.Interaction):
        await interaction.response.defer()

        colors = []
        hex_colors = []
        for _ in range(5):
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            colors.append((r, g, b))
            hex_colors.append(f"#{r:02x}{g:02x}{b:02x}".upper())

        width = 500
        height = 100
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)

        for i, color in enumerate(colors):
            draw.rectangle([i * 100, 0, (i + 1) * 100, height], fill=color)

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        file = discord.File(fp=buffer, filename="palette.png")

        description = "\n".join([f"**Color {i+1}:** `{hc}`" for i, hc in enumerate(hex_colors)])
        embed = discord.Embed(
            title="カラーパレット", description=description, color=discord.Color.from_rgb(*colors[0])
        )
        embed.set_image(url="attachment://palette.png")

        await interaction.followup.send(embed=embed, file=file)


async def setup(bot: commands.Bot):
    await bot.add_cog(PaletteCog(bot))
