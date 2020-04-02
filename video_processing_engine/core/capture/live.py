"""A subservice for storing live video over camera."""

import logging
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from video_processing_engine.core.process.concate import concate_videos
from video_processing_engine.core.process.stats import duration as drn
from video_processing_engine.utils.common import (calculate_duration,
                                                  datetime_to_utc,
                                                  file_size, now,
                                                  timestamp_dirname)
from video_processing_engine.utils.generate import video_type
from video_processing_engine.utils.local import filename
from video_processing_engine.utils.logs import log as _log
from video_processing_engine.utils.opencv import (camera_live,
                                                  configure_camera_url)
from video_processing_engine.utils.paths import live


def ffmpeg_str(source: str,
               file_name: str,
               duration: Union[timedelta, float, int, str],
               camera_timeout: Union[float, int, str] = 30.0) -> str:
  """Returns FFMPEG's main command to run using subprocess module.

  Returns FFMPEG's custom command for recording the live feed & storing
  it in a file for further processing.

  Args:
    source: RTSP camera url.
    file_name: Path where you need to save the output file.
    duration: Duration in secs that needs to be captured by FFMPEG.

  Returns:
    FFMPEG compatible & capable string for video recording over RTSP. 
  """
  ffmpeg = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
  return (f'{ffmpeg} -loglevel error -y -rtsp_transport tcp -i {source} '
          f'-vcodec copy -acodec copy -t {duration} {file_name} '
          f'-timeout {camera_timeout}')


def save_num_video(bucket_name: str,
                   order_name: str,
                   duration: Union[float, int, str],
                   num_of_clips: int,
                   camera_address: str,
                   camera_username: str = 'admin',
                   camera_password: str = 'iamironman') -> None:
  """Saves "N" number of live video streams."""
  vid_type = video_type(True, True, True)
  file = os.path.join(live, f'{bucket_name}{order_name}{vid_type}.mp4')
  for idx in range(1, num_of_clips + 1):
    file = filename(file, idx)
    url = configure_camera_url(
        camera_address, camera_username, camera_password)
    subprocess.check_call(ffmpeg_str(url, file, duration), shell=True)


def start_live_recording(bucket_name: str,
                         order_name: str,
                         start_time: str,
                         end_time: str,
                         camera_address: str,
                         camera_username: str = 'xames3',
                         camera_password: str = 'iamironman',
                         camera_port: Union[int, str] = 554,
                         camera_timeout: Union[float, int] = 30.0,
                         timestamp_format: str = '%H:%M:%S',
                         log: logging.Logger = None) -> Optional[str]:
  """Saves videos based on time duration."""
  log = _log(__file__) if log is None else log
  run_date = datetime.now().strftime('%Y-%m-%d')
  start_time, end_time = f'{run_date} {start_time}', f'{run_date} {end_time}'
  duration = calculate_duration(start_time, end_time, timestamp_format, True)
  force_close = datetime.strptime(
    end_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc).timestamp()
  vid_type = video_type(True, True, True)
  temp_path = os.path.join(live,
                           f'{bucket_name}{order_name}_{timestamp_dirname()}')
  if not os.path.isdir(temp_path):
    os.mkdir(temp_path)
  temp_file = os.path.join(temp_path,
                           f'{bucket_name}{order_name}{vid_type}.mp4')
  url = configure_camera_url(camera_address, camera_username,
                             camera_password, int(camera_port))
  slept_duration, idx = 0, 1
  if duration != 0:
    try:
      while True:
        if camera_live(camera_address, camera_port, camera_timeout, log):
          file = filename(temp_file, idx)
          log.info('Recording started for selected camera.')
          os.system(ffmpeg_str(url, file, duration, camera_timeout))
          stop_utc = now().replace(tzinfo=timezone.utc).timestamp()
          stop_secs = now().second
          _old_file = file_size(file)
          old_duration = stop_secs if _old_file == '300.0 bytes' else drn(file)
          duration = duration - old_duration - slept_duration
          slept_duration = 0
          idx += 1
          if (force_close <= stop_utc) or (duration <= 0):
            output = concate_videos(temp_path, delete_old_files=True)
            if output:
              return output
        else:
          log.warning('Unable to record because of poor network connectivity.')
          slept_duration += camera_timeout
          log.warning('Compensating lost time & attempting after 30 secs.')
          time.sleep(camera_timeout)
    except Exception as error:
      log.critical(f'Something went wrong because of {error}')


def trigger_live_capture(bucket_name: str,
                         order_name: str,
                         start_time: str,
                         end_time: str,
                         camera_address: str,
                         camera_username: str = 'xames3',
                         camera_password: str = 'iamironman',
                         camera_port: Union[int, str] = 554,
                         camera_timeout: Union[float, int] = 30.0,
                         timestamp_format: str = '%H:%M:%S',
                         log: logging.Logger = None) -> Optional[str]:
  """Starts video recording as per the triggering point."""
  log = _log(__file__) if log is None else log
  run_date = datetime.now().strftime('%Y-%m-%d')
  _start_time = f'{run_date} {start_time}'
  while True:
    if str(now()) >= _start_time:
      return start_live_recording(bucket_name, order_name, start_time,
                                  end_time, camera_address, camera_username,
                                  camera_password, camera_port, camera_timeout,
                                  timestamp_format, log)
    time.sleep(1.0)


def trigger_utc_capture(bucket_name: str,
                        order_name: str,
                        start_time: str,
                        end_time: str,
                        camera_timezone: str,
                        camera_address: str,
                        camera_username: str = 'xames3',
                        camera_password: str = 'iamironman',
                        camera_port: Union[int, str] = 554,
                        camera_timeout: Union[float, int] = 30.0,
                        timestamp_format: str = '%H:%M:%S',
                        ui_timestamp_format: str = '%Y-%m-%d %H:%M:%S',
                        log: logging.Logger = None) -> str:
  """Starts video recording as per the triggering point."""
  log = _log(__file__) if log is None else log
  run_date = datetime.now().strftime('%Y-%m-%d')
  _start_time = f'{run_date} {start_time}'
  _start_time = datetime_to_utc(_start_time,
                                camera_timezone,
                                ui_timestamp_format)
  log.info('Video processing engine is scheduled to start '
           f'recording at {_start_time}.')
  while True:
    if str(now()) == str(_start_time):
      log.info('Video processing engine has started recording.')
      recorded_file =  start_live_recording(bucket_name, order_name, start_time,
                                            end_time, camera_address,
                                            camera_username, camera_password,
                                            camera_port, camera_timeout,
                                            timestamp_format, log)
      log.info('Video processing engine has stopped recording.')
      if recorded_file is None:
        return 'RecordingError'
      else:
        return recorded_file
    time.sleep(1.0)
