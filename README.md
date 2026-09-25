# カード利用料・口座引落集計ツール

## 1. 概要

複数のクレジットカード利用明細CSVを明細単位で取り込み、カードごとに設定された引落口座へ集約する月次集計ツールです。

カード利用明細には**利用日**と**請求月**を保持します。集計時は請求月を基準とし、銀行口座ごとに次の金額を合算して出力します。

- クレジットカード利用額
- 口座に設定された月次の銀行引落額
- 上記2項目の合計額

カードと銀行口座の紐付け、および銀行引落額は月単位で変更できます。

## 2. 目的

- 複数カードの請求額を一元管理する
- 銀行口座ごとの月次引落予定額を把握する
- カードの引落口座変更を履歴として管理する
- 銀行引落額の月次変更を履歴として管理する
- 元CSVと取り込んだ明細を追跡可能にする
- 同一CSVまたは同一明細の重複取込を防止する

## 3. 技術構成

| 区分 | 採用技術 |
|---|---|
| 実行環境 | Python 3.x |
| データベース | SQLite |
| CSV処理 | Python標準ライブラリ `csv` または `pandas` |
| 集計 | SQL View |
| バッチ実行 | Windows Batch File |
| 出力 | CSV。将来的にExcel出力へ拡張可能 |

## 4. システム構成

```text
カード会社CSV
    ↓
カード別CSVインポーター
    ↓
入力値検証・正規化
    ↓
SQLite Database
    ↓
月別・銀行口座別集計View
    ↓
CSVレポート出力
```

## 5. ディレクトリ構成

```text
card-payment-manager/
├─ README.md
├─ requirements.txt
├─ run.bat
├─ config/
│  └─ settings.toml
├─ input/
│  ├─ rakuten/
│  │  ├─ raw/
│  │  │  ├─ 202608.csv
│  │  │  └─ 202609.csv
│  │  └─ imported/
│  ├─ smbc/
│  │  ├─ raw/
│  │  └─ imported/
│  └─ jcb/
│     ├─ raw/
│     └─ imported/
├─ output/
│  ├─ 202608/
│  └─ 202609/
├─ db/
│  └─ payment.db
├─ logs/
├─ sql/
│  ├─ schema.sql
│  ├─ seed.sql
│  └─ views.sql
├─ src/
│  ├─ main.py
│  ├─ database.py
│  ├─ import_service.py
│  ├─ report_service.py
│  ├─ models/
│  └─ importers/
│     ├─ base.py
│     ├─ rakuten.py
│     ├─ smbc.py
│     └─ jcb.py
└─ tests/
   ├─ test_importers.py
   ├─ test_aggregation.py
   └─ fixtures/
```

### 5.1 入力フォルダの方針

カード会社ごとにCSV形式が異なるため、年月ではなく**カード種別を第1階層**とします。

- `input/<card_code>/raw/`: 未取込CSV
- `input/<card_code>/imported/`: 正常取込済みCSV
- フォルダ名の `card_code` をカード識別子として使用
- ファイル名は原則 `YYYYMM.csv`
- CSV内の請求月を正とし、ファイル名の年月は検証用として扱う

正常終了後にCSVを `raw` から `imported` へ移動します。異常終了時は移動せず、ログへエラーを記録します。

## 6. 用語

| 用語 | 説明 |
|---|---|
| 利用日 | 商品またはサービスをカードで利用した日 |
| 請求月 | カード会社が利用額を請求する対象月。本ツールのカード集計基準 |
| 引落月 | 銀行口座から実際に引き落とされる月。初期版では請求月と同一として扱い、必要に応じて将来拡張する |
| 銀行引落額 | カード利用料とは別に、銀行口座ごとに月単位で設定する金額 |
| 適用月 | カードと口座の紐付けや銀行引落額が有効になる月 |

## 7. 機能要件

### 7.1 マスタ管理

- 銀行口座を登録・更新できる
- クレジットカードを登録・更新できる
- カードごとにCSVインポーター種別を設定できる
- カードと銀行口座の紐付けを月単位で変更できる
- 銀行口座ごとの銀行引落額を月単位で変更できる

### 7.2 CSV取込

- `input/*/raw/*.csv` を再帰的に検索する
- 親フォルダのカードコードから対象カードを特定する
- カード別インポーターでCSVを読み込む
- 各明細を共通形式へ正規化する
- 利用日、請求月、利用先、金額を保持する
- ファイルハッシュを記録し、同一ファイルの再取込を防止する
- 明細の一意キーを作成し、同一明細の重複登録を防止する
- 1ファイル単位のトランザクションで登録する
- 取込成功時のみ入力CSVを `imported` へ移動する
- 取込結果をログへ出力する

