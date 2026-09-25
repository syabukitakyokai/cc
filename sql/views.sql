--------------------------------------------------
-- カード別月次集計
--------------------------------------------------

DROP VIEW IF EXISTS v_monthly_card_usage;

CREATE VIEW v_monthly_card_usage AS
SELECT
    cu.withdrawal_month,

    cc.id AS card_id,
    cc.card_code,
    cc.card_name,

    COUNT(*) AS detail_count,

    SUM(cu.amount) AS amount

FROM card_usage cu

INNER JOIN credit_card cc
    ON cc.id = cu.card_id

GROUP BY
    cu.withdrawal_month,
    cc.id,
    cc.card_code,
    cc.card_name;

--------------------------------------------------
-- カード利用額を銀行口座へ集約
--------------------------------------------------

DROP VIEW IF EXISTS v_monthly_bank_card_usage;

CREATE VIEW v_monthly_bank_card_usage AS
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

GROUP BY
    cm.month,
    ba.id,
    ba.account_code,
    ba.account_name;

--------------------------------------------------
-- 銀行口座別固定引落額
--------------------------------------------------

DROP VIEW IF EXISTS v_monthly_bank_fixed_payment;

CREATE VIEW v_monthly_bank_fixed_payment AS
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

GROUP BY
    cm.month,
    ba.id;

--------------------------------------------------
-- 最終集計
--------------------------------------------------

DROP VIEW IF EXISTS v_monthly_bank_summary;

CREATE VIEW v_monthly_bank_summary AS
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
    ON fixed.withdrawal_month = card.withdrawal_month
    AND fixed.bank_account_id = card.bank_account_id;

--------------------------------------------------
-- 銀行口座別内訳
--------------------------------------------------

DROP VIEW IF EXISTS v_monthly_bank_detail;

CREATE VIEW v_monthly_bank_detail AS

--------------------------------------------------
-- カード利用額
--------------------------------------------------

SELECT
    usage.withdrawal_month,

    ba.id AS bank_account_id,
    ba.account_code,
    ba.account_name,

    'CARD' AS item_type,

    cc.card_code AS item_code,
    cc.card_name AS item_name,

    usage.amount

FROM v_monthly_card_usage usage

INNER JOIN card_bank_account_assignment assignment
    ON assignment.card_id = usage.card_id
    AND assignment.start_month <= usage.withdrawal_month
    AND (
        assignment.end_month IS NULL
        OR usage.withdrawal_month <= assignment.end_month
    )

INNER JOIN credit_card cc
    ON cc.id = usage.card_id

INNER JOIN bank_account ba
    ON ba.id = assignment.bank_account_id

UNION ALL

--------------------------------------------------
-- 固定引落
--------------------------------------------------

SELECT
    cm.month AS withdrawal_month,

    ba.id AS bank_account_id,
    ba.account_code,
    ba.account_name,

    'PAYMENT' AS item_type,

    payment.id AS item_code,
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
    ON ba.id = payment.bank_account_id;
    