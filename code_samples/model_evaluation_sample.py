"""
KKBox Churn RCA++ — Model Evaluation Sample

Selected excerpt from the private project.

Purpose
-------
Evaluate churn-risk ranking using metrics suited to an imbalanced
classification problem.

Headline metrics used in the project:
- ROC-AUC
- PR-AUC
- top-decile churn capture
- top-decile lift
"""

import numpy as np
import pandas as pd

from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
)


def top_decile_metrics(
    y_true,
    y_score,
    top_pct: float = 0.10,
):
    """
    Measure how effectively the model concentrates actual churners
    inside the highest-risk portion of the population.
    """

    results = pd.DataFrame(
        {
            "actual": np.asarray(y_true),
            "score": np.asarray(y_score),
        }
    ).sort_values(
        "score",
        ascending=False,
    )

    top_n = int(len(results) * top_pct)

    top_group = results.iloc[:top_n]

    total_churners = results["actual"].sum()
    captured_churners = top_group["actual"].sum()

    capture_rate = (
        captured_churners / total_churners
    )

    overall_churn_rate = (
        results["actual"].mean()
    )

    top_group_churn_rate = (
        top_group["actual"].mean()
    )

    lift = (
        top_group_churn_rate /
        overall_churn_rate
    )

    return {
        "population_targeted_pct": top_pct,
        "subscribers_targeted": top_n,
        "churners_captured": int(captured_churners),
        "capture_rate": capture_rate,
        "lift": lift,
    }


def evaluate_churn_model(
    y_true,
    predicted_probability,
):
    """
    Return ranking metrics for a churn model.
    """

    return {
        "roc_auc": roc_auc_score(
            y_true,
            predicted_probability,
        ),
        "pr_auc": average_precision_score(
            y_true,
            predicted_probability,
        ),
        **top_decile_metrics(
            y_true,
            predicted_probability,
        ),
    }


# Final project result on out-of-time holdout:
#
# ROC-AUC:          0.8711
# PR-AUC:           0.5914
# Top-10% capture:  60.34%
# Top-10% lift:     6.03x