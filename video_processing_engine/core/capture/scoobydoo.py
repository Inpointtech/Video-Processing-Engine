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
                                                  datetime_to_utc, file_size,
                                                  now, timestamp_dirname)
from video_processing_engine.utils.generate import video_type
from video_processing_engine.utils.local import filename
from video_processing_engine.utils.logs import log as _log
from video_processing_engine.utils.opencvapi import (camera_live,
                                                     configure_camera_url)
from video_processing_engine.utils.paths import live as _lr


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
    camera_timeout: Maximum time to wait until disconnection occurs.

  Returns:
    FFMPEG compatible & capable string for video recording over RTSP. 
  """
  timeout = float(camera_timeout)
  ffmpeg = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
  return (f'{ffmpeg} -loglevel error -y -rtsp_transport tcp -i {source} '
          f'-vcodec copy -acodec copy -t {duration} {file_name} '
          f'-timeout {timeout}')


def live(bucket_name: str,
         order_name: str,
         run_date: str,
         start_time: str,
         end_time: str,
         camera_address: str,
         camera_username: str = 'xames3',
         camera_password: str = 'iamironman',
         camera_port: Union[int, str] = 554,
         camera_timeout: Union[float, int, str] = 30.0,
         timestamp_format: str = '%H:%M:%S',
         log: logging.Logger = None) -> Optional[str]:
  """Record live videos based on time duration using FFMPEG.

  Args:
    bucket_name: S3 bucket name.
    order_name: Order name.
    run_date: Date when to record the video.
    start_time: Time when to start recording the video.
    end_time: Time when to stop recording the video.
    camera_address: Camera's IP address.
    camera_username: Camera username.
    camera_password: Camera password.
    camera_port: Camera port number.
    camera_timeout: Maximum time to wait until disconnection occurs.
    timestamp_format: Timestamp for checking the recording start time.
    log: Logger object.
  """
  log = _log(__file__) if log is None else log

  camera_port = int(camera_port)
  camera_timeout = float(camera_timeout)

  start_time, end_time = f'{run_date} {start_time}', f'{run_date} {end_time}'
  duration = calculate_duration(start_time, end_time, timestamp_format, True)
  force_close = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
  force_close = force_close.replace(tzinfo=timezone.utc).timestamp()

  vid_type = video_type(True, True, True)
  temp = os.path.join(_lr, f'{bucket_name}{order_name}')

  if not os.path.isdir(temp):
    os.mkdir(temp)
  temp_file = os.path.join(temp, f'{bucket_name}{order_name}{vid_type}.mp4')

  url = configure_camera_url(camera_address, camera_username,
                             camera_password, camera_port)
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
            output = concate_videos(temp, delete_old_files=True)
            if output:
              return output
        else:
          log.warning('Unable to record because of poor network connectivity.')
          slept_duration += camera_timeout
          log.warning('Compensating lost time & attempting after 30 secs.')
          time.sleep(camera_timeout)
    except Exception as error:
      log.critical(f'Something went wrong because of {error}')
