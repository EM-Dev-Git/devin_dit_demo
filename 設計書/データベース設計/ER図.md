# ER図設計書

## 1. 概要

### 目的
トランスクリプトから議事録作成APIシステムのエンティティ関係図（ER図）を詳細に定義し、データ構造とエンティティ間の関係を視覚的に明確化する

### 対象範囲
- 概念レベルER図
- 論理レベルER図
- 物理レベルER図
- エンティティ関係の詳細定義

### 前提条件
- リレーショナルデータベースモデル
- 第3正規形までの正規化
- SQLite データベースの使用

## 2. 設計方針

### 基本方針
- **明確性**: 理解しやすいエンティティ関係の表現
- **完全性**: 全てのビジネスルールを反映
- **一貫性**: 統一された記法の使用
- **拡張性**: 将来的な機能追加に対応可能

### 制約事項
- SQLite の機能制限
- 外部キー制約の適切な設定
- パフォーマンスを考慮した設計

### 品質要件
- **可読性**: 関係者が理解しやすい図表
- **正確性**: 実装と一致する設計
- **保守性**: 変更に対応しやすい構造

## 3. 概念レベルER図

### 3.1 基本エンティティ関係

```mermaid
erDiagram
    USER {
        int id PK "ユーザーID"
        string username UK "ユーザー名"
        string email UK "メールアドレス"
        string hashed_password "ハッシュ化パスワード"
        datetime created_at "作成日時"
        datetime updated_at "更新日時"
    }
    
    MINUTES {
        int id PK "議事録ID"
        int user_id FK "ユーザーID"
        string title "会議タイトル"
        text transcript "トランスクリプト"
        text generated_minutes "生成議事録"
        datetime created_at "作成日時"
    }
    
    USER ||--o{ MINUTES : "作成する"
```

### 3.2 エンティティ概要

#### User（ユーザー）
- **説明**: システムを利用するユーザーの情報
- **主要属性**: ユーザー名、メールアドレス、パスワード
- **ビジネスルール**: 
  - ユーザー名とメールアドレスは一意
  - パスワードはハッシュ化して保存

#### Minutes（議事録）
- **説明**: 生成された議事録の情報
- **主要属性**: タイトル、トランスクリプト、生成議事録
- **ビジネスルール**: 
  - 必ずユーザーに紐づく
  - トランスクリプトは必須

## 4. 論理レベルER図

### 4.1 詳細エンティティ関係

```mermaid
erDiagram
    USER {
        int id PK
        varchar username UK
        varchar email UK
        varchar hashed_password
        timestamp created_at
        timestamp updated_at
    }
    
    MINUTES {
        int id PK
        int user_id FK
        varchar title
        text transcript
        text generated_minutes
        timestamp created_at
    }
    
    USER ||--o{ MINUTES : "1:N"
```

### 4.2 関係詳細

#### User - Minutes 関係
- **関係名**: "作成する" (creates)
- **カーディナリティ**: 1:N（一対多）
- **参加制約**: 
  - User側: オプション（ユーザーは議事録を持たなくても良い）
  - Minutes側: 必須（議事録は必ずユーザーに属する）
- **参照整合性**: CASCADE DELETE（ユーザー削除時に関連議事録も削除）

### 4.3 属性詳細

#### User エンティティ
| 属性名 | データ型 | 制約 | 説明 |
|--------|----------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 主キー |
| username | VARCHAR(50) | NOT NULL, UNIQUE | ユーザー名 |
| email | VARCHAR(100) | NOT NULL, UNIQUE | メールアドレス |
| hashed_password | VARCHAR(255) | NOT NULL | ハッシュ化パスワード |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW | 更新日時 |

#### Minutes エンティティ
| 属性名 | データ型 | 制約 | 説明 |
|--------|----------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 主キー |
| user_id | INTEGER | FK, NOT NULL | 外部キー（User.id） |
| title | VARCHAR(200) | NULL | 会議タイトル |
| transcript | TEXT | NOT NULL | 元トランスクリプト |
| generated_minutes | TEXT | NOT NULL | 生成議事録 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | 作成日時 |

## 5. 物理レベルER図

### 5.1 実装レベル関係図

