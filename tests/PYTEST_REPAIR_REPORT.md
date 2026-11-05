# Pytest repair and QCD regression report

## Outcome

The authorized test work is complete. The suite cannot pass until the developer corrects two confirmed production defects. All remaining failures expose those defects; no failing financial tests were skipped, xfailed, deleted or patched around.

| Run | Passed | Failed | Errored | Skipped | Xfailed | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Initial | 1608 | 231 | 280 | 2 | 0 | 2121 |
| Final | 1975 | 208 | 0 | 2 | 0 | 2185 |

- 309 previously nonpassing cases now pass: 72 initial failures and 237 initial errors. This includes restoration of test execution through the Windows temporary-directory launcher, not just assertion/fixture edits.
- 64 new cases: 41 direct-engine QCD cases, 21 deterministic QCD cases, one persistence workflow, and one configuration ownership parameter. Of these, 58 pass and six hit the production withdrawal-mode crash.
- 202 original cases remain failing. All original financial invariants and approved numerical reference files are preserved.
- One existing GUI test was renamed from `test_edit_retirement_controls` to `test_edit_withdrawal_strategies`; this is not counted as a new case.

## Root causes and repairs

1. Legacy namespace and dataclass configuration doubles lacked `qcd_settings`. Their original QCD-disabled financial scenarios now explicitly supply disabled QCD input. The core dataclass fixture creates a fresh dictionary per instance.
2. Synthetic core and summary payloads lacked QCD, QCD/RMD-offset and taxable-RMD fields. Fixtures now carry the current schema and retain prior required-RMD values. Updated report expectations distinguish required and taxable RMDs.
3. Headless GUI fixtures lacked independently owned per-person QCD settings. Workflow, scenario and persistence fixtures now construct and copy that state.
4. Retirement-editor tests imported the removed combined editor. They now exercise `WithdrawalsEditFrame`, `SequenceRiskEditFrame` and `RmdQcdEditFrame` directly, retaining field validation, mode toggling and RMD writeback checks. Editor-routing assertions protect the replacement withdrawal screen.
5. Configuration schema tests account for the additional field and verify QCD deep-copy ownership across construction/replacement.
6. The RMD orchestration test now checks actual nonzero distributions rather than counting harmless zero-QCD calls; it still proves each required amount is distributed exactly once to the correct owner.
7. Numerical reference setup previously computed every scenario before any assertion. A lazy cached case runner now isolates cases, allowing eight independent comparisons despite the withdrawal-mode defect. Tests validate default-disabled QCD settings before projecting the additive input schema and independently derive only the six new output fields. No reference file or approved numerical value was regenerated or changed.
8. Python 3.13 mode-0700 directory ACLs exclude this Windows sandbox token. Merely setting `--basetemp` still failed. `tests/run_sandbox_pytest.py` temporarily uses inherited ACLs for directory creation in the test process, restores `os.mkdir`, and runs normal pytest. Financial functions are not patched. Intermediate permission failures and the original baseline remain in the logs.

## QCD coverage

- Disabled behavior: comprehensive exact core comparison against default-disabled settings; existing numerical-reference comparisons.
- Fixed and percent-of-RMD settings; independent husband/wife settings and per-owner annual limits.
- Whole-year eligibility at 70/71, death, inclusive configured start/end ages and multi-year activation.
- QCD below, equal to and above RMD; fixed QCD with RMD disabled; percent QCD becomes zero without an RMD.
- The modeled 111,000 annual per-person limit, inflation, path-specific historical inflation and available pre-tax asset caps. Taxable/Roth/HSA/real-estate assets cannot fund QCDs.
- Withdrawal-engine checks prove QCD counts against the gross target, decreases spendable cash, and leaves the correct portfolio/account balances. Six real withdrawal-mode integration cases remain active and blocked by the production NameError.
- Expense-mode checks prove QCD is additional portfolio outflow that cannot fund household expenses, offsets taxable RMD, and is excluded from household income and MAGI. Tax-enabled QCD coverage checks zero taxable income/tax when QCD fully satisfies the RMD.
- Nominal/real field propagation, core-to-summary arrays, year-by-year/tax/executive report dictionaries, persistence and GUI conversion ownership.

## Production defects and limitations

See `tests/PRODUCTION_ISSUES.md` for conditions, expected/actual behavior, financial impact and recommended investigation.

- 207 failures: `run_sim_core_withdrawals.simulate_withdrawal_year` reads undefined `roth_conversion`, including QCD-disabled scenarios. Production correction is required before downstream withdrawal-mode integration and five numerical reference cases can execute.
- One failure: advanced building tutorial references removed `edit_retirement_controls` on the current GUI interface.
- Eight executable reference cases have exactly equal approved leaves, including floating-point arrays; there are no sub-tolerance numerical changes in those cases. See `tests/numerical_comparison.json`. Five reference cases remain blocked, so full numerical equivalence cannot be claimed.
- Two existing Tk-availability skips occurred. No new skips or xfails were introduced.
- QCD age and limit tests follow the established educational annual model, not an independent tax-law certification.

## Commands and evidence

Initial complete run:

```text
python -m pytest -q --tb=short > tests/pytest_baseline.log 2>&1
```