### 7.3 集計

指定した請求月について、以下を集計します。

1. カード別利用額
2. カードと銀行口座の月次紐付け
3. 銀行口座別カード利用額
4. 銀行口座別の銀行引落額
5. 銀行口座別総引落予定額

```text
銀行口座別総引落予定額
= カード利用額合計
+ 銀行引落額合計
```

### 7.4 レポート出力

- 銀行口座別月次集計
- カード別月次集計
- カード利用明細一覧
- 取込エラー一覧

## 8. データベース設計

月は `YYYY-MM` 形式の `TEXT`、金額は浮動小数点誤差を避けるため**円単位の `INTEGER`**として保持します。

### 8.1 `bank_account`

| 列名 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | INTEGER | PK | 銀行口座ID |
| account_code | TEXT | NOT NULL, UNIQUE | システム上の口座コード |
| account_name | TEXT | NOT NULL | 表示名 |
| display_order | INTEGER | NOT NULL DEFAULT 0 | 表示順 |
| enabled | INTEGER | NOT NULL DEFAULT 1 | 有効フラグ |
| created_at | TEXT | NOT NULL | 登録日時 |
| updated_at | TEXT | NOT NULL | 更新日時 |

口座番号などの機密情報は、集計に不要なため原則保存しません。

### 8.2 `credit_card`

| 列名 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | INTEGER | PK | カードID |
| card_code | TEXT | NOT NULL, UNIQUE | 入力フォルダ名と対応するコード |
| card_name | TEXT | NOT NULL | 表示名 |
| importer_type | TEXT | NOT NULL | 使用するインポーター種別 |
| enabled | INTEGER | NOT NULL DEFAULT 1 | 有効フラグ |
| created_at | TEXT | NOT NULL | 登録日時 |
| updated_at | TEXT | NOT NULL | 更新日時 |

カード番号は保存しません。識別が必要な場合も末尾4桁など必要最小限に限定します。

### 8.3 `card_bank_account_assignment`

カードと銀行口座の月次紐付け履歴です。

| 列名 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | INTEGER | PK | ID |
| card_id | INTEGER | NOT NULL, FK | カードID |
| bank_account_id | INTEGER | NOT NULL, FK | 銀行口座ID |
| start_month | TEXT | NOT NULL | 適用開始月 |
| end_month | TEXT | NULL | 適用終了月。NULLは無期限 |
| created_at | TEXT | NOT NULL | 登録日時 |

同一カードについて適用期間が重複しないよう、登録処理で検証します。

### 8.4 `bank_monthly_payment`

銀行口座ごとの月次引落設定です。金額変更時は既存行を上書きせず、新しい適用期間を追加します。

| 列名 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | INTEGER | PK | ID |
| bank_account_id | INTEGER | NOT NULL, FK | 銀行口座ID |
| payment_name | TEXT | NOT NULL | 引落項目名 |
| amount | INTEGER | NOT NULL | 円単位の金額 |
| start_month | TEXT | NOT NULL | 適用開始月 |
| end_month | TEXT | NULL | 適用終了月。NULLは無期限 |
| created_at | TEXT | NOT NULL | 登録日時 |

複数の引落項目を口座ごとに登録できる設計とします。

### 8.5 `import_file`

| 列名 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | INTEGER | PK | 取込ファイルID |
| card_id | INTEGER | NOT NULL, FK | カードID |
| original_file_name | TEXT | NOT NULL | 元ファイル名 |
| relative_path | TEXT | NOT NULL | 入力時の相対パス |
| file_hash | TEXT | NOT NULL, UNIQUE | SHA-256ハッシュ |
| billing_month | TEXT | NULL | ファイルの対象請求月 |
| status | TEXT | NOT NULL | `processing`、`success`、`failed` |
| row_count | INTEGER | NOT NULL DEFAULT 0 | 読込行数 |
| imported_count | INTEGER | NOT NULL DEFAULT 0 | 登録件数 |
| skipped_count | INTEGER | NOT NULL DEFAULT 0 | スキップ件数 |
| error_message | TEXT | NULL | エラー内容 |
| imported_at | TEXT | NOT NULL | 取込日時 |

### 8.6 `card_usage`

