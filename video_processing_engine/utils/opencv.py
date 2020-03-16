"""Utility for making convenient use of OpenCV."""

import socket
from typing import Any, List, Optional, Tuple, Union

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
import cv2
import imutils
import numpy as np

from video_processing_engine.vars.color import green, yellow


def rescale(frame: np.ndarray,
            width: Optional[int] = 300,
            height: Optional[int] = None,
            interpolation: Optional[Any] = cv2.INTER_AREA) -> np.ndarray:
  """Rescale the frame.

  Rescale the stream to a desirable size. This is required before
  performing the necessary operations.

  Args:
    frame: Numpy array of the image frame.
    width: Width (default: None) to be rescaled to.
    height: Height (default: None) to be rescaled to.
    interpolation: Interpolation algorithm (default: INTER_AREA) to be
                    used.

  Returns:
    Rescaled numpy array for the input frame.
  """
  dimensions = None
  frame_height, frame_width = frame.shape[:2]
  # If both width & height are None, then return original frame size.
  # No rescaling will be done in that case.
  if width is None and height is None:
    return frame
  if width and height:
    dimensions = (width, height)
  elif width is None:
    ratio = height / float(frame_height)
    dimensions = (int(frame_width * ratio), height)
  else:
    ratio = width / float(frame_width)
    dimensions = (width, int(frame_height * ratio))
  return cv2.resize(frame, dimensions, interpolation=interpolation)


def disconnect(stream: np.ndarray) -> None:
  """Disconnect stream and exit the program."""
  stream.release()
  cv2.destroyAllWindows()


def draw_bounding_box(frame: np.ndarray,
                      x0_y0: Tuple,
                      x1_y1: Tuple,
                      color: List = green,
                      alpha: Union[float, int] = 0.3,
                      thickness: int = 2) -> None:
  """Draw bounding box using the Numpy tuple.
  Draws the bounding box around the detection using tuple of numpy
  coordinates.
  Args:
    frame: Numpy array of the image frame.
    x0_y0: Tuple of top left coordinates.
    x1_y1: Tuple of bottom right coordinates.
    color: Bounding box (default: yellow) color.
    alpha: Opacity of the detected region overlay.
    thickness: Thickness (default: 1) of the bounding box.
  Note:
    This method can be used for drawing the bounding boxes around
    objects whose coordinates are derived from a Machine Learning based
    model.
    * For Haar based detections, use the below settings -
        draw_bounding_box(frame, x0, y0, (x1 - x0), (y1 - y0))
    * For adding the detection name, add the below settings - 
        (x0, y0), (x1, y1) = x0_y0, x1_y1
        cv2.rectangle(frame, (x0, y1), (x1, y1 + 20), color, -1)
  """
  overlay = frame.copy()
  cv2.rectangle(overlay, x0_y0, x1_y1, color, -1)
  cv2.rectangle(frame, x0_y0, x1_y1, color, thickness)
  cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


def positional_feed(frame: np.ndarray,
                    name: str = 'Stream feed',
                    pos_x: int = None,
                    pos_y: int = None) -> None:
  """Displays the stream feed at a particular position.

  Displays the stream. Provides an option to display the stream at X, Y
  position.

  Args:
    frame: Numpy array of the image frame.
    name: Name for the display feed.
    pos_x: X-position of the displayed feed.
    pos_y: Y-position of the displayed feed.
  """
  cv2.namedWindow(name)
  if pos_x == None or pos_y == None:
    pos_x = pos_y = 0
  cv2.moveWindow(name, pos_x, pos_y)
  cv2.imshow(name, frame)


def configure_camera_url(camera_address: str,
                         camera_username: str = 'admin',
                         camera_password: str = 'iamironman',
                         camera_port: int = 554,
                         camera_stream_address: str = 'H.264',
                         camera_protocol: str = 'rtsp') -> str:
  """Configure camera url for testing."""
  return (f'{camera_protocol}://{camera_username}:{camera_password}@'
          f'{camera_address}:{camera_port}/{camera_stream_address}')


def draw_centroid(frame: np.ndarray,
                  radius: int = 5,
                  color: List = yellow,
                  thickness: int = 1) -> None:
  """Draw centroid for the detected shape/contour."""
  gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  blur_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)
  threshold = cv2.threshold(blur_frame, 60, 255, cv2.THRESH_BINARY)[1]
  contours = cv2.findContours(threshold.copy(),
                              cv2.RETR_EXTERNAL,
                              cv2.CHAIN_APPROX_SIMPLE)
  contours = imutils.grab_contours(contours)
  for contour in contours:
    moment = cv2.moments(contour)
    x = int(moment['m10'] / moment['m00']) if moment['m00'] > 0 else 0
    y = int(moment['m01'] / moment['m00']) if moment['m00'] > 0 else 0
    cv2.drawContours(frame, [contour], -1, color, thickness)
    cv2.circle(frame, (x, y), radius, color, -1)


def camera_live(camera_address: str,
                camera_port: Union[int, str] = 554,
                timeout: Optional[Union[float, int]] = 10.0) -> bool:
  """Check if any camera connectivity is available."""
  # You can find the reference code here:
  # https://gist.github.com/yasinkuyu/aa505c1f4bbb4016281d7167b8fa2fc2
  try:
    camera_port = int(camera_port)
    socket.create_connection((camera_address, camera_port), timeout = timeout)
    return True
  except OSError:
    pass
  return False
