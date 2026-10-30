from types import SimpleNamespace

import pytest

from src.warpsimlab.gui import gui_validation as mod


@pytest.mark.parametrize("parser", [mod.parse_integer, mod.parse_finite_float])
def test_numeric_options_and_inclusive_limits(parser):
    assert parser(" 1,000 ", allow_commas=True, minimum=1000, maximum=1000) == 1000
    assert parser("0", minimum=0) == 0
    assert parser(" ", allow_blank=True) is None
    for raw in ("", "bad", "1,000", "-1", "1001"):
        with pytest.raises(mod.GUIValidationError):
            parser(raw, minimum=0, maximum=1000)


@pytest.mark.parametrize("raw", ["nan", "inf", "-inf", "1e999"])
def test_float_rejects_nonfinite_values(raw):
    with pytest.raises(mod.GUIValidationError, match="finite"):
        mod.parse_finite_float(raw)


def test_scientific_notation_and_integer_syntax():
    assert mod.parse_finite_float("1e2") == 100
    with pytest.raises(mod.GUIValidationError, match="Scientific"):
        mod.parse_finite_float("1E2", allow_scientific=False)
    for raw in ("1.0", "1e2"):
        with pytest.raises(mod.GUIValidationError, match="integer"):
            mod.parse_integer(raw)


def test_validation_failure_marks_toplevel():
    root = SimpleNamespace()
    mod.mark_validation_failed(SimpleNamespace(winfo_toplevel=lambda: root))
    assert root._warpsimlab_validation_failed is True
