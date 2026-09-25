--------------------------------------------------
-- 銀行口座
--------------------------------------------------

CREATE TABLE bank_account (
    id INTEGER PRIMARY KEY,

    account_code TEXT NOT NULL UNIQUE,
    account_name TEXT NOT NULL,

    display_order INTEGER NOT NULL DEFAULT 0,

    enabled INTEGER NOT NULL DEFAULT 1,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------
-- クレジットカード
--------------------------------------------------

CREATE TABLE credit_card (
    id INTEGER PRIMARY KEY,

    card_code TEXT NOT NULL UNIQUE,
    card_name TEXT NOT NULL,

    importer_type TEXT NOT NULL,

    enabled INTEGER NOT NULL DEFAULT 1,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------
-- カード → 銀行口座紐付履歴
--------------------------------------------------

CREATE TABLE card_bank_account_assignment (
    id INTEGER PRIMARY KEY,

    card_id INTEGER NOT NULL,
    bank_account_id INTEGER NOT NULL,

    start_month TEXT NOT NULL,
    end_month TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (card_id)
        REFERENCES credit_card(id),

    FOREIGN KEY (bank_account_id)
        REFERENCES bank_account(id)
);

--------------------------------------------------
-- 銀行口座固定引落
--------------------------------------------------

CREATE TABLE bank_monthly_payment (
    id INTEGER PRIMARY KEY,

    bank_account_id INTEGER NOT NULL,

    payment_name TEXT NOT NULL,
    amount INTEGER NOT NULL,

    start_month TEXT NOT NULL,
    end_month TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bank_account_id)
        REFERENCES bank_account(id)
);

--------------------------------------------------
-- CSV取込履歴
--------------------------------------------------

CREATE TABLE import_file (
    id INTEGER PRIMARY KEY,

    card_id INTEGER NOT NULL,

    original_file_name TEXT NOT NULL,
    relative_path TEXT NOT NULL,

    file_hash TEXT NOT NULL UNIQUE,

    withdrawal_month TEXT,

    status TEXT NOT NULL,

    row_count INTEGER NOT NULL DEFAULT 0,
    imported_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,

    error_message TEXT,

    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (card_id)
        REFERENCES credit_card(id)
);

--------------------------------------------------
-- カード利用明細
--------------------------------------------------

CREATE TABLE card_usage (
    id INTEGER PRIMARY KEY,

    card_id INTEGER NOT NULL,
    import_file_id INTEGER NOT NULL,

    usage_date TEXT NOT NULL,

    withdrawal_month TEXT NOT NULL,

    merchant_name TEXT NOT NULL,

    amount INTEGER NOT NULL,

    description TEXT,

    original_row_number INTEGER NOT NULL,

    source_detail_id TEXT,

    detail_hash TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (card_id)
        REFERENCES credit_card(id),

    FOREIGN KEY (import_file_id)
        REFERENCES import_file(id)
);

--------------------------------------------------
-- インデックス
--------------------------------------------------

CREATE INDEX ix_card_usage_withdrawal_month
ON card_usage(withdrawal_month);

CREATE INDEX ix_card_usage_card_id
ON card_usage(card_id);

CREATE INDEX ix_card_bank_assignment_card_id
ON card_bank_account_assignment(card_id);

CREATE INDEX ix_bank_monthly_payment_account
ON bank_monthly_payment(bank_account_id);

--------------------------------------------------
-- 重複取込防止
--------------------------------------------------

CREATE UNIQUE INDEX ux_card_usage_detail
ON card_usage (
    card_id,
    withdrawal_month,
    detail_hash
);