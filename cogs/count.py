import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


class CountDatabase:
    def __init__(self, path: str = "data/counts.sqlite3"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(counts)").fetchall()
            }
            if columns and "guild_id" in columns:
                connection.execute("ALTER TABLE counts RENAME TO counts_by_guild")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS counts (
                    name TEXT PRIMARY KEY,
                    value INTEGER NOT NULL DEFAULT 0
                )
                """
            )

            if columns and "guild_id" in columns:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO counts (name, value)
                    SELECT name, value FROM counts_by_guild ORDER BY guild_id
                    """
                )
                connection.execute("DROP TABLE counts_by_guild")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def create(self, name: str, value: int) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO counts (name, value) VALUES (?, ?)",
                (name, value),
            )
            return cursor.rowcount == 1

    def get(self, name: str) -> int | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT value FROM counts WHERE name = ?",
                (name,),
            ).fetchone()
        return None if row is None else row["value"]

    def update(self, name: str, value: int) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE counts SET value = ? WHERE name = ?",
                (value, name),
            )
            return cursor.rowcount == 1

    def delete(self, name: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM counts WHERE name = ?",
                (name,),
            )
            return cursor.rowcount == 1

    def list(self) -> list[sqlite3.Row]:
        with self._connection() as connection:
            return connection.execute(
                "SELECT name, value FROM counts ORDER BY name",
            ).fetchall()


class CountUserAccess:
    def __init__(self, path: str = "data/count_users.json"):
        self.path = Path(path)

    def is_allowed(self, user_id: int) -> bool:
        try:
            with self.path.open(encoding="utf-8") as file:
                settings = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return False

        allowed_users = settings.get("allowed_user_ids", [])
        return str(user_id) in {str(allowed_user_id) for allowed_user_id in allowed_users}


count_group = app_commands.Group(name="count", description="カウントを管理します")
count_group = app_commands.allowed_installs(guilds=True, users=True)(count_group)
count_group = app_commands.allowed_contexts(
    guilds=True, dms=True, private_channels=True
)(count_group)


class CountCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.database = CountDatabase()
        self.access = CountUserAccess()

    @count_group.command(name="create", description="新しいカウントを作成します")
    @app_commands.describe(name="カウント名", initial_value="初期値")
    async def count_create(
        self, interaction: discord.Interaction, name: str, initial_value: int = 0
    ):
        if not await self._require_user(interaction):
            return

        name = name.strip()
        if not name or len(name) > 50:
            await interaction.response.send_message("カウント名は1〜50文字で指定してください。", ephemeral=True)
            return

        if self.database.create(name, initial_value):
            await interaction.response.send_message(f"`{name}` を {initial_value} で作成しました。")
        else:
            await interaction.response.send_message(f"`{name}` はすでに存在します。", ephemeral=True)

    @count_group.command(name="add", description="カウントを増減します")
    @app_commands.describe(name="カウント名", amount="増減する値")
    async def count_add(self, interaction: discord.Interaction, name: str, amount: int = 1):
        if not await self._require_user(interaction):
            return

        name = name.strip()
        current = self.database.get(name)
        if current is None:
            await interaction.response.send_message(f"`{name}` は見つかりません。", ephemeral=True)
            return

        new_value = current + amount
        self.database.update(name, new_value)
        await interaction.response.send_message(f"`{name}` は **{new_value}** になりました。")

    @count_group.command(name="set", description="カウントを指定した値に変更します")
    @app_commands.describe(name="カウント名", value="設定する値")
    async def count_set(self, interaction: discord.Interaction, name: str, value: int):
        if not await self._require_user(interaction):
            return

        name = name.strip()
        if not self.database.update(name, value):
            await interaction.response.send_message(f"`{name}` は見つかりません。", ephemeral=True)
            return
        await interaction.response.send_message(f"`{name}` を **{value}** に設定しました。")

    @count_group.command(name="show", description="カウントの現在値を表示します")
    @app_commands.describe(name="カウント名")
    async def count_show(self, interaction: discord.Interaction, name: str):
        if not await self._require_user(interaction):
            return

        name = name.strip()
        value = self.database.get(name)
        if value is None:
            await interaction.response.send_message(f"`{name}` は見つかりません。", ephemeral=True)
            return
        await interaction.response.send_message(f"**{name}: {value}**")

    @count_group.command(name="list", description="カウント一覧を表示します")
    async def count_list(self, interaction: discord.Interaction):
        if not await self._require_user(interaction):
            return

        rows = self.database.list()
        if not rows:
            await interaction.response.send_message("カウントはまだありません。", ephemeral=True)
            return
        description = "\n".join(f"**{row['name']}:** {row['value']}" for row in rows)
        await interaction.response.send_message(description)

    @count_group.command(name="delete", description="カウントを削除します")
    @app_commands.describe(name="カウント名")
    async def count_delete(self, interaction: discord.Interaction, name: str):
        if not await self._require_user(interaction):
            return

        name = name.strip()
        if not self.database.delete(name):
            await interaction.response.send_message(f"`{name}` は見つかりません。", ephemeral=True)
            return
        await interaction.response.send_message(f"`{name}` を削除しました。")

    async def _require_user(self, interaction: discord.Interaction) -> bool:
        if not self.access.is_allowed(interaction.user.id):
            await interaction.response.send_message(
                "このコマンドを使用する権限がありません。", ephemeral=True
            )
            return False
        return True


async def setup(bot: commands.Bot):
    bot.tree.add_command(count_group)
    await bot.add_cog(CountCog(bot))
