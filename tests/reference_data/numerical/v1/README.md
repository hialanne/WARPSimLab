# Accepted pre-refactor numerical references

These thirteen payloads cover six scenario families. Every payload contains the
complete core dictionary: 105 arrays, including nested financial breakdowns,
year zero, masks, path metadata and terminal indices. Pipeline payloads also
include the integer `effective_years`; the raw mortality payload retains the
requested ten-year allocation, including two post-terminal columns.

`manifest.json` records the accepted source identification, Python/NumPy
versions, UTC capture date, complete schema, activation evidence and capture
times. `inputs/*.json` contain resolved public pre-run scenario inputs, not
runtime caches. `<workspace>` is a portable prefix for the absolute historical
CSV paths used by production loaders. The CSVs contain synthetic percentages
derived from the existing isolation scenario, not an authentic market dataset.
NPZ arrays are lossless and load with `allow_pickle=False`.

Normal pytest execution only reads these files. It fails on missing references,
unexpected fields, incompatible shapes/dtypes, scenario drift, inactive coverage
checks or numerical differences. It never captures, replaces or repairs them.
Floating values use `abs(actual-reference) <= 1e-8 + 1e-13*abs(reference)`;
integers, Booleans, structure, years, tax brackets, survivor factors and negative
bracket sentinels compare exactly. NaN positions and infinity signs must match.

Run the reference suite from the project root:

```powershell
python -m pytest tests/deterministic_tests/test_numerical_references.py
```

Capture is a separate, explicit action, authorized only for an identified
accepted simulator. The initial capture used the current accepted pre-refactor
workspace, labeled WARPSimLab 4.5.0. No Git operations or source hashing were
used. To capture a separately approved future version, choose a new output
directory and identify its accepted source:

```powershell
python -m tests.tools.capture_numerical_references --source-version 'accepted version or commit' --output tests/reference_data/numerical/v2
```

The utility refuses to overwrite existing input/output datasets or a manifest.
For an explicitly approved correction affecting selected cases, use repeatable
`--case` arguments and a separate output directory, then verify all differences
before replacing only authorized datasets. Do not delete v1 or recapture it to
make refactored code pass. An interface adapter can change while the approved
core schema and expected numbers remain.

Scenario activation findings are documented in
`codex_reports/numerical_reference_implementation.md`. In particular, the original
two S3 cases did not activate tax-funding withdrawals; the supplemental
`s3_tax_funding` case does. Qualified HSA spending and Roth withdrawal reporting
are exercised in their respective modes rather than assumed equivalent.

**Approved reporting correction (2026-10-29):** the confirmed expense-mode Roth
reporting bug is fixed. Only `outputs/s3_expenses.npz` was refreshed: path 0,
year index 3 (2029), `roth_withdrawals` changed from $0 to $45,000, matching the
Roth balance actually spent. Every other result value is unchanged, and all
twelve unaffected NPZs and all input definitions were preserved byte-for-byte.
The affected case's `reporting_correction` entry in `manifest.json` records its
separate source/capture provenance; the original global provenance still applies
to the initial dataset capture. See `codex_reports/roth_withdrawal_reporting_fix.md`
for verification and test results. The original implementation report describes
the pre-correction behavior and remains an unchanged historical record.

The married raw case extends only the requested horizon to ten years so final
death at year index eight leaves observable padding. The other married cases
retain the proposed eight-year horizon. RNG/library changes can alter seeded
results; investigate in the recorded environment rather than relaxing tolerances.
