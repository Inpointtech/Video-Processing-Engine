"""Complete video processing engine in one go."""

import csv
import json
import os
from typing import Union

from video_processing_engine.core.capture.live import \
    trigger_live_capture as lc
from video_processing_engine.core.process.compress import compress_video
from video_processing_engine.core.process.trim import (trim_by_factor,
                                                       trim_num_parts,
                                                       trim_sample_section,
                                                       trim_sub_sample,
                                                       trim_by_points)
from video_processing_engine.utils.aws import (create_s3_bucket,
                                               upload_to_bucket)
from video_processing_engine.utils.common import now
from video_processing_engine.utils.generate import (bucket_name, order_name,
                                                    video_type)
from video_processing_engine.utils.local import (
    create_copy, rename_aaaa_file, rename_original_file)
from video_processing_engine.utils.paths import downloads, reports_path
from video_processing_engine.vars import dev


def spin(json_obj: Union[bytes, str]) -> None:
  """Spin the Video processing engine."""
  try:
    start = now()
    upload_list = []
    temp_list = []
    trim_upload = []
    urls = []
    compression_ratio = 50
    original_file = None
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
      original_file = os.path.join(downloads,
                                   f'{json_data.get("stored_filename", None)}.mp4')
      file_status = True
      if file_status is None:
        raise Exception('File not selected.')
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
      print('Trimming sample portion of the video...')
      temp = trim_sample_section(cloned_file, int(sampling_rate))
      temp_list.append(temp)
    perform_compression = json_data.get('perform_compression', None)
    perform_trimming = json_data.get('perform_trimming', None)
    if perform_trimming:
      trim_compressed = json_data.get('trim_compressed', None)
    else:
      trim_compressed = False
    final_file = rename_aaaa_file(cloned_file,
                                  video_type(perform_compression,
                                             perform_trimming,
                                             trim_compressed))
    # modify_fps = json_data.get('modify_fps', None)
    upload_list.append(final_file)
    if perform_compression:
      compression_ratio = int(json_data.get('compression_ratio',
                                            compression_ratio))
      # if modify_fps:
      #   modified_fps = json_data.get('modified_fps', None)
      # else:
      #   modified_fps = fps(cloned_file)
      print('Compressing the video...')
      temp = compress_video(final_file, compression_ratio)
      temp_list.append(temp)
      if trim_compressed:
        if json_data.get('trim_type', None) == 'trim_by_factor':
          clip_length = json_data.get('clip_length', 30)
          trim_factor = json_data.get('trim_factor', 's')
          last_clip = json_data.get('last_clip', False)
          trim_upload = trim_by_factor(final_file, trim_factor,
                                       clip_length, last_clip)
        elif json_data.get('trim_type', None) == 'trim_num_parts':
          number_of_clips = json_data.get('number_of_clips', 24)
          equal_distribution = json_data.get('equal_distribution', True)
          clip_length = json_data.get('clip_length', 30)
          trim_upload = trim_num_parts(final_file, int(number_of_clips),
                                       equal_distribution, clip_length)
        elif json_data.get('trim_type', None) == 'trim_sub_sample':
          start_time = json_data.get('start_time', None)
          end_time = json_data.get('end_time', None)
          sample_start_time = json_data.get('sample_start_time', None)
          sample_end_time = json_data.get('sample_end_time', None)
          timestamp_format = json_data.get('timestamp_format', '%H:%M:%S')
          trim_upload = trim_sub_sample(final_file, start_time, end_time,
                                        sample_start_time, sample_end_time,
                                        timestamp_format)
        elif json_data.get('trim_type', None) == 'trim_by_points':
          start_time = json_data.get('point_start_time', 0)
          end_time = json_data.get('point_end_time', 30)
          trim_factor = json_data.get('trim_factor', 's')
          trim_upload = trim_by_points(final_file, start_time, end_time,
                                       trim_factor)
    elif perform_trimming:
      if json_data.get('trim_type', None) == 'trim_by_factor':
        clip_length = json_data.get('clip_length', 30)
        trim_factor = json_data.get('trim_factor', 's')
        last_clip = json_data.get('last_clip', False)
        trim_upload = trim_by_factor(final_file, trim_factor,
                                     clip_length, last_clip)
      elif json_data.get('trim_type', None) == 'trim_num_parts':
        number_of_clips = json_data.get('number_of_clips', 24)
        equal_distribution = json_data.get('equal_distribution', True)
        clip_length = json_data.get('clip_length', 30)
        trim_upload = trim_num_parts(final_file, int(number_of_clips),
                                     equal_distribution, clip_length)
      elif json_data.get('trim_type', None) == 'trim_sub_sample':
        start_time = json_data.get('start_time', None)
        end_time = json_data.get('end_time', None)
        sample_start_time = json_data.get('sample_start_time', None)
        sample_end_time = json_data.get('sample_end_time', None)
        timestamp_format = json_data.get('timestamp_format', '%H:%M:%S')
        trim_upload = trim_sub_sample(final_file, start_time, end_time,
                                      sample_start_time, sample_end_time,
                                      timestamp_format)
      elif json_data.get('trim_type', None) == 'trim_by_points':
          start_time = json_data.get('point_start_time', 0)
          end_time = json_data.get('point_end_time', 30)
          trim_factor = json_data.get('trim_factor', 's')
          trim_upload = trim_by_points(final_file, start_time, end_time,
                                       trim_factor)
    upload_list.extend(trim_upload)
    print('Creating S3 bucket...')
    create_s3_bucket('',
                     '',
                     bucket_name=bucket)
    print('Uploading trimmed videos onto S3 bucket...')
    for file in upload_list:
      url = upload_to_bucket('',
                             '',
                             bucket, file)
      urls.append(url)
    print('Exporting public URLs...')
    with open(os.path.join(reports_path, f'{bucket}.csv'),
              'a', encoding=dev.DEF_CHARSET) as csv_file:
      _file = csv.writer(csv_file, delimiter='\n', quoting=csv.QUOTE_MINIMAL)
      _file.writerow(urls)
    temp_list.extend(upload_list)
    print('Cleaning up....')
    for file in temp_list:
      os.remove(file)
    print(f'Total time taken for processing this order is {now() - start}.')
  except Exception as error:
    print(error)
    raise error
