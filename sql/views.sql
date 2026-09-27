BEGIN TRANSACTION;

--------------------------------------------------
-- 利用明細への引落月付与
--------------------------------------------------

DROP VIEW IF EXISTS
    v_card_usage_with_withdrawal_month;

CREATE VIEW
    v_card_usage_with_withdrawal_month
AS
SELECT
    cu.id AS card_usage_id,

    cu.card_id,

    cc.card_code,
    cc.card_name,

    cu.import_file_id,
    cu.usage_date,

    cc.statement_start_day,
    cc.withdrawal_month_offset,

    strftime(
        '%Y-%m',
        date(
            cu.usage_date,
            'start of month',

            CASE
                WHEN CAST(
                    strftime(
                        '%d',
                        cu.usage_date
                    )
                    AS INTEGER
                ) >= cc.statement_start_day
                THEN '+0 months'
                ELSE '-1 month'
            END,

            printf(
                '+%d months',
                cc.withdrawal_month_offset
            )
        )
    ) AS withdrawal_month,

    cu.merchant_name,
    cu.amount,
    cu.description,
    cu.original_row_number,
    cu.source_detail_id,
    cu.detail_hash,
    cu.created_at

FROM card_usage cu

INNER JOIN credit_card cc
    ON cc.id = cu.card_id;

--------------------------------------------------
-- カード別月次集計
--------------------------------------------------

DROP VIEW IF EXISTS
    v_monthly_card_usage;

CREATE VIEW
    v_monthly_card_usage
AS
SELECT
    withdrawal_month,

    card_id,
    card_code,
    card_name,

    COUNT(*) AS detail_count,
    SUM(amount) AS amount

FROM v_card_usage_with_withdrawal_month

GROUP BY
    withdrawal_month,
    card_id,
    card_code,
    card_name;

--------------------------------------------------
-- 銀行口座別カード利用額
--------------------------------------------------

DROP VIEW IF EXISTS
    v_monthly_bank_card_usage;

CREATE VIEW
    v_monthly_bank_card_usage
AS
SELECT
    cm.month AS withdrawal_month,

    ba.id AS bank_account_id,
    ba.account_code,
    ba.account_name,

    COALESCE(
        SUM(card_usage.amount),
        0
    ) AS card_amount

FROM calendar_month cm

CROSS JOIN bank_account ba

LEFT JOIN card_bank_account_assignment assignment
    ON assignment.bank_account_id = ba.id
    AND assignment.start_month <= cm.month
    AND (
        assignment.end_month IS NULL
        OR cm.month <= assignment.end_month
    )

LEFT JOIN v_monthly_card_usage card_usage
    ON card_usage.card_id = assignment.card_id
    AND card_usage.withdrawal_month = cm.month

WHERE ba.enabled = 1

GROUP BY
    cm.month,
    ba.id,
    ba.account_code,
    ba.account_name;

--------------------------------------------------
-- 銀行口座別固定引落額
--------------------------------------------------

DROP VIEW IF EXISTS
    v_monthly_bank_fixed_payment;

CREATE VIEW
    v_monthly_bank_fixed_payment
AS
SELECT
    cm.month AS withdrawal_month,

    ba.id AS bank_account_id,

    COALESCE(
        SUM(payment.amount),
        0
    ) AS fixed_payment_amount

FROM calendar_month cm

CROSS JOIN bank_account ba

LEFT JOIN bank_monthly_payment payment
    ON payment.bank_account_id = ba.id
    AND payment.start_month <= cm.month
    AND (
        payment.end_month IS NULL
        OR cm.month <= payment.end_month
    )

WHERE ba.enabled = 1

GROUP BY
    cm.month,
    ba.id;

--------------------------------------------------
-- 銀行口座別月次集計
--------------------------------------------------

DROP VIEW IF EXISTS
    v_monthly_bank_summary;

CREATE VIEW
    v_monthly_bank_summary
AS
SELECT
    card.withdrawal_month,

    card.bank_account_id,
    card.account_code,
    card.account_name,

    card.card_amount,

    fixed.fixed_payment_amount,

    card.card_amount
        + fixed.fixed_payment_amount
        AS total_amount

FROM v_monthly_bank_card_usage card

INNER JOIN v_monthly_bank_fixed_payment fixed
    ON fixed.withdrawal_month
        = card.withdrawal_month
    AND fixed.bank_account_id
        = card.bank_account_id;

--------------------------------------------------
-- 銀行口座別月次内訳
--------------------------------------------------

DROP VIEW IF EXISTS
    v_monthly_bank_detail;

CREATE VIEW
    v_monthly_bank_detail
AS

SELECT
    usage.withdrawal_month,

    ba.id AS bank_account_id,
    ba.account_code,
    ba.account_name,

    'CARD' AS item_type,

    usage.card_code AS item_code,
    usage.card_name AS item_name,

    usage.amount

FROM v_monthly_card_usage usage

INNER JOIN card_bank_account_assignment assignment
    ON assignment.card_id = usage.card_id
    AND assignment.start_month
        <= usage.withdrawal_month
    AND (
        assignment.end_month IS NULL
        OR usage.withdrawal_month
            <= assignment.end_month
    )

INNER JOIN bank_account ba
    ON ba.id = assignment.bank_account_id

WHERE ba.enabled = 1

UNION ALL

SELECT
    cm.month AS withdrawal_month,

    ba.id AS bank_account_id,
    ba.account_code,
    ba.account_name,

    'PAYMENT' AS item_type,

    CAST(payment.id AS TEXT) AS item_code,
    payment.payment_name AS item_name,

    payment.amount

FROM calendar_month cm

INNER JOIN bank_monthly_payment payment
    ON payment.start_month <= cm.month
    AND (
        payment.end_month IS NULL
        OR cm.month <= payment.end_month
    )

INNER JOIN bank_account ba
    ON ba.id = payment.bank_account_id

WHERE ba.enabled = 1;

COMMIT;