```mermaid
erDiagram
    users {
        INTEGER id PK
        VARCHAR_50 username UK
        VARCHAR_100 email UK
        VARCHAR_255 hashed_password
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    minutes {
        INTEGER id PK
        INTEGER user_id FK
        VARCHAR_200 title
        TEXT transcript
        TEXT generated_minutes
        TIMESTAMP created_at
    }
    
    users ||--o{ minutes : "user_id"
```

### 5.2 インデックス設計

#### Primary Key インデックス
```sql
-- 自動作成される主キーインデックス
CREATE UNIQUE INDEX pk_users ON users (id);
CREATE UNIQUE INDEX pk_minutes ON minutes (id);
```

#### Unique インデックス
```sql
-- ユーザー名一意インデックス
CREATE UNIQUE INDEX uk_users_username ON users (username);

-- メールアドレス一意インデックス
CREATE UNIQUE INDEX uk_users_email ON users (email);
```

#### Foreign Key インデックス
```sql
-- 外部キーインデックス
CREATE INDEX ix_minutes_user_id ON minutes (user_id);
```

#### 検索用インデックス
```sql
-- 複合インデックス（ユーザー別議事録検索用）
CREATE INDEX ix_minutes_user_created ON minutes (user_id, created_at DESC);

-- 日付インデックス
CREATE INDEX ix_minutes_created_at ON minutes (created_at DESC);
```

### 5.3 制約定義

#### 外部キー制約
```sql
ALTER TABLE minutes 
ADD CONSTRAINT fk_minutes_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) 
ON DELETE CASCADE 
ON UPDATE CASCADE;
```

#### チェック制約
```sql
-- ユーザー名長さ制約
ALTER TABLE users ADD CONSTRAINT ck_users_username_length 
CHECK (LENGTH(username) >= 3 AND LENGTH(username) <= 50);

-- メールアドレス長さ制約
ALTER TABLE users ADD CONSTRAINT ck_users_email_length 
CHECK (LENGTH(email) <= 100);

-- トランスクリプト最小長制約
ALTER TABLE minutes ADD CONSTRAINT ck_minutes_transcript_length 
CHECK (LENGTH(transcript) >= 10);

-- タイトル長さ制約
ALTER TABLE minutes ADD CONSTRAINT ck_minutes_title_length 
CHECK (title IS NULL OR LENGTH(title) <= 200);
```

## 6. 拡張ER図

### 6.1 将来拡張を考慮したER図

```mermaid
erDiagram
    USER {
        int id PK
        string username UK
        string email UK
        string hashed_password
        datetime created_at
        datetime updated_at
    }
    
    TEAM {
        int id PK
        string name UK
        string description
        datetime created_at
    }
    
    USER_TEAM {
        int user_id FK
        int team_id FK
        string role
        datetime joined_at
    }
    
    MINUTES {
        int id PK
        int user_id FK
        int team_id FK
        string title
        text transcript
        text generated_minutes
        datetime created_at
    }
    
    TEMPLATE {
        int id PK
        int user_id FK
        string name
        text content
        datetime created_at
    }
    
    CATEGORY {
        int id PK
        string name UK
        string description
        datetime created_at
    }
    
    MINUTES_CATEGORY {
        int minutes_id FK
        int category_id FK
    }
    
    USER ||--o{ USER_TEAM : "belongs_to"
    TEAM ||--o{ USER_TEAM : "has_member"
    USER ||--o{ MINUTES : "creates"
    TEAM ||--o{ MINUTES : "owns"
    USER ||--o{ TEMPLATE : "creates"
    MINUTES ||--o{ MINUTES_CATEGORY : "has"
    CATEGORY ||--o{ MINUTES_CATEGORY : "categorizes"
```

### 6.2 拡張エンティティ説明

#### Team（チーム）
- **目的**: チーム機能の実装
- **関係**: User との多対多関係（USER_TEAM経由）
- **属性**: チーム名、説明、作成日時

#### Template（テンプレート）
- **目的**: 議事録テンプレート機能
- **関係**: User との一対多関係
- **属性**: テンプレート名、内容、作成日時

#### Category（カテゴリ）
- **目的**: 議事録分類機能
- **関係**: Minutes との多対多関係（MINUTES_CATEGORY経由）
- **属性**: カテゴリ名、説明、作成日時

## 7. ビジネスルール図

### 7.1 制約関係図

