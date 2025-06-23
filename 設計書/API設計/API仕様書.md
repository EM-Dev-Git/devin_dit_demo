# API仕様書

## 1. 概要

### 目的
トランスクリプトから議事録作成APIシステムの詳細なAPI仕様を定義し、開発者が実装・利用するための完全な技術仕様を提供する

### 対象範囲
- 全APIエンドポイントの詳細仕様
- リクエスト/レスポンス形式
- 認証・認可方式
- エラーハンドリング

### 前提条件
- OpenAPI 3.0 仕様準拠
- RESTful API 設計原則
- JSON 形式でのデータ交換

## 2. 設計方針

### 基本方針
- **一貫性**: 統一されたAPI設計パターン
- **セキュリティ**: JWT認証による適切なアクセス制御
- **使いやすさ**: 直感的で理解しやすいAPI設計
- **拡張性**: 将来的な機能追加に対応可能

### 制約事項
- JWT トークンの有効期限（24時間）
- OpenAI API の利用制限
- リクエストサイズの制限

### 品質要件
- **応答時間**: 認証系 < 500ms、議事録生成 < 30秒
- **可用性**: 99.9%以上
- **セキュリティ**: OWASP Top 10 対応

## 3. API 基本情報

### サーバー情報
```yaml
openapi: 3.0.0
info:
  title: Transcript to Meeting Minutes API
  description: API for generating meeting minutes from transcripts using OpenAI
  version: 1.0.0
  contact:
    name: API Support
    email: support@example.com
servers:
  - url: https://api.example.com/v1
    description: Production server
  - url: http://localhost:8000
    description: Development server
```

### 認証方式
```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT token obtained from /auth/login endpoint
```

## 4. 認証系API

### 4.1 ユーザー登録

#### POST /auth/register
```yaml
summary: 新規ユーザー登録
description: |
  新しいユーザーアカウントを作成します。
  ユーザー名とメールアドレスは一意である必要があります。
tags:
  - Authentication
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          username:
            type: string
            minLength: 3
            maxLength: 50
            pattern: '^[a-zA-Z0-9_-]+$'
            description: ユーザー名（英数字、アンダースコア、ハイフンのみ）
            example: "user123"
          email:
            type: string
            format: email
            maxLength: 100
            description: メールアドレス
            example: "user@example.com"
          password:
            type: string
            minLength: 8
            maxLength: 128
            description: パスワード（8文字以上）
            example: "securePassword123"
        required:
          - username
          - email
          - password
responses:
  201:
    description: ユーザー登録成功
    content:
      application/json:
        schema:
          type: object
          properties:
            id:
              type: integer
              description: ユーザーID
              example: 1
            username:
              type: string
              description: ユーザー名
              example: "testuser"
            email:
              type: string
              description: メールアドレス
              example: "test@example.com"
            created_at:
              type: string
              format: date-time
              description: 作成日時
              example: "2025-06-23T07:30:00Z"
  400:
    description: バリデーションエラー
  409:
    description: ユーザー名またはメールアドレスが既に存在
  500:
    description: サーバー内部エラー
```

### 4.2 ユーザーログイン

#### POST /auth/login
```yaml
summary: ユーザーログイン
description: |
  ユーザー認証を行い、JWTアクセストークンを発行します。
  トークンの有効期限は24時間です。
tags:
  - Authentication
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          username:
            type: string
            description: ユーザー名
            example: "testuser"
          password:
            type: string
            description: パスワード
            example: "testpassword123"
        required:
          - username
          - password
responses:
  200:
    description: ログイン成功
    content:
      application/json:
        schema:
          type: object
          properties:
            access_token:
              type: string
              description: JWTアクセストークン
              example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            token_type:
              type: string
              enum: [bearer]
              description: トークンタイプ
              example: "bearer"
  401:
    description: 認証失敗
  500:
    description: サーバー内部エラー
```

### 4.3 トークンリフレッシュ

#### POST /auth/refresh
```yaml
summary: アクセストークンリフレッシュ
description: |
  現在のJWTトークンを使用して新しいアクセストークンを発行します。
tags:
  - Authentication
security:
  - bearerAuth: []
responses:
  200:
    description: トークンリフレッシュ成功
    content:
      application/json:
        schema:
          type: object
          properties:
            access_token:
              type: string
              description: 新しいJWTアクセストークン
              example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            token_type:
              type: string
              enum: [bearer]
              description: トークンタイプ
              example: "bearer"
  401:
    description: 無効なトークン
```

## 5. 議事録系API

### 5.1 議事録生成

