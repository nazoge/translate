# Translate Bot

Discord 上でメッセージを右クリックして翻訳できるボットです。日本語↔英語・日本語↔その他言語の自然な翻訳を Gemini を使って実行します。

## 概要

- Discord のコンテキストメニューから「翻訳する」を選択できます
- 送信されたメッセージ本文を Gemini で翻訳します
- 既存の Discord Markdown やメンション等は保持したまま翻訳します

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

3. アプリケーションを起動します

   ```bash
   python app.py
   ```

## Docker で起動

```bash
docker compose up --build
```

## ファイル構成

- `app.py` : Discord ボット本体
- `requirements.txt` : Python 依存関係
- `Dockerfile` : Docker イメージ定義
- `docker-compose.yml` : Docker Compose 設定

## 備考

- Bot は Discord のコンテキストメニュー機能を利用して翻訳を実行します
- 既存のメッセージ内容をそのまま翻訳し、結果を Embed で返信します
