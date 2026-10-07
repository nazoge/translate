import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
import pytz
from discord import app_commands
from discord.ext import commands

from utils.database import (
    add_reminder,
    delete_reminder,
    delete_reminders_by_user,
    disable_reminder,
    get_enabled_reminders,
    get_reminder_by_id,
    get_reminders_by_user,
    init_db,
    update_reminder_time,
)
from utils.time_parser import (
    format_datetime,
    format_interval,
    parse_interval,
    parse_time,
)

DEFAULT_TIMEZONE = "Asia/Tokyo"


async def timezone_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    current_lower = current.lower()
    matches = [
        tz
        for tz in pytz.all_timezones
        if current_lower in tz.lower()
    ][:25]
    return [app_commands.Choice(name=tz, value=tz) for tz in matches]


class ConfirmClearView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.confirmed = False

    @discord.ui.button(label="削除する", style=discord.ButtonStyle.danger)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "他のユーザーの操作はできません。", ephemeral=False
            )
            return
        await delete_reminders_by_user(self.user_id)
        self.confirmed = True
        await interaction.response.edit_message(
            content="✅ すべてのリマインダーを削除しました。", view=None
        )
        self.stop()

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "他のユーザーの操作はできません。", ephemeral=False
            )
            return
        await interaction.response.edit_message(
            content="キャンセルしました。", view=None
        )
        self.stop()


