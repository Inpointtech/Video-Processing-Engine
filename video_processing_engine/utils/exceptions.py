"""Utility for raising internal exceptions."""

from video_processing_engine.utils.common import now


class VideoProcessingEngineError(Exception):
  """Create a reference to the reference object."""
  pass


class BucketNameZeroError(VideoProcessingEngineError):
  def __str__(self):
    return ('Bucket name index must not start from 0. '
            f'Exception raised at {now()}.')


class HashValueHasZeroError(VideoProcessingEngineError):
  def __str__(self):
    return ('Hash value cannot be 0. '
            f'Exception raised at {now()}.')


class HashValueLimitExceedError(VideoProcessingEngineError):
  def __str__(self):
    return ('Hash value exceeded it\'s limits. '
            f'Exception raised at {now()}.')