#### POST /minutes/generate
```yaml
summary: 議事録生成
description: |
  トランスクリプトを入力として、OpenAI APIを使用して構造化された議事録を生成します。
  生成された議事録はデータベースに保存されます。
tags:
  - Minutes
security:
  - bearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          transcript:
            type: string
            minLength: 10
            maxLength: 10000
            description: 会議のトランスクリプト
            example: "今日の会議では、新しいプロジェクトについて話し合いました。参加者は田中さん、佐藤さん、鈴木さんでした。"
          title:
            type: string
            maxLength: 200
            description: 会議のタイトル（オプション）
            example: "週次定例会議"
        required:
          - transcript
responses:
  200:
    description: 議事録生成成功
    content:
      application/json:
        schema:
          type: object
          properties:
            id:
              type: integer
              description: 議事録ID
              example: 1
            user_id:
              type: integer
              description: ユーザーID
              example: 1
            title:
              type: string
              nullable: true
              description: 会議タイトル
              example: "プロジェクト企画会議"
            transcript:
              type: string
              description: 元のトランスクリプト
              example: "今日の会議では..."
            generated_minutes:
              type: string
              description: 生成された議事録
              example: "# 会議議事録\n## 日時・参加者\n..."
            created_at:
              type: string
              format: date-time
              description: 作成日時
              example: "2025-06-23T07:30:00Z"
  400:
    description: バリデーションエラー
  401:
    description: 認証が必要
  500:
    description: 議事録生成エラー
```

### 5.2 議事録履歴取得

#### GET /minutes/history
```yaml
summary: 議事録履歴取得
description: |
  認証されたユーザーの議事録履歴を取得します。
  ページネーション機能により、大量のデータを効率的に取得できます。
tags:
  - Minutes
security:
  - bearerAuth: []
parameters:
  - name: skip
    in: query
    description: スキップする件数
    required: false
    schema:
      type: integer
      minimum: 0
      default: 0
      example: 0
  - name: limit
    in: query
    description: 取得する最大件数
    required: false
    schema:
      type: integer
      minimum: 1
      maximum: 100
      default: 10
      example: 10
responses:
  200:
    description: 履歴取得成功
    content:
      application/json:
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: 議事録ID
                example: 1
              title:
                type: string
                nullable: true
                description: 会議タイトル
                example: "プロジェクト企画会議"
              created_at:
                type: string
                format: date-time
                description: 作成日時
                example: "2025-06-23T07:30:00Z"
  401:
    description: 認証が必要
```

### 5.3 特定議事録取得

#### GET /minutes/{minutes_id}
```yaml
summary: 特定議事録詳細取得
description: |
  指定されたIDの議事録詳細を取得します。
  ユーザーは自分が作成した議事録のみアクセス可能です。
tags:
  - Minutes
security:
  - bearerAuth: []
parameters:
  - name: minutes_id
    in: path
    description: 議事録ID
    required: true
    schema:
      type: integer
      minimum: 1
      example: 1
responses:
  200:
    description: 議事録取得成功
    content:
      application/json:
        schema:
          type: object
          properties:
            id:
              type: integer
              description: 議事録ID
              example: 1
            user_id:
              type: integer
              description: ユーザーID
              example: 1
            title:
              type: string
              nullable: true
              description: 会議タイトル
              example: "プロジェクト企画会議"
            transcript:
              type: string
              description: 元のトランスクリプト
              example: "今日の会議では..."
            generated_minutes:
              type: string
              description: 生成された議事録
              example: "# 会議議事録\n## 日時・参加者\n..."
            created_at:
              type: string
              format: date-time
              description: 作成日時
              example: "2025-06-23T07:30:00Z"
  401:
    description: 認証が必要
  403:
    description: アクセス権限なし
  404:
    description: 議事録が見つからない
```

## 6. ユーザー管理系API

### 6.1 プロフィール取得

#### GET /users/profile
```yaml
summary: ユーザープロフィール取得
description: |
  認証されたユーザーのプロフィール情報を取得します。
tags:
  - Users
security:
  - bearerAuth: []
responses:
  200:
    description: プロフィール取得成功
    content:
      application/json:
        schema:
          type: object
          properties:
            username:
              type: string
              description: ユーザー名
              example: "testuser"
            email:
              type: string
              description: メールアドレス
              example: "test@example.com"
  401:
    description: 認証が必要
```

### 6.2 プロフィール更新

#### PUT /users/profile
```yaml
summary: ユーザープロフィール更新
description: |
  認証されたユーザーのプロフィール情報を更新します。
  ユーザー名とメールアドレスは一意である必要があります。
tags:
  - Users
security:
  - bearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          username:
            type: string
            minLength: 3
            maxLength: 50
            pattern: '^[a-zA-Z0-9_-]+$'
            description: 新しいユーザー名（オプション）
            example: "newusername"
          email:
            type: string
            format: email
            maxLength: 100
            description: 新しいメールアドレス（オプション）
            example: "newemail@example.com"
responses:
  200:
    description: プロフィール更新成功
    content:
      application/json:
        schema:
          type: object
          properties:
            username:
              type: string
              description: 更新されたユーザー名
              example: "newusername"
            email:
              type: string
              description: 更新されたメールアドレス
              example: "newemail@example.com"
  400:
    description: バリデーションエラー
  401:
    description: 認証が必要
  409:
    description: ユーザー名またはメールアドレスが既に存在
```

