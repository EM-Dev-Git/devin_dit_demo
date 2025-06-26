# コード実装 (Code Implementation)

このフォルダには、トランスクリプトから議事録作成APIシステムの完全な実装が含まれています。

## 構成

### メインアプリケーション
- `main.py` - FastAPIアプリケーションのメインエントリーポイント
- `requirements.txt` - 必要な依存関係
- `.env.example` - 環境変数の設定例

### モジュール (`modules/`)
- `database.py` - データベースモデルとセッション管理
- `auth.py` - JWT認証とパスワードハッシュ化
- `graph_client.py` - Microsoft Graph SDK統合
- `openai_client.py` - OpenAI API統合
- `logger.py` - ログ設定

### ルーター (`routers/`)
- `auth.py` - 認証エンドポイント（JWT + Microsoft Graph）
- `users.py` - ユーザー管理エンドポイント
- `minutes.py` - 議事録生成エンドポイント
- `graph.py` - Microsoft Graphトランスクリプト取得エンドポイント

### スキーマ (`schemas/`)
- `auth.py` - 認証関連のPydanticモデル
- `users.py` - ユーザー関連のPydanticモデル
- `minutes.py` - 議事録関連のPydanticモデル
- `graph.py` - Microsoft Graph関連のPydanticモデル

## 機能

### 基本機能
- JWT認証システム
- ユーザー登録・管理
- OpenAI連携による議事録自動生成
- ログ機能

### Microsoft Graph SDK統合
- OAuth2認証フロー
- Microsoft Teamsミーティングトランスクリプト取得
- 自動トークンリフレッシュ
- Graphトランスクリプトから直接議事録生成

## 使用方法

1. 依存関係のインストール:
```bash
pip install -r requirements.txt
```

2. 環境変数の設定:
```bash
cp .env.example .env
# .envファイルを編集して必要な設定を追加
```

3. アプリケーションの起動:
```bash
uvicorn main:app --reload
```

## API エンドポイント

### 認証
- `POST /auth/register` - ユーザー登録
- `POST /auth/login` - ログイン
- `POST /auth/refresh` - トークンリフレッシュ
- `POST /auth/graph/authorize` - Microsoft Graph認証開始
- `POST /auth/graph/callback` - OAuth認証コールバック
- `GET /auth/graph/status` - Graph認証状態確認

### 議事録
- `POST /minutes/generate` - 手動トランスクリプトから議事録生成
- `GET /minutes/{id}` - 議事録取得
- `GET /minutes/` - ユーザーの議事録一覧

### Microsoft Graph
- `GET /graph/meetings/{meeting_id}/transcripts` - ミーティングトランスクリプト一覧
- `GET /graph/transcripts/{transcript_id}/content` - トランスクリプト内容取得
- `POST /graph/transcripts/generate-minutes` - Graphトランスクリプトから議事録生成

### ユーザー
- `GET /users/me` - 現在のユーザー情報取得
