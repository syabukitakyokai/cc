BEGIN TRANSACTION;

--------------------------------------------------
-- 銀行口座マスタ
--------------------------------------------------

INSERT INTO bank_account (
    account_code,
    account_name,
    display_order,
    enabled
)
VALUES (
    'rakuten_bank',
    '楽天銀行',
    1,
    1
)
ON CONFLICT (account_code)
DO UPDATE SET
    account_name = excluded.account_name,
    display_order = excluded.display_order,
    enabled = excluded.enabled;

INSERT INTO bank_account (
    account_code,
    account_name,
    display_order,
    enabled
)
VALUES (
    'sbi_bank',
    '住信SBIネット銀行',
    2,
    1
)
ON CONFLICT (account_code)
DO UPDATE SET
    account_name = excluded.account_name,
    display_order = excluded.display_order,
    enabled = excluded.enabled;

--------------------------------------------------
-- クレジットカードマスタ
--------------------------------------------------

INSERT INTO credit_card (
    card_code,
    card_name
)
VALUES (
    'rakuten_master',
    '楽天カード'
)
ON CONFLICT (card_code)
DO UPDATE SET
    card_name = excluded.card_name;

INSERT INTO credit_card (
    card_code,
    card_name
)
VALUES (
    'rakuten_pink',
    '楽天PINKカード'
)
ON CONFLICT (card_code)
DO UPDATE SET
    card_name = excluded.card_name;

INSERT INTO credit_card (
    card_code,
    card_name
)
VALUES (
    'smbc',
    '三井住友カード'
)
ON CONFLICT (card_code)
DO UPDATE SET
    card_name = excluded.card_name;

--------------------------------------------------
-- カード・銀行口座紐付け
--------------------------------------------------

INSERT INTO card_bank_account_assignment (
    card_id,
    bank_account_id,
    start_month,
    end_month
)
VALUES (
    (
        SELECT id
        FROM credit_card
        WHERE card_code = 'rakuten_master'
    ),
    (
        SELECT id
        FROM bank_account
        WHERE account_code = 'rakuten_bank'
    ),
    '2026-01',
    NULL
)
ON CONFLICT (
    card_id,
    start_month
)
DO UPDATE SET
    bank_account_id = excluded.bank_account_id,
    end_month = excluded.end_month;

INSERT INTO card_bank_account_assignment (
    card_id,
    bank_account_id,
    start_month,
    end_month
)
VALUES (
    (
        SELECT id
        FROM credit_card
        WHERE card_code = 'rakuten_pink'
    ),
    (
        SELECT id
        FROM bank_account
        WHERE account_code = 'rakuten_bank'
    ),
    '2026-01',
    NULL
)
ON CONFLICT (
    card_id,
    start_month
)
DO UPDATE SET
    bank_account_id = excluded.bank_account_id,
    end_month = excluded.end_month;


INSERT INTO card_bank_account_assignment (
    card_id,
    bank_account_id,
    start_month,
    end_month
)
VALUES (
    (
        SELECT id
        FROM credit_card
        WHERE card_code = 'smbc'
    ),
    (
        SELECT id
        FROM bank_account
        WHERE account_code = 'sbi_bank'
    ),
    '2026-01',
    NULL
)
ON CONFLICT (
    card_id,
    start_month
)
DO UPDATE SET
    bank_account_id = excluded.bank_account_id,
    end_month = excluded.end_month;

--------------------------------------------------
-- 銀行口座の月次引落設定
--------------------------------------------------

INSERT INTO bank_monthly_payment (
    bank_account_id,
    payment_name,
    amount,
    start_month,
    end_month
)
VALUES (
    (
        SELECT id
        FROM bank_account
        WHERE account_code = 'rakuten_bank'
    ),
    '固定引落',
    50000,
    '2026-01',
    NULL
)
ON CONFLICT (
    bank_account_id,
    payment_name,
    start_month
)
DO UPDATE SET
    amount = excluded.amount,
    end_month = excluded.end_month;

