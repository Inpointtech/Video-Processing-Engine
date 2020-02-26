"""A subservice for compressing the videos."""

from typing import Optional

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
from moviepy.editor import VideoFileClip as vfc

from video_processing_engine.utils.hasher import h_extension
from video_processing_engine.core.process.stats import bitrate as b, fps as f
from video_processing_engine.utils.local import temporary_copy


def compress_video(file: str,
                   codec: Optional[str] = 'libx264',
                   bitrate: Optional[int] = 400,
                   fps: Optional[int] = 24,
                   audio: Optional[bool] = False,
                   preset: Optional[str] = 'ultrafast',
                   threads: Optional[int] = 15) -> str:
  """Compresses video."""
  if b(file) < 400:
    bitrate = 400
  if f(file) < 24:
    fps = 24
  temp = temporary_copy(file)
  video = vfc(temp, audio=audio, verbose=True)
  video.write_videofile(file, codec=codec, fps=fps, audio=audio,
                        preset=preset, threads=threads, bitrate=f'{bitrate}k',
                        logger=None)
  return temp


def choose_extension(codec: Optional[str] = 'libx264') -> str:
    """Returns suitable file extension."""
    return h_extension.get(codec, 'mp4')
