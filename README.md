# Credit Risk Modeling - Data Engineering Task

A data engineering pipeline for predicting customer credit risk (90-day default prediction) using transaction data.

## Quick Start

1. **Prepare the data:**
   ```bash
   python data_prep/prepare_data.py
   ```
   This generates `artifacts/training_set.csv` with engineered features.

2. **Explore the data:**
   ```bash
   python explore_data.py
   ```

## Documentation

- **[Feature Documentation](feature_documentation.md)** - Detailed explanation of all engineered features, their rationale, and credit risk interpretation
- **[Data Preparation Script](data_prep/prepare_data.py)** - Implementation of feature engineering pipeline
- **[Null Data Handling Strategy](null_data_handling_strategy.md)** - Strategy for handling missing values in labels and transactions datasets

## Features

The pipeline engineers 11 features from transaction data:
- **Volume/Amount**: Transaction count, total debit/credit, average amount, debit-to-credit ratio
- **Temporal**: Days since last credit, income stability ratio
- **Behavioral Flags**: Consistent salary, risky spending, rent/mortgage, subscriptions

See [feature_documentation.md](feature_documentation.md) for complete details.

## Challenges & Reflections

**What part of the exercise did you find most challenging, and why?**

The most significant challenge was working with limited data—only 11 rows of transaction data spanning just 3 days of transaction timestamps. This constraint required making careful assumptions about data patterns and customer behavior, making it difficult to identify robust patterns suitable for production pipelines.

The sparse transaction history limited the ability to extract meaningful temporal patterns, seasonal trends, and behavioral signals. Particularly challenging was the description field—with more diverse and detailed transaction descriptions, we could extract richer insights into spending behavior (merchant categories, payment types, transaction purposes) that would significantly enhance credit risk prediction. The limited sample size meant that feature engineering decisions had to balance between capturing meaningful signals.

**What tradeoffs did you make? (e.g., speed vs. accuracy, simplicity vs. completeness)**

The tradeoffs varied by feature based on their importance for the 90-day default prediction task:

- **Flag Consistent Salary**: Prioritized **accuracy and completeness**. Since consistent income is critical for predicting default within 90 days, the feature requires salary transactions in at least 90% of months where the customer has transaction records. This rigorous threshold ensures we capture true income stability rather than occasional salary payments.

- **Flag Risky Spend**: Prioritized **speed and simplicity**. A single occurrence of gambling, betting, or crypto-related transactions flags a customer as risky. While a consistency-based approach (similar to salary) would be more accurate, the logical deduction is that even one instance of risky spending behavior indicates elevated risk—someone who gambles once is already showing signs of financial risk-taking behavior. This simpler approach balances detection speed with practical risk assessment.
