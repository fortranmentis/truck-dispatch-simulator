# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 19:54:51 2024

@author: sang
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
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

def main_gui():
    def run_schedule():
        try:
            # 입력 값 가져오기
            dispatch_sequence = entry_sequence.get().split()
            dispatch_interval = int(entry_interval.get())
            start_time_input = entry_start_time.get()
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
            output_text.delete('1.0', tk.END)
            output_text.insert(tk.END, "--- 트럭별 작업 스케줄 ---\n")
            for truck in trucks:
                output_text.insert(tk.END, f"\n트럭 {truck.name} ({truck.truck_type}):\n")
                for task_name, start, end in truck.schedule:
                    output_text.insert(tk.END, f"{task_name}: {start.strftime('%H:%M:%S')} ~ {end.strftime('%H:%M:%S')} (도착: {truck.arrival_times[task_name].strftime('%H:%M:%S')})\n")

            # 제품상차 시 동시에 작업하는 트럭들 출력
            output_text.insert(tk.END, "\n--- 제품상차 시 동시에 작업하는 트럭들 ---\n")
            groups = resource_manager.get_product_loading_groups()
            for start_time_grp, end_time_grp, trucks_in_group in groups:
                truck_names = ', '.join([t.name for t in trucks_in_group])
                output_text.insert(tk.END, f"{start_time_grp.strftime('%H:%M:%S')} ~ {end_time_grp.strftime('%H:%M:%S')}: {truck_names}\n")

            # 총 소요 시간 계산
            total_times = []
            공차_total = []
            공병_total = []

            for truck in trucks:
                # 총 소요 시간: 마지막 작업의 종료 시간 - 시작 시간
                total_time = truck.schedule[-1][2] - truck.start_time
                total_times.append(total_time)

                if truck.truck_type == '공차트럭':
                    공차_total.append(total_time)
                else:
                    공병_total.append(total_time)

            # 평균 소요 시간 계산 함수
            def average_time(time_list):
                if not time_list:
                    return timedelta(0)
                total = sum([t.total_seconds() for t in time_list])
                avg_seconds = total / len(time_list)
                return timedelta(seconds=avg_seconds)

            overall_avg = average_time(total_times)
            공차_avg = average_time(공차_total)
            공병_avg = average_time(공병_total)

            # 결과 출력
            output_text.insert(tk.END, "\n--- 소요 시간 통계 ---\n")
            for truck, total_time in zip(trucks, total_times):
                hours, remainder = divmod(total_time.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                output_text.insert(tk.END, f"트럭 {truck.name} 전체 소요시간: {int(hours)}시간 {int(minutes)}분 {int(seconds)}초\n")

            # 전체 평균 소요시간
            overall_hours, overall_remainder = divmod(overall_avg.total_seconds(), 3600)
            overall_minutes, overall_seconds = divmod(overall_remainder, 60)
            output_text.insert(tk.END, f"\n전체 트럭 평균 소요시간: {int(overall_hours)}시간 {int(overall_minutes)}분 {int(overall_seconds)}초\n")

            # 공차 평균 소요시간
            공차_hours, 공차_remainder = divmod(공차_avg.total_seconds(), 3600)
            공차_minutes, 공차_seconds = divmod(공차_remainder, 60)
            output_text.insert(tk.END, f"공차트럭 평균 소요시간: {int(공차_hours)}시간 {int(공차_minutes)}분 {int(공차_seconds)}초\n")

            # 공병 평균 소요시간
            공병_hours, 공병_remainder = divmod(공병_avg.total_seconds(), 3600)
            공병_minutes, 공병_seconds = divmod(공병_remainder, 60)
            output_text.insert(tk.END, f"공병트럭 평균 소요시간: {int(공병_hours)}시간 {int(공병_minutes)}분 {int(공병_seconds)}초\n")

        except Exception as e:
            messagebox.showerror("오류", f"입력값을 확인해주세요.\n{e}")

    # GUI 창 생성
    window = tk.Tk()
    window.title("트럭 스케줄링 프로그램")

    # 배차 순서 입력
    lbl_sequence = tk.Label(window, text="배차 순서를 입력하세요 (예: 병1 공1 병2 ...):")
    lbl_sequence.grid(column=0, row=0, padx=10, pady=5, sticky='w')
    entry_sequence = tk.Entry(window, width=50)
    entry_sequence.grid(column=0, row=1, padx=10, pady=5)

    # 배차 간격 입력
    lbl_interval = tk.Label(window, text="배차 간격을 입력하세요 (분 단위):")
    lbl_interval.grid(column=0, row=2, padx=10, pady=5, sticky='w')
    entry_interval = tk.Entry(window, width=20)
    entry_interval.grid(column=0, row=3, padx=10, pady=5, sticky='w')

    # 첫차 시작 시간 입력
    lbl_start_time = tk.Label(window, text="첫차의 시작 시간을 입력하세요 (예: 09:00):")
    lbl_start_time.grid(column=0, row=4, padx=10, pady=5, sticky='w')
    entry_start_time = tk.Entry(window, width=20)
    entry_start_time.grid(column=0, row=5, padx=10, pady=5, sticky='w')

    # 실행 버튼
    btn_run = tk.Button(window, text="실행", command=run_schedule)
    btn_run.grid(column=0, row=6, padx=10, pady=10)

    # 결과 출력 창
    output_text = scrolledtext.ScrolledText(window, width=100, height=30)
    output_text.grid(column=0, row=7, padx=10, pady=10)

    window.mainloop()

if __name__ == "__main__":
    main_gui()