```mermaid
graph TB
    subgraph "User制約"
        U1[username: 3-50文字]
        U2[email: 有効形式]
        U3[password: 8文字以上]
        U4[username: 一意]
        U5[email: 一意]
    end
    
    subgraph "Minutes制約"
        M1[transcript: 10文字以上]
        M2[title: 200文字以下]
        M3[user_id: 必須]
        M4[generated_minutes: 必須]
    end
    
    subgraph "関係制約"
        R1[User削除時Minutes削除]
        R2[Minutes作成時User存在確認]
    end
    
    U1 --> User
    U2 --> User
    U3 --> User
    U4 --> User
    U5 --> User
    
    M1 --> Minutes
    M2 --> Minutes
    M3 --> Minutes
    M4 --> Minutes
    
    R1 --> UserMinutes[User-Minutes関係]
    R2 --> UserMinutes
```

### 7.2 データフロー図

```mermaid
graph LR
    subgraph "ユーザー登録フロー"
        A1[ユーザー情報入力] --> A2[重複チェック]
        A2 --> A3[パスワードハッシュ化]
        A3 --> A4[User作成]
    end
    
    subgraph "議事録生成フロー"
        B1[トランスクリプト入力] --> B2[ユーザー認証]
        B2 --> B3[OpenAI API呼び出し]
        B3 --> B4[Minutes作成]
        B4 --> B5[User-Minutes関連付け]
    end
    
    A4 --> B2
```

## 8. 正規化検証図

### 8.1 正規化プロセス

```mermaid
graph TB
    subgraph "非正規化テーブル"
        T0[user_minutes_combined<br/>id, username, email, password,<br/>minutes_id, title, transcript,<br/>generated_minutes, created_at]
    end
    
    subgraph "1NF適用"
        T1[各属性が原子値<br/>繰り返しグループなし]
    end
    
    subgraph "2NF適用"
        T2[部分関数従属の除去<br/>複合キーの分解]
    end
    
    subgraph "3NF適用"
        T3A[users<br/>id, username, email,<br/>hashed_password, timestamps]
        T3B[minutes<br/>id, user_id, title,<br/>transcript, generated_minutes,<br/>created_at]
    end
    
    T0 --> T1
    T1 --> T2
    T2 --> T3A
    T2 --> T3B
```

### 8.2 関数従属性図

```mermaid
graph LR
    subgraph "Users テーブル"
        U_ID[id] --> U_ALL[username, email,<br/>hashed_password,<br/>created_at, updated_at]
        U_USERNAME[username] --> U_OTHER[id, email,<br/>hashed_password,<br/>created_at, updated_at]
        U_EMAIL[email] --> U_OTHER2[id, username,<br/>hashed_password,<br/>created_at, updated_at]
    end
    
    subgraph "Minutes テーブル"
        M_ID[id] --> M_ALL[user_id, title,<br/>transcript,<br/>generated_minutes,<br/>created_at]
    end
```

## 9. パフォーマンス考慮図

### 9.1 インデックス効果図

```mermaid
graph TB
    subgraph "クエリパターン"
        Q1[ユーザー認証<br/>WHERE username = ?]
        Q2[議事録一覧<br/>WHERE user_id = ?<br/>ORDER BY created_at DESC]
        Q3[特定議事録<br/>WHERE id = ? AND user_id = ?]
    end
    
    subgraph "使用インデックス"
        I1[uk_users_username]
        I2[ix_minutes_user_created]
        I3[pk_minutes + ix_minutes_user_id]
    end
    
    Q1 --> I1
    Q2 --> I2
    Q3 --> I3
```

### 9.2 データアクセスパターン

```mermaid
sequenceDiagram
    participant App as Application
    participant DB as Database
    participant UI as User Index
    participant MI as Minutes Index
    
    App->>DB: SELECT * FROM users WHERE username = ?
    DB->>UI: Index Seek
    UI-->>DB: Row Location
    DB-->>App: User Data
    
    App->>DB: SELECT * FROM minutes WHERE user_id = ? ORDER BY created_at DESC
    DB->>MI: Index Seek + Sort
    MI-->>DB: Sorted Row Locations
    DB-->>App: Minutes List
```

## 10. 実装マッピング

### 10.1 SQLAlchemy マッピング図

```mermaid
classDiagram
    class User {
        +Integer id
        +String username
        +String email
        +String hashed_password
        +DateTime created_at
        +DateTime updated_at
        +relationship minutes
    }
    
    class Minutes {
        +Integer id
        +Integer user_id
        +String title
        +Text transcript
        +Text generated_minutes
        +DateTime created_at
        +relationship user
    }
    
    User ||--o{ Minutes : "one-to-many"
```

