"""
KKBox Churn RCA++ — SHAP Validation Sample

Selected excerpt from the private project.

Purpose
-------
Validate that model-agnostic SHAP feature contributions reconstruct
the churn probability produced by the selected model.

This validation was added after an initial tree-specific SHAP
implementation produced inconsistent explanations.
"""

import numpy as np
import pandas as pd
import shap


def predict_probability(
    estimator,
    X,
):
    """
    Return positive-class churn probability.
    """
    return estimator.predict_proba(X)[:, 1]


def validate_shap_additivity(
    shap_values,
    model_probability,
):
    """
    Verify:

        baseline prediction
        + feature contributions
        ≈ model prediction
    """

    reconstructed_probability = (
        shap_values.base_values
        + shap_values.values.sum(axis=1)
    )

    check = pd.DataFrame(
        {
            "shap_reconstructed":
                reconstructed_probability,

            "model_probability":
                model_probability,
        }
    )

    check["absolute_difference"] = (
        check["shap_reconstructed"]
        - check["model_probability"]
    ).abs()

    return {
        "maximum_difference":
            check["absolute_difference"].max(),

        "average_difference":
            check["absolute_difference"].mean(),
    }


# Example model-agnostic explainer:
#
# explainer = shap.Explainer(
#     model_function,
#     background_data,
#     algorithm="permutation",
#     feature_names=feature_names,
# )
#
# shap_values = explainer(
#     explanation_data,
# )
#
# validation = validate_shap_additivity(
#     shap_values,
#     model_probability,
# )
#
# Project validation result:
#
# maximum_difference:
# 1.33e-15
#
# average_difference:
# 8.23e-17
#
# Both values are effectively floating-point noise.