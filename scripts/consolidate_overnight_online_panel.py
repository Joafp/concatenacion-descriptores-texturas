"""Fail-closed consolidation of the 94 authorized online conditions; no models/fits."""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
METHODS = {'Adaptive-selection-margin', 'Completa-22', 'Ens-diversidad', 'Ens-tombola', 'Top-4'}
EXPECTED = {'FMD': 15, 'CUReT': 2, 'DTD': 10, 'Outex13Official1360': 1,
            'SoilOriginal': 15, 'KTHTIPS2b': 4}


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def select_jobs(repo):
    analysis = repo / 'results/analysis'
    original_path = analysis / 'overnight_f1_latency_20261028/manifest.json'
    original = read(original_path)
    cache = {str(original_path): original}
    sources = {str(original_path): digest(original_path)}
    output = []
    for old in original['jobs']:
        ds, clf, fold = old['dataset'], old['classifier'], old['outer_fold']
        folder = None
        if ds == 'CUReT':
            folder = 'overnight_online_resume_20261029_v2' if clf == 'resmlp' and fold == 1 else 'overnight_multidataset_online_20261029_v1'
        elif ds == 'DTD':
            if clf == 'svm':
                folder = ('overnight_online_resume_20261029_v2' if fold == 0 else
                          'overnight_online_resume_20261029_v3' if fold <= 3 else
                          'overnight_online_resume_20261029_v4' if fold <= 6 else
                          'overnight_online_resume_20261029_v5')
            else:
                folder = ('overnight_online_resume_20261029_v6' if fold <= 2 else
                          'overnight_online_retry_20261101_DTD_resmlp_f3' if fold == 3 else
                          'overnight_online_resume_20261031_v8' if fold <= 6 else
                          'overnight_online_resume_20261101_v9')
        elif ds == 'Outex13Official1360':
            folder = 'blocker_resolution_20261101/queue_v1'
        elif ds == 'SoilOriginal':
            folder = 'blocker_resolution_20261101/soil_pending_v1'
        elif ds == 'KTHTIPS2b':
            folder = 'blocker_resolution_20261101/kth_alias_redispatch_v1'
        elif ds != 'FMD':
            raise ValueError('unexpected dataset')
        path = analysis / folder / 'manifest.json' if folder else original_path
        if str(path) not in cache:
            cache[str(path)] = read(path)
            sources[str(path)] = digest(path)
        hits = [j for j in cache[str(path)]['jobs'] if j['id'] == old['id']]
        if len(hits) != 1:
            raise ValueError('missing/duplicate lineage: ' + old['id'])
        selected = hits[0]
        for key in ('id', 'dataset', 'classifier', 'seed', 'outer_fold'):
            if selected[key] != old[key]:
                raise ValueError('scientific identity drift: ' + key)
        output.append(selected)
    validate_identities(output)
    return output, sources


def validate_identities(jobs):
    if len(jobs) != 94 or len({j['id'] for j in jobs}) != 94:
        raise ValueError('full 94 unique conditions required')
    observed = Counter((j['dataset'], j['classifier']) for j in jobs)
    expected = Counter({(d, c): n for d, n in EXPECTED.items() for c in ('svm', 'resmlp')})
    if observed != expected:
        raise ValueError('dataset/classifier condition coverage mismatch')


def macro_f1(truth, prediction):
    labels = sorted(set(truth))
    if not set(prediction).issubset(labels):
        raise ValueError('prediction class outside full test class set')
    true_count, pred_count = Counter(truth), Counter(prediction)
    tp = Counter(t for t, p in zip(truth, prediction) if t == p)
    return statistics.mean(2 * tp[c] / (true_count[c] + pred_count[c]) for c in labels)


def audit_condition(job):
    import numpy as np

    online, quality, audit_dir = [Path(job[k]) for k in ('online_run', 'quality_run', 'online_audit')]
    status_path = online / 'status.json'
    status, audit, q = read(status_path), read(audit_dir / 'audit.json'), read(quality / 'status.json')
    if status['status'] != 'batch1_online_f1_and_timing_complete' or not status['full_external_coverage']:
        raise ValueError('incomplete full online output: ' + job['id'])
    if audit['status'] != 'ONLINE_CALL_RECORDS_REAGGREGATED' or digest(status_path) != audit['source_status_sha256']:
        raise ValueError('audit/status mismatch: ' + job['id'])
    if digest(quality / 'status.json') != status['quality_status_sha256']:
        raise ValueError('frozen quality status drift')
    for key in ('dataset', 'classifier', 'seed', 'outer_fold'):
        if status[key] != job[key]:
            raise ValueError('online identity drift: ' + key)
    if digest(job['config']) != job['config_sha256']:
        raise ValueError('configuration drift')
    for name, sha in q['output_sha256'].items():
        if digest(quality / name) != sha:
            raise ValueError('quality artifact drift: ' + name)
    if digest(quality / 'frozen_decisions.json') != q['frozen_decisions_sha256']:
        raise ValueError('frozen decision drift')
    if set(status['rows']) != set(q['external_indices']) or len(status['rows']) != len(q['external_indices']):
        raise ValueError('external partition mismatch')
    with (online / 'online_calls.csv').open() as f:
        calls = list(csv.DictReader(f))
    with (online / 'online_summary.csv').open() as f:
        summaries = {r['policy']: r for r in csv.DictReader(f)}
    expected_rows = set(status['rows'])
    keys = {(int(r['repeat']), int(r['row_index']), r['policy']) for r in calls}
    if (set(summaries) != METHODS or {r['policy'] for r in calls} != METHODS
            or len(calls) != audit['call_rows'] or len(keys) != len(calls)
            or len(calls) != len(expected_rows) * 5 or status['repeats'] != 1
            or {int(r['repeat']) for r in calls} != {0}):
        raise ValueError('call/method/repetition coverage mismatch')
    records, times_by_method = [], {}
    identity = {k: job[k] for k in ('id', 'dataset', 'classifier', 'seed', 'outer_fold')}
    reserve = job['id'] == 'DTD_svm_s42_f6'
    for method in sorted(METHODS):
        rows = [r for r in calls if r['policy'] == method]
        if {int(r['row_index']) for r in rows} != expected_rows:
            raise ValueError('per-policy external coverage mismatch')
        times = [float(r['ms']) for r in rows]
        if any(not math.isfinite(v) or v <= 0 for v in times):
            raise ValueError('nonfinite/nonpositive time')
        f1 = macro_f1([int(r['label']) for r in rows], [int(r['prediction']) for r in rows])
        mean = statistics.mean(times)
        if abs(f1 - float(summaries[method]['macro_f1_online'])) > 1e-10 or abs(mean - float(summaries[method]['mean_ms'])) > 1e-8:
            raise ValueError('raw-call F1/mean differs from summary')
        records.append(dict(identity, method=method, images=len(rows), calls=len(times),
                            macro_f1_online=f1, mean_ms=mean, median_ms=float(np.median(times)),
                            p95_ms=float(np.percentile(times, 95)), physical_timing_reserve=reserve))
        times_by_method[method] = times
    provenance = {str(p): digest(p) for p in (status_path, audit_dir / 'audit.json',
        online / 'online_calls.csv', online / 'online_summary.csv', quality / 'status.json',
        quality / 'fitted_heads.joblib', quality / 'frozen_decisions.json', Path(job['config']))}
    return records, times_by_method, provenance


