import os
import discord
import asyncio
import random
import io
from PIL import Image, ImageDraw
from discord import app_commands
from google import genai
from google.genai import types
from dotenv import load_dotenv
from ddgs import DDGS

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
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

def fetch_images_sync(query):
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

class TranslationApp(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("Application commands synced globally.")

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
        embed.set_footer(text="app by nazoge")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Error during translation: {e}")
        await interaction.followup.send("翻訳中にエラーが発生しました。しばらく経ってから再度お試しください。")

@client.tree.command(name="image", description="画像を検索します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(query="検索するキーワード")
async def image_search(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    images = await asyncio.to_thread(fetch_images_sync, query)

    if not images:
        await interaction.followup.send("画像が見つからなかったか、取得に失敗しました。時間をおいて再試行してください。")
        return

    view = ImageView(query, images, interaction.user.id)
    embed = discord.Embed(title=f"検索結果: {query}")
    embed.set_image(url=images[0])
    embed.set_footer(text=f"1 / {len(images)}")

    await interaction.followup.send(embed=embed, view=view)

@client.tree.command(name="palette", description="ランダムなカラーパレットを生成します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def random_palette(interaction: discord.Interaction):
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
    embed = discord.Embed(title="カラーパレット", description=description, color=discord.Color.from_rgb(*colors[0]))
    embed.set_image(url="attachment://palette.png")

    await interaction.followup.send(embed=embed, file=file)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)