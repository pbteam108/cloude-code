/**
 * シンプルなチャットアプリ（Slack ライク）
 *
 * 主な特徴:
 *   検索ボックスに「マイチャット」と入力すると、
 *   川村真緒 (Kawamura Mao) のチャットが自動的に開きます。
 */

"use strict";

/* =========================================================================
 * データモデル
 * =======================================================================*/

/** @typedef {{ author: string, time: string, text: string }} Message */
/** @typedef {{ id: string, name: string, type: "channel"|"dm",
 *              participant?: string, initial: string, messages: Message[] }} Chat */

/** @type {Chat[]} */
const CHATS = [
  {
    id: "kawamura-mao",
    name: "川村真緒",
    type: "dm",
    participant: "川村真緒",
    initial: "川",
    messages: [
      { author: "川村真緒", time: "9:02", text: "おはようございます！今日の打ち合わせ、10時からで大丈夫でしたか？" },
      { author: "あなた", time: "9:05", text: "おはよう！はい、10時で問題ないです。資料そろえておきますね。" },
      { author: "川村真緒", time: "9:06", text: "ありがとうございます。よろしくお願いします🙌" },
      { author: "川村真緒", time: "9:41", text: "先ほどの件、共有フォルダにまとめておきました。確認お願いします。" },
    ],
  },
  {
    id: "general",
    name: "一般",
    type: "channel",
    initial: "一",
    messages: [
      { author: "佐藤健", time: "8:30", text: "みなさんおはようございます。今週もよろしくお願いします。" },
      { author: "田中優子", time: "8:45", text: "おはようございます！本日の全体会議は15時からです。" },
    ],
  },
  {
    id: "random",
    name: "ランダム",
    type: "channel",
    initial: "ラ",
    messages: [
      { author: "田中優子", time: "12:10", text: "近くに新しいカフェができたらしいですよ☕" },
      { author: "佐藤健", time: "12:15", text: "いいですね、ランチ行きましょう！" },
    ],
  },
  {
    id: "suzuki-taro",
    name: "鈴木太郎",
    type: "dm",
    participant: "鈴木太郎",
    initial: "鈴",
    messages: [
      { author: "鈴木太郎", time: "16:20", text: "例の見積もり、明日までに送りますね。" },
      { author: "あなた", time: "16:22", text: "助かります、よろしくお願いします！" },
    ],
  },
];

/* =========================================================================
 * 「マイチャット」→ 川村真緒 のマッピング
 * -------------------------------------------------------------------------
 * ここを変更すれば、別のキーワード／別のチャットへ簡単に切り替えられます。
 * =======================================================================*/

/** 「マイチャット」検索で開くチャットの id */
const MY_CHAT_TARGET_ID = "kawamura-mao";

/**
 * 入力を正規化して「マイチャット」を指しているか判定するための同義語リスト。
 * 全て小文字・空白除去した状態で比較します。
 */
const MY_CHAT_ALIASES = ["マイチャット", "まいちゃっと", "mychat", "my chat"];

/**
 * 検索クエリが「マイチャット」を意味するかどうかを判定する。
 * 空白をトリム／除去し、大文字小文字を無視して緩やかに一致させる。
 * @param {string} rawQuery
 * @returns {boolean}
 */
function isMyChatQuery(rawQuery) {
  // 前後空白を除去し、内部の空白も詰め、小文字化して比較する
  const normalized = rawQuery.trim().replace(/\s+/g, " ").toLowerCase();
  const compact = normalized.replace(/\s+/g, "");
  // 空入力では判定を発火させない（検索欄が空のときにジャンプしないようにする）
  if (compact === "") {
    return false;
  }
  return MY_CHAT_ALIASES.some((alias) => {
    const a = alias.toLowerCase();
    const aCompact = a.replace(/\s+/g, "");
    // 完全一致、または入力が別名の前方一致（部分入力「マイ」など）で一致
    return normalized === a || aCompact.startsWith(compact);
  });
}

/* =========================================================================
 * DOM 参照
 * =======================================================================*/

const searchInput = document.getElementById("searchInput");
const chatListEl = document.getElementById("chatList");
const chatTitleEl = document.getElementById("chatTitle");
const chatSubtitleEl = document.getElementById("chatSubtitle");
const threadEl = document.getElementById("thread");
const composerInput = document.getElementById("composerInput");
const composerSend = document.getElementById("composerSend");

/** 現在選択中のチャット id */
let activeChatId = null;

/* =========================================================================
 * ヘルパー
 * =======================================================================*/

/** id からチャットを取得する */
function getChatById(id) {
  return CHATS.find((chat) => chat.id === id) || null;
}

/**
 * クエリでチャットを絞り込む。
 * チャット名・参加者名・メッセージ本文のいずれかに一致すれば残す。
 * @param {string} query
 * @returns {Chat[]}
 */
