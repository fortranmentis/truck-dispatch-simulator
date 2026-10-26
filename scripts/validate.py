"""Reproduce baseline behavior and known limitations without opening the GUI."""
import ast
import importlib.util
import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    sources = sorted(ROOT.glob('*.py'))
    for source in sources:
        ast.parse(source.read_text(encoding='utf-8-sig'), filename=source.name)
    spec = importlib.util.spec_from_file_location('truck_simulator', ROOT / '공병공차계산4.py')
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    start = datetime(1900, 1, 1, 9)
    baselines = {}
    for kind, expected in [('공병트럭', 55), ('공차트럭', 44)]:
        truck = app.Truck(kind, start, kind)
        app.schedule_truck(truck, app.ResourceManager())
        elapsed = (truck.current_time - start).total_seconds() / 60
        assert elapsed == expected, (kind, elapsed)
        baselines[kind] = elapsed

    names = '병1 병2 병3 병4 병5 병6 병7 공1 공2 공3 공4 병8'.split()
    manager = app.ResourceManager()
    trucks = []
    for index, name in enumerate(names):
        truck = app.Truck(name, start + timedelta(minutes=5 * index),
                          '공병트럭' if '병' in name else '공차트럭')
        app.schedule_truck(truck, manager)
        trucks.append(truck)
    for truck in trucks:
        for task, begin, end in truck.schedule:
            assert end >= begin >= truck.arrival_times[task]
        for previous, current in zip(truck.schedule, truck.schedule[1:]):
            assert previous[2] == truck.arrival_times[current[0]]
    resource_overlaps = {}
    for resource, schedule in manager.resource_schedules.items():
        ordered = sorted(schedule, key=lambda item: item[1])
        resource_overlaps[resource] = sum(a[1] < b[2] and b[1] < a[2]
                                         for index, a in enumerate(ordered)
                                         for b in ordered[index + 1:])
    events = [(begin, 1) for _, begin, _ in manager.product_loading]
    events += [(end, -1) for _, _, end in manager.product_loading]
    occupancy = peak = 0
    for _, delta in sorted(events):
        occupancy += delta
        peak = max(peak, occupancy)

    # A future reservation is ignored by the current single-resource algorithm.
    edge = app.ResourceManager()
    first = app.Truck('병A', start, '공병트럭')
    second = app.Truck('공B', start, '공차트럭')
    future_begin, future_end = edge.schedule_resource('CO2', first, start + timedelta(minutes=10), 5)
    actual_begin, actual_end = edge.schedule_resource('CO2', second, start + timedelta(minutes=8), 5)
    overlap_reproduced = actual_begin < future_end and future_begin < actual_end
    assert overlap_reproduced

    # The same-time priority block receives an empty overlap list after the loop.
    edge = app.ResourceManager()
    edge.schedule_resource('CO2', first, start, 5)
    empty_begin, _ = edge.schedule_resource('CO2', second, start, 4)
    priority_not_applied = empty_begin == start + timedelta(minutes=5)
    assert priority_not_applied

    print(json.dumps({
        'python_sources_parsed': len(sources),
        'single_truck_minutes': baselines,
        'sample_trucks': len(trucks),
        'sample_mean_turnaround_minutes': sum((t.current_time - t.start_time).total_seconds() / 60 for t in trucks) / len(trucks),
        'sample_peak_product_loading': peak,
        'sample_product_loading_capacity_satisfied': peak <= 4,
        'sample_chronology_checks': 'passed',
        'sample_exclusive_resource_overlap_pairs': resource_overlaps,
        'known_future_reservation_overlap_reproduced': overlap_reproduced,
        'known_same_time_priority_limitation_reproduced': priority_not_applied,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
