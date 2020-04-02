"""A subservice for face detection and recognition."""

import csv
import logging
import os
import time
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

from video_processing_engine.utils.common import seconds_to_datetime as s2d
from video_processing_engine.utils.local import filename
from video_processing_engine.utils.logs import log as _log
from video_processing_engine.utils.opencv import draw_bounding_box, rescale
from video_processing_engine.utils.paths import (caffemodel, frontal_haar,
                                                 prototxt)
from video_processing_engine.vars import color, dev
from video_processing_engine.vars import models as md


def face_meta(boxes: int, occurence: Union[float, int]) -> str:
  box = 'Face' if boxes == 1 else 'Faces'
  return f'{boxes} {box} detected at {s2d(int(occurence / 1000))}'


def redact_faces(file: str,
                 use_ml_model: bool = True,
                 resize: bool = True,
                 resize_width: int = 640,
                 debug_mode: bool = True,
                 log: logging.Logger = None) -> Optional[str]:
  """Apply face redaction in video using CaffeModel."""
  log = _log(__file__) if log is None else log
  dynamic_conf = 0.1
  x0, y0, x1, y1 = 0, 0, 0, 0
  boxes, temp_csv_entries = [], []
  directory = os.path.join(os.path.dirname(file), Path(file).stem)
  if not os.path.isdir(directory):
    os.mkdir(directory)
  temp_file = os.path.join(directory, f'{Path(file).stem}.mp4')
  if debug_mode:
    log.info('Debug mode - Enabled.')
  log.info(f'Redacting faces from "{os.path.basename(file)}".')
  try:
    net = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
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
        blob = cv2.dnn.blobFromImage(frame, 1.0, (width, height),
                                    (104.0, 177.0, 123.0))
        net.setInput(blob)
        detected_faces = net.forward()
        bounding_boxes = []
        for idx in range(0, detected_faces.shape[2]):
          if detected_faces[0, 0, idx, 2] > dynamic_conf:
            time.sleep(dynamic_conf)
            coords = detected_faces[0, 0, idx, 3:7] * np.array([width, height,
                                                                width, height])
            bounding_boxes.append(coords.astype('int'))
            x0, y0, x1, y1 = coords.astype('int')
            x_bias, y_bias = (x1 - x0) * 0.04, (y1 - y0) * 0.04
            (x0, y0), (x1, y1) = ((int(x0 + x_bias), int(y0 + y_bias)),
                                  (int(x1 - x_bias), int(y1 - y_bias)))
            if debug_mode:
              draw_bounding_box(frame, (x0, y0), (x1, y1), color.red)
            try:
              frame[y0:y1, x0:x1] = cv2.GaussianBlur(frame[y0:y1, x0:x1],
                                                     (21, 21), 0)
            except Exception:
              pass
            dynamic_conf = detected_faces[0, 0, idx, 2]
            if dynamic_conf > 0.3:
              dynamic_conf = 0.15
          boxes.append([x1, y1])
          status = face_meta(len(boxes), stream.get(cv2.CAP_PROP_POS_MSEC))
          log.info(status)
          temp_csv_entries.append(status)
      else:
        face_cascade = cv2.CascadeClassifier(frontal_haar)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, 1.3, 5)
        for (x0, y0, x1, y1) in faces:
          if debug_mode:
            draw_bounding_box(frame, (x0, y0), (x0 + x1, y0 + y1), color.red)
          try:
            frame[y0:(y0 + y1),
                  x0:(x0 + x1)] = cv2.GaussianBlur(frame[y0:(y0 + y1),
                                                         x0:(x0 + x1)],
                                                   (21, 21), 0)
          except Exception:
            pass
          boxes.append([x1, y1])
          status = face_meta(len(boxes), stream.get(cv2.CAP_PROP_POS_MSEC))
          log.info(status)
          temp_csv_entries.append(status)
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
      _file = csv.writer(csv_file, delimiter='\n', quoting=csv.QUOTE_MINIMAL)
      _file.writerow(temp_csv_entries)
    log.info('Applying H264 encoding for bypassing browser issues.')
    os.system(f'ffmpeg -loglevel error -y -i {filename(temp_file, 1)} -vcodec '
              f'libx264 {temp_file}')
  except Exception as error:
    log.critical(f'Something went wrong because of {error}')
