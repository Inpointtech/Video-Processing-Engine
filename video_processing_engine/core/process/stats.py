"""A subservice for showing statistics the videos."""

import os
from statistics import median
from typing import Tuple, Union

import cv2
import speedtest
from moviepy.editor import VideoFileClip as vfc

from video_processing_engine.utils.common import check_internet, file_size, seconds_to_datetime
from video_processing_engine.utils.hasher import h_extension

video_file_extensions = ('.3gp', '.mp4', '.avi', '.webm', '.divx', '.f4v',
                         '.flv', '.m4v', '.mpg', '.mts', '.mxf', '.ogm', '.qt',
                         '.vob', '.wmv', '.3g2', '.3gpp', '.mov', '.mkv',
                         '.h265', '.ogv', '.ts', '.dat', '.m2ts', '.m2v',
                         '.3GP', '.MP4', '.AVI', '.WEBM', '.DIVX', '.F4V',
                         '.FLV', '.M4V', '.MPG', '.MTS', '.MXF', '.OGM', '.QT',
                         '.VOB', '.WMV', '.3G2', '.3GPP', '.MOV', '.MKV',
                         '.OGV', '.TS', '.DAT', '.M2TS', '.M2V', '.H265',
                         '.265')


def codec(file: str) -> str:
  """Returns type of codec used in the video file."""
  return dict(map(reversed, h_extension.items()))[os.path.splitext(file)[1][1:]]


def duration(file: str,
             for_humans: bool = False) -> Union[float, str, int]:
  """Returns duration of the video file."""
  if for_humans:
    mins, secs = divmod(vfc(file, audio=False).duration, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)
  else:
    return vfc(file, audio=False).duration


def bitrate(file: str) -> int:
  """Returns bitrate of the video file."""
  # You can find the reference code here:
  # https://www.ezs3.com/public/What_bitrate_should_I_use_when_encoding_my_video_How_do_I_optimize_my_video_for_the_web.cfm
  return (vfc(file, audio=False).size[0] * vfc(file, audio=False).size[1] *
          (vfc(file, audio=False).reader.nframes // vfc(file, audio=False).duration) * 0.07 // 1000)


def fps(file: str) -> Union[float, int]:
  """Returns fps of the video file."""
  return cv2.VideoCapture(file).get(cv2.CAP_PROP_FPS)


def check_usable_length(file: str, num_clips: int = 24,
                        minimum_length: int = 30) -> bool:
  """Returns boolean value after checking usuable video length."""
  return True if duration(file) >= num_clips * minimum_length else False


def new_bitrate(file: str) -> int:
  """Returns bitrate of the video file."""
  import subprocess

  bit = subprocess.check_output(f"ffprobe -hide_banner -loglevel 0 -of flat -i '{file}' -select_streams v -show_entries 'format=bit_rate'", shell=True)
  return int(bit.decode().replace('"', '').strip('format.bit_rate='))


def all_stats(file: str) -> Tuple:
  """Returns all the statistics of the video file."""
  return (os.path.basename(file), duration(file, True), int(bitrate(file)),
          fps(file), codec(file), file_size(file), check_usable_length(file))


def usuable_difference(video_length: Union[float, int],
                       num_clips: int = 24,
                       minimum_length: int = 30) -> bool:
  """Returns boolean value after checking the difference."""
  return True if video_length >= num_clips * minimum_length else False


def minimum_sampling_rate(num_clips: int = 24, minimum_length: int = 30) -> int:
  """Return minimum sampling rate required."""
  return num_clips * minimum_length


def ctc(file: str,
        sampling_rate: Union[float, int, str],
        factor: str = 's') -> str:
  """Returns an approximate* time of completion of the activity."""
  sampling_rate = float(sampling_rate)
  length = float(duration(file))

  temp_etc = median((length, os.stat(file).st_size)) / 100000
  bias = temp_etc + (sampling_rate * length * 0.05)

  if check_internet():
    upload_speed = speedtest.Speedtest().upload() / 1000000
  else:
    upload_speed = 0.00001

  total_etc = (temp_etc / upload_speed) + bias
  return seconds_to_datetime(int(total_etc))