function filterChats(query) {
  const q = query.trim().toLowerCase();
  if (!q) return CHATS;
  return CHATS.filter((chat) => {
    if (chat.name.toLowerCase().includes(q)) return true;
    if (chat.participant && chat.participant.toLowerCase().includes(q)) return true;
    return chat.messages.some((m) => m.text.toLowerCase().includes(q));
  });
}

/* =========================================================================
 * 描画
 * =======================================================================*/

/**
 * サイドバーのチャット一覧を描画する。
 * @param {Chat[]} chats 表示するチャット
 */
function renderChatList(chats) {
  chatListEl.innerHTML = "";

  if (chats.length === 0) {
    const empty = document.createElement("p");
    empty.className = "chat-list__empty";
    empty.textContent = "一致するチャットがありません";
    chatListEl.appendChild(empty);
    return;
  }

  chats.forEach((chat) => {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "chat-item";
    if (chat.id === activeChatId) item.classList.add("is-active");
    item.dataset.chatId = chat.id;

    const prefix = chat.type === "channel" ? "# " : "";
    const lastMessage = chat.messages[chat.messages.length - 1];
    const preview = lastMessage ? lastMessage.text : "";

    item.innerHTML = `
      <span class="chat-item__avatar">${chat.initial}</span>
      <span class="chat-item__body">
        <span class="chat-item__name">${prefix}${escapeHtml(chat.name)}</span>
        <span class="chat-item__preview">${escapeHtml(preview)}</span>
      </span>
    `;

    item.addEventListener("click", () => selectChat(chat.id));
    chatListEl.appendChild(item);
  });
}

/**
 * メインエリアに指定チャットのスレッドを描画する。
 * @param {Chat} chat
 */
function renderThread(chat) {
  const prefix = chat.type === "channel" ? "# " : "";
  chatTitleEl.textContent = `${prefix}${chat.name}`;
  chatSubtitleEl.textContent =
    chat.type === "channel" ? "チャンネル" : `${chat.participant} とのダイレクトメッセージ`;

  threadEl.innerHTML = "";
  chat.messages.forEach((msg) => {
    const row = document.createElement("div");
    row.className = "message";
    row.innerHTML = `
      <span class="message__avatar">${escapeHtml(msg.author.charAt(0))}</span>
      <div class="message__content">
        <div class="message__meta">
          <span class="message__author">${escapeHtml(msg.author)}</span>
          <span class="message__time">${escapeHtml(msg.time)}</span>
        </div>
        <div class="message__text">${escapeHtml(msg.text)}</div>
      </div>
    `;
    threadEl.appendChild(row);
  });

  // 最新メッセージが見えるよう一番下までスクロール
  threadEl.scrollTop = threadEl.scrollHeight;
}

/**
 * チャットを選択して表示する。サイドバーのアクティブ状態も更新する。
 * @param {string} chatId
 */
function selectChat(chatId) {
  const chat = getChatById(chatId);
  if (!chat) return;
  activeChatId = chatId;

  // アクティブ状態の付け替え
  chatListEl.querySelectorAll(".chat-item").forEach((el) => {
    el.classList.toggle("is-active", el.dataset.chatId === chatId);
  });

  renderThread(chat);
}

/** XSS を避けるための簡易エスケープ */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/* =========================================================================
 * 検索の処理
 * =======================================================================*/

/**
 * 検索クエリを処理する。
 *   - 「マイチャット」系のクエリなら川村真緒のチャットを自動で開く。
 *   - それ以外はチャット一覧を絞り込む。
 * @param {string} query
 */
function handleSearch(query) {
  // 最優先: 「マイチャット」→ 川村真緒 を自動表示
  if (isMyChatQuery(query)) {
    const target = getChatById(MY_CHAT_TARGET_ID);
    if (target) {
      renderChatList(CHATS); // 一覧は全件表示に戻す
      selectChat(MY_CHAT_TARGET_ID);
    }
    return;
  }

  // 通常の絞り込み
  renderChatList(filterChats(query));
}

/* =========================================================================
 * メッセージ送信（デモ用: メモリ上のみ）
 * =======================================================================*/

function sendMessage() {
  const text = composerInput.value.trim();
  if (!text || !activeChatId) return;
  const chat = getChatById(activeChatId);
  if (!chat) return;

  const now = new Date();
  const time = `${now.getHours()}:${String(now.getMinutes()).padStart(2, "0")}`;
  chat.messages.push({ author: "あなた", time, text });

  composerInput.value = "";
  renderThread(chat);
  renderChatList(filterChats(searchInput.value)); // プレビュー更新
}

/* =========================================================================
 * イベント登録
 * =======================================================================*/

searchInput.addEventListener("input", (e) => handleSearch(e.target.value));
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleSearch(e.target.value);
});

composerSend.addEventListener("click", sendMessage);
composerInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});

/* =========================================================================
 * 初期化
 * =======================================================================*/

renderChatList(CHATS);
selectChat(CHATS[0].id); // 起動時は先頭のチャット（川村真緒）を表示
