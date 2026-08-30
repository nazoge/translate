import discord
from discord import app_commands
from discord.ext import commands


class LookupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="lookup", description="指定したユーザーIDのアカウント情報を表示します")
    @app_commands.describe(user_id="調べるユーザーID")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def lookup(self, interaction: discord.Interaction, user_id: str):
        try:
            uid = int(user_id)
        except ValueError:
            await interaction.response.send_message("ユーザーIDは数字で指定してください。", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)

        try:
            user = await self.bot.fetch_user(uid)
        except discord.NotFound:
            await interaction.followup.send("指定したユーザーIDが見つかりません。", ephemeral=True)
            return
        except discord.HTTPException as exc:
            await interaction.followup.send(f"ユーザー情報の取得に失敗しました: {exc.text}", ephemeral=True)
            return

        try:
            embed = discord.Embed(title="ユーザー情報", color=discord.Color.blue())
            embed.set_thumbnail(url=user.display_avatar.url)
            if user.banner:
                embed.set_image(url=user.banner.url)

            fields = [
                ("ユーザー名", user.name, True),
                ("グローバル表示名", user.global_name or "未設定", True),
                ("表示名", user.display_name, True),
                ("ユーザーID", f"`{user.id}`", False),
                ("識別子", f"#{user.discriminator}" if user.discriminator and user.discriminator != "0" else "未設定", True),
                ("Bot", "はい" if user.bot else "いいえ", True),
                ("システムアカウント", "はい" if user.system else "いいえ", True),
                ("公式認証済み", "はい" if user.verified else "不明 / いいえ", True),
                ("MFA (2段階認証)", "有効" if user.mfa_enabled else "無効 / 不明", True),
            ]

            nitro_text = {0: "なし", 1: "Nitro Classic", 2: "Nitro", 3: "Nitro Basic"}.get(user.premium_type, "不明")
            fields.append(("Nitro", nitro_text, True))

            if user.public_flags:
                flags = [name.replace("_", " ").title() for name, value in user.public_flags if value]
                fields.append(("公開バッジ", ", ".join(flags) or "なし", False))

            fields.extend([
                ("アバター", f"[リンク]({user.display_avatar.url})" if user.avatar else "デフォルト", True),
                ("バナー", f"[リンク]({user.banner.url})" if user.banner else "未設定", True),
                ("アクセントカラー", str(user.accent_color) if user.accent_color else "未設定", True),
                ("作成日時", discord.utils.format_dt(user.created_at, style="F"), False),
                ("作成日時 (相対)", discord.utils.format_dt(user.created_at, style="R"), False),
            ])

            for name, value, inline in fields[:25]:
                embed.add_field(name=name, value=value, inline=inline)

            embed.set_footer(text=f"リクエスト: {interaction.user}")
            await interaction.followup.send(embed=embed)
        except Exception as exc:
            await interaction.followup.send(f"Embed の生成中にエラーが発生しました: {exc}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(LookupCog(bot))
