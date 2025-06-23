# Transcript to Meeting Minutes API

トランスクリプトから議事録を自動生成するFastAPI アプリケーション

## 機能

- **JWT認証**: ユーザー登録・ログイン機能
- **議事録生成**: OpenAI APIを使用したトランスクリプトから議事録への変換
- **ユーザー管理**: プロフィール管理機能
- **ログ機能**: 包括的なログ記録
- **環境変数管理**: セキュアな設定管理

## 技術スタック

- **FastAPI**: Webフレームワーク
- **SQLAlchemy**: ORM
- **SQLite**: データベース
- **JWT**: 認証
- **OpenAI API**: AI議事録生成
- **bcrypt**: パスワードハッシュ化

## セットアップ

### 1. 依存関係のインストール

```bash
cd transcript_minutes_api2
poetry install
```

### 2. 環境変数の設定

`.env`ファイルを編集して必要な設定を行ってください：

```env
# OpenAI設定（必須）
OPENAI_API_KEY=your-openai-api-key-here

# JWT設定（本番環境では変更必須）
SECRET_KEY=your-secret-key-here-change-in-production

# その他の設定は必要に応じて調整
```

### 3. アプリケーションの起動

```bash
poetry run python -m app.main
```

または

```bash
poetry run uvicorn app.main:app --reload
```

## API エンドポイント

### 認証
- `POST /auth/register` - ユーザー登録
- `POST /auth/login` - ログイン
- `POST /auth/refresh` - トークンリフレッシュ

### 議事録
- `POST /minutes/generate` - 議事録生成
- `GET /minutes/history` - 生成履歴取得
- `GET /minutes/{id}` - 特定議事録取得

### ユーザー
- `GET /users/profile` - プロフィール取得
- `PUT /users/profile` - プロフィール更新

## API ドキュメント

アプリケーション起動後、以下のURLでAPIドキュメントを確認できます：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 使用例

### 1. ユーザー登録

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

### 2. ログイン

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepassword123"
  }'
```

### 3. 議事録生成

```bash
curl -X POST "http://localhost:8000/minutes/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "transcript": "今日の会議では新しいプロジェクトについて話し合いました...",
    "title": "プロジェクト企画会議"
  }'
```

## ディレクトリ構造

```
transcript_minutes_api2/
├── app/
│   ├── main.py                 # FastAPIアプリケーション
│   ├── routers/               # APIルーター
│   │   ├── auth.py           # 認証エンドポイント
│   │   ├── minutes.py        # 議事録エンドポイント
│   │   └── users.py          # ユーザーエンドポイント
│   ├── modules/              # ビジネスロジック
│   │   ├── auth_handler.py   # JWT認証処理
│   │   ├── database.py       # データベース操作
│   │   ├── logger.py         # ログ機能
│   │   └── openai_client.py  # OpenAI連携
│   └── schemas/              # Pydanticスキーマ
│       ├── auth.py           # 認証スキーマ
│       ├── minutes.py        # 議事録スキーマ
│       └── users.py          # ユーザースキーマ
├── .env                      # 環境変数
├── pyproject.toml           # 依存関係
└── README.md
```

## セキュリティ

- パスワードはbcryptでハッシュ化
- JWT トークンによる認証
- CORS設定による適切なアクセス制御
- 入力値検証

## ログ

アプリケーションは以下の情報をログに記録します：

- API呼び出し情報
- エラー情報
- OpenAI API使用状況
- パフォーマンス情報

ログファイル: `app.log`

## 開発

### テスト実行

```bash
poetry run pytest
```

### コード品質チェック

```bash
poetry run black .
poetry run flake8 .
```

## ライセンス

MIT License
