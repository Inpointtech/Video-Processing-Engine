"""A subservice for trimming the videos."""

import os
import random
from typing import List, Optional, Union

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
from moviepy.editor import VideoFileClip as vfc

from video_processing_engine.utils.local import filename
from video_processing_engine.core.process.stats import duration
from video_processing_engine.utils.local import temporary_copy


def trim_video(file: str,
               output: str,
               start: Optional[Union[float, int]] = 0,
               end: Optional[Union[float, int]] = 30,
               audio: Optional[bool] = False,
               preset: Optional[str] = 'ultrafast',
               threads: Optional[int] = 15) -> None:
  """Trim video."""
  video = vfc(file, audio=audio, verbose=True).subclip(start, end)
  video.write_videofile(output, audio=audio, preset=preset, threads=threads,
                        logger=None, codec='libx264')


def trim_num_video(file: str,
                   num_parts: int,
                   audio: Optional[bool] = False,
                   preset: Optional[str] = 'ultrafast',
                   threads: Optional[int] = 15,
                   display: Optional[bool] = False,
                   return_list: Optional[bool] = True) -> Optional[List]:
  """Trim video in number of equal parts."""
  split_part = duration(file) / num_parts
  start = 0
  # Start splitting the videos into 'num_parts' equal parts.
  video_list = []
  for idx in range(1, num_parts + 1):
    start, end = start, start + split_part
    trim_video(file, filename(file, idx), start, end, audio, preset, threads)
    start += split_part
    video_list.append(filename(file, idx))
    if display:
      print(f'? Video trimmed » {os.path.basename(filename(file, idx))}')
  if return_list:
    return video_list


def trim_random_percentage(file: str, sampling_rate: int) -> str:
  """Trim random % of the video."""
  clip_length = (duration(file) * sampling_rate) // 100
  start = random.randint(1, int(duration(file)))
  end = start + clip_length
  temp = temporary_copy(file)
  trim_video(temp, file, start, end)
  return temp


def trim_by_factor(file: str,
                   factor: Optional[str] = 's',
                   length: Optional[int] = 30,
                   last_clip: Optional[bool] = True,
                   audio: Optional[bool] = False,
                   preset: Optional[str] = 'ultrafast',
                   threads: Optional[int] = 15,
                   display: Optional[bool] = False) -> None:
  """Trim the video by deciding factor."""
  total_length = duration(file)
  idx = 1
  if factor == 'm':
    start, end, length = 0, length * 60, length * 60
  else:
    start, end = 0, length
  while length < total_length:
    trim_video(file, filename(file, idx), start, end, audio, preset, threads)
    if display:
      print(f'? Video length » {duration(filename(file, idx), True)}')
    start, end, idx = end, end + length, idx + 1
    total_length -= length
  else:
    if last_clip:
      start, end = (duration(file) - total_length), duration(file)
      trim_video(file, filename(file, idx), start, end, audio, preset, threads)
      if display:
        print(f'? Video length » {duration(filename(file, idx), True)}')
