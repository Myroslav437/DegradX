"""Import TimeSHAP against current shap.

timeshap 1.0.4 (``timeshap/explainer/kernel/timeshap_kernel.py:53``) imports
``shap.explainers._kernel.Kernel``; shap renamed that class ``KernelExplainer`` in 0.43, and
shap 0.42.1 has no Python 3.12 wheel. Aliasing the old name before import restores the package
unchanged. Validated at S0 (docs/S0_RESEARCH/env.md): exact Shapley values on a linear model to
~1e-14, and agreement with a source-built shap 0.42.1 to 6.7e-16 on a sampled nonlinear case.
The alias is only trusted for the shap version pinned in pyproject.toml.
"""

from __future__ import annotations


def import_timeshap():
    import shap.explainers._kernel as _kernel

    if not hasattr(_kernel, "Kernel"):
        _kernel.Kernel = _kernel.KernelExplainer
    import timeshap.explainer as explainer

    return explainer