| 列名 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | INTEGER | PK | 明細ID |
| card_id | INTEGER | NOT NULL, FK | カードID |
| import_file_id | INTEGER | NOT NULL, FK | 取込ファイルID |
| usage_date | TEXT | NOT NULL | 利用日 `YYYY-MM-DD` |
| billing_month | TEXT | NOT NULL | 請求月 `YYYY-MM` |
| merchant_name | TEXT | NOT NULL | 利用先 |
| amount | INTEGER | NOT NULL | 円単位の利用額 |
| description | TEXT | NULL | 摘要・補足 |
| original_row_number | INTEGER | NOT NULL | 元CSVの行番号 |
| source_detail_id | TEXT | NULL | CSVに明細IDがある場合の値 |
| detail_hash | TEXT | NOT NULL | 正規化後の明細ハッシュ |
| created_at | TEXT | NOT NULL | 登録日時 |

```sql
CREATE UNIQUE INDEX ux_card_usage_detail
ON card_usage(card_id, billing_month, detail_hash);
```

取消・返金は負数金額として保持します。元CSVに明細IDがある場合は、それを優先して重複判定へ使用します。

## 9. 適用期間の判定

```sql
assignment.start_month <= usage.billing_month
AND (
    assignment.end_month IS NULL
    OR usage.billing_month <= assignment.end_month
)
```

銀行引落設定も同様に対象月が適用期間内かを判定します。

## 10. View設計

### 10.1 `v_monthly_card_usage`

請求月・カード単位の利用額を集計します。

- `billing_month`
- `card_id`
- `card_code`
- `card_name`
- `amount`
- `detail_count`

### 10.2 `v_monthly_bank_card_usage`

請求月のカード・口座紐付けを適用し、銀行口座単位にカード利用額を集計します。

- `billing_month`
- `bank_account_id`
- `account_code`
- `account_name`
- `card_amount`
- `detail_count`

### 10.3 `v_monthly_bank_payment`

銀行口座ごとの設定済み銀行引落額を対象月単位で集計します。

- `billing_month`
- `bank_account_id`
- `bank_payment_amount`

設定テーブルだけでは全対象月を生成できないため、実装時は対象月をパラメーターとしてクエリするか、月マスタを追加します。

### 10.4 `v_monthly_bank_summary`

- `billing_month`
- `bank_account_id`
- `account_code`
- `account_name`
- `card_amount`
- `bank_payment_amount`
- `total_amount`

```text
total_amount = card_amount + bank_payment_amount
```

## 11. CSVインポーター仕様

### 11.1 共通インターフェイス

```python
class CardCsvImporter:
    def can_handle(self, card_code: str) -> bool:
        ...

    def read(self, file_path: Path, billing_month: str | None = None):
        ...
```

共通明細モデルの必須項目:

- `usage_date`
- `billing_month`
- `merchant_name`
- `amount`
- `original_row_number`

### 11.2 請求月の決定順

1. CSV内の請求月列
2. カード会社固有のファイルヘッダー
3. コマンドライン引数
4. ファイル名 `YYYYMM.csv`

複数の方法で得た請求月が一致しない場合、初期実装では取込を中止します。

### 11.3 文字コード

カード別インポーターで `UTF-8 with BOM`、`UTF-8`、`CP932` などを明示し、自動判定だけに依存しません。

### 11.4 金額の正規化

- 桁区切りカンマと通貨記号を除去する
- 円単位の整数へ変換する
- 返金・取消は負数へ統一する
- 想定外の小数は黙って丸めず、エラーまたは明示変換する

## 12. 取込処理フロー

1. DBへ接続する
2. `input/*/raw/*.csv` を列挙する
3. 親フォルダ名からカードを特定する
4. SHA-256を計算し、取込済みファイルか確認する
5. `import_file` に `processing` 状態で登録する
6. カード別インポーターでCSVを読み込む
7. 利用日、請求月、利用先、金額を検証・正規化する
8. 明細ハッシュを生成する
9. 1ファイル単位のトランザクションで明細を登録する
10. `import_file` を `success` に更新する
11. CSVを `imported` へ移動する
12. エラー時はロールバックし、`failed` とエラー内容を記録する

## 13. バッチ実行仕様

```bat
python -m src.main init-db
python -m src.main import
python -m src.main report --month 2026-08
python -m src.main run --month 2026-08
```

`run` は未取込CSVの取込後、指定月を集計してレポートを出力します。

## 14. 出力仕様

