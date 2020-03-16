"""Performs entire VPE using JSON."""

from backup.archive.test_scripts.continue_record import contine_recording
import csv
import os
from typing import Union
import json

from video_processing_engine.core.process.compress import compress_video
from video_processing_engine.core.process.trim import (trim_num_parts,
                                                       trim_sample_section)
from video_processing_engine.utils.aws import (create_s3_bucket,
                                               upload_to_bucket)
from video_processing_engine.utils.generate import (bucket_name, order_name,
                                                    video_type)
from video_processing_engine.utils.local import (
    create_copy, rename_aaaa_file, rename_original_file)
from video_processing_engine.utils.paths import reports_path
from video_processing_engine.vars import dev
from video_processing_engine.utils.common import now

import sys

# def parse_json(json_data: dict) -> Optional[Tuple]:
#   country_code = json_data.get('country_code', None)
#   customer_id = json_data.get('customer_id', None)
#   contract_id = json_data.get('contract_id', None)
#   order_id = json_data.get('order_id', None)
#   store_id = json_data.get('store_id', None)
#   area_code = json_data.get('area_code', None)
#   camera_id = json_data.get('camera_id', None)
#   if all([country_code, customer_id, contract_id, order_id,
#           store_id, area_code, camera_id]):
#     return (country_code, customer_id, contract_id, order_id,
#              store_id, area_code, camera_id)
#   else:
#     return None


# _dict = {"country_code": "in", 'customer_id': "0001", 'contract_id': '01', 'order_id': '01', 'store_id': '01', ''}

# json_obj = {"country_code": "in", "customer_id": "0004", "contract_id": "20", "order_id": "6", "store_id": "9", "camera_id": "4", "area_code": "x", "use_stored": False, "original_file": "/home/xames3/Desktop/video_processing_engine/demo/minidemo_march_5/4_hr.mp4", "camera_address": "192.168.0.5",
#             "camera_port": "554", "camera_username": "admin", "camera_password": "user@1234", "stream_duration": 150, "select_sample": False, "sampling_rate": "50", "perform_compression": True, "perform_trimming": True, "trim_compressed": True, "compression_ratio": "60", "number_of_clips": "5"}

# json_obj = json.dumps(json_obj)

def start_all(json_obj: Union[bytes, str]) -> None:
  try:
    start = now()
    print()
    print(f'DEBUGGING Active below at {start}\n')
    upload = s3_queue_list = temp_list = []
    compression_ratio = 50
    json_data = json.loads(json_obj)
    bucket = bucket_name(json_data.get('country_code', None),
                        json_data.get('customer_id', None),
                        json_data.get('contract_id', None),
                        json_data.get('order_id', None))
    order = order_name(json_data.get('store_id', None),
                       json_data.get('area_code', None),
                       json_data.get('camera_id', None),None)
    print(f'Bucket name is {bucket} & Order name is {order}.')
    use_stored = json_data.get('use_stored', None)
    if use_stored:
      print('Choosing a stored video...')
      original_file = json_data.get('original_file', None)
    else:
      print('Choosing live video...')
      original_file = contine_recording(json_data.get('camera_address', None),
                                        json_data.get('camera_port', None),
                                        json_data.get('camera_username', None),
                                        json_data.get('camera_password', None),
                                        json_data.get('stream_duration', None))
    cloned_file = rename_original_file(original_file, bucket, order)
    print('Creating a copy for archiving on AWS Glacier...')
    archived_file = create_copy(cloned_file)
    print('Archive created!')
    select_sample = json_data.get('select_sample', None)
    if select_sample:
      print('Sampling is to be done on the video...')
      sampling_rate = json_data.get('sampling_rate', None)
      temp = trim_sample_section(cloned_file, int(sampling_rate))
      temp_list.append(temp)
      print('Video sampled as per the sampling rate.')
    perform_compression = json_data.get('perform_compression', None)
    perform_trimming = json_data.get('perform_trimming', None)
    if perform_trimming:
      print('Trimming is selected...')
      trim_compressed = json_data.get('trim_compressed', None)
    else:
      trim_compressed = False
    final_file = rename_aaaa_file(cloned_file, video_type(perform_compression,
                                                          perform_trimming, trim_compressed))
    # modify_fps = json_data.get('modify_fps', None)
    if perform_compression:
      print('Performing video compression...')
      compression_ratio = int(json_data.get('compression_ratio', None))
      # if modify_fps:
      #   modified_fps = json_data.get('modified_fps', None)
      # else:
      #   modified_fps = fps(cloned_file)
      temp = compress_video(final_file, compression_ratio)
      print('Video compressed!')
      temp_list.append(temp)
      if trim_compressed:
        print('Compressed video needs to be trimmed in equal parts...')
        number_of_clips = json_data.get('number_of_clips', None)
        upload = trim_num_parts(final_file, int(number_of_clips))
        print('Videos trimmed!')
    elif perform_trimming:
      print('Uncompressed video needs to be trimmed in equal parts...')
      number_of_clips = json_data.get('number_of_clips', None)
      upload = trim_num_parts(final_file, int(number_of_clips))
      print('Videos trimmed!')
    upload.append(final_file)
    try:
      create_s3_bucket(access_key='AKIAR4DHCUP262T3WIUX',
                      secret_key='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',
                      bucket_name=bucket)
    except Exception as error:
      pass
    print(f'"{bucket}" bucket created on S3.')
    urls = []
    for file in upload:
      urls.append(file)
      url = upload_to_bucket('AKIAR4DHCUP262T3WIUX',
                            'B2ii3+34AigsIx0wB1ZU01WLNY6DYRbZttyeTo+5',
                             bucket, file)
      urls.append(url)
    for file in temp_list:
      os.remove(file)
    with open(os.path.join(reports_path, f'{bucket}.csv'),
              'a', encoding=dev.DEF_CHARSET) as csv_file:
      _file = csv.writer(csv_file, delimiter='\n', quoting=csv.QUOTE_MINIMAL)
      _file.writerow(urls)
    print(f'Total time taken for processing this order is {now() - start}.')
  except Exception as error:
    print(error)
    print("An error occured at {}".format(sys.exc_info()[-1].tb_lineno))


# start_all(json_obj)