Final complete run (46.21 seconds):

```text
python tests/run_sandbox_pytest.py tests -q -o addopts= --tb=short -p no:cacheprovider --basetemp=tests/.pytest_tmp_final --junitxml=tests/pytest_final.xml > tests/pytest_final.log 2>&1
```

`-o addopts=` prevents the existing second quiet flag from hiding the final counts. Explicit `tests` collection avoids inaccessible cache directories left by the initial default-cache attempt. The final run collected all 2,185 cases.

Evidence: `pytest_baseline.log`, `pytest_final.log`, `pytest_final.xml`, `test_outcome_analysis.json`, `numerical_comparison.json`, and focused-run logs under `tests/`.

## Verification

- Full final suite executed; it did not pass because of the two documented production defects.
- Focused repairs were rerun: GUI/persistence/configuration/report tests passed; new QCD runs failed only on the identified production withdrawal crash.
- All 45 changed/new Python test files passed syntax and ASCII checks. Newly created source has no comprehensions or single-line loops/branches. Added/modified code was reviewed for compact formatting; unrelated legacy code was retained.
- SHA-256 comparison confirms all 122 production Python files are unchanged. No production, dependency, application configuration, workflow or documentation files were edited. All intentional source changes, reports and test outputs are under `tests/`.
- No Git commands were executed. No packages were installed or upgraded.

## Files

Modified existing Python test files (41):

- `tests/deterministic_tests/test_01_single_person_working_years_cashflow.py`
- `tests/deterministic_tests/test_02_single_person_retirement_transition.py`
- `tests/deterministic_tests/test_03_couple_working_years_combined_household_cashflow.py`
- `tests/deterministic_tests/test_04_manual_expense_deficit_uses_post_tax_assets_first.py`
- `tests/deterministic_tests/test_05_manual_expense_deficit_spills_into_emergency_pre_tax_draw.py`
- `tests/deterministic_tests/test_06_emergency_pre_tax_draw_with_taxes_enabled.py`
- `tests/deterministic_tests/test_07_fixed_dollar_retirement_withdrawal.py`
- `tests/deterministic_tests/test_08_percent_of_portfolio_retirement_withdrawal.py`
- `tests/deterministic_tests/test_09_rmd_only_scenario.py`
- `tests/deterministic_tests/test_10_rmd_plus_withdrawal_scenario.py`
- `tests/deterministic_tests/test_11_401k_contribution_scenario_while_working.py`
- `tests/deterministic_tests/test_12_taxable_account_income_components.py`
- `tests/deterministic_tests/test_13_real_estate_included_vs_excluded.py`
- `tests/deterministic_tests/test_14_real_dollar_deflation_mode.py`
- `tests/deterministic_tests/test_15_fund_expense_drag.py`
- `tests/deterministic_tests/test_16_annual_rebalance_enabled.py`
- `tests/deterministic_tests/test_17_maintain_current_allocation_rebalance_mode.py`
- `tests/deterministic_tests/test_18_overlay_taxes_off.py`
- `tests/deterministic_tests/test_19_overlay_fund_expenses_off.py`
- `tests/deterministic_tests/test_20_overlay_taxes_and_fund_expenses_both_off.py`
- `tests/deterministic_tests/test_27_two_year_vs_multi_year_consistency.py`
- `tests/deterministic_tests/test_28_no_income_no_expense_no_return_conservation.py`
- `tests/deterministic_tests/test_30_single_vs_couple_disabled_second_person_equivalence.py`
- `tests/deterministic_tests/test_core_couple_withdrawal_ownership.py`
- `tests/deterministic_tests/test_numerical_references.py`
- `tests/feature_tests/test_scenario_financial_isolation.py`
- `tests/feature_tests/workflow_helpers.py`
- `tests/module_tests/gui/test_gui_editors.py`
- `tests/module_tests/gui/test_gui_io.py`
- `tests/module_tests/gui/test_gui_retirement.py`
- `tests/module_tests/gui/test_gui_run.py`
- `tests/module_tests/sim/test_run_sim_core.py`
- `tests/module_tests/sim/test_run_sim_core_expenses.py`
- `tests/module_tests/sim/test_run_sim_core_withdrawals.py`
- `tests/module_tests/sim/test_run_sim_summary_report.py`
- `tests/module_tests/sim/test_run_sim_tax_report.py`
- `tests/module_tests/sim/test_simulation.py`
- `tests/module_tests/sim/test_simulation_config.py`
- `tests/module_tests/outputDialogs/summaryDialog/test_summaryIncome.py`
- `tests/module_tests/outputDialogs/summaryDialog/test_summary_dialog.py`
- `tests/feature_tests/monteCarlo/helpers_validation.py`

Created Python test/infrastructure files (4):

- `tests/run_sandbox_pytest.py`
- `tests/deterministic_tests/test_qcd_cashflows.py`
- `tests/feature_tests/test_qcd_workflows.py`
- `tests/module_tests/sim/engines/test_qcd_regression.py`

Created engineering reports: `tests/PRODUCTION_ISSUES.md` and `tests/PYTEST_REPAIR_REPORT.md`, with JSON/XML/log evidence listed above.
