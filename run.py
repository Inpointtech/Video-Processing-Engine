"""Run main code."""

import time

import cv2
import numpy

from video_processing_engine.utils.opencv import (disconnect,
                                                  draw_box_with_tuple, rescale)

try:
  pass
except cv2.error as error:
  pass
