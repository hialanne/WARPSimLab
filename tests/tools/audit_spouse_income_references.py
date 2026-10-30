"""Audit every accepted reference leaf; explicitly apply only approved income deltas."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from tests.numerical_reference_helpers import compare_core, describe_tree, load_reference, read_json
from tests.numerical_reference_scenarios import CASES, DATA, activation_checks, run_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    manifest_path = DATA / 'manifest.json'
    manifest = read_json(manifest_path)
    if args.apply:
        assert not any('spouse_net_income_correction' in entry
                       for entry in manifest['cases'].values()), 'Correction already applied'
    evidence = {'utc': datetime.now(timezone.utc).isoformat(), 'cases': {}}
    replacements = {}
    for name in CASES:
        actual, inputs = run_case(name)
        entry = manifest['cases'][name]
        assert inputs == read_json(DATA / 'inputs' / f'{name}.json')
        assert activation_checks(name, actual) == entry['activation']
        expected = load_reference(DATA, name, entry)
        arrays = {}
        assert describe_tree(actual, arrays) == entry['schema']
        old_arrays = {}
        describe_tree(expected, old_arrays)
        changes = {}
        for field, old in old_arrays.items():
            new = arrays[field]
            equal = (old == new)
            if old.dtype.kind == 'f':
                equal |= np.isnan(old) & np.isnan(new)
            if np.all(equal):
                continue
            assert field in {'net_income_husband', 'net_income_wife'}, (name, field)
            changes[field] = [dict(path=int(p), year_index=int(y),
                                   calendar_year=entry['start_year'] + int(y),
                                   old=float(old[p, y]), new=float(new[p, y]),
                                   removed=float(old[p, y] - new[p, y]))
                              for p, y in np.argwhere(~equal)]
            # Compare every other leaf with the original, unchanged tolerances.
            expected[field] = new.copy()
        compare_core(actual, expected, case=name, start_year=entry['start_year'])
        if changes:
            removed = sum(old_arrays[f] - arrays[f]
                          for f in ('net_income_husband', 'net_income_wife'))
            # Both fields together lose exactly the noncash conversion and any
            # emergency pre-tax cash formerly included only in person reporting.
            np.testing.assert_allclose(
                removed, actual['roth_conversions'] + actual['emergency_pre_tax_used'],
                rtol=1e-13, atol=1e-8)
            replacements[name] = {f: arrays[f] for f in changes}
        path = DATA / 'outputs' / f'{name}.npz'
        evidence['cases'][name] = dict(
            arrays=len(arrays), elements=sum(a.size for a in arrays.values()),
            shape=list(actual['year'].shape), changes=changes,
            before_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        print(name, sum(len(v) for v in changes.values()), 'changed values', flush=True)
    # No writes until every scenario, field, path and year has passed the audit.
    if args.apply:
        for name, changed in replacements.items():
            path = DATA / 'outputs' / f'{name}.npz'
            with np.load(path, allow_pickle=False) as archive:
                preserved = {key: archive[key] for key in archive.files}
            preserved.update(changed)
            np.savez_compressed(path, **preserved)
            manifest['cases'][name]['spouse_net_income_correction'] = dict(
                accepted_source='User-approved corrected development workspace synchronized to WARPSimLab-codex',
                audited_utc=evidence['utc'], fields=sorted(changed),
                reason='Exclude noncash Roth conversions and applicable emergency pre-tax withdrawals from individual net-income reporting; preserve tax allocation.',
                previous_npz_sha256=evidence['cases'][name]['before_sha256'])
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    evidence['applied'] = args.apply
    for name in CASES:
        path = DATA / 'outputs' / f'{name}.npz'
        evidence['cases'][name]['after_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    output = Path('codex_reports/spouse_net_income_reference_audit.json')
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
