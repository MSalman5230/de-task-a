# Feature Engineering Documentation for Credit Risk Modeling

## Overview

This document explains the features engineered for predicting customer credit risk, specifically whether a customer will default within 90 days. Each feature is designed to capture different aspects of customer financial behavior patterns that are predictive of default risk.

**Target Variable:** `defaulted_within_90d` (binary: 0 = no default, 1 = defaulted within 90 days)

---

## Feature Categories

The features are organized into three main categories:
1. **Transaction Volume and Amount Features** - Fundamental financial metrics
2. **Temporal Features** - Recency of income and income stability
3. **Behavioral Flags** - Spending patterns and financial commitments

---

## Feature 1-4: Basic Transaction Aggregations (Required Features)

> **NOTE:** Features 1-4 are required per the task specification. However, better alternatives exist that would provide more meaningful insights for credit risk prediction.

### Feature 1: Number of Transactions (`txn_count`)

**Why:** Higher transaction volume may indicate active account usage and financial engagement.

**Credit Risk Interpretation:**
- Customers with very few transactions may have inactive accounts or financial instability
- Moderate to high transaction counts suggest regular financial activity
- However, this feature alone doesn't tell the whole story

**Better Alternative: Transactions per Month**

Transactions per month would be more informative because:
- It normalizes for account age (a customer with 100 transactions over 1 year vs 10 years have very different activity levels)
- It captures transaction frequency patterns that are more predictive of financial stability
- It allows for seasonality analysis (e.g., higher spending during holidays, which is normal vs. consistently high spending which may indicate financial stress)
- Customers with consistent monthly transaction patterns are typically lower risk

---

### Feature 2: Total Debit (`total_debit`)

**Why:** Total debit represents total spending over the customer's transaction history.

**Credit Risk Interpretation:**
- Higher absolute debit amounts may indicate higher spending levels
- However, absolute values don't account for income scale differences
- Must be considered in context with total credit to assess financial health

**Limitations:**
- Absolute spending amounts are less informative without income context
- A $10,000 debit is very different for someone earning $2,000 vs $20,000 per month
- Better used in combination with total credit or as part of the debit-to-credit ratio

---

### Feature 3: Total Credit (`total_credit`)

**Why:** Total credit represents total income received over the customer's transaction history.

**Credit Risk Interpretation:**
- Higher credit amounts generally indicate higher income levels
- However, absolute values don't capture income stability or recent trends
- Must be considered in context with total debit to assess financial health

**Limitations:**
- Absolute income amounts are less informative without spending context
- Doesn't capture income recency or stability patterns
- Better used in combination with total debit or as part of the debit-to-credit ratio

---

### Feature 4: Average Transaction Amount (`avg_amount`)

**Why:** Captures typical transaction size, indicating spending patterns and financial capacity.

**Credit Risk Interpretation:**
- Extremely high or volatile average amounts may indicate financial stress or irregular income patterns
- However, average alone can be misleading due to outliers

**Better Alternative: Standard Deviation of Transaction Amounts**

Standard deviation of transaction amounts would be more informative because:
- Average can be skewed by outliers (e.g., one large salary payment inflates the average)
- Standard deviation captures transaction amount variability/volatility, which is a stronger predictor of financial instability
- High variability indicates irregular income/spending patterns (e.g., inconsistent salary payments, irregular large purchases), which correlates with higher default risk
- Low variability suggests consistent, predictable financial behavior (lower risk)
- Combined with average, std dev provides both scale and consistency measures

**Example:** A customer with avg $1000 but std dev of $500 (high variability) is riskier than one with avg $1000 and std dev of $50 (low variability)

---

## Feature 5: Debit to Credit Ratio (`debit_to_credit_ratio`)

**Why:** Normalized metric that measures spending relative to income, providing a key credit risk indicator.

**Formula:** `abs(total_debit) / total_credit`

**Credit Risk Interpretation:**
- Ratios > 1.0 indicate spending exceeds income (high risk)
- Ratios between 0.5 and 1.0 indicate moderate spending relative to income
- Ratios < 0.5 indicate healthy savings behavior (low risk)
- It's a normalized metric that accounts for income scale (a $1000 debit is different for someone earning $2000 vs $20,000 per month)
- More interpretable and comparable across customers with different income levels

**Why This Matters:**
- Directly measures spending relative to income, which is a key credit risk indicator
- More predictive than absolute debit or credit values alone
- Captures the fundamental financial health metric: can the customer afford their spending?

