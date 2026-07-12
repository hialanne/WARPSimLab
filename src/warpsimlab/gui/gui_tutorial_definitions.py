def build_basic_tutorial_steps(gui):
    return [
        {
            "title": "Welcome",
            "section_title": "About this tutorial",
            "text": (
                "WARPSimLab starts with a general example already loaded. "
                "This tutorial uses the current financial values and does "
                "not replace or reset them. The buttons across the top are "
                "main menu categories. Most open a second menu containing "
                "the individual screens. For example, Cash Flow opens a "
                "menu containing Normal Income and Expenses. Select Next "
                "to begin."
            ),
            "screen_callback": gui.edit_main_home,
        },
        {
            "title": "Cash Flow -> Normal Income",
            "section_title": "What to review",
            "text": (
                "From the top menu, select Cash Flow, then select Normal "
                "Income. This screen contains the primary personal and "
                "income inputs. Review each person's age, annual income, "
                "retirement age, and Social Security. You may edit these "
                "values during the tutorial. Enable Second Person controls "
                "whether a second person's information is included."
            ),
            "screen_callback": gui.edit_person_data,
        },
        {
            "title": "Cash Flow -> Expenses",
            "section_title": "What to review",
            "text": (
                "From the top menu, select Cash Flow, then select Expenses. "
                "Expenses define yearly household spending. Each expense "
                "can have a start year, an optional end year, an annual "
                "cost, and a comment. Taxes are calculated separately by "
                "the simulator. You may edit or add expenses here."
            ),
            "screen_callback": gui.edit_expenses,
        },
        {
            "title": "Balance Sheet -> Portfolio",
            "section_title": "What to review",
            "text": (
                "From the top menu, select Balance Sheet, then select "
                "Portfolio. In Basic mode, the Portfolio screen presents "
                "starting investable assets using a simplified Savings "
                "entry. Review or edit the current savings values. Select "
                "Next when you are ready to run the simulation."
            ),
            "screen_callback": gui.edit_portfolio_data,
        },
        {
            "title": "Results -> Summary Dialog",
            "section_title": "What to do",
            "text": (
                "Now run the simulation yourself. From the top menu, select "
                "Results, then select Summary Dialog. WARPSimLab will run "
                "the current financial example and open a separate "
                "Simulation Summary window. After the window opens, return "
                "to this tutorial and select Next."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Summary Dialog -> Three Tabs",
            "section_title": "What to review",
            "text": (
                "The Simulation Summary window has three tabs across the "
                "top. Select Portfolio to review assets at the start, "
                "retirement, and end of the simulation. Select Cash Flow "
                "to review income, taxes, expenses, and net cash flow at "
                "selected years. Select Summary to review overall results, "
                "totals, and important simulation assumptions. Review all "
                "three tabs, then close the Simulation Summary window and "
                "return here."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Cash Flow -> Expenses",
            "section_title": "What to do",
            "text": (
                "Now change one input and compare the results. From the top "
                "menu, select Cash Flow, then select Expenses. Change one "
                "annual expense by a noticeable but reasonable amount. Then "
                "select Results, followed by Summary Dialog, and run the "
                "simulation again. Review the Portfolio, Cash Flow, and "
                "Summary tabs and compare them with the earlier results. "
                "Changing one value at a time makes it easier to understand "
                "cause and effect."
            ),
            "screen_callback": gui.edit_expenses,
        },
        {
            "title": "File -> Save Financial Data",
            "section_title": "What to do",
            "text": (
                "WARPSimLab does not automatically preserve your changes "
                "after the program closes. To keep the current financial "
                "scenario, select File from the top menu, then select Save "
                "Financial Data. Choose a file name and location you will "
                "recognize later. To restore a saved scenario in another "
                "session, select File, followed by Load Financial Data. "
                "Saving is optional for this tutorial."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Basic Tutorial Complete",
            "section_title": "What comes next",
            "text": (
                "You have reviewed the primary Basic mode inputs, run the "
                "simulation, explored the Summary Dialog, changed one input, "
                "compared the results, and learned how to save a scenario. "
                "Continue exploring in Basic mode, or select Mode from the "
                "upper-right menu and then select Advanced to reveal additional "
                "inputs, simulation controls, results, and reports. Select "
                "Finish to return to the Tutorials page."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
    ]


def build_advanced_building_tutorial_steps(gui):
    return [
        {
            "title": "Welcome",
            "section_title": "About this tutorial",
            "text": (
                "This tutorial introduces the screens used to build and "
                "configure an advanced WARPSimLab simulation. It uses the "
                "financial values currently loaded and does not copy, reset, "
                "or restore any data. You may edit values while following the "
                "tutorial. Select Next to continue."
            ),
            "screen_callback": gui.edit_main_home,
        },
        {
            "title": "Mode -> Advanced",
            "section_title": "What to do",
            "text": (
                "Advanced features are not available while the simulator is "
                "in Basic mode. From the upper-right menu, select Mode, then "
                "select Advanced. The tutorial will remain on this step while "
                "the simulator rebuilds the screen. After Advanced mode is "
                "selected, select Next."
            ),
            "screen_callback": gui.edit_tutorial_blank,
            "can_advance": lambda: gui.mode_var.get() == "Advanced",
            "validation_message": (
                "Select Mode -> Advanced before continuing."
            ),
        },
        {
            "title": "Advanced Mode Orientation",
            "section_title": "What this means",
            "text": (
                "Advanced mode adds detailed portfolio categories, real "
                "estate, retirement modeling, simulation assumptions and "
                "controls, additional results, Scenario Explorer, and reports. "
                "This tutorial concentrates on building the financial model "
                "and configuring the simulation. A separate tutorial will "
                "cover advanced results, Scenario Explorer, and reports."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Cash Flow -> Normal Income",
            "section_title": "What to review",
            "text": (
                "This screen defines each person's age, earned income, and "
                "retirement timeline. Advanced mode also includes annual "
                "retirement contributions, employer matching, Social Security "
                "start ages, pensions, pension inflation adjustments, and "
                "annuities. Review the timing as well as the dollar amounts. "
                "Income stops and retirement benefits begin according to the "
                "ages entered here. You may edit the current values."
            ),
            "screen_callback": gui.edit_person_data,
        },
        {
            "title": "Balance Sheet -> Portfolio",
            "section_title": "What to review",
            "text": (
                "Advanced mode separates investable assets by both asset class "
                "and tax treatment. Stocks, bonds, and cash can each be entered "
                "as Pre-Tax, After-Tax, or Roth assets. HSA assets are entered "
                "on a separate row. Values are also separated by person when "
                "the second person is enabled. The Total column is calculated "
                "automatically. Real estate is entered on a different screen."
            ),
            "screen_callback": gui.edit_portfolio_data,
        },
        {
            "title": "Balance Sheet -> Real Estate",
            "section_title": "What to review",
            "text": (
                "Real estate is entered separately from the investable "
                "portfolio. Enter the current real estate value assigned to "
                "each person. The Total column is calculated automatically. "
                "These values are included in balance sheet and wealth "
                "calculations, but they remain separate from stocks, bonds, "
                "cash, Roth assets, and other investable accounts."
            ),
            "screen_callback": gui.edit_real_estate,
        },
        {
            "title": "Balance Sheet -> Derived Statistics",
            "section_title": "What to review",
            "text": (
                "Derived Statistics is a read-only review screen. It combines "
                "the portfolio and real estate values already entered. Review "
                "total investable assets, real estate, and total wealth. The "
                "screen also shows the percentage of investable assets in each "
                "tax bucket and in stocks, bonds, and cash. Use these values to "
                "check that the starting balance sheet reflects your intent."
            ),
            "screen_callback": gui.edit_derived_statistics,
        },
        {
            "title": "Retirement -> Spending Model",
            "section_title": "What to decide",
            "text": (
                "The Retirement screen supports two ways to model retirement "
                "spending. Use Manually Entered Expenses uses the expense "
                "schedule entered under Cash Flow. Income pays those expenses, "
                "and the portfolio supplies any remaining shortfall. Use "
                "Automatically Calculated Withdrawals instead takes money from "
                "the portfolio according to a withdrawal rule. Select the "
                "approach that matches the question you want to study."
            ),
            "screen_callback": gui.edit_retirement_controls,
        },
        {
            "title": "Retirement -> Withdrawal Rules",
            "section_title": "What to review",
            "text": (
                "Automatic withdrawal mode can use a portfolio percentage or "
                "a fixed annual dollar amount. A mode ending in + Inflation "
                "adjusts the withdrawal over time for inflation. Enter either "
                "the annual percentage or dollar amount used by the selected "
                "mode. Include RMDs adds required withdrawals from applicable "
                "retirement accounts. These withdrawal controls are disabled "
                "when Manually Entered Expenses is selected."
            ),
            "screen_callback": gui.edit_retirement_controls,
        },
        {
            "title": "Retirement -> Sequence Risk",
            "section_title": "What to review",
            "text": (
                "The right side of the Retirement screen contains optional "
                "sequence-of-returns scenarios. These controls deliberately "
                "apply a downturn at an early, middle, late, or custom point "
                "in the simulation. You can also select its duration and "
                "severity. Use this feature to stress-test retirement timing. "
                "It is an imposed scenario and is separate from the normal "
                "market assumptions used by the simulation."
            ),
            "screen_callback": gui.edit_retirement_controls,
        },
        {
            "title": "Simulation -> Assumptions",
            "section_title": "What to review",
            "text": (
                "Assumptions defines the market environment used by the "
                "simulation. Review the expected yearly gains and volatility "
                "for stocks, bonds, cash, and real estate, along with the "
                "inflation rate. You may select a historical dataset to load "
                "a corresponding set of assumptions, or edit individual "
                "values directly. Selecting a dataset immediately replaces "
                "the displayed market assumptions."
            ),
            "screen_callback": gui.edit_simulation_assumptions,
        },
        {
            "title": "Simulation -> Settings",
            "section_title": "What to review",
            "text": (
                "Settings defines the simulation period and portfolio "
                "mechanics. Review the starting year, number of years, and "
                "number of simulation runs. Fund expenses can be included as "
                "an annual percentage. Rebalancing can maintain the current "
                "allocation, use a preset allocation, use a custom stock, "
                "bond, and cash allocation, or remain disabled."
            ),
            "screen_callback": gui.edit_simulation_settings,
        },
        {
            "title": "Simulation -> Controls: Display and Annotation",
            "section_title": "What to review",
            "text": (
                "This part of Simulation Controls changes how results are "
                "presented. Choose Real for inflation-adjusted values or Raw "
                "for nominal values. Constant Y Plots can make comparisons "
                "between plots easier. Overlays can add taxes, fund expenses, "
                "household expenses, profit or loss, and retirement-age markers "
                "to selected plots. Custom Annotations lets you add your own "
                "labels to generated plots. CSV output can also be enabled when "
                "you want the underlying simulation data written to files."
            ),
            "screen_callback": gui.edit_simulation_controls,
        },
        {
            "title": "Simulation -> Controls: Plot Style",
            "section_title": "What to review",
            "text": (
                "Plot Style determines how simulation results are grouped and "
                "displayed. Fill shows the main result area, Sub Categories "
                "separates components, and Pre / Post Tax Savings separates "
                "assets by tax treatment. Selecting Percentile Bands reveals "
                "Monte Carlo and Historical Windows, two methods used to present "
                "portfolio risk across a range of possible outcomes. Monte Carlo "
                "uses simulated return paths and can use correlated asset returns. "
                "Historical Windows uses overlapping periods from the historical "
                "return data. Percentile Bands can be shown as a filled band, "
                "summary lines, or all simulation lines."
            ),
            "screen_callback": gui.edit_simulation_controls,
        },
        {
            "title": "Building the Simulation Complete",
            "section_title": "What comes next",
            "text": (
                "You have reviewed the detailed financial inputs, starting "
                "balance sheet, retirement spending models, market assumptions, "
                "simulation settings, and display controls used to build an "
                "advanced simulation. A separate Advanced tutorial will cover "
                "advanced results, Scenario Explorer, and reports. Select "
                "Finish to return to the Tutorials page."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
    ]


def build_advanced_analysis_tutorial_steps(gui):
    return [
        {
            "title": "Welcome",
            "section_title": "About this tutorial",
            "text": (
                "This tutorial introduces the advanced result plots, Scenario "
                "Explorer, and reports available in WARPSimLab. This first "
                "section concentrates on the result plots. Running a result "
                "opens a separate figure window. Review the figure, close it, "
                "return to the tutorial, and then select Next."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Mode -> Advanced",
            "section_title": "What to do",
            "text": (
                "Advanced result types, Scenario Explorer, and reports require "
                "Advanced mode. From the upper-right menu, select Mode, then "
                "select Advanced. The tutorial will remain on this step while "
                "the simulator rebuilds the screen. After Advanced mode is "
                "selected, select Next."
            ),
            "screen_callback": gui.edit_tutorial_blank,
            "can_advance": lambda: gui.mode_var.get() == "Advanced",
            "validation_message": (
                "Select Mode -> Advanced before continuing."
            ),
        },
        {
            "title": "Results Overview",
            "section_title": "What this means",
            "text": (
                "The Results menu provides several views of the same financial "
                "simulation. Income Plots show where household income comes "
                "from. Cash Flow Plots add withdrawals, investment income, "
                "expenses, and annual profit or loss. Portfolio Plots show how "
                "investable assets change over time. Operating Balance Plots "
                "show the cumulative household surplus or deficit."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Results -> Income Plots",
            "section_title": "What to do",
            "text": (
                "From the top menu, select Results, then Income Plots. With the "
                "default Fill style, the plot shows total household income over "
                "time. To separate employment income, Social Security, pensions, "
                "annuities, and special income, first select Simulation -> Controls "
                "and choose Sub Categories under Plot Style. Review the figure, "
                "close it, and return here."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Results -> Cash Flow Plots",
            "section_title": "What to do",
            "text": (
                "From the top menu, select Results, then Cash Flow Plots. With "
                "the default Fill style, the plot shows total cash flow together "
                "with the annual surplus or shortfall. To separate ordinary income, "
                "portfolio withdrawals, RMDs, interest, dividends, and other "
                "components, first select Simulation -> Controls and choose Sub "
                "Categories under Plot Style. Review the figure, close it, and "
                "return here."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Results -> Portfolio Plots",
            "section_title": "What to do",
            "text": (
                "From the top menu, select Results, then Portfolio Plots. With "
                "the default Fill style, the plot shows total portfolio value over "
                "time. To separate stocks, bonds, and cash, first select "
                "Simulation -> Controls and choose Sub Categories under Plot Style. "
                "Watch for the portfolio's peak, the effect of retirement "
                "withdrawals, and whether assets approach or fall below zero."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Portfolio Plot Styles",
            "section_title": "What to review",
            "text": (
                "Portfolio Plots reflect the Plot Style selected under "
                "Simulation -> Controls. Fill presents the primary portfolio "
                "projection. Sub Categories separates portfolio components. "
                "Percentile Bands presents portfolio risk across many possible "
                "outcomes using Monte Carlo simulations or Historical Windows. "
                "The bands show the spread of results, while the median line "
                "shows the middle projected outcome."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Results -> Operating Balance Plots",
            "section_title": "What to do",
            "text": (
                "From the top menu, select Results, then Operating Balance "
                "Plots. This view shows the running total of household cash flow "
                "after income, taxes, and expenses. After-tax investment returns "
                "may appear as income, while changes in portfolio market value are "
                "not treated as operating cash flow. Positive values represent an "
                "accumulated operating surplus. Negative values show a cumulative "
                "deficit that must be funded from available assets."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Results -> Scenario Explorer",
            "section_title": "What to do",
            "text": (
                "From the top menu, select Results, then Scenario Explorer. "
                "Scenario Explorer opens a Scenario Dashboard plus separate "
                "cash flow and portfolio plot windows. The dashboard uses "
                "temporary copies of the current financial data, so moving its "
                "sliders does not change the saved scenario or the values in "
                "the main WARPSimLab screens."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Scenario Explorer -> Change One Assumption",
            "section_title": "What to do",
            "text": (
                "Move one Scenario Dashboard slider, such as Percent Stock, "
                "retirement age, inflation, fund expenses, market adjustment, "
                "or the expense or withdrawal setting. The scenario reruns "
                "automatically after the change, and both plot windows update. "
                "Changing one assumption at a time makes it easier to understand "
                "which input caused the result."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Scenario Explorer -> Plot Detail",
            "section_title": "What to review",
            "text": (
                "The Scenario Explorer plots follow the Plot Style selected under "
                "Simulation -> Controls. Fill shows total cash flow and total "
                "portfolio value. Sub Categories separates the underlying income "
                "and portfolio components. Annotate Plots adds a summary of the "
                "temporary assumptions directly to each figure."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Scenario Explorer -> Compare and Resync",
            "section_title": "What to do",
            "text": (
                "Use the Mode list in the Scenario Dashboard to select Compare "
                "Cashflow or Compare Portfolio. The left figure shows the Original "
                "result and the right figure shows the Changed result using matching "
                "axes for direct comparison. Resync discards the temporary changes "
                "and reloads the current main WARPSimLab values. Select Stop when "
                "you are finished with Scenario Explorer."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Reports -> Executive Summary",
            "section_title": "What to do",
            "text": (
                "From the top menu, select Reports, then Executive Summary. "
                "This opens a configuration screen rather than generating the "
                "report immediately. Use the checkboxes to choose which summaries, "
                "plots, risk analyses, and appendices will be included."
            ),
            "screen_callback": gui.edit_report_executive_summary,
        },
        {
            "title": "Executive Summary -> Select Content",
            "section_title": "What to review",
            "text": (
                "The Executive Summary can include the simulation summary, normal "
                "and sub-category portfolio projections, Historical Windows or "
                "Monte Carlo analysis, income visuals, cashflow visuals, cumulative "
                "operating balance, and an assumptions appendix. Selecting many "
                "visuals produces a longer report. HTML is the current supported "
                "output format; PDF is marked as a future option."
            ),
            "screen_callback": gui.edit_report_executive_summary,
        },
        {
            "title": "Executive Summary -> Generate Report",
            "section_title": "What to do",
            "text": (
                "After selecting the desired sections, select Apply. WARPSimLab "
                "saves the report options, runs the current simulation, and writes "
                "an HTML report to Desktop\\WARPSimLab\\Reports. Open the generated "
                "report in your browser and review its highlights, tables, plots, "
                "risk results, and assumptions. Then return to the tutorial."
            ),
            "screen_callback": gui.edit_report_executive_summary,
        },
        {
            "title": "Reports -> Year-by-Year Details",
            "section_title": "What to review",
            "text": (
                "From the top menu, select Reports, then Year-by-Year Details. "
                "This report follows one deterministic simulation path and shows "
                "how income, taxes, expenses, withdrawals, cash flow, portfolio "
                "value, and net worth change each year. Compact provides fewer "
                "high-level columns, while Detailed expands the income, tax, "
                "cash-flow, and portfolio information. You can generate HTML, CSV, "
                "or both, and optionally insert a visual break every five years."
            ),
            "screen_callback": gui.edit_report_year_by_year_details,
        },
        {
            "title": "Reports -> Tax Report",
            "section_title": "What to review",
            "text": (
                "From the top menu, select Reports, then Tax Report. This report "
                "explains how estimated federal, state, and payroll taxes evolve "
                "throughout the simulation. Optional sections analyze Roth assets, "
                "HSA assets, required minimum distributions, and educational tax "
                "commentary. The report can be generated as HTML, CSV, or both. "
                "The underlying tax calculation settings remain under "
                "Cash Flow -> Taxes."
            ),
            "screen_callback": gui.edit_report_taxes,
        },
        {
            "title": "Reports -> Portfolio Risk Reports",
            "section_title": "What to review",
            "text": (
                "The Historical Window Risk Report and Monte Carlo Risk Report "
                "evaluate portfolio sustainability across many market paths. "
                "Historical Window analysis replays rolling periods of actual "
                "historical market returns and inflation. Monte Carlo analysis uses "
                "statistically generated return paths based on the selected market "
                "assumptions. Both reports can include an executive summary, method "
                "explanation, portfolio projection, sustainability analysis, "
                "method-specific insights, and a percentile portfolio table. Their "
                "simulation settings remain under Simulation; these report screens "
                "control report contents and HTML or CSV output."
            ),
            "screen_callback": gui.edit_report_historical_window_risk,
        },
        {
            "title": "Advanced Results Tutorial Complete",
            "section_title": "What comes next",
            "text": (
                "You have completed the advanced results tutorial. You reviewed "
                "the primary result plots, experimented with temporary assumptions "
                "in Scenario Explorer, generated an Executive Summary, and examined "
                "the detailed, tax, and portfolio-risk reports. These tools provide "
                "different levels of analysis, from a quick visual review to annual "
                "detail and broad uncertainty testing. Select Finish to return to "
                "the Tutorials page."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
    ]