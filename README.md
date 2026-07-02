# cloude-code — Slack × Claude 連携ボット

Slack 上で Claude（Anthropic API）と会話できる Slack ボットです。
チャンネルでボットにメンションするか、ボットに DM を送ると Claude が返信します。
スレッド内では会話の文脈を保持したまま応答します。

## 主な機能

- 💬 チャンネルでのメンション（`@ボット名 質問`）に応答
- 📩 ダイレクトメッセージ（DM）に応答
- 🧵 スレッド単位で会話履歴を保持（文脈を踏まえた返信）
- ⚡️ Socket Mode 採用のため、公開 URL やリバースプロキシ不要
- 🔧 モデル・最大トークン数を環境変数で変更可能

## 構成

- 言語 / 実行環境: Node.js 18+（ES Modules）
- Slack SDK: [@slack/bolt](https://slack.dev/bolt-js/)（Socket Mode）
- Claude SDK: [@anthropic-ai/sdk](https://github.com/anthropics/anthropic-sdk-typescript)

## 事前準備

### 1. Slack アプリの作成

1. https://api.slack.com/apps で「Create New App」→「From scratch」を選択
2. **Socket Mode** を有効化し、App-Level Token（`xapp-...`）を発行（スコープ: `connections:write`）
3. **OAuth & Permissions** で Bot Token Scopes を追加:
   - `app_mentions:read`
   - `chat:write`
   - `im:history`
   - `im:read`
   - `channels:history`（チャンネルのスレッド履歴取得用）
   - `groups:history`（プライベートチャンネル用・任意）
4. **Event Subscriptions** を有効化し、Subscribe to bot events に追加:
   - `app_mention`
   - `message.im`
5. ワークスペースにインストールし、Bot User OAuth Token（`xoxb-...`）を取得

### 2. Anthropic API キー

https://console.anthropic.com/ で API キー（`sk-ant-...`）を取得します。

## セットアップ

```bash
npm install
cp .env.example .env   # 取得したトークン類を記入
```

## 環境変数

| 変数名 | 必須 | 説明 |
| --- | --- | --- |
| `SLACK_BOT_TOKEN` | ✅ | Bot User OAuth Token（`xoxb-...`） |
| `SLACK_APP_TOKEN` | ✅ | App-Level Token（`xapp-...`, Socket Mode 用） |
| `SLACK_SIGNING_SECRET` |  | Signing Secret（Socket Mode では任意） |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API キー（`sk-ant-...`） |
| `CLAUDE_MODEL` |  | 使用モデル（既定: `claude-opus-4-8`） |
| `MAX_TOKENS` |  | 応答の最大トークン数（既定: `1024`） |

## 起動

```bash
npm start
# 開発時（ファイル変更で自動再起動）
npm run dev
```

`⚡️ Slack × Claude ボットが起動しました` と表示されれば成功です。

## 使い方

- **チャンネル**: `@ボット名 こんにちは` のようにメンション
- **DM**: ボットに直接メッセージを送信
- **スレッド**: ボットの返信スレッドで続けて話すと、文脈を踏まえて応答します

## ライセンス

MIT
