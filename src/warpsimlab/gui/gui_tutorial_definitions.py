def build_basic_tutorial_steps(gui):
    return [
        {
            "title": "Welcome",
            "section_title": "About this tutorial",
            "text": (
                "WARPSimLab has two operating modes: Basic and Advanced. This tutorial "
                "automatically selects Basic mode, which presents a simplified "
                "interface. The Mode menu in the upper-right corner lets you switch "
                "modes. Changing modes does not reset your financial data.\n\n"
                "This tutorial uses the financial values currently loaded. The buttons "
                "across the top open menus containing the individual screens. For "
                "example, Household contains Age & Longevity, Normal Income, and "
                "Expenses.\n\n"
                "The tutorial opens the relevant input screens automatically. Use Next "
                "and Back to move between steps. If the instructions cover part of a "
                "screen, select Hide Instructions. Select Next to begin."
            ),
            "screen_callback": gui.edit_main_home,
        },
        {
            "title": "Household -> Age & Longevity",
            "section_title": "What to review",
            "text": (
                "Review the current household ages. Enable Second Person if you want to "
                "model two people.\n\n"
                "The Simulation Horizon section determines how long the simulation runs. "
                "For this introductory tutorial, you can leave the existing horizon "
                "settings unchanged."
            ),
            "screen_callback": gui.edit_age_longevity,
        },
        {
            "title": "Household -> Normal Income",
            "section_title": "What to review",
            "text": (
                "Review each person's annual earned income, retirement age, and annual "
                "Social Security benefit. You may edit these values during the tutorial. "
                "Current ages and household membership are configured under Household -> "
                "Age & Longevity."
            ),
            "screen_callback": gui.edit_person_data,
        },
        {
            "title": "Household -> Expenses",
            "section_title": "What to review",
            "text": (
                "Expenses define yearly household spending. Each expense can have a "
                "start year, an optional end year, an annual cost, and a comment. Taxes "
                "are calculated separately by the simulator. You may edit or add "
                "expenses here."
            ),
            "screen_callback": gui.edit_expenses,
        },
        {
            "title": "Balance Sheet -> Portfolio - Amounts",
            "section_title": "What to review",
            "text": (
                "In Basic mode, Portfolio - Amounts presents a simplified Savings ($) "
                "entry for each household member. This entry represents taxable cash and "
                "savings, not every type of investment account. The totals reflect the "
                "portfolio balances. Advanced mode exposes the individual investment and "
                "tax categories.\n\n"
                "Review the current values and select Next when ready to run the "
                "simulation."
            ),
            "screen_callback": gui.edit_portfolio_data,
        },
        {
            "title": "Results -> Simulation Summary",
            "section_title": "What to do",
            "text": (
                "Now run the simulation yourself. From the top menu, select Results, "
                "then select Simulation Summary. WARPSimLab will run the current "
                "financial example and open a separate Simulation Summary window. \n\n"
                "Return to this tutorial and select Next, leaving the "
                "Simulation Summary window open."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Simulation Summary -> Four Tabs",
            "section_title": "What to review",
            "text": (
                "The Simulation Summary window has four tabs. Select Portfolio to review "
                "assets at selected points in the simulation. Select Income to review "
                "wages, Social Security, pensions, and other income. Select Cash Flow to "
                "review taxes, expenses, and net cash flow. Select Summary to review "
                "overall results and simulation assumptions.\n\n"
                "Review the four tabs, close the window, and return here.  Select Next."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Household -> Expenses",
            "section_title": "What to do",
            "text": (
                "Now change one input and compare the results. Change one annual expense "
                "by a noticeable but reasonable amount. Select Results -> Simulation "
                "Summary to run the simulation again. Review the Portfolio, Cash Flow, "
                "and Summary tabs and compare them with the earlier results. Changing "
                "one value at a time makes it easier to understand cause and effect. "
                "Close the summary window and return here."
            ),
            "screen_callback": gui.edit_expenses,
        },
        {
            "title": "File -> Save Financial Data",
            "section_title": "What to do",
            "text": (
                "WARPSimLab does not automatically preserve your changes after the "
                "program closes. To keep your current financial data, select File "
                "from the top menu, then select Save Financial Data. Choose a file name "
                "and location you will recognize later. To restore a saved scenario in "
                "another session, select File, followed by Load Financial Data. Saving "
                "is optional for this tutorial."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Basic Tutorial Complete",
            "section_title": "What comes next",
            "text": (
                "You have reviewed the primary Basic mode inputs, run the simulation, "
                "explored the Simulation Summary, changed one input, compared the "
                "results, and learned how to save a scenario. Continue exploring in "
                "Basic mode, or select Mode from the upper-right menu and then select "
                "Advanced to reveal additional inputs, simulation controls, results, and "
                "reports. Select Finish to return to the Tutorials page."
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
                "This tutorial introduces the screens used to build and configure an "
                "advanced WARPSimLab simulation. It automatically selects Advanced mode. "
                "You can switch modes using the Mode menu in the upper-right corner.\n\n"
                "The tutorial uses the financial values currently loaded and does not "
                "reset them. You may edit values while following the tutorial. The "
                "relevant screens open automatically. Use Hide Instructions if the "
                "instructions cover a control. Select Next to continue."
            ),
            "screen_callback": gui.edit_main_home,
        },
        {
            "title": "Advanced Mode Orientation",
            "section_title": "What this means",
            "text": (
                "Advanced mode adds detailed household income, portfolio categories, "
                "real estate, retirement modeling, simulation assumptions and controls, "
                "additional results, Scenario Explorer, and reports. This tutorial "
                "concentrates on building the financial model and configuring the "
                "simulation. The Advanced Analysis Tutorial covers results and reports."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Household -> Age & Longevity",
            "section_title": "What to review",
            "text": (
                "Enter the current age of each person and choose how long "
                "the simulation should run. Four options are available:\n\n"
                "Fixed simulation horizon: Enter the number of years to simulate.\n\n"
                "Average longevity: Simulate to the age that half of people "
                "your current age are expected to reach.\n\n"
                "Longer-life planning: Simulate to the age that only one "
                "in four people your current age are expected to reach.\n\n"
                "Custom modeled death age: Enter your own estimated age "
                "at death for each person.\n\n"
                "The last three options also allow the simulation to show "
                "how household finances change after one person dies."
            ),
            "screen_callback": gui.edit_age_longevity,
        },
        {
            "title": "Household -> Normal Income",
            "section_title": "What to review",
            "text": (
                "Review annual earned income, retirement ages, Social Security amounts "
                "and starting ages, pensions, pension inflation adjustments, and "
                "annuities. Advanced mode also exposes retirement and HSA contributions "
                "and employer contributions.\n\n"
                "Review the timing as well as the dollar amounts. Current ages are "
                "entered under Age & Longevity."
            ),
            "screen_callback": gui.edit_person_data,
        },
        {
            "title": "Household -> Special Income",
            "section_title": "What to review",
            "text": (
                "Special Income models additional income streams beyond normal "
                "employment and retirement income. Review the available timing and "
                "income options. These streams can represent income that does not fit "
                "the Normal Income screen."
            ),
            "screen_callback": gui.edit_special_income,
        },
        {
            "title": "Household -> Roth Contributions / Conversions",
            "section_title": "What to review",
            "text": (
                "Review the options for modeling Roth contributions and conversions from "
                "tax-deferred accounts. These transactions affect balances among account "
                "types and may affect taxable income and future retirement withdrawals."
            ),
            "screen_callback": gui.edit_roth,
        },
        {
            "title": "Household -> Expenses",
            "section_title": "What to review",
            "text": (
                "Review annual expense amounts, start and end years, and comments. Use "
                "separate expense entries to represent spending that changes over time "
                "or occurs in a particular year. Review any HSA-eligible expenses; these "
                "can be funded from available HSA assets. Taxes and modeled Medicare "
                "costs are handled separately."
            ),
            "screen_callback": gui.edit_expenses,
        },
        {
            "title": "Household -> Medicare & IRMAA",
            "section_title": "What to review",
            "text": (
                "Configure Medicare starting ages and estimated annual Medicare costs "
                "for each enabled household member. WARPSimLab can also model "
                "income-related Medicare surcharges (IRMAA). These generally use "
                "modified adjusted gross income (MAGI) from two years earlier. "
                "Historical MAGI inputs support the initial simulation years."
            ),
            "screen_callback": gui.edit_medicare_irmaa,
        },
        {
            "title": "Household -> Taxes",
            "section_title": "What to review",
            "text": (
                "Review the available tax calculation settings. Taxes affect household "
                "cash flow, withdrawals, and portfolio sustainability. WARPSimLab "
                "estimates taxes for financial simulation purposes; it is not a tax "
                "preparation program."
            ),
            "screen_callback": gui.edit_taxes,
        },
        {
            "title": "Balance Sheet -> Portfolio - Amounts",
            "section_title": "What to review",
            "text": (
                "Advanced mode separates investable assets by tax treatment and asset "
                "class. Enter stocks, bonds, and cash in the Tax-Deferred, Taxable, "
                "Roth, and HSA sections. Values are separated by person when Enable "
                "Second Person is selected. Household and portfolio totals are "
                "calculated automatically. Real estate is entered separately."
            ),
            "screen_callback": gui.edit_portfolio_data,
        },
        {
            "title": "Balance Sheet -> Portfolio - Percentages",
            "section_title": "What to review",
            "text": (
                "This is an alternative way to enter the same investable portfolio "
                "balances. Enter total investable assets for each person, the percentage "
                "in each tax bucket, and the stock, bond, and cash allocation within "
                "each bucket.\n\n"
                "Changes are temporary until you select Apply Percentages. Applying "
                "changes updates the underlying dollar balances used by Portfolio - "
                "Amounts. If you are only reviewing the screen, leave the values "
                "unchanged."
            ),
            "screen_callback": gui.edit_portfolio_percentages,
        },
        {
            "title": "Balance Sheet -> Real Estate",
            "section_title": "What to review",
            "text": (
                "Real estate is entered separately from the investable portfolio. Enter "
                "the current real estate value assigned to each person. The Total column "
                "is calculated automatically. These values are included in balance sheet "
                "and wealth calculations, but they remain separate from stocks, bonds, "
                "cash, Roth assets, and other investable accounts."
            ),
            "screen_callback": gui.edit_real_estate,
        },
        {
            "title": "Balance Sheet -> Derived Statistics",
            "section_title": "What to review",
            "text": (
                "Derived Statistics is a read-only review screen. It combines the "
                "portfolio and real estate values already entered. Review total "
                "investable assets, real estate, and total wealth. The screen also shows "
                "the percentage of investable assets in each tax bucket and in stocks, "
                "bonds, and cash. Use these values to check that the starting balance "
                "sheet reflects your intent."
            ),
            "screen_callback": gui.edit_derived_statistics,
        },
        {
            "title": "Retirement -> Withdrawal Strategies",
            "section_title": "What to review",
            "text": (
                "WARPSimLab supports two approaches to retirement spending:\n\n"
                "Manually Entered Expenses: Continue using the expenses "
                "entered under Household -> Expenses throughout retirement.\n\n"
                "Automatically Calculated Withdrawals: Determine retirement "
                "spending using percentage-based or fixed-dollar portfolio "
                "withdrawals, with optional inflation adjustments.\n\n"
                "Review the available withdrawal methods and the order "
                "in which money is withdrawn from the different accounts."
            ),
            "screen_callback": gui.edit_withdrawal_strategies,
        },
        {
            "title": "Retirement -> RMDs & QCDs",
            "section_title": "What to review",
            "text": (
                "Required Minimum Distributions (RMDs) are mandatory withdrawals from "
                "eligible tax-deferred retirement accounts. Qualified Charitable "
                "Distributions (QCDs) are eligible charitable distributions that can "
                "satisfy part or all of an RMD while reducing taxable distributions.\n\n"
                "Review the available settings for modeling these transactions during "
                "retirement."
            ),
            "screen_callback": gui.edit_rmd_qcd,
        },
        {
            "title": "Retirement -> Sequence-of-Returns Scenarios",
            "section_title": "What to review",
            "text": (
                "Sequence-of-Returns Scenarios allow you to examine the effects of a "
                "market downturn at different points in the simulation. Review the "
                "timing, duration, and severity settings. A downturn near retirement can "
                "have different consequences from an otherwise similar downturn later in "
                "retirement."
            ),
            "screen_callback": gui.edit_sequence_risk,
        },
        {
            "title": "Simulation -> Assumptions",
            "section_title": "What to review",
            "text": (
                "Assumptions defines the market environment used by the simulation. "
                "Review the expected yearly gains and volatility for stocks, bonds, "
                "cash, and real estate, along with the inflation rate. You may select a "
                "historical dataset to load a corresponding set of assumptions, or edit "
                "individual values directly. Selecting a dataset immediately replaces "
                "the displayed market assumptions."
            ),
            "screen_callback": gui.edit_simulation_assumptions,
        },
        {
            "title": "Simulation -> Settings",
            "section_title": "What to review",
            "text": (
                "Review the simulation start year, number of Monte Carlo simulations, "
                "and optional annual fund expenses. The simulation horizon is configured "
                "under Household -> Age & Longevity.\n\n"
                "Starting Portfolio Allocation determines whether the simulation uses "
                "the original stock, bond, and cash allocations or a preset or custom "
                "alternative. Use Original Allocations preserves the allocation of each "
                "investment account.\n\n"
                "Rebalance Every Year is a separate setting. When enabled, each account "
                "is restored to its starting allocation at the end of each simulation "
                "year. Otherwise, allocations can drift as returns differ."
            ),
            "screen_callback": gui.edit_simulation_settings,
        },
        {
            "title": "Simulation -> Controls: Display and Annotation",
            "section_title": "What to review",
            "text": (
                "Simulation Controls determines how results are presented, exported, and "
                "annotated. Real (inflation-adjusted) and Raw (nominal) select the "
                "dollar basis. Constant Y Plots makes plot comparisons easier. Overlays "
                "add information to applicable plots, and Custom Annotations adds your "
                "own labels. Review Include Real Estate in Simulation if you want to "
                "include real estate in the applicable simulation results."
            ),
            "screen_callback": gui.edit_simulation_controls,
        },
        {
            "title": "Simulation -> Controls: Plot Style",
            "section_title": "What to review",
            "text": (
                "Plot Style determines how results are displayed. Fill shows a single "
                "simulation result. Sub Categories separates components. Tax-Deferred / "
                "Taxable Savings separates portfolio results by tax treatment.\n\n"
                "Risk Analysis offers Monte Carlo and Historical Windows. Monte Carlo "
                "uses simulated return paths, with an option for correlated asset "
                "returns. Historical Windows uses historical return sequences. The Risk "
                "Analysis Plot Style controls whether the results appear as filled "
                "bands, summary lines, or all simulation lines."
            ),
            "screen_callback": gui.edit_simulation_controls,
        },
        {
            "title": "Building the Simulation Complete",
            "section_title": "What comes next",
            "text": (
                "You have reviewed household inputs, investable assets and real estate, "
                "retirement spending, RMDs and QCDs, market assumptions, simulation "
                "settings, and display controls. The Advanced Analysis Tutorial covers "
                "results, Scenario Explorer, and reports. Select Finish to return to the "
                "Tutorials page."
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
                "This tutorial introduces advanced result plots, Scenario Explorer, and "
                "reports. It automatically selects Advanced mode. You can switch modes "
                "using the Mode menu in the upper-right corner.\n\n"
                "The tutorial uses the currently loaded financial values. Running a plot "
                "opens a separate window. Review the result, close it, and return to the "
                "tutorial. Report configuration screens open automatically. Select Next "
                "to continue."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Results Overview",
            "section_title": "What this means",
            "text": (
                "The Results menu provides several views of the same financial "
                "simulation. Income Plots show household income. Cash Flow Plots show "
                "cash inflows, outflows, and the annual surplus or shortfall. Portfolio "
                "Plots show changes in investable assets. Cumulative Operating Balance "
                "shows accumulated operating cash flow."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Results -> Scenario Explorer",
            "section_title": "What to do",
            "text": (
                "Select Results -> Scenario Explorer. Scenario Explorer opens the "
                "Scenario Dashboard and separate plot windows. Its controls use "
                "temporary copies of the current financial data. Changing a scenario "
                "does not modify the financial inputs in the main WARPSimLab window."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Scenario Explorer -> Change One Assumption",
            "section_title": "What to do",
            "text": (
                "Move one Scenario Dashboard slider, such as stock percentage, "
                "retirement age, inflation, or spending. The scenario reruns "
                "automatically and the results and plots update. Changing one assumption "
                "at a time makes it easier to understand its effect. The inflation "
                "slider changes nominal return assumptions along with inflation, leaving "
                "real return assumptions unchanged."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Scenario Explorer -> Plot Detail",
            "section_title": "What to review",
            "text": (
                "The Plot Style control offers Fill, Historical Risk, Sub Categories, "
                "and Tax-Deferred / Taxable Savings. Fill shows the main result areas, "
                "Sub Categories separates components, and Historical Risk displays risk "
                "across historical return sequences. The Rebalancing control "
                "independently selects Annual Rebalancing or Not Rebalancing."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Scenario Explorer -> Compare and Resync",
            "section_title": "What to do",
            "text": (
                "Use Mode to select Compare Income, Compare Cash Flow, or Compare "
                "Portfolio. Compare the original and changed results on matching axes. "
                "Reset Scenario discards the temporary changes and reloads the current "
                "main WARPSimLab values. Select Close Explorer when finished."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Results -> Income Plots",
            "section_title": "What to do",
            "text": (
                "Select Results -> Income Plots. Fill shows household income over time. "
                "Sub Categories separates sources such as employment income, Social "
                "Security, pensions, annuities, and special income. Plot Style is "
                "configured under Simulation -> Controls. Review the plot and close it "
                "before continuing."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Results -> Cash Flow Plots",
            "section_title": "What to do",
            "text": (
                "Select Results -> Cash Flow Plots. Review the cash inflows, outflows, "
                "and annual surplus or shortfall. Sub Categories provides a more "
                "detailed view of the components. Plot Style is configured under "
                "Simulation -> Controls. Review the plot and close it before continuing."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Results -> Portfolio Plots",
            "section_title": "What to do",
            "text": (
                "Select Results -> Portfolio Plots. Fill shows portfolio value over "
                "time. Sub Categories separates stocks, bonds, and cash. Watch how the "
                "portfolio changes before and after retirement and whether available "
                "assets become depleted. Review the plot and close it before continuing."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Portfolio Plot Styles",
            "section_title": "What to review",
            "text": (
                "Under Simulation -> Controls, Plot Style offers Fill, Sub Categories, "
                "Tax-Deferred / Taxable Savings, and Risk Analysis. Select Risk Analysis "
                "to model a range of outcomes using Monte Carlo or Historical Windows. "
                "Filled bands and summary lines show the spread of outcomes; the median "
                "represents the middle outcome. The all_lines style shows individual "
                "simulation paths."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Results -> Cumulative Operating Balance",
            "section_title": "What to do",
            "text": (
                "Select Results -> Cumulative Operating Balance. This plot shows "
                "accumulated household operating cash flow. Positive values represent "
                "accumulated operating surplus; negative values represent accumulated "
                "operating shortfall. This is not a separate investment account or a "
                "measure of total portfolio wealth."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
        {
            "title": "Reports -> Executive Summary",
            "section_title": "What to do",
            "text": (
                "The Executive Summary combines simulation summaries, selected plots, "
                "risk analyses, and supporting information in one report. The "
                "configuration screen opens automatically. Review the options before "
                "generating the report."
            ),
            "screen_callback": gui.edit_report_executive_summary,
        },
        {
            "title": "Executive Summary -> Select Content",
            "section_title": "What to review",
            "text": (
                "The Executive Summary can include the simulation summary, normal and "
                "sub-category portfolio projections, Historical Windows or Monte Carlo "
                "analysis, income visuals, cashflow visuals, cumulative operating "
                "balance, and an assumptions appendix. Selecting many visuals produces a "
                "longer report. HTML is the current supported output format; PDF is "
                "marked as a future option."
            ),
            "screen_callback": gui.edit_report_executive_summary,
        },
        {
            "title": "Executive Summary -> Generate Report",
            "section_title": "What to do",
            "text": (
                "After selecting the desired content, select Apply to generate the "
                "report. Review the resulting HTML report in your browser, including its "
                "highlights, tables, plots, risk results, and assumptions. Return to the "
                "tutorial when finished."
            ),
            "screen_callback": gui.edit_report_executive_summary,
        },
        {
            "title": "Reports -> Year-by-Year Details",
            "section_title": "What to review",
            "text": (
                "The Year-by-Year Details report follows a deterministic simulation "
                "path. Review annual income and cash flow, taxes, expenses, withdrawals, "
                "and portfolio balances. The Income/Cash Flow and Portfolio sections "
                "provide complementary views of the simulation. Choose the desired "
                "report options and output format."
            ),
            "screen_callback": gui.edit_report_year_by_year_details,
        },
        {
            "title": "Reports -> Tax and Medicare Report",
            "section_title": "What to review",
            "text": (
                "The Tax and Medicare Report shows estimated federal, state, and payroll "
                "taxes, Medicare costs, and IRMAA over the simulation. It also provides "
                "information about relevant retirement account transactions and tax "
                "assumptions. Review the available report options. Tax and Medicare "
                "settings are configured under Household -> Taxes and Household -> "
                "Medicare & IRMAA."
            ),
            "screen_callback": gui.edit_report_taxes,
        },
        {
            "title": "Reports -> Historical Window Risk Report",
            "section_title": "What to review",
            "text": (
                "Historical Window Risk evaluates the portfolio across rolling periods "
                "of historical market returns and inflation. Review how portfolio "
                "outcomes and sustainability differ depending on the historical period. "
                "Select the desired report options and generate the report if you wish."
            ),
            "screen_callback": gui.edit_report_historical_window_risk,
        },
        {
            "title": "Reports -> Monte Carlo Risk Report",
            "section_title": "What to review",
            "text": (
                "Monte Carlo Risk evaluates portfolio outcomes across statistically "
                "generated return paths. Review the distribution of outcomes and the "
                "modeled sustainability of the portfolio. Compare this approach with "
                "Historical Window Risk, which uses actual historical return sequences."
            ),
            "screen_callback": gui.edit_report_monte_carlo_risk,
        },
        {
            "title": "Reports -> Spending Comparison Report",
            "section_title": "What to review",
            "text": (
                "This report compares the modeled consequences of alternative spending "
                "assumptions. It is available only when manually entered expenses are "
                "used. If you are using withdrawal-based retirement spending, the report "
                "is unavailable and this step can be skipped.\n\n"
                "If available, review the comparison options. The report provides "
                "evidence for evaluating spending choices rather than choosing a "
                "spending level for you."
            ),
            "screen_callback": lambda: (
                gui.edit_report_spending_comparison()
                if gui.simulation_controls.get("use_mode", "expenses") == "expenses"
                else gui.edit_tutorial_blank()
            ),
        },
        {
            "title": "Reports -> Asset Allocation Comparison Report",
            "section_title": "What to review",
            "text": (
                "This report compares alternative stock, bond, and cash allocations "
                "using historical-window analysis. Review the available allocations and "
                "report options. Compare portfolio outcomes and risk across the "
                "alternatives; the report does not select an allocation for you."
            ),
            "screen_callback": gui.edit_report_asset_allocation_comparison,
        },
        {
            "title": "Reports -> Retirement & Social Security Comparison Report",
            "section_title": "What to review",
            "text": (
                "This report compares the modeled effects of alternative retirement and "
                "Social Security starting ages. Review the available timing choices and "
                "compare the resulting financial outcomes. The report provides "
                "information for evaluating alternatives rather than selecting "
                "retirement or claiming ages for you."
            ),
            "screen_callback": gui.edit_report_retirement_ss_comparison,
        },
        {
            "title": "Advanced Results Tutorial Complete",
            "section_title": "What comes next",
            "text": (
                "You have reviewed the primary result plots, experimented with temporary "
                "assumptions in Scenario Explorer, and explored summary, detailed, tax, "
                "risk, and comparison reports. These tools provide different levels of "
                "analysis, from a quick visual review to annual detail and broad "
                "uncertainty testing. Select Finish to return to the Tutorials page."
            ),
            "screen_callback": gui.edit_tutorial_blank,
        },
    ]
