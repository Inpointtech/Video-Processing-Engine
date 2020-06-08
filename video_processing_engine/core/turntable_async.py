"""Complete video processing engine in one go."""

import csv
import json
import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional, Union

from video_processing_engine.core.capture.recording import trigger_utc_capture
from video_processing_engine.core.detect.motion import track_motion
from video_processing_engine.core.process.compress import compress_video
from video_processing_engine.core.process.stats import \
    completion_time_calculator
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

import asyncio


def trimming_callable(json_data: dict,
                      final_file: str,
                      log: logging.Logger) -> Union[Optional[List], str]:
  """Trimming function."""
  trim_upload = []
  if json_data['trim_type'] == 'trim_by_factor':
    clip_length = int(json_data.get('clip_length', 30))
    trim_factor = json_data.get('trim_factor', 's')
    last_clip = json_data.get('last_clip', False)
    log.info('Trimming video by factor.')
    trim_upload = trim_by_factor(final_file, trim_factor,
                                  clip_length, last_clip)
  elif json_data['trim_type'] == 'trim_num_parts':
    number_of_clips = int(json_data.get('number_of_clips', 24))
    equal_distribution = json_data.get('equal_distribution', True)
    clip_length = int(json_data.get('clip_length', 30))
    random_start = json_data.get('random_start', True)
    random_sequence = json_data.get('random_sequence', True)
    log.info(f'Trimming video in {number_of_clips} parts.')
    trim_upload = trim_num_parts(final_file, int(number_of_clips),
                                  equal_distribution, clip_length,
                                  random_start, random_sequence)
  elif json_data['trim_type'] == 'trim_sub_sample':
    start_time = json_data['start_time']
    end_time = json_data['end_time']
    sample_start_time = json_data['sample_start_time']
    sample_end_time = json_data['sample_end_time']
    timestamp_format = json_data.get('timestamp_format', '%H:%M:%S')
    log.info('Trimming portion of the video as per timestamp.')
    trim_upload = trim_sub_sample(final_file, start_time, end_time,
                                  sample_start_time, sample_end_time,
                                  timestamp_format)
  elif json_data['trim_type'] == 'trim_by_points':
    start_time = int(json_data.get('point_start_time', 0))
    end_time = int(json_data.get('point_end_time', 30))
    trim_factor = json_data.get('trim_factor', 's')
    log.info('Trimming video as per start & end time.')
    trim_upload = trim_by_points(final_file, start_time, end_time,
                                  trim_factor)
  return trim_upload


def smash_db(order_id: int, videos: List, urls: List) -> None:
  """Smashes video information into database."""
  video_obj = [{'file_name': os.path.basename(k), 'url': v,
                'video_id': Path(k).stem} for k, v in zip(videos, urls)]
  write_to_db(order_id, video_obj)


def write_to_db(order_id: Union[int, str], video_obj: List[dict]) -> None:
  """Write data to database."""
  for idx in video_obj:
    video_id = idx['video_id']
    video_url = idx['url']
    video_file_name = idx['file_name']
    try:
      create_video_map_obj(order_id, video_id, video_url, video_file_name)
    except Exception as error:
      log.exception(error)