## 7. システム系API

### 7.1 ヘルスチェック

#### GET /healthz
```yaml
summary: システムヘルスチェック
description: |
  システムの稼働状況を確認します。
  認証は不要です。
tags:
  - System
responses:
  200:
    description: システム正常
    content:
      application/json:
        schema:
          type: object
          properties:
            status:
              type: string
              enum: [ok]
              description: システム状態
              example: "ok"
            message:
              type: string
              description: メッセージ
              example: "Transcript to Meeting Minutes API is running"
```

#### GET /
```yaml
summary: ルートエンドポイント
description: |
  APIの基本情報を取得します。
tags:
  - System
responses:
  200:
    description: API情報
    content:
      application/json:
        schema:
          type: object
          properties:
            message:
              type: string
              description: ウェルカムメッセージ
              example: "Welcome to Transcript to Meeting Minutes API"
            docs:
              type: string
              description: API ドキュメントURL
              example: "/docs"
            redoc:
              type: string
              description: ReDoc URL
              example: "/redoc"
```

## 8. 共通スキーマ定義

### 8.1 エラースキーマ
```yaml
components:
  schemas:
    Error:
      type: object
      properties:
        detail:
          type: string
          description: エラーメッセージ
          example: "Error message"
      required:
        - detail
    
    ValidationError:
      type: object
      properties:
        detail:
          type: array
          items:
            type: object
            properties:
              loc:
                type: array
                items:
                  oneOf:
                    - type: string
                    - type: integer
                description: エラー発生箇所
                example: ["body", "username"]
              msg:
                type: string
                description: エラーメッセージ
                example: "ensure this value has at least 3 characters"
              type:
                type: string
                description: エラータイプ
                example: "value_error.any_str.min_length"
            required:
              - loc
              - msg
              - type
      required:
        - detail
```

## 9. レート制限

### 9.1 制限仕様
| エンドポイント | 制限 | ウィンドウ |
|---------------|------|-----------|
| /auth/register | 5回/時間 | 1時間 |
| /auth/login | 10回/分 | 1分 |
| /minutes/generate | 20回/時間 | 1時間 |
| その他 | 100回/分 | 1分 |

### 9.2 制限超過時のレスポンス
```yaml
429:
  description: レート制限超過
  headers:
    X-Rate-Limit-Remaining:
      description: 残り回数
      schema:
        type: integer
        example: 0
    X-Rate-Limit-Reset:
      description: リセット時刻（Unix timestamp）
      schema:
        type: integer
        example: 1703333333
  content:
    application/json:
      schema:
        $ref: '#/components/schemas/Error'
      examples:
        rate_limit_exceeded:
          summary: レート制限超過例
          value:
            detail: "Rate limit exceeded. Try again later."
```

## 10. 実装考慮事項

### 開発時の注意点
- **認証**: 全ての保護されたエンドポイントでJWT認証を実装
- **バリデーション**: Pydantic による厳密な入力値検証
- **エラーハンドリング**: 適切なHTTPステータスコードの返却
- **ログ出力**: 個人情報を含まないログ設計

### 既知の課題
- OpenAI API の利用制限による処理時間の変動
- 大容量トランスクリプトの処理制限
- JWT トークンの無効化機能未実装

### 代替案
- **API バージョニング**: 将来的なバージョン管理
- **WebSocket**: リアルタイム通信対応
- **GraphQL**: より柔軟なデータ取得

## 11. テスト観点

### テスト項目
- **機能テスト**: 各エンドポイントの正常系・異常系テスト
- **認証テスト**: JWT認証の動作確認
- **バリデーションテスト**: 入力値検証の確認
- **パフォーマンステスト**: 応答時間の測定

### 検証方法
- **Swagger UI**: インタラクティブなAPIテスト
- **curl コマンド**: コマンドラインでのテスト
- **自動テスト**: pytest による自動テスト
- **負荷テスト**: locust による負荷テスト

### 合格基準
- **機能**: 全エンドポイントの正常動作
- **パフォーマンス**: 応答時間要件の満足
- **セキュリティ**: 認証・認可の適切な動作

## 12. 運用考慮事項

### 運用時の注意点
- **API監視**: エンドポイント別の監視とアラート
- **ログ分析**: アクセスパターンとエラーの分析
- **セキュリティ監視**: 不正アクセスの検知

### 監視項目
- **API メトリクス**: 応答時間、エラー率、スループット
- **認証メトリクス**: ログイン成功率、トークン使用状況
- **ビジネスメトリクス**: 議事録生成数、ユーザー活動

### 保守方法
- **API ドキュメント**: 最新状態の維持
- **バージョン管理**: 後方互換性の確保
- **セキュリティ更新**: 定期的なパッチ適用

---

**作成日**: 2025年6月23日  
**作成者**: Devin AI  
**バージョン**: 1.0  
**承認者**: 未承認
