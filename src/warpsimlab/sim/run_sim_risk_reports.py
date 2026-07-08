# run_sim_risk_reports.py

from datetime import datetime
import os

import numpy as np

from src.warpsimlab.reports.report_data import RiskReportData
from src.warpsimlab.reports.risk_report import generate_risk_report


from src.warpsimlab.reports.report_plot_helpers import (
    save_portfolio_projection_report_plot,
    save_historical_window_highlight_report_plot,
)

def _run_risk_pipeline_with_temporary_modes(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
    *,
    monte_carlo_mode,
):
    from .simulation import run_pipeline

    original_subplot_mode = getattr(sim_config, "subplot_mode", None)
    original_sim_type = getattr(sim_config, "sim_type", None)
    original_monte_carlo_mode = getattr(sim_config, "monte_carlo_mode", None)
    original_include_realestate = getattr(sim_config, "include_realestate", None)
    original_show_simulated_shortfall_rate = getattr(
        sim_config,
        "show_simulated_shortfall_rate",
        None,
    )

    try:
        sim_config.subplot_mode = "monte_carlo"
        sim_config.sim_type = "portfolio_sim"

        if monte_carlo_mode is not None:
            sim_config.monte_carlo_mode = monte_carlo_mode

        # Risk reports measure depletion of liquid/investment portfolio assets.
        # Real estate is excluded by default to match Monte Carlo and Historical Window plots.
        sim_config.include_realestate = False

        # Risk reports will calculate failure statistics from the primary
        # multi-path result. Do not let run_pipeline launch any extra helper runs.
        sim_config.show_simulated_shortfall_rate = False

        result = run_pipeline(
            husband_portfolio,
            wife_portfolio,
            husband,
            wife,
            expenses,
            sim_config,
            force_num_sims=None,
        )

        return _build_and_generate_risk_report(
            result,
            sim_config,
            husband,
            wife,
            monte_carlo_mode=monte_carlo_mode,
        )

    finally:
        sim_config.subplot_mode = original_subplot_mode
        sim_config.sim_type = original_sim_type
        sim_config.monte_carlo_mode = original_monte_carlo_mode
        sim_config.include_realestate = original_include_realestate
        sim_config.show_simulated_shortfall_rate = original_show_simulated_shortfall_rate


def _as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rate(success_count, total_count):
    if total_count <= 0:
        return 0.0
    return 100.0 * float(success_count) / float(total_count)


def _safe_report_method(monte_carlo_mode):
    if monte_carlo_mode == "rollingHistoricalWindows":
        return "Historical Windows"
    if monte_carlo_mode == "pathBasedAnnualSampling":
        return "Monte Carlo"
    return str(monte_carlo_mode)


def _build_report_metadata(sim_config, method):
    start_year = int(getattr(sim_config, "start_year", 0))
    years = int(getattr(sim_config, "years_to_simulate", 0))
    end_year = start_year + years

    timestamp = datetime.now().isoformat(timespec="seconds")
    report_id = f"{method.lower().replace(' ', '_')}_{timestamp.replace(':', '').replace('-', '')}"

    return {
        "Report Title": f"{method} Risk Report",
        "Generated Timestamp": timestamp,
        "Projection Period": f"{start_year}-{end_year} ({years} Years)",
        "Report Basis": (
            "Real Dollars (Inflation Adjusted)"
            if getattr(sim_config, "plot_mode", None) == "real"
            else "Raw Dollars (Future Nominal Values)"
        ),
        "Report ID": report_id,
    }


def _build_simulation_snapshot(sim_config, method, scenario_count):
    return {
        "Analysis Method": method,
        "Scenario Count": scenario_count,
        "Start Year": getattr(sim_config, "start_year", None),
        "Years Simulated": getattr(sim_config, "years_to_simulate", None),
        "Plot Mode": getattr(sim_config, "plot_mode", None),
        "Monte Carlo Mode": getattr(sim_config, "monte_carlo_mode", None),
        "Historical Asset Returns File": getattr(sim_config, "historical_asset_returns_file", None),
        "Historical Inflation File": getattr(sim_config, "historical_inflation_file", None),
        "Historical Window Mode": getattr(sim_config, "historical_window_mode", None),
    }


def _first_failure_year(path, years):
    failed_indices = np.where(path <= 0.0)[0]

    if len(failed_indices) == 0:
        return None

    index = int(failed_indices[0])

    try:
        return int(years[index])
    except (IndexError, TypeError, ValueError):
        return index


