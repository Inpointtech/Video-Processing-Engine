"""A subservice for showing statistics the videos."""

import os
from statistics import median
from typing import Tuple, Union

import cv2
import speedtest
from moviepy.editor import VideoFileClip as vfc

from video_processing_engine.utils.common import file_size, seconds_to_datetime
from video_processing_engine.utils.hasher import h_extension

video_file_extensions = ('.3gp', '.mp4', '.avi', '.webm',
                         '.mov', '.mkv', '.ogv', '.ts')


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


def check_usable_length(file: str,
                        num_clips: int = 24,
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


def minimum_sampling_rate(num_clips: int = 24,
                          minimum_length: int = 30) -> int:
  """Return minimum sampling rate required."""
  return num_clips * minimum_length


def completion_time_calculator(file: str,
                               sampling_rate: int,
                               factor: str = 's'):
  """Returns an approximate* time of completion of the activity."""
  temp_etc = median((float(duration(file)), os.stat(file).st_size)) / 100000
  trimming_bias = temp_etc + (temp_etc * 2.972158) + (sampling_rate * 0.125)
  upload_speed = speedtest.Speedtest().upload() / 1000000
  total_etc = (temp_etc / upload_speed) + trimming_bias
  return seconds_to_datetime(int(total_etc))
