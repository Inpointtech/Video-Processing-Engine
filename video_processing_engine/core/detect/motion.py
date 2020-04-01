"""A subservice for detection motion in videos."""

import csv
import logging
import os
from pathlib import Path
from typing import Optional, Union

import cv2
import imutils

from video_processing_engine.core.detect.keyclipwriter import KeyClipWriter
from video_processing_engine.core.process.concate import concate_videos
from video_processing_engine.utils.local import filename
from video_processing_engine.utils.logs import log as _log
from video_processing_engine.utils.opencv import (disconnect,
                                                  draw_bounding_box, rescale)
from video_processing_engine.utils.common import seconds_to_datetime as s2d
from video_processing_engine.vars import dev


def motion_meta(boxes: int, occurence: Union[float, int]) -> str:
  box = 'Bounding box' if boxes == 1 else 'Bounding boxes'
  return f'{boxes} {box} detected at {s2d(int(occurence / 1000))}'


def track_motion(file: str,
                 precision: int = 1500,
                 resize: bool = True,
                 resize_width: int = 640,
                 debug_mode: bool = True,
                 log: logging.Logger = None) -> Optional[str]:
  """Track motion in the video using Background Subtraction method."""
  log = _log(__file__) if log is None else log
  kcw = KeyClipWriter(bufSize=32)
  consec_frames, x0, y0, x1, y1 = 0, 0, 0, 0, 0
  boxes, temp_csv_entries = [], []
  directory = os.path.join(os.path.dirname(file), Path(file).stem)
  if not os.path.isdir(directory):
    os.mkdir(directory)
  temp_file = os.path.join(directory, f'{Path(file).stem}.mp4')
  idx = 1
  if debug_mode:
    log.info('Debug mode - Enabled.')
  log.info(f'Analyzing motion for "{os.path.basename(file)}".')
  try:
    stream = cv2.VideoCapture(file)
    fps = stream.get(cv2.CAP_PROP_FPS)
    first_frame = None
    while True:
      valid_frame, frame = stream.read()
      if not valid_frame:
        break
      if frame is None:
        break
      if resize:
        frame = rescale(frame, resize_width)
      update_frame = True
      gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
      gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)
      if first_frame is None:
        first_frame = gray_frame
        continue
      frame_delta = cv2.absdiff(first_frame, gray_frame)
      threshold = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
      threshold = cv2.dilate(threshold, None, iterations=2)
      contours = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL,
                                  cv2.CHAIN_APPROX_SIMPLE)
      contours = imutils.grab_contours(contours)
      for contour in contours:
        if cv2.contourArea(contour) < precision:
          continue
        if debug_mode:
          (x0, y0, x1, y1) = cv2.boundingRect(contour)
          draw_bounding_box(frame, (x0, y0), (x0 + x1, y0 + y1))
        consec_frames = 0
        if not kcw.recording:
          kcw.start(filename(temp_file, idx),
                    cv2.VideoWriter_fourcc(*'mp4v'), fps)
          idx += 1
        boxes.append([x1, y1])
        status = motion_meta(len(boxes), stream.get(cv2.CAP_PROP_POS_MSEC))
        log.info(status)
        temp_csv_entries.append(status)
      boxes = []
      if update_frame:
        consec_frames += 1
      kcw.update(frame)
      if kcw.recording and consec_frames == 32:
        log.info('Saving portion of video with detected motion.')
        kcw.finish()
      if debug_mode:
        cv2.imshow('Video Processing Engine - Motion Detection', frame)
      if cv2.waitKey(1) & 0xFF == int(27):
        disconnect(stream)
    if kcw.recording:
      kcw.finish()
    concate_temp = concate_videos(directory, delete_old_files=True)
    with open(os.path.join(directory, f'{Path(file).stem}.csv'), 'a',
              encoding=dev.DEF_CHARSET) as csv_file:
      log.info('Logging detections into a CSV file.')
      _file = csv.writer(csv_file, delimiter='\n', quoting=csv.QUOTE_MINIMAL)
      _file.writerow(temp_csv_entries)
    if concate_temp:
      if os.path.isfile(concate_temp):
        log.info('Applying H264 encoding for bypassing browser issues.')
        os.system(f'ffmpeg -loglevel error -y -i {concate_temp} -vcodec '
                  f'libx264 {temp_file}')
        log.info('Cleaning up archived files.')
        os.remove(concate_temp)
        return temp_file
  except Exception as error:
    log.critical(f'Something went wrong because of {error}')