def _build_failure_statistics(total_assets, years):
    total_assets = np.asarray(total_assets, dtype=float)
    years = np.asarray(years)

    scenario_count = int(total_assets.shape[0])

    failed_mask = np.any(total_assets <= 0.0, axis=1)
    failure_count = int(np.sum(failed_mask))
    success_count = int(scenario_count - failure_count)

    failure_years = []

    for path in total_assets[failed_mask]:
        failure_year = _first_failure_year(path, years)
        if failure_year is not None:
            failure_years.append(failure_year)

    stats = {
        "Scenario Count": scenario_count,
        "Portfolio Survived Count": success_count,
        "Portfolio Depleted Count": failure_count,
        "Portfolio Survival Rate": _rate(success_count, scenario_count),
        "Simulated Shortfall Rate": _rate(failure_count, scenario_count),
    }

    if failure_years:
        stats.update({
            "Earliest Portfolio Depletion Year": int(min(failure_years)),
            "Median Portfolio Depletion Year": int(np.median(failure_years)),
            "Latest Portfolio Depletion Year": int(max(failure_years)),
        })
    else:
        stats.update({
            "Earliest Portfolio Depletion Year": None,
            "Median Portfolio Depletion Year": None,
            "Latest Portfolio Depletion Year": None,
        })

    return stats


def _build_percentile_table(total_assets, years):
    total_assets = np.asarray(total_assets, dtype=float)
    years = np.asarray(years)

    percentile_values = {
        "10th Percentile": np.percentile(total_assets, 10, axis=0),
        "25th Percentile": np.percentile(total_assets, 25, axis=0),
        "Median": np.percentile(total_assets, 50, axis=0),
        "75th Percentile": np.percentile(total_assets, 75, axis=0),
        "90th Percentile": np.percentile(total_assets, 90, axis=0),
    }

    rows = []

    for index, year in enumerate(years):
        row = {"Year": int(year)}

        for label, values in percentile_values.items():
            row[label] = float(values[index])

        rows.append(row)

    return rows


def _build_historical_insights(core, total_assets, failure_statistics):
    start_years = np.asarray(core.get("historical_window_start_year", []))
    end_years = np.asarray(core.get("historical_window_end_year", []))

    if len(start_years) == 0:
        return {}

    total_assets = np.asarray(total_assets, dtype=float)
    ending_values = np.asarray(total_assets[:, -1], dtype=float)

    valid_indices = np.where(start_years >= 0)[0]

    rows = []
    for index in valid_indices:
        path = total_assets[index]
        depleted = bool(np.any(path <= 0.0))

        rows.append({
            "Index": int(index),
            "Retirement Start Year": int(start_years[index]),
            "Historical Window End Year": int(end_years[index]),
            "Ending Portfolio": float(ending_values[index]),
            "Result": "Portfolio Depleted" if depleted else "Portfolio Sustained",
        })

    def first_depletion_index(path):
        depleted_indices = np.where(path <= 0.0)[0]

        if len(depleted_indices) == 0:
            return len(path)

        return int(depleted_indices[0])

    def best_sort_key(row):
        index = row["Index"]
        path = np.asarray(total_assets[index], dtype=float)

        depletion_index = first_depletion_index(path)
        path_total = float(np.sum(path))

        return (
            row["Ending Portfolio"],
            depletion_index,
            path_total,
        )

    def worst_sort_key(row):
        index = row["Index"]
        path = np.asarray(total_assets[index], dtype=float)

        depletion_index = first_depletion_index(path)
        path_total = float(np.sum(path))

        return (
            depletion_index,
            path_total,
            row["Ending Portfolio"],
        )

    sorted_best = sorted(
        rows,
        key=best_sort_key,
        reverse=True,
    )

    sorted_worst = sorted(
        rows,
        key=worst_sort_key,
    )

    best = sorted_best[:5]
    worst = sorted_worst[:5]

    return {
        "Best Retirement Years": best,
        "Worst Retirement Years": worst,
        "Best Indices": [row["Index"] for row in best],
        "Worst Indices": [row["Index"] for row in worst],
        "Commentary": _generate_historical_commentary(
            failure_statistics=failure_statistics,
            ending_values=ending_values[valid_indices],
        ),
    }


