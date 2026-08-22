# Translate Bot

Discord 上でメッセージを右クリックして翻訳できる多機能ボットです。日本語↔英語・日本語↔その他言語の自然な翻訳を Gemini を使って実行し、画像検索・カラーパレット生成・ワット計算・カウント・ジャンケンなどの便利機能も備えています。

## 機能

### 翻訳（コンテキストメニュー）

- Discord のメッセージを右クリック／長押しして「翻訳する」を選択できます
- 日本語 → 英語、それ以外の言語 → 日本語に自動判定して翻訳します
- Discord Markdown（太字、斜体、引用、スポイラー、コードブロックなど）、メンション、カスタム絵文字を保持します
- 翻訳結果は Embed で返信されます

### スラッシュコマンド

| コマンド | 説明 | インストール形態 |
| --- | --- | --- |
| `/image <query>` | DuckDuckGo で画像を検索し、前後ボタンで切り替え | サーバー・ユーザー |
| `/palette` | ランダムな 5 色カラーパレットを生成 | サーバー・ユーザー |
| `/wcal <元W> <時間> <先W>` | 電子レンジなどの加熱時間をワット換算 | サーバー・ユーザー |
| `/count create/add/set/show/list/delete` | SQLite でカウントを管理 | サーバー・ユーザー |
| `/janken <手>` | Bot とジャンケン | サーバー・ユーザー |

- `/count` は `data/count_users.json` で許可されたユーザーのみ利用できます（サーバー・ユーザーインストール両方で共通）
- 時間指定は `秒` または `MM:SS`、`HH:MM:SS` 形式が利用できます

## 必要な環境

- Python 3.11
- Discord Bot Token
- Gemini API Key

## セットアップ

1. 依存パッケージをインストールします

   ```bash
   pip install -r requirements.txt
   ```

2. プロジェクト直下に `.env` ファイルを作成し、次の環境変数を設定します

   ```env
   DISCORD_TOKEN=your_discord_bot_token
   GEMINI_API_KEY=your_gemini_api_key
   ```

   `example.env` をコピーして使うこともできます。

3. アプリケーションを起動します

   ```bash
   python main.py
   ```

   起動時にグローバルスラッシュコマンドが自動同期されます。

## Docker で起動

```bash
docker compose up --build
```

`data` ディレクトリは `bot-data` ボリュームに永続化されます。

## ファイル構成

- `main.py` : Discord ボット本体・Cog 読み込み
- `requirements.txt` : Python 依存関係
- `Dockerfile` : Docker イメージ定義
- `docker-compose.yml` : Docker Compose 設定
- `example.env` : 環境変数のテンプレート
- `cogs/translate.py` : コンテキストメニュー翻訳機能
- `cogs/image.py` : 画像検索機能
- `cogs/palette.py` : カラーパレット生成機能
- `cogs/watt.py` : ワット計算機能
- `cogs/count.py` : SQLite カウント機能
- `cogs/janken.py` : ジャンケン機能
- `utils/helpers.py` : 画像検索・時間パース・ボタン UI 共通処理
- `data/counts.sqlite3` : カウントデータ（自動作成）
- `data/count_users.json` : カウント機能を利用できるユーザー ID 一覧

## カウント機能の権限設定

`/count` コマンドを利用できるユーザーを `data/count_users.json` に文字列で指定してください。

```json
{
  "allowed_user_ids": [
    "123456789012345678"
  ]
}
```

## 備考

- ユーザーインストールコマンドを利用する場合は、Discord Developer Portal の Installation 設定で有効にし、Bot 再起動後にコマンドを同期してください
- 翻訳モデルには `gemini-3.1-flash-lite` を使用しています
- カウントデータは全サーバー・DM で共通です
