"""Run main code."""

import time

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
import cv2
import numpy

from video_processing_engine.utils.common import toast
from video_processing_engine.utils.opencv import (disconnect,
                                                  draw_box_with_tuple, rescale)
from video_processing_engine.core.redact.faces import detect_faces

while True:
  stream = cv2.VideoCapture(0)
  toast('Success', 'Stream started.')
  time.sleep(2.0)
  # Keep the service running.
  try:
    while stream.isOpened():
      _, frame = stream.read()
      frame = rescale(frame, width=400)
      # detect_faces(frame)
      # Terminate the stream after pressing 'Esc' key.
      if cv2.waitKey(1) & 0xFF == int(27):
        toast('Alert', 'Stream terminated.')
        disconnect(stream)
        exit(0)
      cv2.imshow('Live feed', frame)
    else:
      toast('Warning', 'Stream broken.')
      time.sleep(5.0)
  except cv2.error:
    disconnect(stream)
    toast('Error', 'An error occurred while using OpenCV.')
