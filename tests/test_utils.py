import json

import numpy as np
import pandas as pd

from degradx.utils.checks import CheckTable
from degradx.utils.io import save_table, write_json
from degradx.utils.seeding import derive_seed, rng


def test_seed_sources_are_independent_and_stable():
    a = derive_seed(1, "generation", "matr", 0)
    b = derive_seed(1, "model_init", "matr", 0)
    assert a != b
    assert a == derive_seed(1, "generation", "matr", 0)
    assert derive_seed(1, "generation", "matr", 1) != a
    x = rng(1, "generation", "matr").normal(size=5)
    y = rng(1, "generation", "matr").normal(size=5)
    np.testing.assert_array_equal(x, y)


def test_unknown_seed_source_rejected():
    import pytest

    with pytest.raises(ValueError):
        derive_seed(1, "nonsense")


def test_check_table_exit_code(tmp_path):
    ct = CheckTable()
    ct.require("ok", True, "x", "x")
    ct.require("soft", False, "y", "z", severity="warn")
    assert ct.finalize(tmp_path) == 0
    ct.require("hard", False, "1", "2")
    assert ct.finalize(tmp_path) == 1
    rows = json.loads((tmp_path / "tables" / "checks.json").read_text())
    assert [r["name"] for r in rows] == ["ok", "soft", "hard"]


def test_io_roundtrip_handles_nan(tmp_path):
    write_json({"a": np.float64("nan"), "b": np.arange(3)}, tmp_path / "x.json")
    assert json.loads((tmp_path / "x.json").read_text()) == {"a": None, "b": [0, 1, 2]}
    csv, js = save_table(pd.DataFrame({"u": [1, 2], "v": [0.5, np.nan]}), tmp_path / "t")
    assert csv.exists() and js.exists()
