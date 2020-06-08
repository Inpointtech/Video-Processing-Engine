"""Complete video processing engine in one go."""

import json
import logging
import os
import shutil
from datetime import datetime
from csv import QUOTE_MINIMAL, writer
from pathlib import Path
from typing import List, Optional, Union

from video_processing_engine.core.capture.scoobydoo import live
from video_processing_engine.core.detect.motion import track_motion
from video_processing_engine.core.process.sylvester import compress_video
from video_processing_engine.core.process.stats import ctc
from video_processing_engine.core.process.trim import (trim_by_factor,
                                                       trim_by_points,
                                                       trim_num_parts,
                                                       trim_sample_section,
                                                       trim_sub_sample)
from video_processing_engine.core.redact.faces import redact_faces
from video_processing_engine.utils.boto_wrap import (create_s3_bucket,
                                                     upload_to_bucket)
from video_processing_engine.utils.bs_postgres import create_video_map_obj
from video_processing_engine.utils.common import now
from video_processing_engine.utils.generate import (bucket_name, order_name,
                                                    video_type)
from video_processing_engine.utils.local import (
    create_copy, rename_aaaa_file, rename_original_file)
from video_processing_engine.utils.logs import log
from video_processing_engine.utils.paths import downloads, reports
from video_processing_engine.vars import dev


def trimming_callable(json_data: dict,
                      final_file: str,
                      log: logging.Logger) -> Union[Optional[List], str]:
  """Trimming function."""
  trimmed = []

  trim_type = json_data['trim_type']
  clip_length = json_data.get('clip_length', 30)
  trim_factor = json_data.get('trim_factor', 's')
  last_clip = json_data.get('last_clip', False)
  number_of_clips = json_data.get('number_of_clips', 24)
  equal_distribution = json_data.get('equal_distribution', True)
  random_start = json_data.get('random_start', True)
  random_sequence = json_data.get('random_sequence', True)
  start_time = json_data['start_time']
  end_time = json_data['end_time']
  sample_start_time = json_data['sample_start_time']
  sample_end_time = json_data['sample_end_time']
  timestamp_format = json_data.get('timestamp_format', '%H:%M:%S')
  pt_start_time = json_data.get('point_start_time', 0)
  pt_end_time = json_data.get('point_end_time', 30)

  if trim_type == 'trim_by_factor':
    log.info('Trimming video by factor.')
    trimmed = trim_by_factor(final_file, trim_factor, clip_length, last_clip)
  elif trim_type == 'trim_num_parts':
    log.info(f'Trimming video in {number_of_clips} parts.')
    trimmed = trim_num_parts(final_file, number_of_clips, equal_distribution,
                             clip_length, random_start, random_sequence)
  elif trim_type == 'trim_sub_sample':
    log.info('Trimming portion of the video as per timestamp.')
    trimmed = trim_sub_sample(final_file, start_time, end_time,
                                  sample_start_time, sample_end_time,
                                  timestamp_format)
  elif trim_type == 'trim_by_points':
    log.info('Trimming video as per start & end time.')
    trimmed = trim_by_points(final_file, pt_start_time, pt_end_time,
                             trim_factor)

  return trimmed


def smash_db(order_id: int, videos: List, urls: List) -> None:
  """Smashes video information into database.

  Args:
    order_id: Primary key of Order ID.
    videos: List of names of videos uploaded to S3.
    urls: List of urls of video uploaded to S3.
  """
  order_id = int(order_id)
  video_obj = [{'file_name': os.path.basename(k), 'url': v,
                'video_id': Path(k).stem} for k, v in zip(videos, urls)]
  write_to_db(order_id, video_obj)


def write_to_db(order_id: Union[int, str], video_obj: List[dict]) -> None:
  """Write data to database.

  Args:
    order_id: Primary key of Order ID.
    video_obj: List of dictionary of file, id & url.
  """
  for idx in video_obj:
    video_id = idx['video_id']
    video_url = idx['url']
    video_file_name = idx['file_name']
    try:
      create_video_map_obj(order_id, video_id, video_url, video_file_name)
    except Exception as error:
      log.exception(error)


