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

        try:
            user = await self.bot.fetch_user(uid)
        except discord.NotFound:
            await interaction.response.send_message("指定したユーザーIDが見つかりません。", ephemeral=True)
            return
        except discord.HTTPException as exc:
            await interaction.response.send_message(f"ユーザー情報の取得に失敗しました: {exc.text}", ephemeral=True)
            return

        embed = discord.Embed(title="ユーザー情報", color=discord.Color.blue())
        embed.set_thumbnail(url=user.display_avatar.url)
        if user.banner:
            embed.set_image(url=user.banner.url)

        embed.add_field(name="ユーザー名", value=user.name, inline=True)
        embed.add_field(name="グローバル表示名", value=user.global_name or "未設定", inline=True)
        embed.add_field(name="表示名", value=user.display_name, inline=True)
        embed.add_field(name="ユーザーID", value=f"`{user.id}`", inline=False)
        embed.add_field(name="識別子", value=f"#{user.discriminator}" if user.discriminator and user.discriminator != "0" else "未設定", inline=True)
        embed.add_field(name="Bot", value="はい" if user.bot else "いいえ", inline=True)
        embed.add_field(name="システムアカウント", value="はい" if user.system else "いいえ", inline=True)
        embed.add_field(name="公式認証済み", value="はい" if user.verified else "不明 / いいえ", inline=True)
        embed.add_field(name="MFA (2段階認証)", value="有効" if user.mfa_enabled else "無効 / 不明", inline=True)

        nitro_text = {0: "なし", 1: "Nitro Classic", 2: "Nitro", 3: "Nitro Basic"}.get(user.premium_type, "不明")
        embed.add_field(name="Nitro", value=nitro_text, inline=True)

        if user.public_flags:
            flags = [name.replace("_", " ").title() for name, value in user.public_flags if value]
            embed.add_field(name="公開バッジ", value=", ".join(flags) or "なし", inline=False)

        embed.add_field(name="アバター", value=f"[リンク]({user.display_avatar.url})" if user.avatar else "デフォルト", inline=True)
        embed.add_field(name="バナー", value=f"[リンク]({user.banner.url})" if user.banner else "未設定", inline=True)
        embed.add_field(name="アクセントカラー", value=str(user.accent_color) if user.accent_color else "未設定", inline=True)
        embed.add_field(name="作成日時", value=discord.utils.format_dt(user.created_at, style="F"), inline=False)
        embed.add_field(name="作成日時 (相対)", value=discord.utils.format_dt(user.created_at, style="R"), inline=False)

        embed.set_footer(text=f"リクエスト: {interaction.user}")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(LookupCog(bot))
