import random
import discord
from discord import app_commands
from discord.ext import commands


class GameRandomCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="game_random",
        description="登録されたゲームからランダムに一つ選びます",
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def game_random(self, interaction: discord.Interaction):
        games = ["EFT", "Minecraft", "LoL"]
        # 必要とあればここにゲームを追加
        chosen = random.choice(games)
        await interaction.response.send_message(f"{chosen}")


async def setup(bot: commands.Bot):
    await bot.add_cog(GameRandomCog(bot))