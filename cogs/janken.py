import random

import discord
from discord import app_commands
from discord.ext import commands


class JankenCog(commands.Cog):
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.command(name="janken", description="Botとジャンケンします")
    @app_commands.describe(hand="出す手")
    @app_commands.choices(
        hand=[
            app_commands.Choice(name="グー", value="グー"),
            app_commands.Choice(name="チョキ", value="チョキ"),
            app_commands.Choice(name="パー", value="パー"),
        ]
    )
    async def janken(self, interaction: discord.Interaction, hand: app_commands.Choice[str]):
        bot_hand = random.choice(["グー", "チョキ", "パー"])
        if hand.value == bot_hand:
            result = "あいこ"
        elif (hand.value, bot_hand) in (("グー", "チョキ"), ("チョキ", "パー"), ("パー", "グー")):
            result = "あなたの勝ち"
        else:
            result = "Botの勝ち"

        await interaction.response.send_message(
            f"あなた: **{hand.value}**\nBot: **{bot_hand}**\n\n## {result}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(JankenCog(bot))