async def spin(json_obj: Union[bytes, str], log: logging.Logger) -> None:
  """Spin the Video processing engine."""
  try:
    start = now()
    upload_list, temp_list, trim_upload, urls = [], [], [], []
    original_file = None
    # log.info('Video processing engine started spinning.')
    json_data = json.loads(json_obj)
    log.info(f"Video processing engine started spinning for camera {json_data.get('camera_id', 0)}.")
    log.info('Parsed consumer JSON request.')
    bucket = bucket_name(json_data.get('country_code', 'xa'),
                         json_data.get('customer_id', 0),
                         json_data.get('contract_id', 0),
                         json_data.get('order_id', 0), log)
    order = order_name(json_data.get('store_id', 0),
                       json_data.get('area_code', 'e'),
                       json_data.get('camera_id', 0),
                       start, log)
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
      trigger = trigger_utc_capture
      original_file = trigger(bucket, order,
                              json_data['start_time'],
                              json_data['end_time'],
                              json_data.get('camera_timezone', 'UTC'),
                              json_data['camera_address'],
                              json_data.get('camera_username', 'admin'),
                              json_data['camera_password'],
                              int(json_data.get('camera_port', 554)),
                              float(json_data.get('camera_timeout', 30.0)),
                              json_data.get('timestamp_format', '%H:%M:%S'),
                              log)
    cloned_file = rename_original_file(original_file, bucket, order)
    temp_file = str(cloned_file)
    log.info('Created backup of the original video.')
    # TODO(xames3): Add code to move this file to AWS Glacier.
    archived_file = create_copy(cloned_file)
    sampling_rate = float(json_data['sampling_rate'])
    log.info('Commencing core processes, estimated time of completion is '
             f'{completion_time_calculator(cloned_file, sampling_rate)}.')
    if json_data.get('analyze_motion', False):
      cloned_file = track_motion(cloned_file, log=log, debug_mode=False)
      log.info('Fixing up the symbolic link of the motion detected video.')
      shutil.move(cloned_file, temp_file)
      log.info('Symbolic link has been restored for the motion detected video.')
      cloned_file = temp_file
    else:
      log.info('Skipping motion analysis.')
    log.info(f'Randomly sampling {sampling_rate}% of the original video.')
    temp = trim_sample_section(temp_file, sampling_rate)
    temp_list.append(temp)
    if json_data.get('analyze_face', False):
      temp_file = str(cloned_file)
      cloned_file = redact_faces(cloned_file, log=log, debug_mode=False)
      log.info('Fixing up the symbolic link of the redacted video.')
      shutil.move(cloned_file, temp_file)
      log.info('Symbolic link has been restored for the redacted video.')
      cloned_file = temp_file
    else:
      log.info('Skipping face redaction.')
    perform_compression = json_data.get('perform_compression', True)
    perform_trimming = json_data.get('perform_trimming', True)
    if perform_trimming:
      trim_compressed = json_data.get('trim_compressed', True)
    else:
      trim_compressed = False
    log.info('Renaming original video as per internal nomenclature.')
    final_file = rename_aaaa_file(cloned_file,
                                  video_type(perform_compression,
                                             perform_trimming,
                                             trim_compressed))
    upload_list.append(final_file)
    if perform_compression:
      log.info('Compressing video as required.')
      final_file = compress_video(final_file, log)
      if trim_compressed:
        trim_upload = trimming_callable(json_data, final_file, log)
    elif perform_trimming:
      trim_upload = trimming_callable(json_data, final_file, log)
    upload_list.extend(trim_upload)
    try:
      create_s3_bucket('AKIAR4DHCUP262T3WIUX',
                       'B2ii3+34AigsIx0wB1ZU01WLNY6DYRbZttyeTo+5',
                       bucket, log)
      log.info('Created bucket on Amazon S3 for this order.')
    except Exception:
      pass
    log.info('Uploading video to the S3 bucket.')
    for idx, file in enumerate(upload_list):
      url = upload_to_bucket('AKIAR4DHCUP262T3WIUX',
                             'B2ii3+34AigsIx0wB1ZU01WLNY6DYRbZttyeTo+5',
                             bucket, file, log)
      urls.append(url)
      log.info(f'Uploaded {idx + 1}/{len(upload_list)} > '
               f'{os.path.basename(file)} on to S3 bucket.')
    log.info('Exporting public URLs.')
    with open(os.path.join(reports, f'{bucket}.csv'),
              'a', encoding=dev.DEF_CHARSET) as csv_file:
      _file = csv.writer(csv_file, delimiter='\n', quoting=csv.QUOTE_MINIMAL)
      _file.writerow(urls)
    temp_list.extend(upload_list)
    smash_db(json_data.get('order_pk', 0), upload_list, urls)
    log.info('Written values into the database.')
    log.info('Cleaning up the directory.')
    for idx, file in enumerate(temp_list):
      os.remove(file)
      log.warning(f'Removed file {idx + 1}/{len(temp_list)} > '
                  f'{os.path.basename(file)} from current machine.')
    log.info('Total time taken for processing this order was '
             f'{now() - start}.')
  except KeyboardInterrupt:
    log.error('Video processing engine interrupted.')
    exit(0)
  except Exception as error:
    log.exception(error)
    log.critical('Something went wrong while video processing was running.')


