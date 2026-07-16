import os
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


class TranslationBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.default(),
        )

    async def setup_hook(self):
        await self.load_extension("cogs.translate")
        await self.load_extension("cogs.image")
        await self.load_extension("cogs.palette")
        await self.load_extension("cogs.watt")
        await self.tree.sync()
        print("✓ Application commands synced globally.")

    async def on_ready(self):
        print(f"✓ Logged in as {self.user} (ID: {self.user.id})")
        print("------")


async def main():
    bot = TranslationBot()
    await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
