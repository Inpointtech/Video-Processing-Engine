"""Utility to access and download files."""

import os
from typing import Optional
from urllib.parse import unquote, urlsplit

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
import requests
from requests.exceptions import RequestException
from urllib3.exceptions import RequestError

from video_processing_engine.utils.paths import downloads
from video_processing_engine.vars import dev


def filename_from_url(public_url: str) -> str:
  """Returns filename from public url.

  Args:
    public_url: Url of the file.

  Returns:
    Extracted filename from its url.

  Raises:
    ValueError: If the url has arbitrary characters.
  """
  url_path = urlsplit(public_url).path
  basename = os.path.basename(unquote(url_path))
  if (os.path.basename(basename) != basename or
      unquote(os.path.basename(url_path)) != basename):
    raise ValueError('URL has invalid characters. Cannot parse the same.')
  return basename


def download_from_url(public_url: str,
                      filename: Optional[str] = None,
                      download_path: str = downloads) -> Optional[bool]:
  """Downloads file from the url.

  Downloads file from the url and saves it in downloads folder.

  Args:
    public_url: Url of the file.
    filename: Filename (default: None) for the downloaded file.
    download_path: Path (default: ./downloads/) for saving file.

  Returns:
    Boolean value if the file is downloaded or not.

  Raises:
    RequestError: If any error occurs while making an HTTP request.
    RequestException: If any exception occurs if `requests` related
    exceptions occur.

  Notes:
    This function is tested on AWS S3 public urls and can download the
    same. This function doesn't work if tried on google drive. For
    accessing/downloading files over Google Drive, please use -
    `download_from_google_drive()`.
  """
  try:
    download_item = requests.get(public_url, stream=True)
    if filename is None:
      filename = filename_from_url(public_url)
    with open(os.path.join(download_path, filename), 'wb') as file:
      file.write(download_item.content)
    return True
  except (RequestError, RequestException):
    return None


def download_from_google_drive(shareable_url: str,
                               filename: str,
                               download_path: str = downloads
                               ) -> Optional[bool]:
  """Downloads file from the shareable url.

  Downloads file from shareable url and saves it in downloads folder.

  Args:
    shareable_url: Url of the file.
    filename: Filename (default: None) for the downloaded file.
    download_path: Path (default: ./downloads/) for saving file.

  Returns:
    Boolean value if the file is downloaded or not.

  Raises:
    ResponseError: If any unexpected response/error occurs.
    ResponseNotChunked: If the response is not sending correct `chunks`.

  Notes:
    This function is capable of downloading files from Google Drive iff
    these files are shareable using 'Anyone with the link' link sharing
    option.
  """
  try:
    file_id = shareable_url.split('https://drive.google.com/open?id=')[1]
    session = requests.Session()
    response = session.get(dev.DRIVE_DOWNLOAD_URL,
                          params={'id': file_id},
                          stream=True)
    token = _fetch_confirm_token(response)
    if token:
      params = {'id': file_id, 'confirm': token}
      response = session.get(dev.DRIVE_DOWNLOAD_URL, params=params, stream=True)
    with open(os.path.join23678