async def run_command_shell(command: str):
  """Run command in subprocess (shell)

  Note:
    This can be used if you wish to execute e.g. "copy"
    on Windows, which can only be executed in the shell.
  """
  _log = log(__file__)
  process = await asyncio.create_subprocess_shell(command,
                                                stderr=asyncio.subprocess.PIPE)
  _, stderr = await process.communicate()
  result = stderr.decode().strip()
  return result


def make_chunks(l, n):
  """Yield successive n-sized chunks from l.

  Note:
    Taken from https://stackoverflow.com/a/312464
  """
  for i in range(0, len(l), n):
    yield l[i:i + n]


def run_asyncio_commands(tasks, max_concurrent_tasks=0):
  """Run tasks asynchronously using asyncio and return results

  If max_concurrent_tasks are set to 0, no limit is applied.

  Note:
    By default, Windows uses SelectorEventLoop, which does not support
    subprocesses. Therefore ProactorEventLoop is used on Windows.
    https://docs.python.org/3/library/asyncio-eventloops.html#windows
  """

  all_results = []

  if max_concurrent_tasks == 0:
    chunks = [tasks]
  else:
    chunks = make_chunks(l=tasks, n=max_concurrent_tasks)

  for tasks_in_chunk in chunks:
    loop = asyncio.get_event_loop()
    commands = asyncio.gather(*tasks_in_chunk)
    results = loop.run_until_complete(commands)
    all_results += results
    loop.close()
  return all_results


async def main(lis):
  loop = asyncio.get_running_loop()
  futures = [loop.run_in_executor(None, spin, (i, log(__file__))) for i in lis]
  results = await asyncio.gather(*futures)