def spin(json_obj: str,
         run_date: str, curr: datetime, log: logging.Logger) -> None:
  """Spin the Video processing engine."""
  try:
    start = now()
    upload, junk, trimmed, urls = [], [], [], []
    org_file = None
    report = os.path.join(reports, '{}.csv')

    json_data = json.loads(json_obj)
    log.info('Parsed consumer JSON request.')

    country = json_data.get('country_code', 'xa')
    customer = json_data.get('customer_id', 0)
    contract = json_data.get('contract_id', 0)
    order = json_data.get('order_id', 0)
    store = json_data.get('store_id', 0)
    area = json_data.get('area_code', 'e')
    camera = json_data.get('camera_id', 0)
    use_stored = json_data.get('use_stored', False)
    start_time = json_data['start_time']
    end_time = json_data['end_time']
    address = json_data['camera_address']
    username = json_data.get('camera_username', 'admin')
    password = json_data['camera_password']
    port = json_data.get('camera_port', 554)
    timeout = (json_data.get('camera_timeout', 30.0))
    timestamp = json_data.get('timestamp_format', '%H:%M:%S')
    sampling_rate = json_data['sampling_rate']
    motion = json_data.get('analyze_motion', False)
    face = json_data.get('analyze_face', False)
    compress = json_data.get('perform_compression', True)
    trim = json_data.get('perform_trimming', True)
    trimpress = json_data.get('trim_compressed', True)
    db_order = json_data.get('order_pk', 0)

    log.info(f'Video processing engine started spinning for camera #{camera}')

    bucket = bucket_name(country, customer, contract, order, log)
    order = order_name(store, area, camera, curr, log)

    if use_stored:
      dl_file = json_data['sub_json']['stored_filename']
      org_file = os.path.join(downloads, f'{dl_file}.mp4')
      log.info('Using downloaded video for this order.')

      if not os.path.isfile(org_file):
        log.error('File not selected for processing.')
        raise Exception('[e] File not selected for processing.')

    else:
      log.info(f'Recording from camera #{camera} for this order.')
      org_file = live(bucket, order, run_date, start_time, end_time, address,
                      username, password, port, timeout, timestamp, log)

    if org_file:
      cloned = rename_original_file(org_file, bucket, order)
      temp = cloned

      log.info('Created backup of the original video.')
      # TODO(xames3): Add code to move this file to AWS Glacier.
      archived = create_copy(cloned)

      log.info('Commencing core processes, estimated time of completion is '
              f'{ctc(cloned, sampling_rate)}.')

      if motion:
        cloned = track_motion(cloned, log=log, debug_mode=False)

        if not cloned:
          cloned = archived

        log.info('Fixing up the symbolic link of the motion detected video.')
        shutil.move(cloned, temp)
        log.info('Symbolic link has been restored for motion detected video.')
        cloned = temp
      else:
        log.info('Skipping motion analysis.')

      log.info(f'Randomly sampling {sampling_rate}% of the original video.')

      temp = trim_sample_section(temp, sampling_rate)
      junk.append(temp)

      if face:
        temp = cloned
        cloned = redact_faces(cloned, log=log, debug_mode=False)

        if not cloned:
          cloned = archived

        log.info('Fixing up the symbolic link of the redacted video.')
        shutil.move(cloned, temp)
        log.info('Symbolic link has been restored for the redacted video.')
        cloned = temp
      else:
        log.info('Skipping face redaction.')

      if not trim:
        trimpress = False

      log.info('Renaming original video as per internal nomenclature.')
      final = rename_aaaa_file(cloned, video_type(compress, trim, trimpress))
      upload.append(final)

      if compress:
        log.info('Compressing video as required.')
        final = compress_video(final, log)

        if trimpress:
          trimmed = trimming_callable(json_data, final, log)

      elif trim:
        trimmed = trimming_callable(json_data, final, log)

      if trimmed:
        upload.extend(trimmed)

      try:
        create_s3_bucket('AKIAR4DHCUP262T3WIUX',
                         'B2ii3+34AigsIx0wB1ZU01WLNY6DYRbZttyeTo+5',
                         bucket, log)
      except Exception:
        pass

      log.info('Uploading video to the S3 bucket.')
      for idx, file in enumerate(upload):
        url = upload_to_bucket('AKIAR4DHCUP262T3WIUX',
                               'B2ii3+34AigsIx0wB1ZU01WLNY6DYRbZttyeTo+5',
                               bucket, file, log)
        urls.append(url)
        log.info(f'Uploaded {idx + 1}/{len(upload)} > '
                 f'{os.path.basename(file)} on to S3 bucket.')

      log.info('Exporting public URLs.')
      with open(report.format(bucket), 'a', encoding=dev.DEF_CHARSET) as _csv:
        writer(_csv, delimiter='\n', quoting=QUOTE_MINIMAL).writerow(urls)

      junk.extend(upload)

      # smash_db(db_order, upload, urls)
      log.info('Written values into the database.')

      log.info('Cleaning up the directory.')
      for idx, file in enumerate(junk):
        os.remove(file)
        log.warning(f'Removed file {idx + 1}/{len(junk)} > '
                    f'{os.path.basename(file)} from current machine.')

      log.info(f'Processing this order took around {now() - start}.')
  except KeyboardInterrupt:
    log.error('Spinner interrupted.')
  except Exception as error:
    log.exception(error)
    log.critical('Something went wrong while video processing was running.')


