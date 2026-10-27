# KKBox Churn RCA++ — Project Summary

## Overview

This project explores customer churn from two complementary angles:

1. **Root Cause Analysis** — identifying what changed during major churn deterioration periods
2. **Predictive Modelling** — identifying which subscribers are most likely to churn next

The objective was to move beyond simply reporting a churn rate or building a prediction model in isolation.

The full workflow was designed around the business decision process:

**Detect → Localize → Diagnose → Size → Recommend → Predict → Explain**

---

## Business Challenge

A churn spike tells the business that retention performance has worsened, but it does not explain:

- which customer or subscription states are involved
- whether the issue is concentrated in a specific payment or plan population
- whether churn increased because a risky population became larger
- whether an existing population suddenly became more likely to churn
- how much of the deterioration can be associated with a particular driver
- which subscribers should be prioritised for retention activity

The project therefore separates diagnosis from prediction.

The RCA asks:

> **What changed at population level?**

The predictive model asks:

> **Who appears most likely to churn next?**

---

# Part 1 — Historical Root Cause Analysis

## Data Foundation

The analysis began with a data audit covering member, label, and transaction files.

Key data-quality considerations included:

- multiple valid transaction rows for the same subscriber and day
- substantial missing member information
- invalid raw age values
- unusual expiry-date states
- differences between distributed transaction files
- class imbalance in the official churn labels

Raw source data was preserved unchanged, with analytical rules documented in a data contract and decision log.

---

## Churn Reconstruction

The official KKBox churn-labelling implementation was reviewed to understand transaction sequencing and renewal-gap logic.

A historical churn reconstruction was then developed using the available transaction data.

The reconstructed February 2017 labels achieved approximately:

- **98.77% agreement** with comparable official labels
- **99.41% churn precision**
- **73.23% churn recall**

The remaining mismatches were concentrated in cases that could not be reproduced from the distributed transaction snapshot.

Because of this, reconstructed churn labels were used for historical analysis, while official labels were retained for predictive modelling.

---

## Detecting Priority Churn Events

Monthly churn episodes were reconstructed from February 2015 through February 2017.

Three deterioration periods were selected for deeper RCA:

| Event | Churn Rate |
|---|---:|
| April 2015 | **19.27%** |
| September 2015 | **10.16%** |
| November 2016 | **8.67%** |

These events represented different types of churn deterioration.

---

## April 2015 — New Subscription-State Anomaly

April showed the most extreme churn spike.

A new family of zero-day and above-list transaction states appeared suddenly at scale.

The primary driver population accounted for approximately:

- **72.6K additional churn episodes**
- **94.7% of the overall increase in churners**

The same subscription state remained present afterward, but its churn rate dropped sharply.

This suggests that the state itself was not permanently equivalent to churn.

The pattern instead points toward a period-specific operational or subscription-state issue that would warrant investigation into areas such as billing, migration, or transaction processing.

---

## September 2015 — Renewal Risk Deterioration

September represented a different mechanism.

The PM41 + 8–30 day population already existed at scale before the event.

Its churn rate increased from approximately:

**4.88% → 12.56%**

The primary driver accounted for:

- **23.3K additional churn episodes**
- **90.9% of the overall increase**

This indicates deterioration within an established renewal/payment population rather than the appearance of a new customer state.

The operational response would therefore focus more on payment authorisation, retry behaviour, renewal failure, and recovery processes.

---

## November 2016 — High-Risk State Expansion

November represented another distinct mechanism.

A PM35 + short-plan + zero-paid state had already demonstrated very high churn risk historically.

The November spike occurred because approximately **52K subscription episodes** entered this state, with a churn rate of approximately **95.8%**.

This was therefore primarily a population-expansion problem.

The key business question becomes:

> Why were so many subscribers entering an already high-risk subscription state?

---

# Opportunity Sizing

Historical scenario sizing was used to estimate the scale of potential mitigation.

| Mitigation Scenario | Potential Churn Episodes Avoided |
|---|---:|
| 10% | ~14.6K |
| 25% | ~36.5K |
| 50% | ~72.9K |

These scenarios illustrate historical opportunity only.

They are not forecasts or guaranteed retention outcomes.

---

# Executive Dashboard

A three-page Looker Studio dashboard was created to translate the RCA into an executive decision flow.

### Page 1 — Executive Overview

Focus:

> What happened and how large was the deterioration?

### Page 2 — Root Cause Analysis

Focus:

> What drove each churn event?

