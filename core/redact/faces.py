"""A subservice for face detection and recognition."""

from typing import Optional

import cv2
import numpy as np

from video_processing_engine.utils.opencv import draw_box_with_tuple, rescale
from video_processing_engine.utils.paths import caffe_model, prototext
from video_processing_engine.vars import models

# Loading serialized CaffeModel for face detection.
net = cv2.dnn.readNetFromCaffe(prototext, caffe_model)


def detect_faces(frame: np.ndarray,
                 confidence: Optional[float] = models.DETECTED_FACE_CONFIDENCE
                 ) -> None:
  """Detect faces in the frame.

  Detect faces in the frame and draw bounding box around the detected
  faces.

  Args:
    frame: Numpy array of the captured frame.
    confidence: Floating (default: 0.7) value for facial confidence.

  Notes:
    Faces will only be detected if the confidence scores are above the
    `models.DETECTED_FACE_CONFIDENCE` value.
  """
  height, width = frame.shape[:2]
  # You can learn more about blob here:
  # https://www.pyimagesearch.com/2017/11/06/deep-learning-opencvs-blobfromimage-works/
  blob = cv2.dnn.blobFromImage(rescale(frame, 300, 300), 1.0, (299, 299),
                               (104.0, 177.0, 123.0))
  # cv2.dnn.blobFromImage(frame, scalefactor, size, mean)
  # frame: Frame which we need to preprocess before feeding to DNN.
  # scalefactor: If we need to scale the blob, alter this parameter.
  # size: Spatial size our CNN expects. Ideal values are 224 x 224,
  #       227 x 227 & 299 x 299.
  # mean: Mean subtraction values.
  net.setInput(blob)
  detected_faces = net.forward()
  # Loop over all the detected faces in the frame.
  for idx in range(detected_faces.shape[2]):
    coords = detected_faces[0, 0, idx, 3:7] * np.array([width, height,
                                                        width, height])
    detected_confidence = detected_faces[0, 0, idx, 2]
    # Draw a bounding box only if the detected faces have confidence
    # score above DETECTED_FACE_CONFIDENCE threshold.
    if detected_confidence < confidence:
      continue
    x0, y0, x1, y1 = coords.astype('int')
    draw_box_with_tuple(frame, (x0, y0), (x1, y1))
