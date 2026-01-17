"""
Data Preparation Script for Credit Risk Modeling

This script prepares transaction data for credit risk prediction by engineering
features that capture customer financial behavior patterns. The target variable
is whether a customer defaults within 90 days.

Feature Engineering Strategy:
- Transaction volume and amount features (fundamental financial metrics)
- Temporal features (recency of income, income stability)
- Behavioral flags (spending patterns, financial commitments)
"""

from pathlib import Path
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)


def clean_text(s: str) -> str:
    """Clean and normalize text descriptions for keyword matching."""
    s = s.lower()
    s = re.sub(r"[^a-z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


if __name__ == "__main__":
    # Load data
    tx = pd.read_csv(DATA_DIR / "transactions.csv", parse_dates=["txn_timestamp"])
    labels = pd.read_csv(DATA_DIR / "labels.csv")

    # Clean description text for keyword matching
    tx["clean_desc"] = tx["description"].fillna("").apply(clean_text)

    # Get reference date (most recent transaction date) for temporal calculations
    reference_date = tx["txn_timestamp"].max()

    # ============================================================================
    # FEATURE 1-3: Basic Transaction Aggregations (Required Features as per task specification)
    # ============================================================================
    # NOTE: These features are required per the task specification. However, better alternatives
    # exist that would provide more meaningful insights for credit risk prediction.

    # Feature 1: Number of transactions (txn_count) - REQUIRED
    # Why: Higher transaction volume may indicate active account usage and financial engagement.
    # Credit Risk: Customers with very few transactions may have inactive accounts or financial
    # instability. Moderate to high transaction counts suggest regular financial activity.
    #
    # BETTER ALTERNATIVE: Transactions per month would be more informative because:
    # - It normalizes for account age (a customer with 100 transactions over 1 year vs 10 years
    #   have very different activity levels)
    # - It captures transaction frequency patterns that are more predictive of financial stability
    # - It allows for seasonality analysis (e.g., higher spending during holidays, which is normal
    #   vs. consistently high spending which may indicate financial stress)
    # - Customers with consistent monthly transaction patterns are typically lower risk

    # Feature 2: Total debit and total credit - REQUIRED
    # Why: Total debit represents total spending, while total credit represents total income.
    # Credit Risk: High debit-to-credit ratios indicate overspending. Negative net cash flow
    # (debits > credits) is a strong predictor of default risk.
    #
    # BETTER ALTERNATIVE: debit_to_credit_ratio (included below) is more predictive because:
    # - It's a normalized metric that accounts for income scale (a $1000 debit is different for
    #   someone earning $2000 vs $20,000 per month)
    # - It directly measures spending relative to income, which is a key credit risk indicator
    # - Ratios > 1.0 indicate spending exceeds income (high risk), while ratios < 0.5 indicate
    #   healthy savings behavior (low risk)
    # - It's more interpretable and comparable across customers with different income levels

    # Feature 3: Average transaction amount (avg_amount) - REQUIRED
    # Why: Captures typical transaction size, indicating spending patterns and financial capacity.
    # Credit Risk: Extremely high or volatile average amounts may indicate financial stress
    # or irregular income patterns.
    #
    # BETTER ALTERNATIVE: Standard deviation of transaction amounts would be more informative because:
    # - Average can be skewed by outliers (e.g., one large salary payment inflates the average)
    # - Standard deviation captures transaction amount variability/volatility, which is a stronger
    #   predictor of financial instability
    # - High variability indicates irregular income/spending patterns (e.g., inconsistent salary
    #   payments, irregular large purchases), which correlates with higher default risk
    # - Low variability suggests consistent, predictable financial behavior (lower risk)
    # - Combined with average, std dev provides both scale and consistency measures
    # However, average alone doesn't tell the whole story - a customer with avg $1000 but std dev
    # of $500 (high variability) is riskier than one with avg $1000 and std dev of $50 (low variability)

    agg = (
        tx.groupby("customer_id")
        .agg(
            txn_count=("transaction_id", "count"),
            total_debit=("amount", lambda x: x[x < 0].sum()),
            total_credit=("amount", lambda x: x[x > 0].sum()),
            avg_amount=("amount", "mean"),
        )
        .reset_index()
    )

    # Calculate debit to credit ratio
    agg["debit_to_credit_ratio"] = np.where(agg["total_credit"] > 0, abs(agg["total_debit"]) / agg["total_credit"], np.nan)

    # ============================================================================
    # FEATURE 4: Days Since Last Credit (Recency Feature)
    # ============================================================================

    # Why: Measures how recently a customer received income (credit transactions).
    # Credit Risk: Customers who haven't received income recently are at higher risk of default,
    # especially given the 90-day default window. This is critical for tree-based models and
    # can be used to derive binary flags (e.g., has_recent_salary) for regression models.
    # Rationale: If a customer defaults within 90 days, lack of recent income is a key indicator.

    last_credit_dates = tx[tx["amount"] > 0].groupby("customer_id")["txn_timestamp"].max().reset_index().rename(columns={"txn_timestamp": "last_credit_date"})

    agg = agg.merge(last_credit_dates, on="customer_id", how="left")
    agg["days_since_last_credit"] = (reference_date - agg["last_credit_date"]).dt.days
    agg["days_since_last_credit"] = agg["days_since_last_credit"].fillna((reference_date - tx["txn_timestamp"].min()).days + 1)  # If no credit, use max days
    agg = agg.drop(columns=["last_credit_date"])

    # ============================================================================
    # FEATURE 5: Income Stability Ratio
    # ============================================================================

    # Why: Measures consistency of income by comparing recent income (last 30 days) to
    # lifetime average monthly income.
    # Formula: Total Credit (Last 30 Days) / Average Monthly Credit (Lifetime)
    # Credit Risk: A ratio < 1 indicates declining income, which is a strong predictor of
    # default. Stable or increasing income (ratio >= 1) suggests lower risk. This captures
    # income trends that simple averages miss.

    # Calculate total credit in last 30 days
    thirty_days_ago = reference_date - timedelta(days=30)
    recent_credits = (
        tx[(tx["amount"] > 0) & (tx["txn_timestamp"] >= thirty_days_ago)]
        .groupby("customer_id")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "credit_last_30d"})
    )

    # Calculate average monthly credit (lifetime)
    # Get date range for each customer
    customer_date_ranges = tx.groupby("customer_id")["txn_timestamp"].agg(["min", "max"]).reset_index()
    customer_date_ranges["days_active"] = (customer_date_ranges["max"] - customer_date_ranges["min"]).dt.days + 1
    customer_date_ranges["months_active"] = customer_date_ranges["days_active"] / 30.0
    customer_date_ranges["months_active"] = customer_date_ranges["months_active"].clip(lower=1.0)

    # Calculate average monthly credit
    customer_date_ranges = customer_date_ranges.merge(agg[["customer_id", "total_credit"]], on="customer_id")
    customer_date_ranges["avg_monthly_credit"] = customer_date_ranges["total_credit"] / customer_date_ranges["months_active"]

    # Merge and calculate income stability ratio
    agg = agg.merge(recent_credits[["customer_id", "credit_last_30d"]], on="customer_id", how="left")
    agg = agg.merge(
        customer_date_ranges[["customer_id", "avg_monthly_credit"]],
        on="customer_id",
        how="left",
    )
    agg["credit_last_30d"] = agg["credit_last_30d"].fillna(0)
    agg["income_stability_ratio"] = np.where(agg["avg_monthly_credit"] > 0, agg["credit_last_30d"] / agg["avg_monthly_credit"], np.nan)

    # ============================================================================
    # FEATURE 6: Flag Consistent Salary
    # ============================================================================

    # Why: Identifies customers with regular, consistent income sources (payroll, salary, etc.).
    # Logic: Customer must have at least one salary-related transaction in 90% of months
    # where they have transaction records.
    # Credit Risk: Consistent salary indicates stable employment and predictable income,
    # which significantly reduces default risk. Irregular income patterns are associated
    # with higher default rates.

    salary_keywords = ["payroll", "salary", "dividend", "dwp", "payout", "bonus"]
    salary_pattern = "|".join([rf"\b{kw}\b" for kw in salary_keywords])

    # Identify salary transactions
    tx["is_salary"] = tx["clean_desc"].str.contains(salary_pattern, case=False, na=False).astype(int)

    # Group by customer and month
    tx["year_month"] = tx["txn_timestamp"].dt.to_period("M")
    monthly_salary = tx.groupby(["customer_id", "year_month"]).agg(has_salary=("is_salary", "max")).reset_index()

    # Calculate salary consistency
    salary_consistency = (
        monthly_salary.groupby("customer_id").agg(months_with_transactions=("year_month", "count"), months_with_salary=("has_salary", "sum")).reset_index()
    )
    salary_consistency["salary_consistency_ratio"] = salary_consistency["months_with_salary"] / salary_consistency["months_with_transactions"]
    salary_consistency["flag_consistent_salary"] = (salary_consistency["salary_consistency_ratio"] >= 0.9).astype(int)

    agg = agg.merge(
        salary_consistency[["customer_id", "flag_consistent_salary"]],
        on="customer_id",
        how="left",
    )
    agg["flag_consistent_salary"] = agg["flag_consistent_salary"].fillna(0).astype(int)

    # ============================================================================
    # FEATURE 7: Flag Risky Spend
    # ============================================================================

    # Why: Identifies customers engaging in high-risk spending behaviors (gambling, crypto).
    # Credit Risk: Risky spending patterns are strongly correlated with financial instability
    # and poor financial decision-making, leading to higher default rates. Customers who
    # gamble or invest heavily in volatile assets may have cash flow problems.

    risky_keywords = ["bet", "casino", "crypto", "gambling"]
    risky_pattern = "|".join([rf"\b{kw}\b" for kw in risky_keywords])

    risky_transactions = (
        tx[tx["clean_desc"].str.contains(risky_pattern, case=False, na=False)]
        .groupby("customer_id")["transaction_id"]
        .count()
        .reset_index()
        .rename(columns={"transaction_id": "risky_txn_count"})
    )

    agg = agg.merge(risky_transactions, on="customer_id", how="left")
    agg["flag_risky_spend"] = (agg["risky_txn_count"] > 0).astype(int)
    agg = agg.drop(columns=["risky_txn_count"])

    # ============================================================================
    # FEATURE 8: Flag Rent/Mortgage
    # ============================================================================

    # Why: Identifies customers with housing-related financial commitments.
    # Credit Risk: Customers paying rent/mortgage have fixed monthly obligations. While
    # this indicates responsibility, it also means less disposable income. Combined with
    # low income stability, housing payments can strain finances and increase default risk.

    housing_keywords = ["rent", "mortgage", "housing", "council"]
    housing_pattern = "|".join([rf"\b{kw}\b" for kw in housing_keywords])

    housing_transactions = (
        tx[tx["clean_desc"].str.contains(housing_pattern, case=False, na=False)]
        .groupby("customer_id")["transaction_id"]
        .count()
        .reset_index()
        .rename(columns={"transaction_id": "housing_txn_count"})
    )

    agg = agg.merge(housing_transactions, on="customer_id", how="left")
    agg["flag_rent_mortgage"] = (agg["housing_txn_count"] > 0).astype(int)
    agg = agg.drop(columns=["housing_txn_count"])

    # ============================================================================
    # FEATURE 9: Flag Subscription
    # ============================================================================

    # Why: Identifies customers with recurring subscription payments.
    # Credit Risk: Subscriptions represent recurring financial commitments. While typically
    # small amounts, multiple subscriptions can add up. Customers with subscriptions but
    # declining income may struggle to maintain these commitments, indicating financial stress.

    subscription_keywords = ["netflix", "amazon prime", "hulu"]
    subscription_pattern = "|".join([rf"\b{kw.replace(' ', r'\s+')}\b" for kw in subscription_keywords])

    subscription_transactions = (
        tx[tx["clean_desc"].str.contains(subscription_pattern, case=False, na=False)]
        .groupby("customer_id")["transaction_id"]
        .count()
        .reset_index()
        .rename(columns={"transaction_id": "subscription_txn_count"})
    )

    agg = agg.merge(subscription_transactions, on="customer_id", how="left")
    agg["flag_subscription"] = (agg["subscription_txn_count"] > 0).astype(int)
    agg = agg.drop(columns=["subscription_txn_count"])

    # ============================================================================
    # Merge with Labels and Save
    # ============================================================================

    # Merge with labels
    df = agg.merge(labels, on="customer_id", how="left")

    # Select final feature columns (remove intermediate calculation columns)
    feature_columns = [
        "customer_id",
        "txn_count",
        "total_debit",
        "total_credit",
        "avg_amount",
        "debit_to_credit_ratio",
        "days_since_last_credit",
        "income_stability_ratio",
        "flag_consistent_salary",
        "flag_risky_spend",
        "flag_rent_mortgage",
        "flag_subscription",
        "defaulted_within_90d",
    ]

    df = df[feature_columns]

    # Save to CSV
    df.to_csv(ARTIFACTS_DIR / "training_set.csv", index=False)
    print(f"✅ Successfully wrote {ARTIFACTS_DIR / 'training_set.csv'}")
    print(f"   Shape: {df.shape}")
    print(f"   Features: {len(feature_columns) - 2} (excluding customer_id and target)")
    print(f"   Target variable: defaulted_within_90d")