INSERT INTO bank_monthly_payment (
    bank_account_id,
    payment_name,
    amount,
    start_month,
    end_month
)
VALUES (
    (
        SELECT id
        FROM bank_account
        WHERE account_code = 'sbi_bank'
    ),
    '固定引落',
    10000,
    '2026-01',
    NULL
)
ON CONFLICT (
    bank_account_id,
    payment_name,
    start_month
)
DO UPDATE SET
    amount = excluded.amount,
    end_month = excluded.end_month;

--------------------------------------------------
-- 動作確認用のCSV取込履歴
--------------------------------------------------

INSERT INTO import_file (
    card_id,
    original_file_name,
    relative_path,
    file_hash,
    withdrawal_month,
    status,
    row_count,
    imported_count,
    skipped_count,
    error_message
)
VALUES (
    (
        SELECT id
        FROM credit_card
        WHERE card_code LIKE 'rakuten_%'
    ),
    '202609.csv',
    'input/rakuten/imported/202609.csv',
    'seed-file-hash-rakuten-202609',
    '2026-09',
    'success',
    2,
    2,
    0,
    NULL
)
ON CONFLICT (file_hash)
DO UPDATE SET
    card_id = excluded.card_id,
    original_file_name = excluded.original_file_name,
    relative_path = excluded.relative_path,
    withdrawal_month = excluded.withdrawal_month,
    status = excluded.status,
    row_count = excluded.row_count,
    imported_count = excluded.imported_count,
    skipped_count = excluded.skipped_count,
    error_message = excluded.error_message;

--------------------------------------------------
-- 動作確認用カード利用明細
--------------------------------------------------

INSERT INTO card_usage (
    card_id,
    import_file_id,
    usage_date,
    withdrawal_month,
    merchant_name,
    amount,
    description,
    original_row_number,
    source_detail_id,
    detail_hash
)
VALUES (
    (
        SELECT id
        FROM credit_card
        WHERE card_code LIKE 'rakuten_%'
    ),
    (
        SELECT id
        FROM import_file
        WHERE file_hash = 'seed-file-hash-rakuten-202609'
    ),
    '2026-08-05',
    '2026-09',
    'Amazon',
    2580,
    '動作確認用明細',
    1,
    'seed-rakuten-202609-001',
    'seed-detail-hash-rakuten-202609-001'
)
ON CONFLICT (
    card_id,
    withdrawal_month,
    detail_hash
)
DO UPDATE SET
    import_file_id = excluded.import_file_id,
    usage_date = excluded.usage_date,
    merchant_name = excluded.merchant_name,
    amount = excluded.amount,
    description = excluded.description,
    original_row_number = excluded.original_row_number,
    source_detail_id = excluded.source_detail_id;

INSERT INTO card_usage (
    card_id,
    import_file_id,
    usage_date,
    withdrawal_month,
    merchant_name,
    amount,
    description,
    original_row_number,
    source_detail_id,
    detail_hash
)
VALUES (
    (
        SELECT id
        FROM credit_card
        WHERE card_code LIKE 'rakuten_%'
    ),
    (
        SELECT id
        FROM import_file
        WHERE file_hash = 'seed-file-hash-rakuten-202609'
    ),
    '2026-08-20',
    '2026-09',
    'ENEOS',
    5000,
    '動作確認用明細',
    2,
    'seed-rakuten-202609-002',
    'seed-detail-hash-rakuten-202609-002'
)
ON CONFLICT (
    card_id,
    withdrawal_month,
    detail_hash
)
DO UPDATE SET
    import_file_id = excluded.import_file_id,
    usage_date = excluded.usage_date,
    merchant_name = excluded.merchant_name,
    amount = excluded.amount,
    description = excluded.description,
    original_row_number = excluded.original_row_number,
    source_detail_id = excluded.source_detail_id;

INSERT OR IGNORE INTO calendar_month(month) VALUES ('2026-08');
INSERT OR IGNORE INTO calendar_month(month) VALUES ('2026-09');
INSERT OR IGNORE INTO calendar_month(month) VALUES ('2026-10');

COMMIT;