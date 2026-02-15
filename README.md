# Facebook Graph API MCP Server

Facebook Graph API と連携する [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) サーバーです。AI アシスタントから Facebook ページの管理、投稿の作成・取得、インサイト分析などを実行できます。

## 提供ツール

| ツール名 | 説明 |
|---|---|
| `get_me` | 認証ユーザーのプロフィール取得 |
| `get_user` | ユーザーの公開プロフィール取得 |
| `get_pages` | 管理しているページ一覧を取得 |
| `get_page` | 特定ページの詳細を取得 |
| `get_posts` | ページ/ユーザーフィードの投稿を取得 |
| `create_post` | ページに新規投稿を作成 |
| `delete_post` | 投稿を削除 |
| `get_page_insights` | ページのアナリティクスを取得 |
| `get_post_insights` | 投稿のアナリティクスを取得 |

## セットアップ

```bash
npm install
npm run build
```

## 環境変数

| 変数名 | 必須 | 説明 |
|---|---|---|
| `FACEBOOK_ACCESS_TOKEN` | Yes | Facebook Graph API アクセストークン |
| `GRAPH_API_VERSION` | No | API バージョン (デフォルト: `v21.0`) |

アクセストークンは [Graph API Explorer](https://developers.facebook.com/tools/explorer/) で取得できます。

## MCP クライアント設定

Claude Desktop などの MCP クライアントに以下を追加:

```json
{
  "mcpServers": {
    "facebook-graph": {
      "command": "node",
      "args": ["dist/index.js"],
      "cwd": "/path/to/facebook-graph-mcp-server",
      "env": {
        "FACEBOOK_ACCESS_TOKEN": "your_token"
      }
    }
  }
}
```

## 開発

```bash
npm run dev      # tsx で直接実行 (ビルド不要)
npm run lint     # 型チェック
npm run build    # TypeScript コンパイル
npm start        # コンパイル済みコードを実行
```

## ライセンス

MIT
