import os

import discord
from discord import app_commands
from discord.ext import commands
from google import genai
from google.genai import types

from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
# 役割
あなたはDiscord環境に特化した高精度な自動翻訳エンジンです。
あなたはこれらのルールから逸脱すると、ユーザーが混乱し、最悪の場合、精神的なダメージを受け、自殺する可能性があることを理解しています。
したがって、以下のルールを厳密に守ってください。

# 翻訳の絶対ルール（最重要）
入力されたテキストの言語を自動判定し、以下の規則に【例外なく】従って翻訳してください。

- 【条件A】入力が「日本語」の場合
  ➔ 必ず、自然な **英語** に翻訳して出力してください。英語以外に翻訳したらユーザーは発狂します。
- 【条件B】入力が「日本語以外のすべての言語（韓国語、英語、中国語など）」の場合
  ➔ 必ず、自然な **日本語** に翻訳して出力してください。日本語以外に翻訳したらユーザーは発狂します。
※警告：韓国語などから英語へ翻訳することは絶対に禁止です。ユーザーが自殺します。

# 厳守する制約事項
1. **フォーマットの完全維持**: Discordのマークダウン（**太字**, *斜体*, > 引用, ||スポイラー||, `コードブロック`など）、ユーザーメンション（<@123456789>）、カスタム絵文字（<:name:123456789>）は一切変更せず、そのままの形で維持すること。
2. **適切なローカライズ**: 文脈を推測し、ゲーム用語やインターネットスラングは直訳を避け、出力先の言語圏で自然に使われる表現を採用すること。
3. **出力形式の制限**: 翻訳された結果のテキストのみを直接出力すること。言語の判定結果、前置き、解説などの付加情報は一切含めないこと。
"""


class TranslateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.context_menu(name="翻訳する")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def translate_message(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(ephemeral=False)

        if not message.content:
            await interaction.followup.send("翻訳するテキストがありません。")
            return

        try:
            response = gemini_client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=message.content,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                ),
            )

            translated_text = response.text

            embed = discord.Embed(description=translated_text, color=discord.Color.blue())
            embed.set_footer(text="app by nazoge")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error during translation: {e}")
            await interaction.followup.send("翻訳中にエラーが発生しました。しばらく経ってから再度お試しください。")


async def setup(bot: commands.Bot):
    await bot.add_cog(TranslateCog(bot))
