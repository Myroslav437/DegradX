"""Matplotlib style of the DegradX paper figures.

Usage (as in ``paper/img/scripts/fig_*.py``)::

    import style            # or: from degradx.viz import style
    style.apply()
    ax.plot(x, y, color=style.GREY)

Provenance
----------
The original ``style.py`` was not committed. This module is a reconstruction
from the published PDFs ``paper/img/fig_{loop,generator,mean_component,
weights}.pdf`` (Matplotlib 3.10.8 pdf backend, per their /Creator field):

* fonts: ``pdffonts`` lists DejaVuSerif + STIXGeneral-{Regular,Italic}, all
  Type 3  ->  ``font.family='serif'``, ``mathtext.fontset='stix'``, fonttype 3;
* text sizes (PyMuPDF spans): tick labels 8 pt, axis labels 9 pt, legend 7 pt;
* PDF drawing operators: ticks 3.0 pt long, 0.8 pt wide, pointing out; spines
  0.8 pt; one invisible single-point ``Line2D`` in fig_generator and
  fig_weights carries a 1.2 pt width that no script sets  ->
  ``lines.linewidth=1.2``;
* the annotation grey is RGB 0.35 (text #595959)  ->  ``GREY='0.35'``;
* page size exceeds/undercuts figsize (e.g. fig_loop 4.611 in figsize ->
  334.872 pt = 4.651 in with all artists inside the canvas)  ->
  ``savefig.bbox='tight'`` with ``pad_inches=0.02``.

Validation: with Matplotlib 3.10.8 (numpy 2.5.3), running the four unmodified
scripts against this module reproduces all four PDFs byte-for-byte (sha256
equal) when ``TZ=UTC`` and ``SOURCE_DATE_EPOCH`` are set to each original
CreationDate; without that, only the CreationDate string differs (content
streams identical, 150-dpi raster difference 0 pixels). Ablation showed that
``font.size``, ``axes.titlesize`` and ``pdf.fonttype`` are not constrained by
the four figures (every text there that would use them has an explicit size,
and fonttype 3 is the default); the values below are choices.

Residual mismatch: ``fig_tstr.pdf`` (Figure 5) has no script and is NOT in
this family (6.0-6.4 pt text, 0.7 pt lines, grey #555555, DejaVuSerif-Italic
math instead of STIX); this module does not reproduce it. The default
(coloured) property cycle is intentionally left unchanged because its colour
is written into the reproduced PDFs; always pass ``color=`` explicitly.
"""
from __future__ import annotations

import re

import matplotlib as mpl

# -- constant referenced by the paper scripts (reconstructed, verified) ------
GREY = "0.35"  # annotation text, arrows, secondary labels

# -- page geometry (PRIMEarxiv.sty: \newgeometry{textwidth=6.5in}) ----------
TEXTWIDTH_IN = 6.5
TEXTWIDTH_PT = 468.0

# -- recommended encodings for Results figures (a convention, not measured) --
# Grey levels and widths are taken from those already used in Figures 1-4.
MEASURED = "0.55"         # measured data, single summary line (Fig. 3 unit B)
MEASURED_BUNDLE = "0.70"  # measured data, many thin per-unit lines, background
GENERATED = "black"       # generated data, always black
REFERENCE = "0.6"         # chance / saturation / threshold lines (Fig. 2)
FILL = "0.82"             # shaded bands (Fig. 2 graded field)
LW_MAIN = 1.2             # summary series (= lines.linewidth)
LW_THIN = 0.6             # per-unit bundles and reference lines

RC = {
    # constrained by the published PDFs
    "font.family": "serif",
    "mathtext.fontset": "stix",
    "lines.linewidth": 1.2,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7,
    "xtick.major.size": 3.0,
    "ytick.major.size": 3.0,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    # Matplotlib defaults, pinned against a local matplotlibrc (the PDFs show
    # 0.8 pt spines/ticks pointing out; fonttype 3 per pdffonts)
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "pdf.fonttype": 3,
    # unconstrained by the PDFs; chosen to match the explicit sizes in scripts
    "font.size": 9,
    "axes.titlesize": 8.5,
}


def apply() -> None:
    """Reset to Matplotlib defaults, then apply the paper style."""
    mpl.rcdefaults()
    mpl.rcParams.update(RC)


def despine(ax) -> None:
    """Hide top and right spines, as every axes figure in the paper does."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def printed_scale(pdf_path: str, fraction: float) -> float:
    """Scale LaTeX applies to a saved PDF included at ``fraction\\linewidth``.

    Figures 1-4 print at 0.98-1.12; aim for 1.00-1.05 so that 9/8/7 pt text
    prints at about that size next to the 10 pt body.
    """
    with open(pdf_path, "rb") as fh:
        m = re.search(rb"/MediaBox \[ *0 0 ([0-9.]+) ([0-9.]+) *\]", fh.read())
    if m is None:
        raise ValueError(f"no MediaBox found in {pdf_path}")
    return fraction * TEXTWIDTH_PT / float(m.group(1))
