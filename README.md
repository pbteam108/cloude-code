# cloude-code

Gmail の「重要なメール」を抽出する Python ツールです。Gmail API を使って、
重要・スター付きなどの条件に合致するメールを検索し、一覧表示・CSV 出力します。

## 特長

- Gmail が判定した「重要」ラベルやスター付きメールを抽出
- 検索クエリを自由に変更可能（差出人・期間・未読など Gmail の検索演算子をそのまま利用）
- 結果を見やすく一覧表示、または CSV に保存
- **読み取り専用スコープ** のみを使用（メールの変更・送信・削除は行いません）

## セットアップ

### 1. Gmail API の認証情報を用意する

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. 「API とサービス」→「ライブラリ」から **Gmail API** を有効化
3. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」
   - アプリケーションの種類: **デスクトップアプリ**
4. 作成した認証情報の JSON をダウンロードし、`credentials.json` として
   このディレクトリに配置

> `credentials.json` と `token.json` は機密情報です。`.gitignore` 済みなので
> リポジトリにコミットされません。

### 2. 依存関係をインストール

```bash
pip install -r requirements.txt
```

## 使い方

```bash
# 既定（重要 or スター付き）で最新 20 件を表示
python gmail_extractor.py

# 未読の重要メールだけ、最新 50 件を CSV に保存
python gmail_extractor.py \
    --query "is:unread (label:important OR is:starred)" \
    --max 50 \
    --csv important.csv

# 特定の差出人からの重要メール
python gmail_extractor.py --query "label:important from:boss@example.com"
```

初回実行時はブラウザが開き、Google アカウントへのアクセス許可を求められます。
許可すると `token.json` が保存され、次回以降は自動で再利用されます。

### オプション

| オプション   | 説明                                       | 既定値                          |
| ------------ | ------------------------------------------ | ------------------------------- |
| `--query`    | Gmail 検索クエリ（重要メールの判定条件）   | `label:important OR is:starred` |
| `--max`      | 取得する最大件数                           | `20`                            |
| `--csv PATH` | 指定すると結果を CSV ファイルに保存        | （なし）                        |

### 検索クエリの例

`--query` には [Gmail の検索演算子](https://support.google.com/mail/answer/7190)
をそのまま使えます。

| やりたいこと                       | クエリ例                                  |
| ---------------------------------- | ----------------------------------------- |
| 重要かつ未読                       | `label:important is:unread`               |
| 過去7日以内の重要メール            | `label:important newer_than:7d`           |
| 添付ファイル付きの重要メール       | `label:important has:attachment`          |
| 特定の差出人                       | `from:example@gmail.com`                  |