```text
output/202608/bank_summary_202608.csv
output/202608/card_summary_202608.csv
output/202608/card_usage_202608.csv
```

銀行口座別月次集計の列:

| 列名 | 説明 |
|---|---|
| billing_month | 請求月 |
| account_code | 口座コード |
| account_name | 口座名 |
| card_amount | カード利用額 |
| bank_payment_amount | 銀行引落額 |
| total_amount | 合計額 |

## 15. エラー処理

次の場合はファイル全体をロールバックします。

- カードフォルダに対応するマスタが存在しない
- 必須列が存在しない
- 利用日を変換できない
- 請求月を決定できない
- 金額を整数へ変換できない
- ファイル名とCSV内の請求月が矛盾する
- 対象月のカード・口座紐付けが存在しない
- 同一カードに期間重複する口座設定がある

同一明細が既に存在する場合の初期値はエラーとし、将来的に警告スキップを選べるようにします。

## 16. ログ仕様

- 実行開始・終了日時
- 対象ファイルとカード
- 読込件数、登録件数、スキップ件数
- 請求月
- エラー内容

カード番号、口座番号、認証情報、CSV全行はログへ出力しません。

## 17. セキュリティ要件

- カード番号、セキュリティコード、銀行口座番号は保存しない
- 不要な機密列はDBへ保存しない
- DB、入力CSV、出力CSVのアクセス権を必要最小限にする
- SQLはプレースホルダーを使用する
- バックアップも本体と同等に保護する

## 18. テスト方針

### インポーター

- カード会社ごとの正常CSVを共通形式へ変換できる
- 文字コード、日付形式、返金明細を処理できる
- 必須列不足と不正金額を検出できる

### 集計

- 複数カードを同一口座へ集約できる
- 口座変更月の前後で正しい口座へ集約される
- 銀行引落額変更月の前後で正しい金額が適用される
- カード利用がない口座も銀行引落額を出力できる
- 銀行引落額がない口座もカード利用額を出力できる
- 返金を含む合計額が正しい

### 冪等性

- 同一ファイルを再実行しても重複登録されない
- 取込途中で失敗しても中途半端な明細が残らない
- 失敗後に修正したCSVを再取込できる

## 19. 実装順序

1. ディレクトリと設定ファイルを作成する
2. SQLiteスキーマを作成する
3. マスタ登録方法を実装する
4. 共通インポーターインターフェイスを作成する
5. 1社分のインポーターを実装する
6. 取込履歴と重複防止を実装する
7. 集計Viewを実装する
8. CSVレポート出力を実装する
9. `run.bat` を作成する
10. 他カードのインポーターを追加する
11. テストと運用ログを整備する

## 20. ベストプラクティス

- 元CSVは加工せず保存する
- 金額は `REAL` ではなく円単位の `INTEGER` で保持する
- 月次設定は上書きせず、適用期間で履歴管理する
- CSV形式差は巨大な条件分岐ではなくカード別クラスへ分離する
- 取込はファイル単位のトランザクションとする
- ファイル名だけを請求月の唯一の情報源にしない

## 21. アンチパターン

### 月フォルダを第1階層にする

カード別のCSV形式、再処理、インポーター選択が複雑になります。カード別フォルダを第1階層にします。

### 月次合計だけを保存する

利用先確認、重複確認、返金確認ができません。明細を保存し、合計はViewで算出します。

### 現在の引落口座だけをカードマスタへ持たせる

過去月の再集計結果が変わります。適用期間付き履歴テーブルを使います。

### 取込済み判定をファイル名だけにする

同名ファイルの差し替えを検知できません。ファイルハッシュと明細ハッシュを併用します。

### 取込後に元CSVを削除する

再現や障害解析ができません。正常取込後は `imported` へ移動して保持します。

## 22. 将来拡張

- 実際の引落月を保持し、請求月と分離する
- 銀行残高と月末予測残高を管理する
- Excelレポートを生成する
- Power BIなどへ連携する
- カテゴリ自動分類を追加する
- GUIでマスタと月次設定を編集する
- API・PDF明細取込へ対応する

## 23. 初期実装の対象範囲

- SQLiteによるローカル運用
- 円建てのみ
- CSV取込のみ
- カード別フォルダ構成
- 利用日と請求月の保持
- 月別・銀行口座別集計
- CSVレポート出力
- バッチファイルからの実行

GUI、クラウド同期、銀行残高管理、実引落日の管理は初期版の対象外です。