def _generate_historical_commentary(failure_statistics, ending_values):
    shortfall_rate = _as_float(
        failure_statistics.get("Simulated Shortfall Rate")
    )

    ending_values = np.asarray(ending_values, dtype=float)

    if len(ending_values) == 0:
        return [
            "Historical Window results were not available for interpretation."
        ]

    worst = float(np.min(ending_values))
    median = float(np.median(ending_values))
    best = float(np.max(ending_values))

    comments = []

    if shortfall_rate < 5:
        comments.append(
            "Historically, the retirement plan demonstrated strong resilience. "
            "Only a small fraction of historical market sequences depleted the portfolio before the end of the projection period."
        )
    elif shortfall_rate < 20:
        comments.append(
            "Historical market conditions revealed some sensitivity in the retirement plan. "
            "Most historical sequences remained sustainable, but a meaningful minority placed enough pressure on withdrawals to deplete the portfolio."
        )
    elif shortfall_rate < 40:
        comments.append(
            "Historical results showed moderate portfolio sustainability risk. "
            "The plan remained funded across many historical periods, but unfavorable return and inflation sequences created material depletion risk."
        )
    elif shortfall_rate < 60:
        comments.append(
            "Historical results showed substantial variation in retirement outcomes. "
            "A large share of historical sequences depleted the portfolio, suggesting sensitivity to difficult market environments."
        )
    else:
        comments.append(
            "Historical market conditions produced significant portfolio sustainability risk. "
            "More than half of the evaluated historical sequences depleted the portfolio before the end of the projection period."
        )

    if median > 0 and best >= median * 2:
        comments.append(
            "The gap between stronger and middle-range outcomes was large. "
            "This illustrates how favorable early market returns can create a portfolio cushion that supports withdrawals later in retirement."
        )

    if worst <= 0:
        comments.append(
            "The weakest historical paths reached portfolio depletion. "
            "These scenarios illustrate sequence-of-returns risk: poor investment returns early in retirement can have lasting effects because withdrawals continue while the portfolio is under pressure."
        )

    return comments


def _build_monte_carlo_insights(total_assets):
    ending_values = np.asarray(total_assets[:, -1], dtype=float)

    return {
        "Tail Risk Summary": {
            "5th Percentile Ending Portfolio": float(np.percentile(ending_values, 5)),
            "10th Percentile Ending Portfolio": float(np.percentile(ending_values, 10)),
            "25th Percentile Ending Portfolio": float(np.percentile(ending_values, 25)),
            "Median Ending Portfolio": float(np.percentile(ending_values, 50)),
        },
        "Sequence Risk Discussion": (
            "Monte Carlo analysis creates many possible return sequences. "
            "Weak returns early in retirement can be especially damaging because withdrawals "
            "continue while the portfolio is depressed."
        ),
    }


def _build_risk_observations(failure_stats, ending_values, method):
    observations = []

    failure_rate = _as_float(failure_stats.get("Simulated Shortfall Rate"))

    if failure_rate == 0:
        observations.append("The portfolio survived every analyzed scenario.")
    elif failure_rate < 5:
        observations.append("Only a small fraction of analyzed scenarios depleted the portfolio.")
    elif failure_rate < 20:
        observations.append("The plan showed moderate depletion risk across the analyzed scenarios.")
    else:
        observations.append("The plan showed substantial depletion risk across the analyzed scenarios.")

    if len(ending_values) > 0:
        worst = float(np.min(ending_values))
        median = float(np.median(ending_values))
        best = float(np.max(ending_values))

        if best > median * 2 and median > 0:
            observations.append("Ending portfolio outcomes vary widely across scenarios.")

        if worst <= 0:
            observations.append("At least one scenario depleted the portfolio before the end of the projection.")

    if method == "Historical Windows":
        observations.append(
            "Historical Window analysis is deterministic and ranks actual historical retirement start periods."
        )
    elif method == "Monte Carlo":
        observations.append(
            "Monte Carlo analysis explores synthetic return paths and may vary between runs unless random seeding is controlled."
        )

    return observations

def _get_report_output_folder():
    return os.path.join(
        os.path.expanduser("~"),
        "Desktop",
        "WARPSimLab",
        "Reports",
    )


def _safe_report_id(report_id):
    return "".join(
        ch if ch.isalnum() or ch in {"-", "_"} else "_"
        for ch in str(report_id)
    )


