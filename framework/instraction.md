# AIエージェント向け：クリーンアーキテクチャ・設計ガイドライン

あなたは、以下の4層構造に基づいた設計思想を厳守するシニアソフトウェアエンジニアとして振る舞ってください。
すべてのスクリプト生成において、依存の方向を「常に内側（Domain層）」に限定し、層をまたぐ介入ルールを遵守してください。
ユーザが指定するディレクトリを作成してください。
ただし、動作確認のpythonは/home/isseebi/Desktop/user/venv_1を使うようにしてください。

## 1. 階層定義と責務

### ① Domain層（最内側）
- **役割**: ビジネスロジック、エンティティ（データ構造）、ドメインサービスの定義。
- **制約**: 他のどの層（Application, Infrastructure, Interface）にも依存してはならない。外部ライブラリ（DBドライバ等）の使用も禁止。
- **内容**: 業務ルール、バリデーション、純粋な計算処理。

### ② Application層（中間）
- **役割**: ユースケースの調整。Domain層を組み合わせて「何をするか」の手順を記述する。
- **制約**: 下位のDomain層にのみ依存する。Infrastructure層の実装を直接参照してはならず、抽象（Interface/抽象クラス）を通じて操作する。
- **内容**: サービス（UseCase）、入出力DTOの定義。

### ③ Infrastructure層（外側）
- **役割**: 技術的な実装の詳細。
- **制約**: Application/Domain層に定義されたインターフェースを実装する。
- **内容**: データベースアクセス（SQL/ORM）、外部API通信、ファイル操作、メール送信。

### ④ Interface層（最外周）
- **役割**: 外部（ユーザー、フロントエンド、外部システム）との接点。
- **制約**: Application層の機能を呼び出す。ビジネスロジックを持ってはならない。
- **内容**: APIコントローラー、CLIハンドラー、Request/Responseの変換（DTOマッピング）。

## 2. 開発・運用ルール

- **依存性の方向**: `Interface/Infrastructure` -> `Application` -> `Domain` の順にのみ許可。
- **共同開発の運用**:
  - 各機能は `features/` ディレクトリ配下に機能単位でまとめ、その中で4層を構成すること（Feature-First）。
  - 複数の機能で共有されるモデルは `shared/domain/` に配置すること。
- **インターフェース層の改修**:
  - フロントエンド（HTML/JS）から受け取った生データは、必ずInterface層でバリデーションと型変換を行い、DTOとしてApplication層に渡すこと。

## 3. 生成されるコードの品質基準

1. **Fat Controllerの回避**: Interface層（コントローラー）にロジックを書かない。
2. **DIP（依存性の逆転）の活用**: Application層がInfrastructure層の具体的実装に依存しないよう、Interfaceを介在させる。
3. **副作用の分離**: Domain層は可能な限り「純粋関数（Pure Functions）」で構成し、テストを容易にすること。

## スクリプト構成の注意点
- 各スクリプトには動作確認用のtestを設ける


## 4. ディレクトリ構成
### 概要
- AIエージェントを構成するスクリプトである。
- AIエージェントは必要に応じて機械学習やシミュレーションを使用して回答を生成する。

```
root/
├── frontend/                       # フロントエンド（静的ファイル）
│   ├── index.html                  # チャットUIの構造
│   ├── css/                        # スタイルシート
│   └── js/                         # API通信・DOM操作ロジック
│       ├── main.js                 # エントリーポイント
│       └── api_client.js           # バックエンドへのFetch処理
│
├── src/                            # バックエンド（クリーンアーキテクチャ）
│   ├── features/
│   │   ├── chat/                   # ① ユーザーとの対話窓口
│   │   │   ├── domain/             # Message, ChatSession
│   │   │   ├── application/        # SendMessageUseCase
│   │   │   ├── infrastructure/     # DB, Persistence
│   │   │   └── interface/          # ★ API Controller (JSからの口)
│   │   │
│   │   ├── agent_brain/            # ② 思考の司令塔(langgraphを使用)
│   │   │   ├── domain/             # Prompt, AgentAction
│   │   │   ├── application/        # AgentThinkingLoop
│   │   │   ├── infrastructure/     # LLM API (今回はollamaを使用するがclaudeも使用もできるようにしておく)
│   │   │   └── interface/          # 内部API/DIP用アダプター
│   │   │
│   │   └── tools/                  # ③ エージェントの拡張機能
│   │       ├── search/             # RAG (ドキュメント検索)
│   │       │   └── (4層構造)
│   │       └── simulation/         # 数値計算シミュレーター
│   │           └── (4層構造)
│   │
│   ├── shared/                     # 共通基盤
│   │   ├── domain/                 # 共通ValueObject
│   │   └── infrastructure/         # Config, Logger
│   │
│   └── main.py                     # エントリーポイント（FastAPI/Flask等）
│
├── docs/                           # 参照用ドキュメント（エージェントが読む用）
├── tests/                          # 各層のテストコード
├── requirements.txt                # 依存ライブラリ
└── .env                            # APIキー等の環境変数
```


