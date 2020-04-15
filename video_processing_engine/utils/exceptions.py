"""Utility for raising internal exceptions."""

from video_processing_engine.utils.common import now


class VideoProcessingEngineError(Exception):
  """Create a reference to the reference object."""
  pass


class BucketNameZeroError(VideoProcessingEngineError):
  def __str__(self) -> str:
    return 'Bucket name index must not start from 0.'


class OrderNameZeroError(VideoProcessingEngineError):
  def __str__(self) -> str:
    return 'Order name index must not start from 0.'


class HashValueHasZeroError(VideoProcessingEngineError):
  def __str__(self) -> str:
    return 'Hash value cannot be 0.'


class HashValueLimitExceedError(VideoProcessingEngineError):
  def __str__(self) -> str:
    return 'Hash value exceeded it\'s limits.'
