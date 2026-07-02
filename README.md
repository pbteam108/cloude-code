# taskman

スケジュール付きのタスクを JSON ファイルで管理し、TODO 一覧の表示と
「期限切れ / まもなく期限」の通知を行う、小さな CLI ツールです。

## 概要

- タスクを `tasks.json`（JSON）に保存します。
- 追加・一覧・完了・削除の基本操作をサブコマンドで提供します。
- `notify` コマンドで、期限切れ（OVERDUE）・指定時間以内に期限を迎える
  タスク（UPCOMING）を集計し、通知メッセージを組み立ててコンソールに表示します。
- 任意で Slack Incoming Webhook に通知を POST できます（標準ライブラリの
  `urllib` のみを使用）。

## インストール不要

標準ライブラリのみで動作します（**Python 3.9 以上**）。サードパーティ製の
依存パッケージはありません。リポジトリ直下で次のように実行します。

```bash
python -m taskman --help
```

## 使い方

すべてのコマンドで `--file PATH` を指定して保存先を変更できます
（未指定時は環境変数 `TASKMAN_FILE`、それも無ければカレントディレクトリの
`tasks.json`）。

### タスクを追加する（add）

```bash
python -m taskman add "四半期レポートを提出" --due 2026-07-10
python -m taskman add "定例MTGの準備" --due 2026-07-05T15:00 --notes "アジェンダ共有"
python -m taskman add "いつか読む本を整理"   # 期限なし
```

`--due` は日付 `YYYY-MM-DD`（0 時扱い）または日時 `YYYY-MM-DDTHH:MM` を受け付けます。

### 一覧を表示する（list）

```bash
python -m taskman list            # 既定は todo のみ
python -m taskman list --all      # すべてのステータス
python -m taskman list --status done
```

期限切れのタスクには行頭に `!` が付きます。

### 完了・削除（done / remove）

```bash
python -m taskman done 1
python -m taskman remove 3
```

### 通知（notify）

```bash
python -m taskman notify                 # 既定は今後 24 時間を対象
python -m taskman notify --within 48     # 今後 48 時間
python -m taskman notify --dry-run       # Slack へは送らずメッセージのみ表示
```

Webhook が設定されていなければコンソール表示のみ（これが既定動作）です。

## tasks.json のフォーマット

```json
{
  "tasks": [
    {
      "id": 1,
      "title": "四半期レポートを提出",
      "due": "2026-07-10",
      "status": "todo",
      "notes": "経理部へ送付"
    }
  ]
}
```

- `id`: 一意の整数。
- `title`: タスク名。
- `due`: `null`、日付 `YYYY-MM-DD`、または日時 `YYYY-MM-DDTHH:MM:SS`。
  `null` の場合はスケジュールなしとして扱われます。
- `status`: `"todo"` または `"done"`。
- `notes`: 任意のメモ（省略時は空文字）。

ファイルが存在しない場合は空のタスク一覧として扱われます。JSON が壊れている
場合は分かりやすいエラーを表示します。

## Slack 通知の設定方法

Incoming Webhook の URL を、環境変数またはオプションで渡します。

```bash
# 環境変数で指定
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXX/YYY/ZZZ"
python -m taskman notify --within 48

# オプションで指定
python -m taskman notify --slack-webhook "https://hooks.slack.com/services/XXX/YYY/ZZZ"
```

`--dry-run` を付けると、Webhook が設定されていても送信せずメッセージのみ表示
します。送信に失敗しても警告を表示して処理は継続し、クラッシュしません。

## cron での定期通知の例

毎朝 8 時に、今後 24 時間の TODO を Slack へ通知する例です。

```cron
# crontab -e
0 8 * * * cd /path/to/cloude-code && \
  SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXX/YYY/ZZZ" \
  /usr/bin/python3 -m taskman notify --within 24 >> /tmp/taskman.log 2>&1
```

## テスト

```bash
python -m unittest discover -s tests
# pytest が入っていれば
python -m pytest
```

---

## English (summary)

`taskman` is a dependency-free (standard library only, Python 3.9+) CLI that
stores scheduled tasks in a JSON file, prints your TODO list, and computes
schedule-based notifications.

- `python -m taskman add "Title" --due 2026-07-10 [--notes ...]` — add a task.
- `python -m taskman list [--all] [--status todo|done]` — list tasks; overdue
  ones are flagged with `!`.
- `python -m taskman done <id>` / `python -m taskman remove <id>`.
- `python -m taskman notify [--within HOURS] [--slack-webhook URL] [--dry-run]`
  — summarize OVERDUE and UPCOMING (within N hours, default 24) tasks, print to
  the console, and optionally POST the message to a Slack Incoming Webhook
  (via `--slack-webhook` or the `SLACK_WEBHOOK_URL` env var). Slack failures are
  reported as warnings and never crash the command.

Storage defaults to `./tasks.json`, overridable via `TASKMAN_FILE` or `--file`.
Run the tests with `python -m unittest discover -s tests`.
