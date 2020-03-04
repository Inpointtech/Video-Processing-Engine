"""A subservice for trimming the videos."""

import os
import random
from typing import List, Optional, Union

from video_processing_engine.core.process.stats import (all_stats, duration,
                                                        minimum_sampling_rate,
                                                        usuable_difference)
from video_processing_engine.utils.local import filename, temporary_copy, quick_rename


def trim_video(file: str,
               output: str = None,
               start: Union[float, int, str] = 0,
               end: Union[float, int, str] = 30) -> None:
  """Trims video.

  Trims video as per the requirements.

  Args:
    file: File to be used for trimming.
    output: Path of the output file.
    start: Starting point (default: 0) of the video in secs.
    end: Ending point (default: 30) of the video in secs.
  """
  file, temp = quick_rename(file)
  if output:
    file = output
  os.system(f'ffmpeg -loglevel error -y -ss {start} -i {temp} -t {end} '
            f'-c copy {file}')


def trim_num_parts(file: str,
                   num_parts: int,
                   return_list: bool = True) -> Optional[List]:
  """Trim video in number of equal parts.

  Trims the video as per the number of clips required.

  Args:
    file: File to be used for trimming.
    num_parts: Number of videos to be trimmed into.
    return_list: Boolean (default: True) value to return list of all the
                  trimmed files.
  """
  split_part = duration(file) / num_parts
  start = 0
  # Start splitting the videos into 'num_parts' equal parts.
  video_list = []
  for idx in range(1, num_parts + 1):
    start, end = start, start + split_part
    trim_video(file, filename(file, idx), start, end)
    start += split_part
    video_list.append(filename(file, idx))
  if return_list:
    return video_list


def trim_sample_section(file: str,
                        sampling_rate: int,
                        num_clips: int = 24,
                        minimum_length: int = 30) -> Union[int, str]:
  """Trim a sample portion of the video as per the sampling rate.

  Trims a random sample portion of the video as per the sampling rate.

  Args:
    file: File to be used for trimming.
    sampling_rate: Portion of the video to be trimmed.
    num_clips: Number of videos (default: 24) to be trimmed.
    minimum_length: Minimum video length (default: 30 secs) required.

  Returns:
    Path of the temporary duplicate file created.
  """
  clip_length = (duration(file) * sampling_rate) // 100
  start = random.randint(1, int(duration(file)))
  end = int(start + clip_length)
  if usuable_difference(clip_length, num_clips, minimum_length):
    trim_video(file, start=start, end=end)
    return file
  else:
    return (int((minimum_sampling_rate(num_clips, minimum_length) * 100)
                // duration(file)) + 1)


def trim_by_factor(file: str,
                   factor: str = 's',
                   length: Union[float, int] = 30,
                   last_clip: bool = True) -> None:
  """Trims the video by deciding factor.

  Trims the video as per the deciding factor i.e. trim by mins OR trim
  by secs.

  Args:
    file: File to be used for trimming.
    factor: Trimming factor (default: secs -> s) to consider.
    length: Length (default: 30 secs) of each video clip.
    last_clip: Boolean (default: True) value to consider the remaining
  """
  total_length = duration(file)
  idx = 1
  if factor == 'm':
    start, end, length = 0, length * 60, length * 60
  else:
    start, end = 0, length
  while length < total_length:
    trim_video(file, filename(file, idx), start, end)
    start, end, idx = end, end + length, idx + 1
    total_length -= length
  else:
    if last_clip:
      start, end = (duration(file) - total_length), duration(file)
      trim_video(file, filename(file, idx), start, end)