### 10.2 API エンドポイントマッピング

```mermaid
graph LR
    subgraph "User関連API"
        A1[POST /auth/register] --> User
        A2[POST /auth/login] --> User
        A3[GET /users/profile] --> User
        A4[PUT /users/profile] --> User
    end
    
    subgraph "Minutes関連API"
        B1[POST /minutes/generate] --> Minutes
        B2[GET /minutes/history] --> Minutes
        B3[GET /minutes/{id}] --> Minutes
    end
    
    subgraph "データベース"
        User[users テーブル]
        Minutes[minutes テーブル]
    end
    
    User --> Minutes
```

## 11. 制約検証図

### 11.1 整合性制約チェック

```mermaid
flowchart TD
    Start([データ操作開始]) --> CheckPK{主キー制約}
    CheckPK -->|OK| CheckFK{外部キー制約}
    CheckPK -->|NG| ErrorPK[主キーエラー]
    
    CheckFK -->|OK| CheckUnique{一意制約}
    CheckFK -->|NG| ErrorFK[外部キーエラー]
    
    CheckUnique -->|OK| CheckDomain{ドメイン制約}
    CheckUnique -->|NG| ErrorUnique[一意制約エラー]
    
    CheckDomain -->|OK| Success([操作成功])
    CheckDomain -->|NG| ErrorDomain[ドメイン制約エラー]
    
    ErrorPK --> Rollback[ロールバック]
    ErrorFK --> Rollback
    ErrorUnique --> Rollback
    ErrorDomain --> Rollback
```

### 11.2 トランザクション境界

```mermaid
sequenceDiagram
    participant App as Application
    participant DB as Database
    
    Note over App,DB: ユーザー登録トランザクション
    App->>DB: BEGIN TRANSACTION
    App->>DB: INSERT INTO users
    App->>DB: COMMIT
    
    Note over App,DB: 議事録生成トランザクション
    App->>DB: BEGIN TRANSACTION
    App->>DB: SELECT user (認証)
    App->>DB: INSERT INTO minutes
    App->>DB: COMMIT
```

## 12. 運用考慮事項

### 12.1 バックアップ対象

```mermaid
graph TB
    subgraph "バックアップ対象"
        DB[app.db]
        WAL[app.db-wal]
        SHM[app.db-shm]
    end
    
    subgraph "バックアップ方式"
        FULL[フルバックアップ]
        INCR[増分バックアップ]
    end
    
    DB --> FULL
    WAL --> INCR
    SHM --> INCR
```

### 12.2 監視ポイント

```mermaid
graph LR
    subgraph "監視項目"
        SIZE[ファイルサイズ]
        PERF[クエリ性能]
        CONN[接続数]
        LOCK[ロック状況]
    end
    
    subgraph "アラート条件"
        A1[サイズ > 1GB]
        A2[応答時間 > 3秒]
        A3[接続数 > 100]
        A4[ロック待機 > 30秒]
    end
    
    SIZE --> A1
    PERF --> A2
    CONN --> A3
    LOCK --> A4
```

## 13. テスト観点

### 13.1 データ整合性テスト

```mermaid
graph TB
    subgraph "テスト項目"
        T1[主キー重複テスト]
        T2[外部キー制約テスト]
        T3[一意制約テスト]
        T4[NOT NULL制約テスト]
        T5[チェック制約テスト]
    end
    
    subgraph "期待結果"
        R1[エラー発生]
        R2[エラー発生]
        R3[エラー発生]
        R4[エラー発生]
        R5[エラー発生]
    end
    
    T1 --> R1
    T2 --> R2
    T3 --> R3
    T4 --> R4
    T5 --> R5
```

### 13.2 パフォーマンステスト

```mermaid
graph LR
    subgraph "負荷パターン"
        L1[単一ユーザー]
        L2[10並行ユーザー]
        L3[100並行ユーザー]
    end
    
    subgraph "測定項目"
        M1[応答時間]
        M2[スループット]
        M3[リソース使用率]
    end
    
    L1 --> M1
    L2 --> M2
    L3 --> M3
```

---

**作成日**: 2025年6月23日  
**作成者**: Devin AI  
**バージョン**: 1.0  
**承認者**: 未承認
