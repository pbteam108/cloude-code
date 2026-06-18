#!/usr/bin/env python3
"""Gmail の重要なメールを抽出するツール.

Gmail API を使って、条件に合致する「重要なメール」を取得し、一覧として出力します。

抽出条件（既定）:
  - Gmail が "重要" と判定したメール (label:important)
  - スター付きメール (is:starred)
  - 上記いずれかかつ未読、を既定とするが --query で自由に変更可能

使い方:
  1. Google Cloud Console で Gmail API を有効化し、OAuth クライアント
     (デスクトップアプリ) の認証情報をダウンロードして credentials.json として
     このディレクトリに置く。
  2. 依存関係をインストール: pip install -r requirements.txt
  3. 実行: python gmail_extractor.py

例:
  # 既定（重要 or スター付き）で最新20件
  python gmail_extractor.py

  # 未読の重要メールだけ、最新50件をCSVに保存
  python gmail_extractor.py --query "is:unread (label:important OR is:starred)" \
      --max 50 --csv important.csv

  # 特定の差出人からの重要メール
  python gmail_extractor.py --query "label:important from:boss@example.com"
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from dataclasses import dataclass

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 読み取り専用スコープ（メールの閲覧のみ。変更・送信・削除はしない）
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# 「重要なメール」の既定の検索クエリ
DEFAULT_QUERY = "label:important OR is:starred"

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


@dataclass
class Message:
    """抽出した1通のメールの要約情報."""

    id: str
    sender: str
    subject: str
    date: str
    snippet: str

    def as_row(self) -> list[str]:
        return [self.id, self.date, self.sender, self.subject, self.snippet]


def authenticate() -> Credentials:
    """OAuth 認証を行い、認証済みクレデンシャルを返す.

    初回はブラウザで同意を求め、token.json に保存する。
    2回目以降は token.json を再利用し、必要なら自動でリフレッシュする。
    """
    creds: Credentials | None = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                sys.exit(
                    f"認証情報ファイル '{CREDENTIALS_FILE}' が見つかりません。\n"
                    "Google Cloud Console で OAuth クライアント (デスクトップアプリ) を作成し、\n"
                    "JSON をダウンロードして credentials.json として配置してください。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return creds


def _header(headers: list[dict], name: str) -> str:
    """メッセージヘッダから指定名の値を取得する（大文字小文字を無視）."""
    name_lower = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name_lower:
            return h.get("value", "")
    return ""


def fetch_messages(service, query: str, max_results: int) -> list[Message]:
    """検索クエリに合致するメールを取得し、Message のリストを返す."""
    messages: list[Message] = []
    page_token: str | None = None
    remaining = max_results

    while remaining > 0:
        batch_size = min(remaining, 100)
        resp = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=batch_size, pageToken=page_token)
            .execute()
        )
        ids = [m["id"] for m in resp.get("messages", [])]
        for msg_id in ids:
            detail = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg_id,
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )
            headers = detail.get("payload", {}).get("headers", [])
            messages.append(
                Message(
                    id=msg_id,
                    sender=_header(headers, "From"),
                    subject=_header(headers, "Subject"),
                    date=_header(headers, "Date"),
                    snippet=detail.get("snippet", ""),
                )
            )

        remaining = max_results - len(messages)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return messages


def print_messages(messages: list[Message]) -> None:
    """抽出結果を見やすく標準出力に表示する."""
    if not messages:
        print("条件に合致する重要なメールは見つかりませんでした。")
        return

    print(f"\n重要なメール {len(messages)} 件を抽出しました:\n")
    for i, m in enumerate(messages, 1):
        print(f"[{i}] {m.subject or '(件名なし)'}")
        print(f"    差出人: {m.sender}")
        print(f"    日時  : {m.date}")
        print(f"    概要  : {m.snippet[:120]}")
        print()


def write_csv(messages: list[Message], path: str) -> None:
    """抽出結果を CSV に書き出す."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "date", "from", "subject", "snippet"])
        for m in messages:
            writer.writerow(m.as_row())
    print(f"CSV を書き出しました: {path} ({len(messages)} 件)")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gmail の重要なメールを抽出します。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
        help="Gmail 検索クエリ。重要メールの判定条件を指定します。",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=20,
        help="取得する最大件数。",
    )
    parser.add_argument(
        "--csv",
        metavar="PATH",
        help="指定すると結果を CSV ファイルに保存します。",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.max <= 0:
        sys.exit("--max は 1 以上を指定してください。")

    try:
        creds = authenticate()
        service = build("gmail", "v1", credentials=creds)
        messages = fetch_messages(service, args.query, args.max)
    except HttpError as error:
        sys.exit(f"Gmail API エラー: {error}")

    print_messages(messages)
    if args.csv:
        write_csv(messages, args.csv)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
