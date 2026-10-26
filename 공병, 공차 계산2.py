# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 15:56:14 2024

@author: sang
"""

from datetime import datetime, timedelta

# 트럭 클래스 정의
class Truck:
    def __init__(self, name, start_time, truck_type):
        self.name = name
        self.start_time = start_time  # 시작 시간
        self.current_time = start_time  # 현재 시간
        self.truck_type = truck_type
        self.schedule = []  # 작업 스케줄 (작업명, 시작 시간, 종료 시간)
        self.product_loading_time = None  # 제품상차 시간 저장

        # 각 작업의 도착 시간 및 실제 시작 시간 저장
        self.arrival_times = {}  # 작업명: 도착 시간
        self.actual_start_times = {}  # 작업명: 실제 시작 시간

# 작업 시간 (분 단위)
process_times = {
    '공병트럭': [
        ('검수(공병하차대기)', 5, True),
        ('이동1', 2, False),
        ('공병하차', 8, True),
        ('이동2', 3, False),
        ('제품상차', 15, '제품상차'),
        ('이동3', 3, False),
        ('선전품상차', 5, True),
        ('이동4', 2, False),
        ('CO2', 5, True),
        ('출하캐노피', 2, False),
        ('출고검사 및 전표', 5, False)
    ],
    '공차트럭': [
        ('검수(공병하차대기)', 5, True),
        ('이동1', 0, False),
        ('공병하차', 0, False),  # 스킵
        ('이동2', 2, False),
        ('제품상차', 17, '제품상차'),
        ('이동3', 4, False),
        ('선전품상차', 5, True),
        ('이동4', 1, False),
        ('CO2', 4, True),
        ('출하캐노피', 3, False),
        ('출고검사 및 전표', 3, False)
    ]
}

# 자원 관리자 클래스
class ResourceManager:
    def __init__(self):
        # 각 자원의 스케줄: 작업 시작 시간, 종료 시간, 트럭
        self.resource_schedules = {
            '검수(공병하차대기)': [],
            '공병하차': [],
            '선전품상차': [],
            'CO2': []
        }
        self.product_loading = []  # 제품상차 스케줄

    # 자원 스케줄링 함수
    def schedule_resource(self, resource_name, truck, arrival_time, duration):
        # 해당 자원의 기존 스케줄 가져오기
        schedule = self.resource_schedules[resource_name]

        # 가능한 시작 시간을 도착 시간으로 초기화
        possible_start_time = arrival_time

        while True:
            # 자원이 사용 중인지 확인 (이미 도착한 트럭들만 고려)
            overlapping_trucks = [
                s for s in schedule
                if not (s[2] <= possible_start_time or s[1] >= possible_start_time + timedelta(minutes=duration))
                and s[1] <= possible_start_time  # 트럭이 이미 도착한 경우만 고려
            ]

            if not overlapping_trucks:
                # 자원이 사용 중이 아님
                break
            else:
                # 현재 작업 중인 트럭의 종료 시간 중 가장 빠른 시간으로 시작 시간 이동
                earliest_end_time = min(s[2] for s in overlapping_trucks)
                possible_start_time = earliest_end_time

        # 같은 시간에 도착한 트럭들 처리 (공차 우선)
        same_time_trucks = [s for s in overlapping_trucks if s[1] == arrival_time]
        if same_time_trucks:
            if truck.truck_type == '공차트럭':
                pass  # 그대로 진행
            else:
                for s_truck, s_start, s_end in same_time_trucks:
                    if s_truck.truck_type == '공차트럭':
                        possible_start_time = s_end
                        break

        start_time = possible_start_time
        end_time = start_time + timedelta(minutes=duration)
        schedule.append((truck, start_time, end_time))
        self.resource_schedules[resource_name] = schedule
        return start_time, end_time

    # 제품상차 스케줄링 함수
    def schedule_product_loading(self, truck, arrival_time, duration):
        # 제품상차는 동시에 최대 4대까지 가능
        schedule = self.product_loading

        # 가능한 시작 시간을 도착 시간으로 초기화
        possible_start_time = arrival_time

        while True:
            # 해당 시간대에 작업 중인 트럭 수 확인
            overlapping_trucks = [
                s for s in schedule
                if not (s[2] <= possible_start_time or s[1] >= possible_start_time + timedelta(minutes=duration))
                and s[1] <= possible_start_time  # 트럭이 이미 도착한 경우만 고려
            ]

            if len(overlapping_trucks) < 4:
                # 작업 가능
                break
            else:
                # 현재 작업 중인 트럭들의 종료 시간 중 가장 빠른 시간으로 시작 시간 이동
                earliest_end_time = min(s[2] for s in overlapping_trucks)
                possible_start_time = earliest_end_time

        end_time = possible_start_time + timedelta(minutes=duration)
        schedule.append((truck, possible_start_time, end_time))
        self.product_loading = schedule
        return possible_start_time, end_time

    # 제품상차 작업 중인 트럭들 그룹화 (구성이 변경될 때마다)
    def get_product_loading_groups(self):
        events = []
        for truck, start_time, end_time in self.product_loading:
            events.append((start_time, 'start', truck))
            events.append((end_time, 'end', truck))
        # 시간 순으로 정렬, 종료 이벤트를 시작 이벤트보다 먼저 처리
        events.sort(key=lambda x: (x[0], 0 if x[1] == 'end' else 1))

        current_trucks = set()
        groups = []
        last_time = None

        for time, event_type, truck in events:
            if last_time is not None and current_trucks:
                groups.append((last_time, time, list(current_trucks)))
            if event_type == 'start':
                current_trucks.add(truck)
            else:
                current_trucks.remove(truck)
            last_time = time

        return groups

def schedule_truck(truck, resource_manager):
    for task_name, duration, resource in process_times[truck.truck_type]:
        arrival_time = truck.current_time
        truck.arrival_times[task_name] = arrival_time  # 도착 시간 기록

        if resource == True:
            # 독점 자원 스케줄링
            start_time, end_time = resource_manager.schedule_resource(
                resource_name=task_name,
                truck=truck,
                arrival_time=arrival_time,
                duration=duration
            )
        elif resource == '제품상차':
            # 제품상차 스케줄링
            start_time, end_time = resource_manager.schedule_product_loading(
                truck, arrival_time, duration
            )
            truck.product_loading_time = (start_time, end_time)  # 제품상차 시간 저장
        else:
            # 자원 필요 없음
            start_time = arrival_time
            end_time = start_time + timedelta(minutes=duration)

        # 작업 스케줄 업데이트
        truck.schedule.append((task_name, start_time, end_time))
        truck.actual_start_times[task_name] = start_time  # 실제 시작 시간 기록
        truck.current_time = end_time  # 현재 시간 업데이트

def main():
    # 입력 받기
    dispatch_sequence = input("배차 순서를 입력하세요 (예: '병1 병2 공1 병3 ...'): ").split()
    dispatch_interval = int(input("배차 간격을 입력하세요 (분 단위): "))
    start_time_input = input("첫차의 시작 시간을 입력하세요 (예: '9:00'): ")
    start_time = datetime.strptime(start_time_input, '%H:%M')

    trucks = []
    resource_manager = ResourceManager()

    # 트럭 생성 및 초기화
    for idx, name in enumerate(dispatch_sequence):
        truck_type = '공병트럭' if '병' in name else '공차트럭'
        dispatch_time = start_time + timedelta(minutes=dispatch_interval * idx)
        truck = Truck(name, dispatch_time, truck_type)
        trucks.append(truck)

    # 트럭별 스케줄링
    for truck in trucks:
        schedule_truck(truck, resource_manager)

    # 결과 출력
    for truck in trucks:
        print(f"\n트럭 {truck.name} ({truck.truck_type}):")
        for task_name, start, end in truck.schedule:
            print(f"{task_name}: {start.strftime('%H:%M:%S')} ~ {end.strftime('%H:%M:%S')} (도착: {truck.arrival_times[task_name].strftime('%H:%M:%S')})")

    # 제품상차 시 동시에 작업하는 트럭들 출력
    print("\n제품상차 시 동시에 작업하는 트럭들:")
    groups = resource_manager.get_product_loading_groups()
    for start_time, end_time, trucks_in_group in groups:
        truck_names = ', '.join([t.name for t in trucks_in_group])
        print(f"{start_time.strftime('%H:%M:%S')} ~ {end_time.strftime('%H:%M:%S')}: {truck_names}")

if __name__ == "__main__":
    main()



