import json
# from video_processing_engine.core.consumer.insync import json_obj_1

json_obj = '''{
    "country_code": f"{country_code}"
    "customer_id": f"{customer_id}"
    "contract_id": f"{contract_id}"
    "order_id": f"{order_id}"
    "store_id": f"{store_id}"
    "camera_id": f"{camera_id}"
    "area_code": f"{area_code}"
    "use_stored": f"{use_stored}"
    "original_file": f"{original_file}"
    "camera_address": f"{camera_address}"
    "camera_port": f"{camera_port}"
    "camera_username": f"{camera_username}"
    "camera_password": f"{camera_password}"
    "start_time": f"{start_time}"
    "end_time": f"{end_time}"
    "camera_timeout": f"{camera_timeout}"
    "timestamp_format": f"{timestamp_format}"
    "perform_compression": f"{perform_compression}"
    "perform_trimming": f"{perform_trimming}"
    "trim_compressed": f"{trim_compressed}"
    "trim_num_parts": f"{trim_num_parts}"
    "equal_distribution": f"{equal_distribution}"
    "clip_length": f"{clip_length}"
    "trim_sample_section": f"{trim_sample_section}"
    "trim_by_factor": f"{trim_by_factor}"
    "factor": f"{factor}"
    "last_clip": f"{last_clip}"
    "select_sample": f"{select_sample}"
    "sampling_rate": f"{sampling_rate}"
    "compression_ratio": f"{compression_ratio}"
    "number_of_clips": f"{number_of_clips}"
}'''

json_data = json.loads(json_obj)
print(json_data)

xa = json_data.get('last_clip', None)
print(xa, type(xa))
