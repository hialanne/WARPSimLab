from types import SimpleNamespace

import pytest

from src.warpsimlab.gui.gui_realEstate import RealEstateEditFrame


@pytest.mark.parametrize("couple", [False, True])
def test_real_estate_commits_and_totals(tk_root, couple):
    husband = SimpleNamespace(real_estate=100000)
    wife = SimpleNamespace(real_estate=200000) if couple else None
    frame = RealEstateEditFrame(tk_root, husband, wife)
    assert frame.total_real_estate_var.get() == ("300,000" if couple else "100,000")
    frame._validate_real_estate_on_focusout("125,000", "husband")
    if couple:
        frame._validate_real_estate_on_focusout("0", "wife")
    tk_root.update_idletasks()
    assert husband.real_estate == 125000
    assert frame.total_real_estate_var.get() == "125,000"


@pytest.mark.parametrize("raw", ["-1", "nan", "1e3", "", "bad"])
def test_bad_real_estate_preserves_model_and_display(tk_root, validation_errors, raw):
    portfolio = SimpleNamespace(real_estate=1000)
    frame = RealEstateEditFrame(tk_root, portfolio)
    frame._validate_real_estate_on_focusout(raw, "husband")
    tk_root.update_idletasks()
    assert portfolio.real_estate == 1000
    assert frame.h_real_estate_var.get() == "1,000"
    assert frame.total_real_estate_var.get() == "1,000"
    assert validation_errors
