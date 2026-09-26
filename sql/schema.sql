BEGIN TRANSACTION;

--------------------------------------------------
-- 銀行口座マスタ
--------------------------------------------------

CREATE TABLE IF NOT EXISTS bank_account (
    id INTEGER PRIMARY KEY,

    account_code TEXT NOT NULL UNIQUE,
    account_name TEXT NOT NULL,

    display_order INTEGER NOT NULL DEFAULT 0,

    enabled INTEGER NOT NULL DEFAULT 1
        CHECK (enabled IN (0, 1)),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------
-- クレジットカードマスタ
--------------------------------------------------

CREATE TABLE IF NOT EXISTS credit_card (
    id INTEGER PRIMARY KEY,

    card_code TEXT NOT NULL UNIQUE,
    card_name TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------
-- カード・銀行口座紐付け履歴
--------------------------------------------------

CREATE TABLE IF NOT EXISTS card_bank_account_assignment (
    id INTEGER PRIMARY KEY,

    card_id INTEGER NOT NULL,
    bank_account_id INTEGER NOT NULL,

    start_month TEXT NOT NULL
        CHECK (
            length(start_month) = 7
            AND start_month GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'
            AND substr(start_month, 6, 2) BETWEEN '01' AND '12'
        ),

    end_month TEXT
        CHECK (
            end_month IS NULL
            OR (
                length(end_month) = 7
                AND end_month GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'
                AND substr(end_month, 6, 2) BETWEEN '01' AND '12'
                AND end_month >= start_month
            )
        ),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (card_id)
        REFERENCES credit_card(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (bank_account_id)
        REFERENCES bank_account(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

--------------------------------------------------
-- 銀行口座の月次引落設定
--------------------------------------------------

CREATE TABLE IF NOT EXISTS bank_monthly_payment (
    id INTEGER PRIMARY KEY,

    bank_account_id INTEGER NOT NULL,

    payment_name TEXT NOT NULL,
    amount INTEGER NOT NULL
        CHECK (amount >= 0),

    start_month TEXT NOT NULL
        CHECK (
            length(start_month) = 7
            AND start_month GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'
            AND substr(start_month, 6, 2) BETWEEN '01' AND '12'
        ),

    end_month TEXT
        CHECK (
            end_month IS NULL
            OR (
                length(end_month) = 7
                AND end_month GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'
                AND substr(end_month, 6, 2) BETWEEN '01' AND '12'
                AND end_month >= start_month
            )
        ),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bank_account_id)
        REFERENCES bank_account(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

--------------------------------------------------
-- CSV取込履歴
--------------------------------------------------

CREATE TABLE IF NOT EXISTS import_file (
    id INTEGER PRIMARY KEY,

    card_id INTEGER NOT NULL,

    original_file_name TEXT NOT NULL,
    relative_path TEXT NOT NULL,

    file_hash TEXT NOT NULL UNIQUE,

    withdrawal_month TEXT
        CHECK (
            withdrawal_month IS NULL
            OR (
                length(withdrawal_month) = 7
                AND withdrawal_month GLOB
                    '[0-9][0-9][0-9][0-9]-[0-9][0-9]'
                AND substr(withdrawal_month, 6, 2)
                    BETWEEN '01' AND '12'
            )
        ),

    status TEXT NOT NULL
        CHECK (
            status IN (
                'processing',
                'success',
                'failed'
            )
        ),

    row_count INTEGER NOT NULL DEFAULT 0
        CHECK (row_count >= 0),

    imported_count INTEGER NOT NULL DEFAULT 0
        CHECK (imported_count >= 0),

    skipped_count INTEGER NOT NULL DEFAULT 0
        CHECK (skipped_count >= 0),

    error_message TEXT,

    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (card_id)
        REFERENCES credit_card(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

--------------------------------------------------
-- カード利用明細
--------------------------------------------------

CREATE TABLE IF NOT EXISTS card_usage (
    id INTEGER PRIMARY KEY,

    card_id INTEGER NOT NULL,
    import_file_id INTEGER NOT NULL,

    usage_date TEXT NOT NULL
        CHECK (
            length(usage_date) = 10
            AND usage_date GLOB
                '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        ),

    withdrawal_month TEXT NOT NULL
        CHECK (
            length(withdrawal_month) = 7
            AND withdrawal_month GLOB
                '[0-9][0-9][0-9][0-9]-[0-9][0-9]'
            AND substr(withdrawal_month, 6, 2)
                BETWEEN '01' AND '12'
        ),

    merchant_name TEXT NOT NULL,

    -- 返金・取消は負数で保持するため、負数を許可する
    amount INTEGER NOT NULL,

    description TEXT,

    original_row_number INTEGER NOT NULL
        CHECK (original_row_number > 0),

    source_detail_id TEXT,

    detail_hash TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (card_id)
        REFERENCES credit_card(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (import_file_id)
        REFERENCES import_file(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

--------------------------------------------------
-- 一意制約
--------------------------------------------------

-- 同一カードの同じ開始月に、
-- 複数の引落口座が設定されるのを防ぐ
CREATE UNIQUE INDEX IF NOT EXISTS
    ux_card_bank_account_assignment_start
ON card_bank_account_assignment (
    card_id,
    start_month
);

-- 同じ口座・項目・開始月の重複設定を防ぐ
CREATE UNIQUE INDEX IF NOT EXISTS
    ux_bank_monthly_payment_start
ON bank_monthly_payment (
    bank_account_id,
    payment_name,
    start_month
);

-- 同一明細の重複取込を防ぐ
CREATE UNIQUE INDEX IF NOT EXISTS
    ux_card_usage_detail
ON card_usage (
    card_id,
    withdrawal_month,
    detail_hash
);

--------------------------------------------------
-- 検索用インデックス
--------------------------------------------------

CREATE INDEX IF NOT EXISTS
    ix_card_usage_withdrawal_month
ON card_usage (
    withdrawal_month
);

CREATE INDEX IF NOT EXISTS
    ix_card_usage_card_id
ON card_usage (
    card_id
);

CREATE INDEX IF NOT EXISTS
    ix_card_usage_import_file_id
ON card_usage (
    import_file_id
);

CREATE INDEX IF NOT EXISTS
    ix_card_bank_account_assignment_card_id
ON card_bank_account_assignment (
    card_id
);

CREATE INDEX IF NOT EXISTS
    ix_card_bank_account_assignment_bank_account_id
ON card_bank_account_assignment (
    bank_account_id
);

CREATE INDEX IF NOT EXISTS
    ix_bank_monthly_payment_bank_account_id
ON bank_monthly_payment (
    bank_account_id
);

CREATE INDEX IF NOT EXISTS
    ix_import_file_card_id
ON import_file (
    card_id
);

CREATE INDEX IF NOT EXISTS
    ix_import_file_withdrawal_month
ON import_file (
    withdrawal_month
);

--------------------------------------------------
-- updated_at自動更新トリガー
--------------------------------------------------

CREATE TRIGGER IF NOT EXISTS
    trg_bank_account_updated_at
AFTER UPDATE ON bank_account
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE bank_account
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS
    trg_credit_card_updated_at
AFTER UPDATE ON credit_card
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE credit_card
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

--------------------------------------------------
-- 月マスタ
--------------------------------------------------

CREATE TABLE IF NOT EXISTS calendar_month (
    month TEXT PRIMARY KEY
        CHECK (
            length(month) = 7
            AND month GLOB
                '[0-9][0-9][0-9][0-9]-[0-9][0-9]'
            AND substr(month, 6, 2)
                BETWEEN '01' AND '12'
        )
);

COMMIT;