#!/usr/bin/env bash
# S0: build the DegradX Python environment and LaTeX toolchain (idempotent, no sudo).
# Run from the repository root:   bash scripts/s0_setup_env.sh
#
# Environment overrides (optional):
#   DEGRADX_VENV      venv location            (default: .venv)
#   DEGRADX_PYTHON    interpreter for the venv (default: python3.12, falling back to python3)
#   DEGRADX_SKIP_TEX  set to 1 to skip installing TinyTeX
set -euo pipefail

REPO_ROOT="$(pwd)"
if [[ ! -f "${REPO_ROOT}/requirements-lock.txt" || ! -f "${REPO_ROOT}/pyproject.toml" ]]; then
    echo "error: run from the DegradX repository root (requirements-lock.txt and pyproject.toml not found in $(pwd))" >&2
    exit 1
fi

VENV="${DEGRADX_VENV:-${REPO_ROOT}/.venv}"
TORCH_INDEX="https://download.pytorch.org/whl/cu130"
# LaTeX: TinyTeX (a portable TeX Live, no sudo) so the paper builds with pdfTeX, the engine that
# produced the committed paper.pdf. tectonic (XeTeX) was tried first and silently drops the paper's
# em/en dashes and non-ASCII author-name glyphs under inputenc+fontenc; see docs/TOOLING.md.
TEX_ROOT="${REPO_ROOT}/.tools"
TEX_BIN="${TEX_ROOT}/.TinyTeX/bin/x86_64-linux"
TEX_PACKAGES="collection-latexrecommended collection-fontsrecommended collection-latexextra latexdiff"

# ---------------------------------------------------------------- 1. venv
PY="${DEGRADX_PYTHON:-}"
if [[ -z "${PY}" ]]; then
    if command -v python3.12 >/dev/null 2>&1; then PY=python3.12; else PY=python3; fi
fi
if ! "${PY}" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)'; then
    echo "error: ${PY} is not Python 3.12 (pyproject requires >=3.12,<3.13)" >&2
    exit 1
fi
if [[ ! -x "${VENV}/bin/python" ]]; then
    echo "==> creating venv at ${VENV} with ${PY}"
    "${PY}" -m venv "${VENV}"
else
    echo "==> venv exists at ${VENV}"
fi
VPY="${VENV}/bin/python"
"${VPY}" -m pip install --quiet --upgrade pip

# ---------------------------------------------------------------- 2. locked dependencies
echo "==> installing requirements-lock.txt (torch from ${TORCH_INDEX})"
"${VPY}" -m pip install --quiet -r "${REPO_ROOT}/requirements-lock.txt" --extra-index-url "${TORCH_INDEX}"

# ---------------------------------------------------------------- 3. project package (editable)
if [[ -f "${REPO_ROOT}/src/degradx/__init__.py" ]]; then
    echo "==> installing degradx (editable, no deps: the lock already provides them)"
    "${VPY}" -m pip install --quiet --no-deps -e "${REPO_ROOT}"
else
    echo "==> src/degradx/__init__.py not found; skipping editable install of degradx"
fi

# ---------------------------------------------------------------- 4. TinyTeX (pdfLaTeX, bibtex, latexdiff)
if [[ "${DEGRADX_SKIP_TEX:-0}" != "1" ]]; then
    if [[ -x "${TEX_BIN}/pdflatex" ]]; then
        echo "==> TinyTeX already present in ${TEX_ROOT}/.TinyTeX"
    else
        echo "==> installing TinyTeX into ${TEX_ROOT}/.TinyTeX"
        mkdir -p "${TEX_ROOT}"
        curl -fsSL "https://yihui.org/tinytex/install-bin-unix.sh" -o "${TEX_ROOT}/install-tinytex.sh"
        TINYTEX_DIR="${TEX_ROOT}" sh "${TEX_ROOT}/install-tinytex.sh" --no-path
    fi
    # shellcheck disable=SC2086
    "${TEX_BIN}/tlmgr" install ${TEX_PACKAGES} >/dev/null
fi

# ---------------------------------------------------------------- 5. verification summary
echo "==> verification"
set +e
CUBLAS_WORKSPACE_CONFIG="${CUBLAS_WORKSPACE_CONFIG:-:4096:8}" "${VPY}" - <<'PYEOF'
import importlib.metadata as md, json, os, sys, warnings
warnings.filterwarnings("ignore")
ok = True
def row(k, v): print(f"  {k:<28} {v}")
row("python", sys.version.split()[0] + "  (" + sys.executable + ")")
import numpy; row("numpy", numpy.__version__)
import torch
row("torch", f"{torch.__version__}  (CUDA build {torch.version.cuda}, cuDNN {torch.backends.cudnn.version()})")
cuda = torch.cuda.is_available()
row("torch.cuda.is_available", cuda)
if cuda:
    arch = torch.cuda.get_arch_list()
    cap = torch.cuda.get_device_capability(0)
    need = f"sm_{cap[0]}{cap[1]}"
    row("device", f"{torch.cuda.get_device_name(0)}  ({need})")
    row("arch list has device arch", f"{need in arch}  {arch}")
    ok &= need in arch
    try:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True)
        torch.manual_seed(0)
        lstm = torch.nn.LSTM(4, 8, batch_first=True).cuda()
        out, _ = lstm(torch.randn(2, 10, 4, device="cuda"))
        out.sum().backward()
        row("deterministic LSTM fwd+bwd", "OK")
    except Exception as e:  # noqa: BLE001
        row("deterministic LSTM fwd+bwd", f"FAILED: {type(e).__name__}: {e}")
        ok = False
else:
    ok = False
import batteryml  # noqa: F401
try:
    du = json.loads(md.distribution("batteryml").read_text("direct_url.json") or "{}")
    commit = du.get("vcs_info", {}).get("commit_id", "?")
except Exception:  # noqa: BLE001
    commit = "?"
row("batteryml", f"{md.version('batteryml')}  (commit {commit})")
import shap.explainers._kernel as _k
if not hasattr(_k, "Kernel"):
    _k.Kernel = _k.KernelExplainer  # TimeSHAP 1.0.4 compatibility alias (see pyproject.toml)
import timeshap.explainer  # noqa: F401
row("timeshap", f"{md.version('timeshap')}  (explainer import OK, shap {md.version('shap')})")
import captum
row("captum", captum.__version__)
try:
    import degradx  # noqa: F401
    row("degradx", "importable")
except ImportError:
    row("degradx", "not installed (src/degradx missing)")
sys.exit(0 if ok else 2)
PYEOF
py_status=$?
set -e

if [[ -x "${TEX_BIN}/pdflatex" ]]; then
    printf '  %-28s %s\n' "pdflatex" "$("${TEX_BIN}/pdflatex" --version | head -1)"
    printf '  %-28s %s\n' "latexdiff" "$("${TEX_BIN}/latexdiff" --version 2>&1 | head -1)"
fi
exit "${py_status}"
