"""Complete video processing engine in one go."""

import csv
import json
import os
from typing import Union

from video_processing_engine.core.capture.live import \
    trigger_live_capture as lc
from video_processing_engine.core.process.compress import compress_video
from video_processing_engine.core.process.trim import (trim_num_parts,
                                                       trim_sample_section)
from video_processing_engine.utils.aws import (create_s3_bucket,
                                               upload_to_bucket)
from video_processing_engine.utils.common import now
from video_processing_engine.utils.generate import (bucket_name, order_name,
                                                    video_type)
from video_processing_engine.utils.local import (create_copy, rename_aaaa_file,
                                                 rename_original_file)
from video_processing_engine.utils.paths import reports_path
from video_processing_engine.vars import dev


def spin(json_obj: Union[bytes, str]) -> None:
  """Spin the Video processing engine."""
  try:
    start = now()
    upload = temp_list = []
    compression_ratio = 20
    json_data = json.loads(json_obj)
    bucket = bucket_name(json_data.get('country_code', 'xx'),
                         json_data.get('customer_id', 0),
                         json_data.get('contract_id', 0),
                         json_data.get('order_id', 0))
    order = order_name(json_data.get('store_id', 0),
                       json_data.get('area_code', 'e'),
                       json_data.get('camera_id', 0),
                       start)
    use_stored = json_data.get('use_stored', False)
    if use_stored:
      original_file = json_data.get('original_file', None)
    else:
      original_file = lc(bucket, order,
                         json_data.get('start_time', None),
                         json_data.get('end_time', None),
                         json_data.get('camera_address', None),
                         json_data.get('camera_username', None),
                         json_data.get('camera_password', None),
                         json_data.get('camera_port', 554),
                         float(json_data.get('camera_timeout', 30.0)),
                         json_data.get('timestamp_format', '%H:%M:%S'))
    cloned_file = rename_original_file(original_file, bucket, order)
    # TODO(xames3): Add code to move this file to AWS Glacier.
    archived_file = create_copy(cloned_file)
    select_sample = json_data.get('select_sample', None)
    if select_sample:
      sampling_rate = json_data.get('sampling_rate', None)
      temp = trim_sample_section(cloned_file, int(sampling_rate))
      temp_list.append(temp)
    perform_compression = json_data.get('perform_compression', None)
    perform_trimming = json_data.get('perform_trimming', None)
    if perform_trimming:
      trim_compressed = json_data.get('trim_compressed', None)
    else:
      trim_compressed = False
    final_file = rename_aaaa_file(cloned_file, video_type(perform_compression,
                                                          perform_trimming, trim_compressed))
    # modify_fps = json_data.get('modify_fps', None)
    if perform_compression:
      compression_ratio = int(json_data.get('compression_ratio', None))
      # if modify_fps:
      #   modified_fps = json_data.get('modified_fps', None)
      # else:
      #   modified_fps = fps(cloned_file)
      temp = compress_video(final_file, compression_ratio)
      temp_list.append(temp)
      if trim_compressed:
        number_of_clips = json_data.get('number_of_clips', None)
        upload = trim_num_parts(final_file, int(number_of_clips))
    elif perform_trimming:
      number_of_clips = json_data.get('number_of_clips', None)
      upload = trim_num_parts(final_file, int(number_of_clips))
    upload.append(final_file)
    # create_s3_bucket(json_data.get('aws_access_key', None),
    #                  json_data.get('aws_secret_key', None),
    #                  bucket_name=bucket)
    urls = []
    for file in upload:
      urls.append(file)
      # url = upload_to_bucket(json_data.get('aws_access_key', None),
      #                        json_data.get('aws_secret_key', None),
      #                        bucket, file)
      urls.append(url)
    for file in temp_list:
      os.remove(file)
    with open(os.path.join(reports_path, f'{bucket}.csv'),
              'a', encoding=dev.DEF_CHARSET) as csv_file:
      _file = csv.writer(csv_file, delimiter='\n', quoting=csv.QUOTE_MINIMAL)
      _file.writerow(urls)
    print(f'Total time taken for processing this order is {now() - start}.')
  except Exception as error:
    raise