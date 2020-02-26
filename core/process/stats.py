"""A subservice for showing statistics the videos."""

import os
from typing import Optional, Tuple, Union

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
import cv2
from moviepy.editor import VideoFileClip as vfc

from video_processing_engine.utils.hasher import h_extension


def codec(file: str) -> str:
  """Returns type of codec used in the video file."""
  return dict(map(reversed, h_extension.items()))[os.path.splitext(file)[1][1:]]


def duration(file: str,
             for_humans: Optional[bool] = False) -> Union[float, str]:
  """Returns duration of the video file."""
  if for_humans:
    mins, secs = divmod(vfc(file).duration, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)
  else:
    return vfc(file).duration


def bitrate(file: str) -> int:
  """Returns bitrate of the video file."""
  # You can find the reference code here:
  # https://www.ezs3.com/public/What_bitrate_should_I_use_when_encoding_my_video_How_do_I_optimize_my_video_for_the_web.cfm
  return (vfc(file).size[0] * vfc(file).size[1] *
          (vfc(file).reader.nframes // vfc(file).duration) * 0.07 // 1000)


def fps(file: str) -> Union[float, int]:
  """Returns fps of the video file."""
  return cv2.VideoCapture(file).get(cv2.CAP_PROP_FPS)


def check_usable_length(file: str, minimum_length: Optional[int] = 30) -> bool:
  """Returns boolean value after checking usuable video length."""
  return True if duration(file) >= 24 * minimum_length else False


def all_stats(file: str) -> Tuple:
  """Returns all the statistics of the video file."""
  return (os.path.basename(file), duration(file, True), bitrate(file),
          fps(file), codec(file), check_usable_length(file))
