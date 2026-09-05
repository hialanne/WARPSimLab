import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path
from pprint import pformat


class WARPSimLabInternalError(RuntimeError):
    def __init__(self, message, diagnostic_path=None):
        self.original_message = message
        self.diagnostic_path = diagnostic_path

        if diagnostic_path:
            message = f"{message}\nDiagnostic file written to: {diagnostic_path}"
        else:
            message = f"{message}\nWARPSimLab was unable to write a diagnostic file."

        super().__init__(message)


def _format_value(value):
    try:
        if hasattr(value, "__dict__"):
            return pformat(vars(value), width=120, compact=True, sort_dicts=True)
        return pformat(value, width=120, compact=True, sort_dicts=True)
    except Exception:
        try:
            return repr(value)
        except Exception:
            return "<unable to format value>"


def _write_diagnostic_report(message, sim_config, context, call_stack):
    try:
        target_dir = Path.home() / "Desktop" / "WARPSimLab" / "Diagnostics"
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now()
        log_file = target_dir / timestamp.strftime("WARPSimLab_error_%Y-%m-%d_%H%M%S.txt")

        with open(log_file, "w", encoding="utf-8") as f:
            f.write("WARPSimLab Internal Error Diagnostic\n")
            f.write("====================================\n\n")
            f.write(f"Date/time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} (local time)\n")
            f.write(f"WARPSimLab version: {getattr(sim_config, 'warpsimlab_version', 'Unknown')}\n")
            f.write(f"Python version: {sys.version}\n")
            f.write(f"Operating system: {platform.platform()}\n\n")

            f.write("Error\n")
            f.write("-----\n")
            f.write(f"{message}\n\n")

            if context:
                f.write("Error Context\n")
                f.write("-------------\n")
                for key, value in sorted(context.items()):
                    f.write(f"{key}: {_format_value(value)}\n")
                f.write("\n")

            excluded_config_keys = {
                "root",
                "_expense_inflation_factors",
                "_husband_pension_factors",
                "_wife_pension_factors",
                "_income_inflation_factors",
                "_inflation_factors",
                "_roth_inflation_factor_cache",
                "_roth_scheduled_flows",
                "_tax_year_cache",
                "_mc_rng",
            }

            if sim_config is not None:
                f.write("Simulation Configuration\n")
                f.write("------------------------\n")
                try:
                    for key, value in sorted(vars(sim_config).items()):
                        if key not in excluded_config_keys:
                            f.write(f"{key}: {_format_value(value)}\n")
                except Exception as exc:
                    f.write(f"<unable to record sim_config: {exc}>\n")
                f.write("\n")

            f.write("Call Stack\n")
            f.write("----------\n")
            f.write("".join(call_stack))

        return log_file

    except Exception:
        return None


def raise_internal_error(message, sim_config, context=None):
    call_stack = traceback.format_stack()[:-1]
    diagnostic_path = _write_diagnostic_report(message, sim_config, context or {}, call_stack)

    print()
    print("WARPSimLab encountered an internal simulation error.")

    if diagnostic_path:
        print(f"A diagnostic file was written to: {diagnostic_path}")
    else:
        print("WARPSimLab was unable to write a diagnostic file.")

    print()

    raise WARPSimLabInternalError(message, diagnostic_path)