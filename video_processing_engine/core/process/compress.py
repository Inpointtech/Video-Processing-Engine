"""A subservice for compressing the videos."""

from typing import Optional, Union

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
from moviepy.editor import VideoFileClip as vfc

from video_processing_engine.utils.hasher import h_extension
from video_processing_engine.core.process.stats import bitrate as b, fps as f
from video_processing_engine.utils.local import temporary_copy


def compress_video(file: str,
                   codec: str = 'libx264',
                   bitrate:  Union[int, str] = 400,
                   fps: Union[float, int] = 24,
                   audio: bool = False,
                   preset: str = 'ultrafast',
                   threads: int = 15) -> str:
  """Compresses video.

  Compresses video as per the requirements.

  Args:
    file: File to be compressed.
    codec: Codec (default: libx264 -> .mp4) to be used for compression.
    bitrate: Bitrate (default: min. 400) used for the compression.
    fps: FPS (default: 24) of the compressed video.
    audio: Boolean (default: False) value to have audio in compressed
           file.
    preset: The speed (default: ultrafast) used for applying the
            compression technique.
    threads: Number of threads (default: 15) to be used for compression.

  Returns:
    Path of the temporary duplicate file created.
  """
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


def choose_extension(codec: str = 'libx264') -> str:
    """Returns suitable file extension."""
    return h_extension.get(codec, 'mp4')
