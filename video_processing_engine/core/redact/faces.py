"""A subservice for face detection and recognition."""

import csv
import logging
import os
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from mtcnn import MTCNN

from video_processing_engine.utils.common import seconds_to_datetime as s2d
from video_processing_engine.utils.local import filename
from video_processing_engine.utils.logs import log as _log
from video_processing_engine.utils.opencvapi import draw_bounding_box, rescale
from video_processing_engine.utils.paths import frontal_haar
from video_processing_engine.vars import color, dev

face_detector = MTCNN(min_face_size=20)


def pixelate(face_roi):
  """Pixelate faces like in ..."""
  # You can find the reference code here:
  # https://www.pyimagesearch.com/2020/04/06/blur-and-anonymize-faces-with-opencv-and-python/
  height, width, _ = face_roi.shape
  blocks = width * 0.01
  x_steps = np.linspace(0, width, 8, dtype='int')
  y_steps = np.linspace(0, height, 8, dtype='int')
  # Looping over blocks in both X & Y direction.
  for y_idx in range(1, len(y_steps)):
    for x_idx in range(1, len(x_steps)):
      x0 = x_steps[x_idx - 1]
      y0 = y_steps[y_idx - 1]
      x1 = x_steps[x_idx]
      y1 = y_steps[y_idx]
      roi = face_roi[y0:y1, x0:x1]
      B, G, R = [int(idx) for idx in cv2.mean(roi)[:3]]
      cv2.rectangle(face_roi, (x0, y0), (x1, y1), (B, G, R), -1)
  # Pixelated blurred face_roi
  return face_roi


def redact_faces(file: str,
                 use_ml_model: bool = True,
                 smooth_blur: bool = True,
                 resize: bool = True,
                 resize_width: int = 640,
                 debug_mode: bool = True,
                 log: logging.Logger = None) -> Optional[str]:
  """Apply face redaction in video using CaffeModel."""
  log = _log(__file__) if log is None else log

  x0, y0, x1, y1 = 0, 0, 0, 0
  boxes, temp_csv_entries = [], []
  face_count = {}

  directory = os.path.join(os.path.dirname(file), f'{Path(file).stem}')

  if not os.path.isdir(directory):
    os.mkdir(directory)

  temp_file = os.path.join(directory, f'{Path(file).stem}_redact.mp4')

  if debug_mode:
    log.info('Debug mode - Enabled.')

  log.info(f'Redacting faces from "{os.path.basename(file)}".')

  try:
    stream = cv2.VideoCapture(file)
    fps = stream.get(cv2.CAP_PROP_FPS)
    width, height = (int(stream.get(cv2.CAP_PROP_FRAME_WIDTH)),
                     int(stream.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    if resize:
      width, height = resize_width, int(height * (resize_width / float(width)))

    save = cv2.VideoWriter(filename(temp_file, 1),
                           cv2.VideoWriter_fourcc(*'mp4v'), fps,
                           (width, height))

    while True:
      valid_frame, frame = stream.read()

      if not valid_frame:
        break

      if frame is None:
        break

      if resize:
        frame = rescale(frame, resize_width)

      height, width = frame.shape[:2]

      if use_ml_model:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_detector.detect_faces(rgb)

        for face_idx in faces:
            # Considering detections which have confidence score higher than the
            # set threshold.
          if face_idx['confidence'] > 0.75:
            x0, y0, x1, y1 = face_idx['box']
            x0, y0 = abs(x0), abs(y0)
            x1, y1 = x0 + x1, y0 + y1

            face = frame[y0:y1, x0:x1]

            if debug_mode:
              draw_bounding_box(frame, (x0, y0), (x1, y1), color.red)
            try:
              if smooth_blur:
                frame[y0:y1, x0:x1] = cv2.GaussianBlur(frame[y0:y1, x0:x1],
                                                       (21, 21), 0)
              else:
                frame[y0:y1, x0:x1] = pixelate(face)
            except Exception:
              pass

          boxes.append([x1, y1])
          face_occurence = s2d(int(stream.get(cv2.CAP_PROP_POS_MSEC) / 1000))

          if face_occurence not in face_count.keys():
            face_count[face_occurence] = []

          face_count[face_occurence].append(len(boxes))
      else:
        face_cascade = cv2.CascadeClassifier(frontal_haar)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, 1.3, 5)

        for (x0, y0, x1, y1) in faces:
          if debug_mode:
            draw_bounding_box(frame, (x0, y0), (x0 + x1, y0 + y1), color.red)
          try:
            if smooth_blur:
              frame[y0:(y0 + y1),
                    x0:(x0 + x1)] = cv2.GaussianBlur(frame[y0:(y0 + y1),
                                                           x0:(x0 + x1)],
                                                     (21, 21), 0)
            else:
              frame[y0:(y0 + y1),
                    x0:(x0 + x1)] = pixelate(frame[y0:(y0 + y1), x0:(x0 + x1)])
          except Exception:
            pass
          boxes.append([x1, y1])
          face_occurence = s2d(int(stream.get(cv2.CAP_PROP_POS_MSEC) / 1000))

          if face_occurence not in face_count.keys():
            face_count[face_occurence] = []

          face_count[face_occurence].append(len(boxes))

      boxes = []
      save.write(frame)

      if debug_mode:
        cv2.imshow('Video Processing Engine - Redaction', frame)

      if cv2.waitKey(1) & 0xFF == int(27):
        break

    stream.release()
    save.release()
    cv2.destroyAllWindows()

    with open(os.path.join(directory, f'{Path(file).stem}.csv'), 'a',
              encoding=dev.DEF_CHARSET) as csv_file:
      log.info('Logging detections into a CSV file.')
      _file = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
      _file.writerow(['Max no. of detections per second', 'Time frame'])
      temp_csv_entries = [(max(v), k) for k, v in face_count.items()]
      _file.writerows(temp_csv_entries)

    log.info('Applying H264 encoding for bypassing browser issues.')
    os.system(f'ffmpeg -loglevel error -y -i {filename(temp_file, 1)} -vcodec '
              f'libx264 {temp_file}')

    return temp_file
  except Exception as error:
    log.critical(f'Something went wrong because of {error}')
