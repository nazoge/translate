import os
import discord
from discord import app_commands
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
あなたはDiscord環境に特化した高精度な翻訳エンジンです。
入力されたテキストの言語を自動で判定し、以下のルールに厳密に従って翻訳してください。

【言語指定】
- 入力が日本語の場合：自然な英語に翻訳する
- 入力が日本語以外（英語、韓国語、中国語など）の場合：自然な日本語に翻訳する

【厳守する制約事項】
1. Discordのマークダウン構文（**太字**, *斜体*, > 引用, ||スポイラー||, `コードブロック` など）は完全に維持すること。
2. ユーザーメンション（<@123456789>）、カスタム絵文字（<:name:123456789>）等は一切変更せず維持すること。
3. 文脈を推測し、ゲーム用語やインターネットスラングは対象言語圏の自然な表現を採用すること。
4. 翻訳結果のみを出力し、解説等の付加情報は一切含めないこと。
"""

class TranslationApp(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("Application commands synced.")

client = TranslationApp()

@client.tree.context_menu(name="翻訳する")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def translate_message(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.defer(ephemeral=False)

    if not message.content:
        await interaction.followup.send("翻訳するテキストがありません。")
        return

    try:
        response = gemini_client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=message.content,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
            )
        )

        translated_text = response.text

        embed = discord.Embed(
            description=translated_text,
            color=discord.Color.blue()
        )
        embed.set_footer(text="code by nazoge")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Error during translation: {e}")
        await interaction.followup.send("翻訳中にエラーが発生しました。しばらく経ってから再度お試しください。")

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)