"""A subservice for compressing the videos."""

import logging
import os
from pathlib import Path

from video_processing_engine.core.process.quality import calc_ssim_psnr
from video_processing_engine.core.process.stats import new_bitrate as b
from video_processing_engine.utils.common import file_size as f


def compress_video(file: str, log: logging.Logger) -> str:
  """Compresses video.

  Compresses video as per the requirements.

  Args:
    file: File to be compressed.
    ratio: Compression ratio to be applied.

  Returns:
    Path of the temporary duplicate file created.
  """
  score, _ = calc_ssim_psnr(file)
  if score < 50.0:
    log.info('Applying 20% compression.')
    bitrate = int(b(file) * 0.8)
  elif 88.0 >= score >= 50.0:
    log.info('Applying 50% compression.')
    bitrate = int(b(file) * 0.5)
  else:
    log.info('Applying 70% compression.')
    bitrate = int(b(file) * 0.3)
  ext = os.path.splitext(file)[1]
  temp = os.path.join(os.path.dirname(file), ''.join([Path(file).stem, '_temp_xa', ext]))
  log.info(f'Original file size on disk is {f(file)}')
  os.rename(file, temp)
  os.system("ffmpeg -loglevel error -y -i {source}  -vcodec libx264 -b {compresion} {file_name}".format(source=temp, compresion=bitrate, file_name=file))
  log.info(f'Compressed file size on disk is {f(file)}')
  os.remove(temp)
  return file
