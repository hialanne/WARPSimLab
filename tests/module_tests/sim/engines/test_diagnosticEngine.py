from types import SimpleNamespace

import pytest

from src.warpsimlab.sim.engines import diagnosticEngine as mod


def test_internal_error_writes_context_and_filters_runtime_state(diagnostic_home, capsys):
    config = SimpleNamespace(warpsimlab_version="test-version", years_to_simulate=12,
                             root="DO_NOT_RECORD_ROOT", _mc_rng="DO_NOT_RECORD_RNG")
    with pytest.raises(mod.WARPSimLabInternalError) as caught:
        mod.raise_internal_error("unbalanced portfolio", config, {"year": 2030, "person": SimpleNamespace(age=65)})
    error = caught.value
    assert error.original_message == "unbalanced portfolio"
    assert error.diagnostic_path.is_relative_to(diagnostic_home)
    report = error.diagnostic_path.read_text(encoding="utf-8")
    for expected in ("unbalanced portfolio", "test-version", "years_to_simulate: 12", "year: 2030", "'age': 65", "Call Stack", "test_internal_error_writes"):
        assert expected in report
    assert "DO_NOT_RECORD" not in report
    assert str(error.diagnostic_path) in str(error)
    assert str(error.diagnostic_path) in capsys.readouterr().out


def test_write_failure_preserves_original_error(monkeypatch, capsys):
    def denied():
        raise PermissionError("denied")
    monkeypatch.setattr(mod, "Path", SimpleNamespace(home=denied))
    with pytest.raises(mod.WARPSimLabInternalError) as caught:
        mod.raise_internal_error("original failure", None)
    assert caught.value.original_message == "original failure"
    assert caught.value.diagnostic_path is None
    assert "unable to write" in str(caught.value)
    assert "unable to write" in capsys.readouterr().out


def test_unformattable_context_does_not_lose_report(diagnostic_home):
    class BrokenRepr:
        __slots__ = ()
        def __repr__(self):
            raise ValueError("cannot format")
    path = mod._write_diagnostic_report("failure", None, {"value": BrokenRepr()}, ["caller\n"])
    assert "<unable to format value>" in path.read_text(encoding="utf-8")
