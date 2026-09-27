BEGIN TRANSACTION;

--------------------------------------------------
-- 銀行口座
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
-- クレジットカード
--------------------------------------------------

-- 1日開始、翌月引落の例
INSERT INTO credit_card (
    card_code,
    card_name,
    statement_start_day,
    withdrawal_month_offset
)
VALUES (
    'rakuten',
    '楽天カード',
    1,
    1
)
ON CONFLICT (card_code)
DO UPDATE SET
    card_name = excluded.card_name,
    statement_start_day
        = excluded.statement_start_day,
    withdrawal_month_offset
        = excluded.withdrawal_month_offset;

-- 16日開始、開始月から2か月後に引き落とす例
INSERT INTO credit_card (
    card_code,
    card_name,
    statement_start_day,
    withdrawal_month_offset
)
VALUES (
    'smbc',
    '三井住友カード',
    16,
    2
)
ON CONFLICT (card_code)
DO UPDATE SET
    card_name = excluded.card_name,
    statement_start_day
        = excluded.statement_start_day,
    withdrawal_month_offset
        = excluded.withdrawal_month_offset;

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
        WHERE card_code = 'rakuten'
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
    bank_account_id
        = excluded.bank_account_id,
    end_month
        = excluded.end_month;

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
    bank_account_id
        = excluded.bank_account_id,
    end_month
        = excluded.end_month;

--------------------------------------------------
-- 銀行口座の固定引落
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
-- 月マスタ
--------------------------------------------------

WITH RECURSIVE months(month) AS (
    SELECT '2026-01'

    UNION ALL

    SELECT strftime(
        '%Y-%m',
        date(
            month || '-01',
            '+1 month'
        )
    )
    FROM months
    WHERE month < '2030-12'
)
INSERT OR IGNORE INTO calendar_month (
    month
)
SELECT month
FROM months;

COMMIT;