def write_csv(path, rows):
    with path.open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def consolidate(repo, output, check_ready=False):
    import numpy as np

    jobs, manifests = select_jobs(repo)
    missing = [j['id'] for j in jobs if not (Path(j['online_audit']) / 'audit.json').exists()]
    if check_ready:
        print(json.dumps({'expected': 94, 'audit_files_present': 94 - len(missing), 'missing': missing,
                          'scope': 'file readiness only, not full audit or completed panel'}))
        return
    if missing:
        raise ValueError('no complete means permitted; missing: ' + repr(missing))
    if output is None or output.exists():
        raise ValueError('new exclusive output directory required')
    records, provenance, pooled = [], dict(manifests), defaultdict(list)
    for job in jobs:
        rows, times, hashes = audit_condition(job)
        records.extend(rows)
        provenance.update(hashes)
        for method, values in times.items():
            pooled[(job['dataset'], job['classifier'], method)].extend(values)
    if len(records) != 470 or sum(r['calls'] for r in records) != 362640:
        raise ValueError('unexpected final call/condition-method total')
    dataset_rows = []
    for (dataset, clf, method), times in sorted(pooled.items()):
        group = [r for r in records if (r['dataset'], r['classifier'], r['method']) == (dataset, clf, method)]
        if len(group) != EXPECTED[dataset]:
            raise ValueError('partial dataset mean prohibited')
        dataset_rows.append(dict(dataset=dataset, classifier=clf, method=method,
            conditions=len(group), calls=len(times), mean_split_macro_f1=statistics.mean(r['macro_f1_online'] for r in group),
            mean_ms_all_calls=statistics.mean(times), median_ms_all_calls=float(np.median(times)),
            p95_ms_all_calls=float(np.percentile(times, 95)),
            physical_timing_reserve=any(r['physical_timing_reserve'] for r in group)))
    # The additional DTD observation is not a 95th condition or a replacement.
    original = next(j for j in jobs if j['id'] == 'DTD_svm_s42_f6')
    additional_dir = repo / 'results/analysis/blocker_resolution_20261101/queue_v1/jobs/DTD_svm_s42_f6_additional'
    extra_job = dict(original, online_run=str(additional_dir / 'online'), online_audit=str(additional_dir / 'online_audit'))
    extra_rows, _, extra_provenance = audit_condition(extra_job)
    provenance.update(extra_provenance)
    provenance[str(Path(__file__).resolve())] = digest(__file__)
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / 'condition_summary.csv', records)
    write_csv(output / 'dataset_summary.csv', dataset_rows)
    write_csv(output / 'additional_DTD_observation.csv', extra_rows)
    coverage = {'status': 'ALL_94_ONLINE_CONDITIONS_REAGGREGATED_WITH_RESERVES',
        'unique_conditions': 94, 'condition_method_rows': 470, 'dataset_classifier_method_rows': 60,
        'primary_calls': 362640, 'additional_calls': 9400, 'all_audited_calls': 372040,
        'quality_and_timing_from_same_calls': True, 'historical_cascade_equivalence_claimed': False,
        'hardware_isolated': False, 'global_inference_performed': False,
        'reservations': ['original DTD/SVM official7 retains physical timing reserve; additional observation does not replace it',
                         'Outex/Soil use explicitly authorized new DeiT representation; historical outputs preserved',
                         'KTH new-panel protocol reconciled; historical cascade equivalence not established',
                         'shared hardware, one timing repetition per image; seeds/folds not independent datasets']}
    for name, value in [('coverage.json', coverage), ('provenance.json', provenance)]:
        with (output / name).open('x') as f:
            f.write(json.dumps(value, indent=2) + '\n')
    print(json.dumps(coverage))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, default=ROOT)
    p.add_argument('--output', type=Path)
    p.add_argument('--check-ready', action='store_true')
    a = p.parse_args()
    consolidate(a.repo.resolve(), a.output.resolve() if a.output else None, a.check_ready)
