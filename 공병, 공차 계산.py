# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 15:35:02 2024

@author: sang
"""

from datetime import datetime, timedelta

def parse_schedule(order, interval_minutes, start_time=None):
    order_list = order.split()
    interval = timedelta(minutes=interval_minutes)
    
    process_times = {
        '병': {
            '검수': timedelta(minutes=5),
            '이동1': timedelta(minutes=2),
            '공병하차': timedelta(minutes=8),
            '이동2': timedelta(minutes=3),
            '제품상차': timedelta(minutes=15),
            '이동3': timedelta(minutes=3),
            '선전품상차': timedelta(minutes=5),
            '이동4': timedelta(minutes=2),
            'CO2': timedelta(minutes=5),
            '출하캐노피': timedelta(minutes=2),
            '출고검사': timedelta(minutes=5),
        },
        '공': {
            '검수': timedelta(minutes=5),
            '이동1': timedelta(minutes=0),
            '공병하차': timedelta(minutes=0),
            '이동2': timedelta(minutes=2),
            '제품상차': timedelta(minutes=17),
            '이동3': timedelta(minutes=4),
            '선전품상차': timedelta(minutes=5),
            '이동4': timedelta(minutes=1),
            'CO2': timedelta(minutes=4),
            '출하캐노피': timedelta(minutes=3),
            '출고검사': timedelta(minutes=3),
        }
    }

    start_times = {}
    truck_schedules = []
    current_time = start_time if start_time else datetime.now()
    
    # 처리 불가능한 공정들에 대한 관리
    restricted_processes = ['검수', '공병하차', '선전품상차', 'CO2']
    ongoing_process = {process: None for process in restricted_processes}
    product_loading_queue = []
    
    for truck in order_list:
        truck_type = truck[0]
        truck_id = truck
        process_time = process_times[truck_type]
        truck_schedule = {'트럭': truck_id, '시작시간': current_time, '상세': []}

        for process, duration in process_time.items():
            # 처리 불가능한 공정들에 대한 스케줄 조정
            if process in restricted_processes:
                if ongoing_process[process] and ongoing_process[process] > current_time:
                    current_time = ongoing_process[process]
            
            truck_schedule['상세'].append((process, current_time))
            current_time += duration
            
            if process in restricted_processes:
                ongoing_process[process] = current_time
            elif process == '제품상차':
                product_loading_queue.append((truck_id, current_time))
                if len(product_loading_queue) > 4:
                    # 제품 상차가 4대 이상 겹치지 않도록 조정
                    waiting_truck, waiting_time = product_loading_queue.pop(0)
                    if waiting_time > current_time:
                        current_time = waiting_time

        start_times[truck_id] = current_time
        truck_schedules.append(truck_schedule)
        current_time += interval  # 다음 트럭 배차 간격 적용
    
    return truck_schedules


def display_schedule(schedules):
    for schedule in schedules:
        print(f"트럭 {schedule['트럭']} 스케줄:")
        for process, time in schedule['상세']:
            print(f"  {process}: {time.strftime('%H:%M:%S')}")
        print()

# 예시 입력
order = '병1 병2 병3 병4 병5 병6 병7 공1 공2 공3 공4 병8'
start_time = datetime(2023, 3, 15, 9, 0)
interval_minutes = 5

# 스케줄 계산
schedules = parse_schedule(order, interval_minutes, start_time)

# 스케줄 출력
display_schedule(schedules)