**Handling Edge Cases:**
- If `total_credit` is 0, the ratio is set to NaN (no income to compare against)
- Should be handled appropriately in modeling (imputation or separate missing indicator)

---

## Feature 6: Days Since Last Credit (`days_since_last_credit`)

**Why:** Measures how recently a customer received income (credit transactions).

**Credit Risk Interpretation:**
- Customers who haven't received income recently are at higher risk of default, especially given the 90-day default window
- This is critical for tree-based models and can be used to derive binary flags (e.g., `has_recent_salary`) for regression models
- **Rationale:** If a customer defaults within 90 days, lack of recent income is a key indicator

**Calculation:**
- Finds the most recent credit transaction for each customer
- Calculates days between the reference date (most recent transaction in dataset) and last credit date
- If no credit transactions exist, uses maximum possible days

**Model Usage:**
- Excellent for tree-based models (XGBoost, Random Forest) as it captures recency patterns
- Can be binarized for regression models (e.g., `has_recent_salary = days_since_last_credit < 30`)

---

## Feature 7: Income Stability Ratio (`income_stability_ratio`)

**Why:** Measures consistency of income by comparing recent income (last 30 days) to lifetime average monthly income.

**Formula:** `Total Credit (Last 30 Days) / Average Monthly Credit (Lifetime)`

**Credit Risk Interpretation:**
- A ratio < 1 indicates declining income, which is a strong predictor of default
- Stable or increasing income (ratio >= 1) suggests lower risk
- This captures income trends that simple averages miss

**Calculation Details:**
1. Calculate total credit received in the last 30 days
2. Calculate average monthly credit over the customer's lifetime (total credit / months active)
3. Divide recent credit by average monthly credit

**Interpretation:**
- Ratio > 1.0: Income is above average (positive signal)
- Ratio = 1.0: Income is stable (neutral to positive)
- Ratio < 1.0: Income is declining (negative signal, higher risk)
- Ratio = 0: No income in last 30 days (very high risk)

**Why This Matters:**
- Customers with declining income are more likely to default as their financial situation deteriorates
- This feature captures temporal trends that static features (like total credit) cannot

---

## Feature 8: Flag Consistent Salary (`flag_consistent_salary`)

**Why:** Identifies customers with regular, consistent income sources (payroll, salary, etc.).

**Logic:** Customer must have at least one salary-related transaction in 90% of months where they have credit transaction records.

**Keywords Detected:** `payroll`, `salary`, `dividend`, `dwp`, `payout`, `bonus`

**Credit Risk Interpretation:**
- Consistent salary indicates stable employment and predictable income, which significantly reduces default risk
- Irregular income patterns are associated with higher default rates
- Binary flag: 1 = consistent salary (90%+ of months), 0 = inconsistent or no salary pattern

**Calculation:**
1. Filter to only credit transactions (amount > 0) - salary/income only comes from credits
2. Identify salary-related transactions using keyword matching on credit transactions
3. Group credit transactions by customer and month
4. Calculate the ratio of months with salary transactions to total months with credit transactions
5. Flag as 1 if ratio >= 0.9, else 0

**Important:** Only credit transactions (incoming money) are considered, as salary/income should only be identified in money coming into the account, not outgoing transactions.

**Why This Matters:**
- Employment stability is a key predictor of creditworthiness
- Regular income allows customers to plan and manage expenses
- Irregular income (freelancers, gig workers) may have higher default risk despite similar total income

---

## Feature 9: Flag Risky Spend (`flag_risky_spend`)

**Why:** Identifies customers engaging in high-risk spending behaviors (gambling, crypto).

**Keywords Detected:** `bet`, `casino`, `crypto`, `gambling`

**Credit Risk Interpretation:**
- Risky spending patterns are strongly correlated with financial instability and poor financial decision-making
- Customers who gamble or invest heavily in volatile assets may have cash flow problems
- Binary flag: 1 = has risky spending transactions, 0 = no risky spending detected

**Why This Matters:**
- Gambling and speculative investments can lead to financial losses
- These behaviors may indicate poor financial judgment or addiction
- Customers with risky spending patterns are more likely to default due to:
  - Losses from gambling/crypto trading
  - Poor financial decision-making
  - Potential addiction-related financial stress

---

## Feature 10: Flag Rent/Mortgage (`flag_rent_mortgage`)

**Why:** Identifies customers with housing-related financial commitments.

**Keywords Detected:** `rent`, `mortgage`, `housing`, `council`

