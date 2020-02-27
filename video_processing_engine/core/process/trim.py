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
               codec: Optional[str] = 'libx264',
               bitrate: Optional[int] = 400,
               fps: Optional[int] = 24,
               audio: Optional[bool] = False,
               preset: Optional[str] = 'ultrafast',
               threads: Optional[int] = 15) -> None:
  """Trims video.

  Trims the video as per the requirements.

  Args:
    file: File to be used for trimming.
    output: Path of the output file.
    start: Starting point (default: 0) of the video in secs.
    end: Ending point (default: 30) of the video in secs.
    codec: Codec (default: libx264 -> .mp4) to be used while trimming.
    bitrate: Bitrate (default: min. 400) used while trimming.
    fps: FPS (default: 24) of the trimmed video clips.
    audio: Boolean (default: False) value to have audio in trimmed
            videos.
    preset: The speed (default: ultrafast) used for applying the
            compression technique on the trimmed videos.
    threads: Number of threads (default: 15) to be used for trimming.
  """
  video = vfc(file, audio=audio, verbose=True).subclip(start, end)
  video.write_videofile(output, codec=codec, fps=fps, audio=audio,
                        preset=preset, threads=threads, bitrate=f'{bitrate}k',
                        logger=None)


def trim_num_parts(file: str,
                   num_parts: int,
                   codec: Optional[str] = 'libx264',
                   bitrate: Optional[int] = 400,
                   fps: Optional[int] = 24,
                   audio: Optional[bool] = False,
                   preset: Optional[str] = 'ultrafast',
                   threads: Optional[int] = 15,
                   verbose: Optional[bool] = False,
                   return_list: Optional[bool] = True) -> Optional[List]:
  """Trim video in number of equal parts.

  Trims the video as per the number of clips required.

  Args:
    file: File to be used for trimming.
    num_parts: Number of videos to be trimmed into.
    codec: Codec (default: libx264 -> .mp4) to be used while trimming.
    bitrate: Bitrate (default: min. 400) used while trimming.
    fps: FPS (default: 24) of the trimmed video clips.
    audio: Boolean (default: False) value to have audio in trimmed
            videos.
    preset: The speed (default: ultrafast) used for applying the
            compression technique on the trimmed videos.
    threads: Number of threads (default: 15) to be used for trimming.
    verbose: Boolean (default: False) value to display the status.
    return_list: Boolean (default: True) value to return list of all the
                 trimmed files.
  """
  split_part = duration(file) / num_parts
  start = 0
  # Start splitting the videos into 'num_parts' equal parts.
  video_list = []
  for idx in range(1, num_parts + 1):
    start, end = start, start + split_part
    trim_video(file, filename(file, idx), start, end, codec, bitrate, fps,
               audio, preset, threads)
    start += split_part
    video_list.append(filename(file, idx))
    if verbose:
      print(f'? Video trimmed » {os.path.basename(filename(file, idx))}')
  if return_list:
    return video_list


def trim_sample_section(file: str,
                        sampling_rate: int,
                        codec: Optional[str] = 'libx264',
                        bitrate: Optional[int] = 400,
                        fps: Optional[int] = 24,
                        audio: Optional[bool] = False,
                        preset: Optional[str] = 'ultrafast',
                        threads: Optional[int] = 15) -> str:
  """Trim a sample portion of the video as per the sampling rate.

  Trims a random sample portion of the video as per the sampling rate.

  Args:
    file: File to be used for trimming.
    sampling_rate: Portion of the video to be trimmed.
    codec: Codec (default: libx264 -> .mp4) to be used while trimming.
    bitrate: Bitrate (default: min. 400) used while trimming.
    fps: FPS (default: 24) of the trimmed video.
    audio: Boolean (default: False) value to have audio in trimmed
            video.
    preset: The speed (default: ultrafast) used for applying the
            compression technique on the trimmed video.
    threads: Number of threads (default: 15) to be used for trimming.

  Returns:
    Path of the temporary duplicate file created.
  """
  clip_length = (duration(file) * sampling_rate) // 100
  start = random.randint(1, int(duration(file)))
  end = start + clip_length
  temp = temporary_copy(file)
  trim_video(temp, file, start, end, codec, bitrate, fps, audio, preset,
             threads)
  return temp


def trim_by_factor(file: str,
                   factor: Optional[str] = 's',
                   length: Optional[int] = 30,
                   last_clip: Optional[bool] = True,
                   codec: Optional[str] = 'libx264',
                   bitrate: Optional[int] = 400,
                   fps: Optional[int] = 24,
                   audio: Optional[bool] = False,
                   preset: Optional[str] = 'ultrafast',
                   threads: Optional[int] = 15,
                   verbose: Optional[bool] = False) -> None:
  """Trims the video by deciding factor.

  Trims the video as per the deciding factor i.e. trim by mins OR trim
  by secs.

  Args:
    file: File to be used for trimming.
    factor: Trimming factor (default: secs -> s) to consider.
    length: Length (default: 30) of each video clip.
    last_clip: Boolean (default: True) value to consider the remaining
               portion of the trimmed video.
    codec: Codec (default: libx264 -> .mp4) to be used while trimming.
    bitrate: Bitrate (default: min. 400) used while trimming.
    fps: FPS (default: 24) of the trimmed video clips.
    audio: Boolean (default: False) value to have audio in trimmed
            videos.
    preset: The speed (default: ultrafast) used for applying the
            compression technique on the trimmed videos.
    threads: Number of threads (default: 15) to be used for trimming.
    verbose: Boolean (default: False) value to display the status.
  """
  total_length = duration(file)
  idx = 1
  if factor == 'm':
    start, end, length = 0, length * 60, length * 60
  else:
    start, end = 0, length
  while length < total_length:
    trim_video(file, filename(file, idx), start, end, codec, bitrate, fps,
               audio, preset, threads)
    if verbose:
      print(f'? Video length » {duration(filename(file, idx), True)}')
    start, end, idx = end, end + length, idx + 1
    total_length -= length
  else:
    if last_clip:
      start, end = (duration(file) - total_length), duration(file)
      trim_video(file, filename(file, idx), start, end, codec, bitrate, fps,
                 audio, preset, threads)
      if verbose:
        print(f'? Video length » {duration(filename(file, idx), True)}')
