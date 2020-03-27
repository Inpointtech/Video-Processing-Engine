"""Complete video processing engine in one go."""

import csv
import json
import os
from typing import Union

from video_processing_engine.core.capture import live
from video_processing_engine.core.process.compress import compress_video
from video_processing_engine.core.process.trim import (trim_by_factor,
                                                       trim_by_points,
                                                       trim_num_parts,
                                                       trim_sample_section,
                                                       trim_sub_sample)
from video_processing_engine.utils.aws import (create_s3_bucket,
                                               upload_to_bucket)
from video_processing_engine.utils.common import now
from video_processing_engine.utils.generate import (bucket_name, order_name,
                                                    video_type)
from video_processing_engine.utils.local import (
    create_copy, rename_aaaa_file, rename_original_file)
from video_processing_engine.utils.logs import log
from video_processing_engine.utils.paths import downloads, reports
from video_processing_engine.vars import dev

log = log(__file__)


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
    log.info('Video processing engine started spinning.')
    json_data = json.loads(json_obj)
    log.info('Parsed consumer JSON request.')
    bucket = bucket_name(json_data.get('country_code', 'xa'),
                         json_data.get('customer_id', 0),
                         json_data.get('contract_id', 0),
                         json_data.get('order_id', 0))
    order = order_name(json_data.get('store_id', 0),
                       json_data.get('area_code', 'e'),
                       json_data.get('camera_id', 0),
                       start)
    use_stored = json_data.get('use_stored', False)
    if use_stored:
      stored_filename = json_data['sub_json']['stored_filename']
      original_file = os.path.join(downloads, f'{stored_filename}.mp4')
      log.info('Using downloaded video for this order.')
      if not os.path.isfile(original_file):
        log.error('File not selected for processing.')
        raise Exception('[e] File not selected for processing.')
    else:
      log.info('Recording from live camera for this order.')
      lc = live.trigger_live_capture
      # lc = live.trigger_utc_capture
      original_file = lc(bucket, order,
                         json_data.get('start_time', None),
                         json_data.get('end_time', None),
                         json_data.get('camera_address', None),
                         json_data.get('camera_username', None),
                         json_data.get('camera_password', None),
                         int(json_data.get('camera_port', 554)),
                         float(json_data.get('camera_timeout', 30.0)),
                         json_data.get('timestamp_format', '%H:%M:%S'))
    cloned_file = rename_original_file(original_file, bucket, order)
    log.info('Created backup of the original video.')
    # TODO(xames3): Add code to move this file to AWS Glacier.
    archived_file = create_copy(cloned_file)
    select_sample = json_data.get('select_sample', None)
    if select_sample:
      sampling_rate = int(json_data.get('sampling_rate', None))
      log.info(f'Randomly sampling {sampling_rate}% of the original video.')
      temp = trim_sample_section(cloned_file, sampling_rate)
      temp_list.append(temp)
    perform_compression = json_data.get('perform_compression', None)
    perform_trimming = json_data.get('perform_trimming', None)
    if perform_trimming:
      trim_compressed = json_data.get('trim_compressed', None)
    else:
      trim_compressed = False
    log.info('Renaming roriginal video as per internal nomenclature.')
    final_file = rename_aaaa_file(cloned_file,
                                  video_type(perform_compression,
                                             perform_trimming,
                                             trim_compressed))
    upload_list.append(final_file)
    if perform_compression:
      compression_ratio = int(json_data.get('compression_ratio',
                                            compression_ratio))
      # temp = compress_video(final_file, compression_ratio)
      # temp_list.append(temp)
      if trim_compressed:
        if json_data.get('trim_type', None) == 'trim_by_factor':
          clip_length = int(json_data.get('clip_length', 30))
          trim_factor = json_data.get('trim_factor', 's')
          last_clip = json_data.get('last_clip', False)
          log.info('Trimming video by factor.')
          trim_upload = trim_by_factor(final_file, trim_factor,
                                       clip_length, last_clip)
        elif json_data.get('trim_type', None) == 'trim_num_parts':
          number_of_clips = int(json_data.get('number_of_clips', 24))
          equal_distribution = json_data.get('equal_distribution', True)
          clip_length = int(json_data.get('clip_length', 30))
          log.info(f'Trimming video in {number_of_clips} parts.')
          trim_upload = trim_num_parts(final_file, int(number_of_clips),
                                       equal_distribution, clip_length)
        elif json_data.get('trim_type', None) == 'trim_sub_sample':
          start_time = json_data.get('start_time', None)
          end_time = json_data.get('end_time', None)
          sample_start_time = json_data.get('sample_start_time', None)
          sample_end_time = json_data.get('sample_end_time', None)
          timestamp_format = json_data.get('timestamp_format', '%H:%M:%S')
          log.info('Trimming portion of the video as per timestamp.')
          trim_upload = trim_sub_sample(final_file, start_time, end_time,
                                        sample_start_time, sample_end_time,
                                        timestamp_format)
        elif json_data.get('trim_type', None) == 'trim_by_points':
          start_time = int(json_data.get('point_start_time', 0))
          end_time = int(json_data.get('point_end_time', 30))
          trim_factor = json_data.get('trim_factor', 's')
          log.info('Trimming video as per start & end time.')
          trim_upload = trim_by_points(final_file, start_time, end_time,
                                       trim_factor)
    elif perform_trimming:
      if json_data.get('trim_type', None) == 'trim_by_factor':
        clip_length = int(json_data.get('clip_length', 30))
        trim_factor = json_data.get('trim_factor', 's')
        last_clip = json_data.get('last_clip', False)
        log.info('Trimming video by factor.')
        trim_upload = trim_by_factor(final_file, trim_factor,
                                     clip_length, last_clip)
      elif json_data.get('trim_type', None) == 'trim_num_parts':
        number_of_clips = int(json_data.get('number_of_clips', 24))
        equal_distribution = json_data.get('equal_distribution', True)
        clip_length = int(json_data.get('clip_length', 30))
        log.info('Trimming video in {number_of_clips} parts.')
        trim_upload = trim_num_parts(final_file, int(number_of_clips),
                                     equal_distribution, clip_length)
      elif json_data.get('trim_type', None) == 'trim_sub_sample':
        start_time = json_data.get('start_time', None)
        end_time = json_data.get('end_time', None)
        sample_start_time = json_data.get('sample_start_time', None)
        sample_end_time = json_data.get('sample_end_time', None)
        timestamp_format = json_data.get('timestamp_format', '%H:%M:%S')
        log.info('Trimming portion of the video as per timestamp.')
        trim_upload = trim_sub_sample(final_file, start_time, end_time,
                                      sample_start_time, sample_end_time,
                                      timestamp_format)
      elif json_data.get('trim_type', None) == 'trim_by_points':
        start_time = int(json_data.get('point_start_time', 0))
        end_time = int(json_data.get('point_end_time', 30))
        trim_factor = json_data.get('trim_factor', 's')
        log.info('Trimming video as per start & end time.')
        trim_upload = trim_by_points(final_file, start_time, end_time,
                                      trim_factor)
    upload_list.extend(trim_upload)
    create_s3_bucket('AKIAR4DHCUP262T3WIUX',
                     'B2ii3+34AigsIx0wB1ZU01WLNY6DYRbZttyeTo+5',
                     bucket_name=bucket)
    log.info('Created bucket on Amazon S3 for this order.')
    log.info('Uploading video to the S3 bucket.')
    for idx, file in enumerate(upload_list):
      url = upload_to_bucket('AKIAR4DHCUP262T3WIUX',
                             'B2ii3+34AigsIx0wB1ZU01WLNY6DYRbZttyeTo+5',
                             bucket, file)
      urls.append(url)
      log.info(f'Uploaded {idx + 1}/{len(upload_list)} > '
               f'{os.path.basename(file)} on to S3 bucket.')
    log.info('Exporting public URLs.')
    with open(os.path.join(reports, f'{bucket}.csv'),
              'a', encoding=dev.DEF_CHARSET) as csv_file:
      _file = csv.writer(csv_file, delimiter='\n', quoting=csv.QUOTE_MINIMAL)
      _file.writerow(urls)
    temp_list.extend(upload_list)
    log.info('Cleaning up the directory.')
    for idx, file in enumerate(temp_list):
      os.remove(file)
      log.warning(f'Removed file {idx + 1}/{len(temp_list)} > '
                  f'{os.path.basename(file)} from current machine.')
    log.info('Total time taken for processing this order was '
             f'{now() - start}.')
  except Exception as error:
    log.critical('Something went wrong while video processing was running.')
    raise error