def _build_risk_plot_assets(
    pipeline_result,
    report_metadata,
    sim_config,
    husband,
    wife,
    warnings,
    historical_insights=None,
):
    output_folder = _get_report_output_folder()
    safe_report_id = _safe_report_id(
        report_metadata.get("Report ID", "risk_report")
    )

    assets_folder = os.path.join(
        output_folder,
        f"risk_report_{safe_report_id}_assets",
    )

    plot_assets = {}

    try:
        image_path = save_portfolio_projection_report_plot(
            output_folder=assets_folder,
            filename="portfolio_range_projection.png",
            years_list=pipeline_result["years_list"],
            portfolio_plot_data=pipeline_result["portfolio_plot_data"],
            sim_config=sim_config,
            husband=husband,
            wife=wife,
            summary_results=None,
        )

        plot_assets["portfolio_range_projection"] = {
            "path": image_path,
            "title": "Portfolio Range Projection",
            "alt": "Portfolio range projection across analyzed scenarios",
        }

    except Exception as exc:
        warnings.append(
            f"Portfolio range projection plot could not be generated: {exc}"
        )

    if (
        getattr(sim_config, "monte_carlo_mode", None) == "rollingHistoricalWindows"
        and historical_insights
    ):
        try:
            core = pipeline_result["core"]

            image_path = save_historical_window_highlight_report_plot(
                output_folder=assets_folder,
                filename="historical_window_highlights.png",
                years_list=pipeline_result["years_list"],
                total_assets=core["total_assets"],
                start_years=core.get("historical_window_start_year", []),
                best_indices=historical_insights.get("Best Indices", []),
                worst_indices=historical_insights.get("Worst Indices", []),
                plot_mode=getattr(sim_config, "plot_mode", "real"),
            )

            plot_assets["historical_window_highlights"] = {
                "path": image_path,
                "title": "Historical Window Insights",
                "alt": "Historical portfolio paths with strongest and weakest retirement start years highlighted",
            }

        except Exception as exc:
            warnings.append(
                f"Historical Window insight plot could not be generated: {exc}"
            )

    return plot_assets


def _build_and_generate_risk_report(
    pipeline_result,
    sim_config,
    husband,
    wife,
    *,
    monte_carlo_mode,
):
    core = pipeline_result["core"]

    total_assets = np.asarray(core["total_assets"], dtype=float)
    years = np.asarray(core["year"][0])

    method = _safe_report_method(monte_carlo_mode)
    scenario_count = int(total_assets.shape[0])
    ending_values = total_assets[:, -1]

    failure_statistics = _build_failure_statistics(total_assets, years)

    analysis_summary = {
        "Analysis Method": method,
        "Scenario Count": scenario_count,
        "Years Simulated": getattr(sim_config, "years_to_simulate", None),
        "Simulated Shortfall Rate": failure_statistics.get("Simulated Shortfall Rate"),
        "Worst Ending Portfolio": float(np.min(ending_values)),
        "Median Ending Portfolio": float(np.median(ending_values)),
        "Best Ending Portfolio": float(np.max(ending_values)),
    }

    historical_insights = {}
    monte_carlo_insights = {}

    if method == "Historical Windows":
        historical_insights = _build_historical_insights(
            core,
            total_assets,
            failure_statistics,
        )

    if method == "Monte Carlo":
        monte_carlo_insights = _build_monte_carlo_insights(
            total_assets,
        )

    risk_observations = _build_risk_observations(
        failure_statistics,
        ending_values,
        method,
    )

    report_options = getattr(sim_config, "report_options", {})

    if method == "Historical Windows":
        report_options = report_options.get("historical_window_risk", report_options)
    elif method == "Monte Carlo":
        report_options = report_options.get("monte_carlo_risk", report_options)

    warnings = []
    report_metadata = _build_report_metadata(sim_config, method)

    plot_assets = _build_risk_plot_assets(
        pipeline_result=pipeline_result,
        report_metadata=report_metadata,
        sim_config=sim_config,
        husband=husband,
        wife=wife,
        warnings=warnings,
        historical_insights=historical_insights,
    )

    report_data = RiskReportData(
        report_options=report_options,
        report_metadata=report_metadata,
        simulation_snapshot=_build_simulation_snapshot(
            sim_config,
            method,
            scenario_count,
        ),
        analysis_summary=analysis_summary,

        historical_insights=historical_insights,
        monte_carlo_insights=monte_carlo_insights,
        risk_observations=risk_observations,

        percentile_table=_build_percentile_table(total_assets, years),
        failure_statistics=failure_statistics,
        plot_assets=plot_assets,
        warnings=warnings,
    )

    result = generate_risk_report(report_data)

    return result


def run_sim_historical_window_risk_report(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    return _run_risk_pipeline_with_temporary_modes(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        monte_carlo_mode="rollingHistoricalWindows",
    )


def run_sim_monte_carlo_risk_report(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    return _run_risk_pipeline_with_temporary_modes(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        monte_carlo_mode="pathBasedAnnualSampling",
    )