class ReminderCog(commands.Cog):
    remind_group = app_commands.Group(
        name="remind", description="リマインダー関連コマンド"
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.scheduler_task: Optional[asyncio.Task] = None

    async def cog_load(self):
        await init_db()
        self.scheduler_task = self.bot.loop.create_task(self.scheduler_loop())

    async def cog_unload(self):
        if self.scheduler_task:
            self.scheduler_task.cancel()

    async def scheduler_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                reminders = await get_enabled_reminders()
                now = datetime.now(timezone.utc)
                for reminder in reminders:
                    remind_at = datetime.fromisoformat(reminder["remind_at"])
                    if remind_at <= now:
                        await self.fire_reminder(reminder)
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Scheduler error: {e}")
                await asyncio.sleep(10)

    async def fire_reminder(self, reminder: dict):
        channel = self.bot.get_channel(reminder["channel_id"])
        if channel is None:
            await disable_reminder(reminder["id"])
            return

        try:
            embed = discord.Embed(
                title="⏰ リマインダー",
                description=reminder["content"],
                color=discord.Color.green(),
            )
            embed.set_footer(text=f"ID: {reminder['id']}")
            await channel.send(
                f"<@{reminder['user_id']}>",
                embed=embed,
                tts=bool(reminder["tts"]),
            )
        except discord.Forbidden:
            print(f"Cannot send reminder {reminder['id']}: Forbidden")
        except Exception as e:
            print(f"Failed to send reminder {reminder['id']}: {e}")

        interval_str = reminder.get("interval")
        expires_at_str = reminder.get("expires_at")
        if interval_str:
            try:
                interval = parse_interval(interval_str)
                next_at = datetime.fromisoformat(reminder["remind_at"]) + interval
                expires_at = (
                    datetime.fromisoformat(expires_at_str)
                    if expires_at_str
                    else None
                )
                if expires_at and next_at > expires_at:
                    await disable_reminder(reminder["id"])
                else:
                    await update_reminder_time(reminder["id"], next_at)
            except Exception as e:
                print(f"Interval scheduling error: {e}")
                await disable_reminder(reminder["id"])
        else:
            await disable_reminder(reminder["id"])

    @remind_group.command(name="set", description="リマインダーを設定します")
    @app_commands.describe(
        time="リマインドまでの時間（例: 10m, 1h, 2d）または絶対日時（例: 2026-10-04 18:00）",
        content="リマインド内容",
        channel="リマインドを送信するチャンネル（未指定時は実行チャンネル）",
        interval="繰り返し間隔（例: 1h, 30m）",
        expires="繰り返しを終了する日時",
        tts="TTSで読み上げるかどうか",
        timezone="日時指定のタイムゾーン",
    )
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    async def remind_set(
        self,
        interaction: discord.Interaction,
        time: str,
        content: str,
        channel: Optional[discord.TextChannel] = None,
        interval: Optional[str] = None,
        expires: Optional[str] = None,
        tts: Optional[bool] = False,
        timezone: Optional[str] = DEFAULT_TIMEZONE,
    ):
        await interaction.response.defer(ephemeral=False)

        try:
            remind_at = parse_time(time, timezone or DEFAULT_TIMEZONE)
        except ValueError as e:
            await interaction.followup.send(str(e))
            return

        parsed_interval = None
        if interval:
            try:
                parsed_interval = parse_interval(interval)
            except ValueError as e:
                await interaction.followup.send(str(e))
                return

        parsed_expires = None
        if expires:
            try:
                parsed_expires = parse_time(expires, timezone or DEFAULT_TIMEZONE)
            except ValueError as e:
                await interaction.followup.send(str(e))
                return

        if parsed_expires and parsed_interval and parsed_expires <= remind_at:
            await interaction.followup.send(
                "❌ expiresは最初のリマインド時刻より後にしてください"
            )
            return

        target_channel = channel or interaction.channel
        if target_channel is None:
            await interaction.followup.send("❌ チャンネルが特定できません")
            return

        permissions = target_channel.permissions_for(interaction.guild.me)
        if not permissions.send_messages:
            await interaction.followup.send(
                "❌ 指定したチャンネルにBotがメッセージを送信できません"
            )
            return

        try:
            reminder_id = await add_reminder(
                user_id=interaction.user.id,
                channel_id=target_channel.id,
                content=content,
                remind_at=remind_at,
                guild_id=interaction.guild_id,
                interval=interval,
                expires_at=parsed_expires,
                tts=tts or False,
                timezone_str=timezone or DEFAULT_TIMEZONE,
            )
        except Exception as e:
            print(f"Database error: {e}")
            await interaction.followup.send(
                "❌ リマインダーの保存中にエラーが発生しました"
            )
            return

        tz_str = timezone or DEFAULT_TIMEZONE
        formatted = format_datetime(remind_at, tz_str)
        response = (
            f"⏰ リマインダーを設定しました\n\n"
            f"内容：{content}\n"
            f"日時：{formatted}"
        )
        if parsed_interval:
            response += f"\n🔁 {format_interval(parsed_interval)}"
        if parsed_expires:
            response += f"\n🛑 終了：{format_datetime(parsed_expires, tz_str)}"
        response += f"\nID: {reminder_id}"

        await interaction.followup.send(response)

    @app_commands.command(name="reminders", description="自分のリマインダー一覧を表示します")
    async def reminders(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        rows = await get_reminders_by_user(interaction.user.id)
        if not rows:
            await interaction.followup.send("📋 リマインダーはありません")
            return

        lines = ["📋 あなたのリマインダー"]
        for row in rows:
            tz_str = row.get("timezone") or DEFAULT_TIMEZONE
            remind_at = datetime.fromisoformat(row["remind_at"])
            lines.append(f"\nID: {row['id']}")
            lines.append(f"⏰ {format_datetime(remind_at, tz_str)}")
            if row.get("interval"):
                interval = parse_interval(row["interval"])
                lines.append(f"🔁 {format_interval(interval)}")
            lines.append(f"📝 {row['content']}")

        await interaction.followup.send("\n".join(lines))

    @remind_group.command(name="cancel", description="リマインダーを削除します")
    @app_commands.describe(id="削除するリマインダーのID")
    async def remind_cancel(self, interaction: discord.Interaction, id: int):
        await interaction.response.defer(ephemeral=False)
        reminder = await get_reminder_by_id(id)
        if reminder is None:
            await interaction.followup.send("❌ リマインダーが存在しません")
            return
        if reminder["user_id"] != interaction.user.id:
            await interaction.followup.send(
                "❌ 自分が作成したリマインダーのみ削除できます"
            )
            return

        await delete_reminder(id)
        await interaction.followup.send(f"✅ リマインダー ID:{id} を削除しました")

    @remind_group.command(name="edit", description="リマインダーの時刻を変更します")
    @app_commands.describe(
        id="編集するリマインダーのID",
        time="新しいリマインド時刻",
        timezone="日時指定のタイムゾーン",
    )
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    async def remind_edit(
        self,
        interaction: discord.Interaction,
        id: int,
        time: str,
        timezone: Optional[str] = DEFAULT_TIMEZONE,
    ):
        await interaction.response.defer(ephemeral=False)
        reminder = await get_reminder_by_id(id)
        if reminder is None:
            await interaction.followup.send("❌ リマインダーが存在しません")
            return
        if reminder["user_id"] != interaction.user.id:
            await interaction.followup.send(
                "❌ 自分が作成したリマインダーのみ編集できます"
            )
            return

        try:
            new_time = parse_time(time, timezone or DEFAULT_TIMEZONE)
        except ValueError as e:
            await interaction.followup.send(str(e))
            return

        await update_reminder_time(id, new_time)
        tz_str = timezone or DEFAULT_TIMEZONE
        await interaction.followup.send(
            f"✅ リマインダー ID:{id} の時刻を {format_datetime(new_time, tz_str)} に変更しました"
        )

    @remind_group.command(name="clear", description="自分のリマインダーをすべて削除します")
    async def remind_clear(self, interaction: discord.Interaction):
        view = ConfirmClearView(interaction.user.id)
        await interaction.response.send_message(
            "本当にすべて削除しますか？", view=view, ephemeral=False
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ReminderCog(bot))
