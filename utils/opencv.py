"""Utility for making convenient use of OpenCV."""

from typing import Any, List, Optional, Tuple, Union

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
import cv2
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


def draw_box_with_tuple(frame: np.ndarray,
                        start_xy: Tuple,
                        end_xy: Tuple,
                        color: Optional[List] = yellow,
                        thickness: Optional[int] = 1) -> None:
  """Draw bounding box using the numpy tuple.

  Draws the bounding box around the detection using tuple of numpy
  coordinates.

  Args:
    frame: Numpy array of the image frame.
    start_xy: Tuple of top left coordinates.
    end_xy: Tuple of bottom right coordinates.
    color: Bounding box (default: yellow) color.
    thickness: Thickness (default: 1) of the bounding box.

  Notes:
    This method can be used for drawing the bounding boxes around
    objects whose coordinates are derived from a Machine Learning based
    model. For Haar based detections, use `draw_box_with_coords()`.
  """
  return cv2.rectangle(frame, start_xy, end_xy, color, thickness)


def draw_box_with_coords(frame: np.ndarray, x: Union[int], y: Union[int],
                         w: Union[int], h: Union[int],
                         color: Optional[List] = green,
                         thickness: Optional[int] = 1) -> None:
  """Draw bounding box using individual coords.

  Draws a bounding box around the detected object using all 4 available
  coordinates. This function is ideal to use with Haar based detections.

  Args:
    frame: Numpy array of the image frame.
    x: Top left X-position of the detected object.
    y: Top left Y-position of the detected object.
    w: Bottom right X-position of the detected object.
    w: Bottom right Y-position of the detected object.
    color: Bounding box (default: green) color.
    thickness: Thickness (default: 1) of the bounding box.
  """
  return cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)


def positional_feed(frame: np.ndarray,
                    name: Optional[str] = 'Stream feed',
                    pos_x: Optional[int] = None,
                    pos_y: Optional[int] = None) -> None:
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
                         camera_username: Optional[str] = 'admin',
                         camera_password: Optional[str] = 'iamironman',
                         camera_port: Optional[int] = 554,
                         camera_stream_address: Optional[str] = 'H.264',
                         camera_protocol: Optional[str] = 'rtsp') -> str:
  """Configure camera url for testing."""
  return (f'{camera_protocol}://{camera_username}:{camera_password}@'
          f'{camera_address}:{camera_port}/{camera_stream_address}')
