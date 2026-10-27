"""
KKBox Churn RCA++ — Feature Engineering Sample

Selected excerpt from the private project.

Purpose
-------
Demonstrates point-in-time-safe transaction feature engineering using DuckDB.

The full project constructs one modelling row per subscriber × prediction
cohort and prevents post-cutoff information from entering predictive features.
"""

import duckdb


def build_transaction_features(
    transactions_path: str,
    labels_path: str,
    feature_cutoff: str,
):
    """
    Build subscriber-level transaction features using only information
    available on or before the prediction cutoff.
    """

    con = duckdb.connect()

    query = f"""
    WITH cohort AS (
        SELECT
            msno,
            is_churn
        FROM read_csv_auto('{labels_path}')
    ),

    transactions AS (
        SELECT
            msno,

            STRPTIME(
                CAST(transaction_date AS VARCHAR),
                '%Y%m%d'
            )::DATE AS transaction_date,

            payment_method_id,
            is_auto_renew,
            is_cancel

        FROM read_csv_auto('{transactions_path}')

        WHERE STRPTIME(
            CAST(transaction_date AS VARCHAR),
            '%Y%m%d'
        )::DATE <= DATE '{feature_cutoff}'
    )

    SELECT
        c.msno,
        c.is_churn,

        -- Recency
        DATE_DIFF(
            'day',
            MAX(t.transaction_date),
            DATE '{feature_cutoff}'
        ) AS days_since_last_transaction,

        -- Frequency
        COUNT(t.transaction_date) FILTER (
            WHERE t.transaction_date
                >= DATE '{feature_cutoff}' - INTERVAL 29 DAY
        ) AS txn_count_30d,

        COUNT(t.transaction_date) FILTER (
            WHERE t.transaction_date
                >= DATE '{feature_cutoff}' - INTERVAL 89 DAY
        ) AS txn_count_90d,

        COUNT(t.transaction_date) FILTER (
            WHERE t.transaction_date
                >= DATE '{feature_cutoff}' - INTERVAL 179 DAY
        ) AS txn_count_180d,

        -- Cancellation behaviour
        SUM(
            CASE
                WHEN t.transaction_date
                        >= DATE '{feature_cutoff}' - INTERVAL 89 DAY
                 AND t.is_cancel = 1
                THEN 1
                ELSE 0
            END
        ) AS cancel_count_90d,

        -- Payment stability
        COUNT(DISTINCT t.payment_method_id) FILTER (
            WHERE t.transaction_date
                >= DATE '{feature_cutoff}' - INTERVAL 179 DAY
        ) AS payment_methods_180d,

        -- Auto-renew behaviour
        AVG(
            CAST(t.is_auto_renew AS DOUBLE)
        ) FILTER (
            WHERE t.transaction_date
                >= DATE '{feature_cutoff}' - INTERVAL 179 DAY
        ) AS auto_renew_share_180d

    FROM cohort c

    LEFT JOIN transactions t
        ON c.msno = t.msno

    GROUP BY
        c.msno,
        c.is_churn
    """

    return con.execute(query).df()


# Example:
#
# features = build_transaction_features(
#     transactions_path="data/raw/transactions.csv",
#     labels_path="data/raw/train.csv",
#     feature_cutoff="2017-01-31",
# )