if __name__ == '__main__':
  st = "17:36:00"
  et = "17:37:00"

  a = {"country_code": "in", "customer_id": "11", "contract_id": "22", "order_id": "33", "store_id": "44", "camera_id": "55", "area_code": "x", "use_stored": False, "access_mode": "s3", "public_url": "", "azure_account_name": "", "azure_account_key": "", "azure_container_name": "", "azure_blob_name": "", "remote_username": False, "remote_password": False, "remote_public_address": False, "remote_file": False, "s3_access_key": "", "s3_secret_key": "", "s3_url": "", "teamviewer_file": "test.mp4", "s3_bucket_name": False, "start_time": st, "end_time": et, "camera_address": "203.192.197.184", "camera_port": "9000", "camera_username": "admin", "camera_password": "AGXIDJ", "timestamp_format": False, "select_sample": True, "sampling_rate": "5", "perform_compression": True, "perform_trimming": True, "trim_compressed": True, "trim_type": "trim_by_factor", "compression_ratio": "60", "number_of_clips": "24", "equal_distribution": True, "clip_length": 30, "trim_factor": "s", "last_clip": False, "sample_start_time": "14:20:00", "sample_end_time": "14:25:00", "camera_timezone": "Asia/Kolkata", "ui_timestamp_format": "%Y-%m-%d %H:%M:%S", "point_start_time": 0, "point_end_time": 30, "analyze_motion": False, "analyze_face": False}

  b = {"country_code": "in", "customer_id": "11", "contract_id": "22", "order_id": "33", "store_id": "44", "camera_id": "56", "area_code": "x", "use_stored": False, "access_mode": "s3", "public_url": "", "azure_account_name": "", "azure_account_key": "", "azure_container_name": "", "azure_blob_name": "", "remote_username": False, "remote_password": False, "remote_public_address": False, "remote_file": False, "s3_access_key": "", "s3_secret_key": "", "s3_url": "", "teamviewer_file": "test.mp4", "s3_bucket_name": False, "start_time": st, "end_time": et, "camera_address": "203.192.197.184", "camera_port": "9001", "camera_username": "admin", "camera_password": "USER@1234", "timestamp_format": False, "select_sample": True, "sampling_rate": "5", "perform_compression": True, "perform_trimming": True, "trim_compressed": True, "trim_type": "trim_by_factor", "compression_ratio": "60", "number_of_clips": "24", "equal_distribution": True, "clip_length": 30, "trim_factor": "s", "last_clip": False, "sample_start_time": "14:20:00", "sample_end_time": "14:25:00", "camera_timezone": "Asia/Kolkata", "ui_timestamp_format": "%Y-%m-%d %H:%M:%S", "point_start_time": 0, "point_end_time": 30, "analyze_motion": False, "analyze_face": False}

  c = {"country_code": "in", "customer_id": "11", "contract_id": "22", "order_id": "33", "store_id": "44", "camera_id": "57", "area_code": "x", "use_stored": False, "access_mode": "s3", "public_url": "", "azure_account_name": "", "azure_account_key": "", "azure_container_name": "", "azure_blob_name": "", "remote_username": False, "remote_password": False, "remote_public_address": False, "remote_file": False, "s3_access_key": "", "s3_secret_key": "", "s3_url": "", "teamviewer_file": "test.mp4", "s3_bucket_name": False, "start_time": st, "end_time": et, "camera_address": "203.192.197.184", "camera_port": "9002", "camera_username": "admin", "camera_password": "user@1234", "timestamp_format": False, "select_sample": True, "sampling_rate": "5", "perform_compression": True, "perform_trimming": True, "trim_compressed": True, "trim_type": "trim_by_factor", "compression_ratio": "60", "number_of_clips": "24", "equal_distribution": True, "clip_length": 30, "trim_factor": "s", "last_clip": False, "sample_start_time": "14:20:00", "sample_end_time": "14:25:00", "camera_timezone": "Asia/Kolkata", "ui_timestamp_format": "%Y-%m-%d %H:%M:%S", "point_start_time": 0, "point_end_time": 30, "analyze_motion": False, "analyze_face": False}

  d = {"country_code": "in", "customer_id": "11", "contract_id": "22", "order_id": "33", "store_id": "44", "camera_id": "58", "area_code": "x", "use_stored": False, "access_mode": "s3", "public_url": "", "azure_account_name": "", "azure_account_key": "", "azure_container_name": "", "azure_blob_name": "", "remote_username": False, "remote_password": False, "remote_public_address": False, "remote_file": False, "s3_access_key": "", "s3_secret_key": "", "s3_url": "", "teamviewer_file": "test.mp4", "s3_bucket_name": False, "start_time": st, "end_time": et, "camera_address": "203.192.197.184", "camera_port": "9003", "camera_username": "admin", "camera_password": "user@1234", "timestamp_format": False, "select_sample": True, "sampling_rate": "5", "perform_compression": True, "perform_trimming": True, "trim_compressed": True, "trim_type": "trim_by_factor", "compression_ratio": "60", "number_of_clips": "24", "equal_distribution": True, "clip_length": 30, "trim_factor": "s", "last_clip": False, "sample_start_time": "14:20:00", "sample_end_time": "14:25:00", "camera_timezone": "Asia/Kolkata", "ui_timestamp_format": "%Y-%m-%d %H:%M:%S", "point_start_time": 0, "point_end_time": 30, "analyze_motion": False, "analyze_face": False}

  a = json.dumps(a)
  b = json.dumps(b)
  c = json.dumps(c)
  d = json.dumps(d)

  cmds = [a, b, c, d]
  loop = asyncio.get_event_loop()
  futures = [loop.run_in_executor(None, spin, (i, log(__file__))) for i in cmds]
  loop.run_forever()

  # tasks = []
  # for command in cmds:
  #   tasks.append(run_command_shell(*command))

  # results = run_asyncio_commands(tasks, max_concurrent_tasks=4)
  # end = time.time()
  # rounded_end = ('{0:.4f}'.format(round(end-start, 4)))
  # print('Script ran in about', str(rounded_end), 'seconds')
