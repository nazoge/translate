import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import parse_time_to_seconds


class WattCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="wcal", description="電子レンジなどのワット計算を行います")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(
        original_watt="元のワット数（W）",
        time="加熱時間（秒、または MM:SS 形式）",
        target_watt="変換先のワット数（W）",
    )
    async def watt_calculator(self, interaction: discord.Interaction, original_watt: float, time: str, target_watt: float):
        await interaction.response.defer()

        try:
            total_seconds = parse_time_to_seconds(time)

            if total_seconds <= 0:
                await interaction.followup.send("時間は0より大きい値を指定してください。")
                return

            if original_watt <= 0 or target_watt <= 0:
                await interaction.followup.send("ワット数は0より大きい値を指定してください。")
                return

            energy = original_watt * total_seconds / 3600
            converted_seconds = energy * 3600 / target_watt

            minutes = int(converted_seconds // 60)
            seconds = int(converted_seconds % 60)
            remaining_ms = int((converted_seconds % 1) * 1000)

            time_str = f"{minutes}:{seconds:02d}"
            if remaining_ms > 0:
                time_str += f".{remaining_ms}ms"

            embed = discord.Embed(
                title="ワット計算結果",
                description=f"**元の設定:** {original_watt}W で {time}\n**変換結果:** {target_watt}W で **{time_str}** ({converted_seconds:.2f}秒)",
                color=discord.Color.green(),
            )
            embed.set_footer(text="app by nazoge")

            await interaction.followup.send(embed=embed)

        except ValueError as e:
            await interaction.followup.send(f"エラー: {str(e)}")
        except Exception as e:
            print(f"Error during watt calculation: {e}")
            await interaction.followup.send("ワット計算中にエラーが発生しました。")


async def setup(bot: commands.Bot):
    await bot.add_cog(WattCog(bot))
