"""Run main code."""

import time

import cv2
import numpy

from video_processing_engine.utils.opencv import (disconnect,
                                                  draw_box_with_tuple, rescale)
from video_processing_engine.utils.common import toast

while True:
  stream = cv2.VideoCapture(0)
  time.sleep(3.0)
  toast('Success', 'Stream started.')
  # Keep the service running.
  try:
    while stream.isOpened():
      _, frame = stream.read()
      frame = rescale(frame, width=400)
      # Terminate the application after pressing 'Esc' key.
      if cv2.waitKey(5) & 0xFF == int(27):
        disconnect(stream)
        exit(0)
      cv2.imshow('Live feed', frame)
    else:
      toast('Warning', 'Stream broken.')
      time.sleep(5.0)
  except cv2.error:
    disconnect(stream)
    toast('Error', 'An error occurred while using OpenCV.')
