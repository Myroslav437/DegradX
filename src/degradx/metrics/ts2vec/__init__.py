"""Vendored TS2Vec (Yue et al., AAAI 2022), official code https://github.com/zhihanyue/ts2vec at commit b0088e1, MIT
licence (LICENSE in this directory). Files copied unchanged except that absolute imports (``from models ...``,
``from utils ...``) were made package-relative. Used only as the representation encoder of the Frechet-style distance
(Jeha et al. 2022 Context-FID; brief S5, docs/TOOLING.md: not pip-installable)."""
from .ts2vec import TS2Vec  # noqa: F401
