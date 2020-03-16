"""A subservice for running turntable in parallel."""

import json
import threading

from video_processing_engine.core.turntable import spin

json_obj_1 = {"country_code": "in", "customer_id": "0001", "contract_id": "2", "order_id": "3", "store_id": "4", "camera_id": "5", "area_code": "p", "use_stored": False, "original_file": "/home/xames3/Desktop/video_processing_engine/demo/minidemo_march_5/4_hr.mp4", "camera_address": "192.168.0.3", "camera_port": "554", "camera_username": "admin", "camera_password": "USER@1234", "start_time": "2020-03-11 11:45:00", "end_time": "2020-03-11 11:50:00", "camera_timeout": "30.0", "timestamp_format": "%Y-%m-%d %H:%M:%S", "select_sample": False, "sampling_rate": "50", "perform_compression": True, "perform_trimming": True, "trim_compressed": True, "compression_ratio": "60", "number_of_clips": "5"}

json_obj_2 = {"country_code": "in", "customer_id": "0008", "contract_id": "16", "order_id": "69", "store_id": "420", "camera_id": "1", "area_code": "x", "use_stored": False, "original_file": "/home/xames3/Desktop/video_processing_engine/demo/minidemo_march_5/4_hr.mp4", "camera_address": "192.168.0.5", "camera_port": "554", "camera_username": "admin", "camera_password": "user@1234", "start_time": "2020-03-11 11:45:00", "end_time": "2020-03-11 11:48:00", "camera_timeout": "30.0", "timestamp_format": "%Y-%m-%d %H:%M:%S", "select_sample": False, "sampling_rate": "50", "perform_compression": True, "perform_trimming": True, "trim_compressed": True, "compression_ratio": "60", "number_of_clips": "5"}

json_obj_1 = json.dumps(json_obj_1)
json_obj_2 = json.dumps(json_obj_2)

print('Started thread 1')
thread_1 = threading.Thread(target=spin, args=([json_obj_1]))
print('Started thread 2')
thread_2 = threading.Thread(target=spin, args=([json_obj_2]))

thread_1.start()
thread_2.start()
thread_1.join()
thread_2.join()
spin(json_obj_1)
print('Done!')
