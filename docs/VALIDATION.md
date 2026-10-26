# Validation evidence / 검증 기록

## Scope

Prepared on **2026-10-27 (Asia/Seoul)** using Python **3.13.5**. The target is the original `공병공차계산4.py`; no scheduling code was changed. Earlier iterations were parsed for syntax only.

The evidence comes from source inspection and direct calls to `Truck`, `ResourceManager`, and `schedule_truck`. Importing the module does not launch the GUI because its entry point is guarded by `if __name__ == '__main__'`.

```bash
python scripts/validate.py
```

## Methods and observations

1. **Syntax:** parse the four root-level Python sources with `ast.parse`.
2. **Baselines:** schedule one truck of each type with a fresh resource manager. Measured turnaround equals the sum of configured durations: 55 minutes for empty-bottle trucks and 44 minutes for empty trucks.
3. **Reference scenario:** use the original 12-truck order, five-minute intervals, and 09:00 first dispatch. Assert nonnegative stage durations, starts no earlier than arrival, and continuity between stages.
4. **Exclusive capacity:** count overlapping reservation pairs at each exclusive station. Positive overlap uses `a.start < b.end and b.start < a.end`.
5. **Product-loading capacity:** sweep start/end events, processing ends before starts at a tied timestamp, and measure maximum active reservations.
6. **Future reservation counterexample:** reserve CO2 at 09:10–09:15, then request 09:08–09:13. Both are accepted although they overlap. The `s[1] <= possible_start_time` predicate excludes the later reservation from the conflict check.
7. **Priority counterexample:** reserve CO2 for an empty-bottle truck at 09:00, then request an empty truck at 09:00. The empty truck starts at 09:05. The post-loop priority block sees an empty overlap list and does not move the empty truck ahead.

## Observed output

```json
{
  "python_sources_parsed": 4,
  "single_truck_minutes": {"공병트럭": 55.0, "공차트럭": 44.0},
  "sample_trucks": 12,
  "sample_mean_turnaround_minutes": 59.333333333333336,
  "sample_peak_product_loading": 5,
  "sample_product_loading_capacity_satisfied": false,
  "sample_chronology_checks": "passed",
  "sample_exclusive_resource_overlap_pairs": {
    "검수(공병하차대기)": 0,
    "공병하차": 0,
    "선전품상차": 3,
    "CO2": 3
  },
  "known_future_reservation_overlap_reproduced": true,
  "known_same_time_priority_limitation_reproduced": true
}
```

**Interpretation:** baseline arithmetic and stage chronology are consistent in these checks, but the reference schedule violates resource constraints. Its mean turnaround is a description of current program output, not a feasible operational performance estimate. Counts refer to overlapping pairs, not the number of affected trucks or distinct conflict periods.

The diagnostic deliberately reports capacity violations rather than treating script completion as an all-green validation result. Assertions check baselines, chronology, and reproduction of known limitations. If scheduling code is later corrected, update the limitation reproductions and this record.

## Boundaries

- No GUI interaction or visual QA was performed.
- No executable was launched, rebuilt, or matched to source.
- No workbook content audit or source-to-workbook reconciliation was performed.
- No observed arrival/departure records, calibration dataset, statistical uncertainty, or production benchmark was supplied or evaluated.
- No full scenario enumeration or guarantee of optimality / feasibility is claimed.

## 한국어 요약

2026-10-27, Python 3.13.5 환경에서 원본 최신 소스를 수정하지 않고 진단했습니다. 원본 소스 4개의 구문 분석, 단독 트럭 기준시간(공병 55분·공차 44분), 12대 예시의 공정 선후관계를 확인했습니다.

다만 12대 예시에서는 제품상차 최대 점유가 5대로 설계상 용량 4대를 초과했고, 선전품상차와 CO2에서 각각 3쌍의 중복 예약이 관측됐습니다. 따라서 평균 59.33분은 자원 충돌이 있는 프로그램 출력의 평균이며, 실행 가능한 배차 계획의 성과 추정값으로 사용할 수 없습니다. 중복 수는 트럭 대수나 충돌 구간 수가 아닌 예약 쌍의 수입니다.

미래 예약을 놓치는 충돌 검사와 동시 도착 공차 우선순위 미적용을 별도 사례로 재현했습니다. 스크립트 정상 종료는 이러한 관측을 재현했다는 의미이며 자원 제약 충족을 뜻하지 않습니다. GUI, 실행파일, 엑셀 내용, 현장 데이터 비교는 검증 범위에 포함하지 않았습니다.
