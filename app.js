import 'dotenv/config';
import pkg from '@slack/bolt';
const { App } = pkg;
import Anthropic from '@anthropic-ai/sdk';

// ---- 環境変数 ----
const {
  SLACK_BOT_TOKEN,
  SLACK_APP_TOKEN,
  SLACK_SIGNING_SECRET,
  ANTHROPIC_API_KEY,
  CLAUDE_MODEL = 'claude-opus-4-8',
  MAX_TOKENS = '1024',
} = process.env;

for (const [key, val] of Object.entries({ SLACK_BOT_TOKEN, SLACK_APP_TOKEN, ANTHROPIC_API_KEY })) {
  if (!val) {
    console.error(`環境変数 ${key} が設定されていません。.env を確認してください。`);
    process.exit(1);
  }
}

const SYSTEM_PROMPT =
  'あなたは Slack 上で動作する親切なアシスタントです。簡潔で分かりやすい日本語で回答してください。';

const anthropic = new Anthropic({ apiKey: ANTHROPIC_API_KEY });

const app = new App({
  token: SLACK_BOT_TOKEN,
  appToken: SLACK_APP_TOKEN,
  signingSecret: SLACK_SIGNING_SECRET,
  socketMode: true,
});

// ボット自身の user_id をキャッシュ
let cachedBotUserId = null;
async function getBotUserId(client) {
  if (!cachedBotUserId) {
    const auth = await client.auth.test();
    cachedBotUserId = auth.user_id;
  }
  return cachedBotUserId;
}

// <@U123> 形式のメンション表記を除去
function stripMentions(text) {
  return (text ?? '').replace(/<@[A-Z0-9]+>/g, '').trim();
}

// スレッドの返信を取得し、Claude 用のメッセージ配列に変換
async function buildHistory(client, channel, threadTs, botUserId) {
  const messages = [];
  if (!threadTs) return messages;

  const res = await client.conversations.replies({ channel, ts: threadTs, limit: 50 });
  for (const m of res.messages ?? []) {
    const text = stripMentions(m.text);
    if (!text) continue;
    const isBot = m.user === botUserId || Boolean(m.bot_id);
    messages.push({ role: isBot ? 'assistant' : 'user', content: text });
  }
  return messages;
}

// Claude API 制約に合わせて整形（同一ロールの連続を結合し、user から始める）
function normalize(messages) {
  const out = [];
  for (const m of messages) {
    const last = out[out.length - 1];
    if (last && last.role === m.role) {
      last.content += '\n' + m.content;
    } else {
      out.push({ role: m.role, content: m.content });
    }
  }
  while (out.length && out[0].role !== 'user') out.shift();
  return out;
}

// 共通の応答処理
async function respond({ event, client, say }) {
  const channel = event.channel;
  const threadTs = event.thread_ts || event.ts;

  try {
    const botUserId = await getBotUserId(client);
    let history = normalize(await buildHistory(client, channel, event.thread_ts, botUserId));

    // スレッド外（新規メンション / DM 冒頭）の場合は現在のメッセージのみ
    if (history.length === 0) {
      history = [{ role: 'user', content: stripMentions(event.text) }];
    }

    const completion = await anthropic.messages.create({
      model: CLAUDE_MODEL,
      max_tokens: Number(MAX_TOKENS),
      system: SYSTEM_PROMPT,
      messages: history,
    });

    const reply =
      completion.content
        .filter((b) => b.type === 'text')
        .map((b) => b.text)
        .join('\n')
        .trim() || '(応答が空でした)';

    await say({ text: reply, thread_ts: threadTs });
  } catch (err) {
    console.error('Claude 呼び出しでエラー:', err);
    await say({ text: `エラーが発生しました: ${err.message}`, thread_ts: threadTs });
  }
}

// チャンネルでのメンション
app.event('app_mention', async ({ event, client, say }) => {
  await respond({ event, client, say });
});

// ダイレクトメッセージ（DM）
app.message(async ({ message, client, say }) => {
  if (message.subtype || message.bot_id) return; // ボット投稿・編集などは無視
  if (message.channel_type !== 'im') return; // DM のみ（チャンネルは app_mention で処理）
  await respond({ event: message, client, say });
});

(async () => {
  const port = process.env.PORT || 3000;
  await app.start(port);
  console.log('⚡️ Slack × Claude ボットが起動しました');
})();
