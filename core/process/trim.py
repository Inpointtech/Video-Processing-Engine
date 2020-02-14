"""A subservice for trimming the videos."""

import os
import shutil
import time
from datetime import timedelta
from pathlib import Path
from typing import Any, Optional, Tuple, Union

from moviepy.editor import VideoFileClip as vfc

from video_processing_engine.utils.hasher import hash_extension


def trim_video(source: Any,
               file: str,
               start: Optional[Union[float, int]] = 0,
               end: Optional[Union[float, int]] = 30,
               codec: Optional[str] = 'libx264',
               bitrate: Optional[int] = 400,
               fps: Optional[int] = 24,
               audio: Optional[bool] = False,
               preset: Optional[str] = 'ultrafast',
               threads: Optional[int] = 15,
               status: Optional[bool] = False) -> None:
  """Trim video."""
  if bitrate < calc_bitrate(source):
    bitrate = bitrate
  trimmed_video = vfc(source, verbose=True).subclip(start, end)
  trimmed_video.write_videofile(file, codec=codec, fps=fps, audio=audio,
                                preset=preset, threads=threads,
                                bitrate=f'{bitrate}k')


def delta(value: Union[float, int], factor: str) -> timedelta:
  """Returns value in timedelta format."""
  if factor == 'mins':
    return timedelta(minutes=value, )
  else:
    return timedelta(seconds=value)


def trim_num_parts(source: Any,
                   num_parts: int,
                   local: Optional[bool] = False,
                   codec: Optional[str] = 'libx264',
                   bitrate: Optional[int] = 400,
                   fps: Optional[int] = 24,
                   audio: Optional[bool] = False,
                   preset: Optional[str] = 'ultrafast',
                   threads: Optional[int] = 15) -> None:
  """Trim video in number of equal parts."""
  total_limit = float(vfc(source).duration)
  split_part = total_limit / num_parts
  start = 0

  if local:
    from video_processing_engine.utils.local import filename
  else:
    # TODO(xames3): Update the below module to be functional with
    # upcoming changes.
    from video_processing_engine.utils.generate import filename

  for idx in range(1, num_parts + 1):
    file = filename(source, idx, choose_extension(codec))
    start, end = start, start + split_part
    trim_video(source, file, start, end, codec,
               bitrate, fps, audio, preset, threads)
    start += split_part


def choose_extension(codec: Optional[str] = 'libx264') -> str:
  """Returns suitable file extension."""
  return hash_extension.get(codec, 'mp4')


def calc_bitrate(source: Any) -> int:
  """Calculates the bitrate for a particular video."""
  # You can find the reference code here:
  # https://www.ezs3.com/public/What_bitrate_should_I_use_when_encoding_my_video_How_do_I_optimize_my_video_for_the_web.cfm
  return (vfc(source).size[0] *
          vfc(source).size[1] *
          (vfc(source).reader.nframes // vfc(source).duration) * 0.07 // 1000)


def check_length(source: Any, minimum_length: Optional[int] = 30) -> bool:
  """Returns boolean value after checking video length."""
  return True if float(vfc(source).duration) >= 24 * minimum_length else False


def random_sample_video(source: Any, sampling_rate: Optional[int] = 2) -> None:
  """Considers a usuable sample based on sampling rate."""
  total_length = float(vfc(source).duration)
  desired_length = (total_length * sampling_rate) / 100
  clipped_length = desired_length / 30


def compress_video(source: Any,
                   codec: Optional[str] = 'libx264',
                   bitrate: Optional[int] = 400,
                   fps: Optional[int] = 24,
                   audio: Optional[bool] = False,
                   preset: Optional[str] = 'ultrafast',
                   threads: Optional[int] = 15) -> Tuple:
  """Trim video in number of equal parts."""
  temp = source.replace(Path(source).stem, 'temporary_compressed')
  shutil.copy(source, temp)
  trim_video(source, temp, 0, int(vfc(source).duration), codec,
             bitrate, fps, audio, preset, threads)
  return temp


# sec = 10 * 3600
# tot = (0.02 * sec)
# eac = tot / 24
# print(tot, eac)