**Credit Risk Interpretation:**
- Customers paying rent/mortgage have fixed monthly obligations
- While this indicates responsibility, it also means less disposable income
- Combined with low income stability, housing payments can strain finances and increase default risk
- Binary flag: 1 = has housing-related transactions, 0 = no housing payments detected

**Why This Matters:**
- Housing is typically the largest monthly expense
- Fixed obligations reduce financial flexibility
- Customers with housing payments but declining income are at high risk
- However, responsible payment of housing costs can also indicate financial discipline (context-dependent)

**Risk Factors:**
- High housing costs relative to income
- Declining income with fixed housing obligations
- Multiple housing-related transactions (potential financial stress)

---

## Feature 11: Flag Subscription (`flag_subscription`)

**Why:** Identifies customers with recurring subscription payments.

**Keywords Detected:** `netflix`, `amazon prime`, `hulu`

**Credit Risk Interpretation:**
- Subscriptions represent recurring financial commitments
- While typically small amounts, multiple subscriptions can add up
- Customers with subscriptions but declining income may struggle to maintain these commitments, indicating financial stress
- Binary flag: 1 = has subscription transactions, 0 = no subscriptions detected

**Why This Matters:**
- Recurring commitments reduce disposable income
- Canceling subscriptions may indicate financial stress
- Multiple subscriptions can represent significant monthly expenses
- However, subscriptions can also indicate normal lifestyle spending (context-dependent)

**Risk Factors:**
- Multiple subscriptions combined with declining income
- High subscription costs relative to income
- Inability to cancel subscriptions despite financial stress

---

## Feature Summary Table

| Feature # | Feature Name | Type | Category |
|-----------|--------------|------|----------|
| 1 | `txn_count` | Numeric | Volume |
| 2 | `total_debit` | Numeric | Amount |
| 3 | `total_credit` | Numeric | Amount |
| 4 | `avg_amount` | Numeric | Amount |
| 5 | `debit_to_credit_ratio` | Numeric | Amount |
| 6 | `days_since_last_credit` | Numeric | Temporal |
| 7 | `income_stability_ratio` | Numeric | Temporal |
| 8 | `flag_consistent_salary` | Binary | Behavioral |
| 9 | `flag_risky_spend` | Binary | Behavioral |
| 10 | `flag_rent_mortgage` | Binary | Behavioral |
| 11 | `flag_subscription` | Binary | Behavioral |

---

## Feature Engineering Strategy

### Temporal Features (High Priority)
- **Days Since Last Credit** and **Income Stability Ratio** are critical because:
  - The target variable is "defaulted within 90 days" - recency matters
  - Income trends predict future financial stability
  - These features capture dynamic financial health

### Behavioral Flags (Medium-High Priority)
- **Flag Consistent Salary** is highly predictive of stable income
- **Flag Risky Spend** indicates poor financial decision-making
- Housing and subscription flags provide context but require combination with other features

### Required Features (Lower Priority)
- Basic aggregations (Features 1-4: txn_count, total_debit, total_credit, avg_amount) are required but less informative
- **Feature 5: Debit to Credit Ratio** derived from required features (total_debit, total_credit) is highly predictive

---

## Model Considerations

### Tree-Based Models (XGBoost, Random Forest)
- Variables like `days_since_last_credit` are kept in continuous form because tree-based models perform better with continuous variables
- All features work well, especially:
  - `days_since_last_credit` (excellent for splits)
  - `income_stability_ratio` (captures trends)
  - `debit_to_credit_ratio` (clear thresholds)

### Regression Models
- If required, continuous variables (e.g., `days_since_last_credit`) can be converted from continuous to binary or one-hot encoded for regression-based models
- May also benefit from:
  - Log transformations for skewed features
  - Interaction terms (e.g., `flag_rent_mortgage * income_stability_ratio`)


---

## Data Quality Considerations

- **Missing Values:** 
  - `income_stability_ratio` may be NaN if customer has no credit transactions
  - `debit_to_credit_ratio` may be NaN if customer has no credit transactions
  - Handle appropriately (imputation or separate missing indicator)

- **Outliers:**
  - `days_since_last_credit` may have extreme values for inactive accounts
  - `income_stability_ratio` may be very high for customers with recent bonuses
  - Consider capping or log transformations

- **Feature Scaling:**
  - Numeric features have different scales (consider standardization for some models)
  - Binary flags don't require scaling

---

## Conclusion

The feature set balances required features with more predictive alternatives. The temporal features (`days_since_last_credit`, `income_stability_ratio`) and behavioral flags (`flag_consistent_salary`, `flag_risky_spend`) are expected to be the most predictive for the 90-day default prediction task.
