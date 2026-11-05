# Production issues found during pytest repair

Production code was not modified. Failing financial and functional tests remain active.

## 1. Confirmed: every withdrawal-mode year raises NameError

- File/function: `src/warpsimlab/sim/run_sim_core_withdrawals.py`, `simulate_withdrawal_year`, lines 197-207.
- Trigger: a living household reaches a year using withdrawal mode, including QCD-disabled simulations and simulations with no requested Roth conversions.
- Expected: reserve the larger of the owner's required RMD or funded QCD before applying Roth conversions, then calculate gross distributions, spendable cash, taxes and remaining assets.
- Actual: `roth_conversion["husband"]` is read before `roth_conversion` is defined. It is neither a parameter nor an assigned local or imported symbol. Execution raises `NameError` at line 198.
- Evidence: existing withdrawal, ownership, tax, retirement-transition and lifecycle tests; five approved numerical-reference cases; six new cases in `tests/deterministic_tests/test_qcd_cashflows.py`. The direct withdrawal-engine QCD tests pass, while the real yearly runner crashes before reaching withdrawal allocation.
- Consequences: withdrawal-mode projections and reports cannot complete. This also blocks validation of downstream Roth reservation, withdrawal-mode income/MAGI and end-to-end QCD accounting.
- Blocks tests: yes; see the final report and pytest XML for the exact affected tests.
- Recommended investigation: review how `requested_roth_flows` stores per-owner conversion amounts and constrain that actual structure before `apply_roth_conversions`. Check that mandatory QCD/RMD reservations survive the correction. A global stub or financial monkeypatch would conceal the error and was not added.

## 2. Confirmed: advanced tutorial calls a removed GUI method

- File/function: `src/warpsimlab/gui/gui_tutorial_definitions.py`, `build_advanced_building_tutorial_steps`.
- Trigger: construct the advanced building tutorial using the current `PortfolioSimulatorGUI` interface.
- Expected: tutorial navigation callbacks reference current withdrawal, RMD/QCD or sequence-risk editor methods.
- Actual: the builder accesses `gui.edit_retirement_controls`, which no longer exists after the retirement editor split. Current methods include `edit_withdrawal_strategies`, `edit_rmd_qcd` and `edit_sequence_risk`.
- Evidence: `tests/module_tests/gui/test_gui_tutorial_definitions.py::test_tutorial_steps_have_callable_navigation_and_live_mode_gate[build_advanced_building_tutorial_steps]` uses `Mock(spec=PortfolioSimulatorGUI)` and raises `AttributeError`. Code inspection confirms the callback is absent from the actual GUI class.
- Consequences: advanced tutorial construction fails; its navigation cannot run.
- Blocks tests: one existing tutorial test.
- Recommended investigation: update the tutorial steps and descriptions to the intended replacement screens. The test was preserved instead of adding a nonexistent method to its mock.

## Environment limitation, not a production defect

Python 3.13 creates mode-0700 Windows directories with private ACLs. Those ACLs exclude this sandbox's token, so pytest's default temporary directories fail with `WinError 5`; specifying a different base alone does not solve it. `tests/run_sandbox_pytest.py` retains inherited directory ACLs for that test process and restores `os.mkdir` afterwards. It changes no financial behavior and requires no package or system changes. Use a fresh `--basetemp` under `tests/`.

## Modeling boundaries

QCD eligibility follows the simulator's whole-year convention: the first modeled eligible age is 71 for the default 70.5 start. Tests cover ages 70 and 71 and inclusive configured start/end ages. Annual limits use the simulator's 2026 base of 111,000 per person and its configured inflation convention. No IRA/401(k) distinctions or deduction rules were introduced. These tests validate the established educational model; they are not an independent tax-law certification.
