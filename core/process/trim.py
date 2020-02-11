"""A subservice for trimming the videos."""

from datetime import timedelta, datetime
from typing import Any, Optional, Union

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
    from bs3.utils.local import filename
  else:
    from bs3.utils.generate import filename

  for idx in range(num_parts):
    file = filename(source, idx, choose_extension(codec))
    start, end = start, start + split_part
    trim_video(source, file, start, end, codec,
               bitrate, fps, audio, preset, threads)
    start += split_part
    print(f'{file} is trimmed.')


def choose_extension(codec: Optional[str] = 'libx264') -> str:
  """Returns suitable file extension."""
  return hash_extension.get(codec, 'mp4')


def calc_bitrate(source: Any) -> int:
  return (vfc(source).size[0] *
          vfc(source).size[1] *
          (vfc(source).reader.nframes // vfc(source).duration) * 0.07 // 1000)