def phase_one(json_obj: str,
              run_date: str, curr: datetime, log: logging.Logger) -> None:
  """Just Phase One."""
  try:
    start = now()
    # upload, junk, trimmed, urls = [], [], [], []
    org_file = None
    # report = os.path.join(reports, '{}.csv')

    json_data = json.loads(json_obj)
    log.info('Parsed consumer JSON request.')

    country = json_data.get('country_code', 'xa')
    customer = json_data.get('customer_id', 0)
    contract = json_data.get('contract_id', 0)
    order = json_data.get('order_id', 0)
    store = json_data.get('store_id', 0)
    area = json_data.get('area_code', 'e')
    camera = json_data.get('camera_id', 0)
    use_stored = json_data.get('use_stored', False)
    start_time = json_data['start_time']
    end_time = json_data['end_time']
    address = json_data['camera_address']
    username = json_data.get('camera_username', 'admin')
    password = json_data['camera_password']
    port = json_data.get('camera_port', 554)
    timeout = (json_data.get('camera_timeout', 30.0))
    timestamp = json_data.get('timestamp_format', '%H:%M:%S')
    sampling_rate = json_data['sampling_rate']
    motion = json_data.get('analyze_motion', False)
    face = json_data.get('analyze_face', False)
    compress = json_data.get('perform_compression', True)
    trim = json_data.get('perform_trimming', True)
    trimpress = json_data.get('trim_compressed', True)
    db_order = json_data.get('order_pk', 0)

    log.info(f'Video processing engine started spinning for camera #{camera}')

    bucket = bucket_name(country, customer, contract, order, log)
    order = order_name(store, area, camera, curr, log)

    if use_stored:
      dl_file = json_data['sub_json']['stored_filename']
      org_file = os.path.join(downloads, f'{dl_file}.mp4')
      log.info('Using downloaded video for this order.')

      if not os.path.isfile(org_file):
        log.error('File not selected for processing.')
        raise Exception('[e] File not selected for processing.')

    else:
      log.info(f'Recording from camera #{camera} for this order.')
      org_file = live(bucket, order, run_date, start_time, end_time, address,
                      username, password, port, timeout, timestamp, log)

    # if org_file:
    #   cloned = rename_original_file(org_file, bucket, order)
    #   temp = cloned

    #   log.info('Created backup of the original video.')
    #   # TODO(xames3): Add code to move this file to AWS Glacier.
    #   archived = create_copy(cloned)

    #   log.info('Commencing core processes, estimated time of completion is '
    #            f'{ctc(cloned, sampling_rate)}.')

    #   if motion:
    #     cloned = track_motion(cloned, log=log, debug_mode=False)

    #     if not cloned:
    #       cloned = archived

    #     log.info('Fixing up the symbolic link of the motion detected video.')
    #     shutil.move(cloned, temp)
    #     log.info('Symbolic link has been restored for motion detected video.')
    #     cloned = temp
    #   else:
    #     log.info('Skipping motion analysis.')

    #   log.info(f'Randomly sampling {sampling_rate}% of the original video.')

    #   temp = trim_sample_section(temp, sampling_rate)
    #   junk.append(temp)

    #   if face:
    #     temp = cloned
    #     cloned = redact_faces(cloned, log=log, debug_mode=False)

    #     if not cloned:
    #       cloned = archived

    #     log.info('Fixing up the symbolic link of the redacted video.')
    #     shutil.move(cloned, temp)
    #     log.info('Symbolic link has been restored for the redacted video.')
    #     cloned = temp
    #   else:
    #     log.info('Skipping face redaction.')

    #   if not trim:
    #     trimpress = False

    #   log.info('Renaming original video as per internal nomenclature.')
    #   final = rename_aaaa_file(cloned, video_type(compress, trim, trimpress))
    #   upload.append(final)

    #   if compress:
    #     log.info('Compressing video as required.')
    #     final = compress_video(final, log)

    #     if trimpress:
    #       trimmed = trimming_callable(json_data, final, log)

    #   elif trim:
    #     trimmed = trimming_callable(json_data, final, log)

    #   if trimmed:
    #     upload.extend(trimmed)

    #   try:
    #     create_s3_bucket('AKIAR4DHCUP262T3WIUX',
    #                      'B2ii3+34AigsIx0wB1ZU01WLNY6DYRbZttyeTo+5',
    #                      bucket, log)
    #   except Exception:
    #     pass

    #   log.info('Uploading video to the S3 bucket.')
    #   for idx, file in enumerate(upload):
    #     url = upload_to_bucket('AKIAR4DHCUP262T3WIUX',
    #                            'B2ii3+34AigsIx0wB1ZU01WLNY6DYRbZttyeTo+5',
    #                            bucket, file, log)
    #     urls.append(url)
    #     log.info(f'Uploaded {idx + 1}/{len(upload)} > '
    #              f'{os.path.basename(file)} on to S3 bucket.')

    #   log.info('Exporting public URLs.')
    #   with open(report.format(bucket), 'a', encoding=dev.DEF_CHARSET) as _csv:
    #     writer(_csv, delimiter='\n', quoting=QUOTE_MINIMAL).writerow(urls)

    #   junk.extend(upload)

    #   # smash_db(db_order, upload, urls)
    #   log.info('Written values into the database.')

    #   log.info('Cleaning up the directory.')
    #   for idx, file in enumerate(junk):
    #     os.remove(file)
    #     log.warning(f'Removed file {idx + 1}/{len(junk)} > '
    #                 f'{os.path.basename(file)} from current machine.')

      log.info(f'Processing this order took around {now() - start}.')
  except KeyboardInterrupt:
    log.error('Spinner interrupted.')
  except Exception as error:
    log.exception(error)
    log.critical('Something went wrong while video processing was running.')