### Page 3 — Actions & Opportunity

Focus:

> What should be investigated and where is the potential opportunity?

The monitoring framework follows:

**Detect → Localize → Diagnose → Act → Monitor**

---

# Part 2 — Predictive Churn Modelling

## Prediction Design

The predictive extension estimates subscriber-level churn risk using information available before each prediction period.

A point-in-time-safe design was used.

### Development cohort

- February 2017 churn cohort
- feature cutoff: **31 January 2017**
- churn rate: **6.39%**

### Out-of-time holdout

- March 2017 churn cohort
- feature cutoff: **28 February 2017**
- churn rate: **8.99%**

The later cohort was kept untouched during model selection.

---

## Feature Engineering

One modelling row was created per subscriber × prediction cohort.

Feature families included:

- transaction recency
- transaction frequency over 30 / 90 / 180-day windows
- cancellation behaviour
- auto-renew behaviour
- payment-method stability
- latest payment and plan state
- pricing behaviour
- expiry timing
- subscriber tenure
- member attributes and missingness

Future transactions, post-cutoff renewal information, and reconstructed churn labels were excluded from the feature set.

---

# Model Development

Three modelling levels were compared:

| Model | ROC-AUC | PR-AUC | Top-10% Capture | Top-10% Lift |
|---|---:|---:|---:|---:|
| Dummy | 0.5000 | 0.0639 | 9.70% | 0.97× |
| Logistic Regression | 0.8558 | 0.4998 | 64.83% | 6.48× |
| **Gradient-Boosted Trees** | **0.8956** | **0.5627** | **67.61%** | **6.76×** |

The gradient-boosted tree model was selected for final out-of-time evaluation.

---

## Final Out-of-Time Performance

The selected model was retrained on the full development cohort and evaluated once on the later March cohort.

Final performance:

- **ROC-AUC:** 0.8711
- **PR-AUC:** 0.5914
- **Top-10% churn capture:** 60.34%
- **Top-10% lift:** 6.03×

A practical interpretation is:

> If retention capacity allowed the business to target only the highest-risk 10% of subscribers, the model would identify approximately 60% of actual churners in the later cohort.

The model therefore retained strong ranking capability despite a higher churn rate and temporal shift in the holdout period.

---

# Explainability and Robustness

Model-agnostic permutation SHAP was used to explain churn probabilities.

The explanation method was explicitly validated by confirming that:

> baseline probability + feature contributions = model prediction

The maximum reconstruction error was approximately **1.3 × 10⁻¹⁵**, effectively floating-point noise.

The strongest global predictive signals included:

- latest auto-renew status
- latest cancellation status
- transaction history
- payment method
- recent transaction activity
- transaction recency
- subscription and expiry state

A separate expiry-feature ablation test showed that removing the entire expiry feature family produced almost no change in validation performance.

This provided additional confidence that the model's performance was not dependent on one potentially fragile data-quality feature.

---

# Key Analytical Insight

The project showed that similar-looking churn spikes can be driven by very different mechanisms.

The three major RCA events represented:

- a **new abnormal subscription state**
- an **existing population becoming riskier**
- an **already high-risk state expanding**

Those distinctions matter because they imply different interventions.

The predictive model then complements the RCA by prioritising which individual subscribers appear most at risk.

Together:

**RCA supports diagnosis and intervention design.**

**Prediction supports prioritisation of retention effort.**

---

# What This Project Demonstrates

This case study demonstrates practical capability across:

- SQL-style analytics using DuckDB
- large-scale transaction-data processing
- data-quality assessment
- analytical decision design
- root-cause decomposition
- business-impact sizing
- executive dashboarding
- point-in-time-safe feature engineering
- imbalanced classification
- out-of-time validation
- model explainability
- translating technical analysis into business action

---

# Limitations

The analysis should be interpreted with several limitations in mind:

- reconstructed historical churn labels do not perfectly reproduce the original competition snapshot
- RCA findings identify historical associations rather than proven causal mechanisms
- member demographic information contains substantial missingness
- predictive performance may change as subscriber behaviour or operational processes evolve
- SHAP explains model behaviour rather than causality
- mitigation scenarios are illustrative historical sizing exercises, not forecasts

---

## Final Takeaway

The project moves beyond a single churn KPI or standalone machine-learning model.

It demonstrates a broader analytics workflow:

> **Detect the deterioration → isolate the mechanism → size the impact → recommend action → prioritise risk → explain the prediction**

That combination turns churn analytics from reporting into a decision-support process.