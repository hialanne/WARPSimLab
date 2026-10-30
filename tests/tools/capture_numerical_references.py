"""Explicit, standalone capture; never invoked by ordinary pytest execution.

Run from the project root with python -m tests.tools.capture_numerical_references.
The utility refuses to replace existing datasets. Intentional financial changes
require a separately approved baseline version, not a pytest update switch.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
from time import perf_counter

import numpy as np

from tests.numerical_reference_helpers import ATOL, RTOL, describe_tree
from tests.numerical_reference_scenarios import CASES, DATA, activation_checks, run_case


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                    encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-version", required=True,
                        help="Accepted source version/commit or explicitly identified workspace snapshot")
    parser.add_argument("--output", type=Path, default=DATA)
    parser.add_argument("--case", action="append", choices=CASES, dest="selected_cases",
                        help="Capture only this case (repeatable) into a new output directory")
    args = parser.parse_args()
    directory = args.output.resolve()
    if ((directory / "manifest.json").exists()
            or any((directory / "outputs").glob("*.npz"))
            or any((directory / "inputs").glob("*.json"))):
        parser.error(f"Refusing to overwrite reference data in {directory}")
    started = perf_counter()
    captured = {}
    selected = args.selected_cases or CASES
    for name in dict.fromkeys(selected):
        tick = perf_counter()
        core, inputs = run_case(name)
        checks = activation_checks(name, core)
        missing = [key for key, active in checks.items() if not active]
        if missing:
            raise RuntimeError(f"{name}: intended mechanisms inactive: {missing}; no capture written")
        arrays = {}
        schema = describe_tree(core, arrays)
        captured[name] = (core, inputs, arrays, schema, checks, perf_counter() - tick)
    if {"s6_baseline", "s6_modified"} <= captured.keys():
        baseline = captured["s6_baseline"][0]["total_assets"]
        modified = captured["s6_modified"][0]["total_assets"]
        assert not np.array_equal(baseline, modified), "Explorer results must differ"
    (directory / "inputs").mkdir(parents=True, exist_ok=True)
    (directory / "outputs").mkdir(parents=True, exist_ok=True)
    manifest = dict(
        format_version=1, accepted_source=args.source_version,
        python=platform.python_version(), numpy=np.__version__,
        captured_utc=datetime.now(timezone.utc).isoformat(),
        comparison=dict(atol=ATOL, rtol=RTOL), cases={},
    )
    for name, (core, inputs, arrays, schema, checks, seconds) in captured.items():
        np.savez_compressed(directory / "outputs" / f"{name}.npz", **arrays)
        write_json(directory / "inputs" / f"{name}.json", inputs)
        config = inputs.get("sim_config", inputs.get("resolved_config"))
        manifest["cases"][name] = dict(
            schema=schema, activation=checks, start_year=config["start_year"],
            requested_years=config["years_to_simulate"],
            boundary=inputs.get("boundary", "pipeline"),
            path_count=core["total_assets"].shape[0],
            retained_year_count=core["total_assets"].shape[1],
            capture_seconds=seconds,
        )
        print(f"{name}: {len(arrays)} arrays, {seconds:.3f}s, "
              f"{(directory / 'outputs' / f'{name}.npz').stat().st_size:,} bytes")
    manifest["capture_seconds"] = perf_counter() - started
    write_json(directory / "manifest.json", manifest)
    print(f"Captured {len(captured)} cases in {manifest['capture_seconds']:.3f}s to {directory}")


if __name__ == "__main__":
    main()
