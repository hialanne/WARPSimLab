# WARPSimLab

## Project overview

WARPSimLab is a personal financial simulator that runs on your desktop. It helps you explore how
different assumptions about income, spending, taxes, investments, and retirement
can affect your long-term financial future.

It supports deterministic projections — a single path through the simulator using
the assumptions you enter — as well as Monte Carlo simulation, historical
market-window analysis, and report generation.

The project is intended for education and exploratory planning. Results are
based on user inputs and assumptions, not predictions or recommendations.

## What WARPSimLab is

WARPSimLab is a local graphical application written in Python with Tkinter. It lets a
user enter personal financial data, run simulations, compare scenarios,
and review charts and report files.

The repository includes historical US asset-return and inflation data, example
financial-data files, and getting-started documents used by the application.

## What WARPSimLab is not

WARPSimLab is not a financial plan, accounting system, tax-preparation program, or a
substitute for professional financial, legal, tax, or investment advice. It does not
guarantee that simulated outcomes will occur.

## Key features

- Income and expense modeling, including recurring and special income and dynamic
  expenses.
- Portfolio projections across taxable, pre-tax, Roth, HSA, cash, and real-estate
  categories.
- Retirement contributions, withdrawals, and required minimum distribution (RMD)
  modeling.
- Federal and state tax-related simulations.
- Deterministic, Monte Carlo, and historical-window analysis.
- Scenario exploration for comparing different assumptions.
- Portfolio, income, cash-flow, operating-balance, and summary visualizations.
- HTML and CSV report generation.

Tax and other financial rules are simplified simulation inputs and logic. Their
presence does not establish current or complete tax-law accuracy.

## Privacy and offline use

WARPSimLab is designed to run locally. Information entered into the
simulator is processed on the user's computer. No personal data is
intentionally transmitted off the user's computer.

## Installation

### Windows packaged release

The bundled project website documents these steps for its Windows ZIP release:

1. Download the WARPSimLab ZIP file.
2. Extract the ZIP file completely.
3. Open the extracted folder.
4. Double-click `WARPSimLab.exe`.

The website notes that the executable is not code-signed, so Windows may display a
security warning.

### Running from source

The source imports Tkinter, NumPy, and Matplotlib. However, this repository does not
contain a dependency manifest or a documented Python-version requirement.

TODO: Add the supported Python version and verified commands for creating an
environment and installing all dependencies.

### Building a packaged application

`WARPSimLab.spec` is a PyInstaller specification for an application named
`WARPSimLab`.

TODO: Add a verified PyInstaller version and build command. The data paths in the
specification should also be checked against the current `src/warpsimlab/` layout
before documenting a reproducible build.

## Running the application

From the repository root, the source launcher is:

```text
python WARPSimLab.py
```

The launcher creates the Tkinter window and starts the desktop application.

## Reports

WARPSimLab can generate the following reports:

- Executive Summary Report (`executive_summary_*.html`).
- Year-by-Year Details Report (`year_by_year_details_*.html` and optional CSV).
- Tax Report (`tax_report_*.html` with optional yearly, lifetime-summary, and
  source-breakdown CSV files).
- Historical Window Risk Report (HTML with optional summary, failure-statistics,
  and percentile CSV files).
- Monte Carlo Risk Report (HTML with optional summary, failure-statistics, and
  percentile CSV files).

Reports are written to a `WARPSimLab/reports` folder on the user's Desktop.

Reports can include generated chart images and simulation assumptions. They summarize
model results; they do not certify those results or turn them into professional
advice.

## Testing

Tests are organized under `tests/` as:

- `deterministic_tests/` for fixed-scenario and simulation-pipeline behavior.
- `feature_tests/` for focused feature validation, currently including Monte Carlo
  behavior.
- `invariant_tests/` for relationships that should hold across simulation results.
- `module_tests/` for data classes, GUI components, plots, reports, simulation code,
  engines, and utilities.

The test files use pytest naming, and `tests/module_tests/pytest.ini` contains pytest
settings. Tests are run using `python -m pytest`.

## Project structure

```text
WARPSimLab.py          Source launcher
WARPSimLab.spec        PyInstaller specification
src/warpsimlab/        Application package
  dataClasses/         Financial state and input data classes
  dataFiles/           Bundled historical market and inflation data
  docs/                In-application PDF documentation
  exampleFiles/        Example financial-data files
  gui/                 Tkinter user interface
  plots/               Charts and plot-data helpers
  reports/             HTML and CSV report generation
  sim/                 Simulation pipeline, runners, and engines
  utils/               Shared constants and utilities
tests/                 Deterministic, feature, invariant, and module tests
warpsimlab-org/        Project website source and published-download assets
README.md              Project README
LICENSE.txt            MIT License
```

## Limitations

- Simulation results depend on inputs supplied by the user.
- Results based on historical data do not predict future market behavior.
- Monte Carlo and historical window outputs describe generated scenarios, not
  guaranteed personal outcomes.
- Tax, retirement, and account rules have been simplified or are incomplete.
- The repository does not currently document supported Python versions, source
  dependency installation, or a reproducible build command.
- TODO: Document supported operating systems after they have been verified. The
  repository provides evidence of a Windows packaged release but does not establish
  support for other platforms.

## Disclaimer

WARPSimLab is provided for exploratory and educational use only. It does not provide
financial, legal, tax, investment, or retirement advice. Do not rely on its output as
the sole basis for decisions. Consider consulting qualified professionals who can
evaluate your circumstances and verify relevant laws, rules, and assumptions.

## License

WARPSimLab is licensed under the MIT License. See `LICENSE.txt` for the full terms.
