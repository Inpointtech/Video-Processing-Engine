"""Utility to access and download files."""

import os
from typing import Optional
from urllib.parse import unquote, urlsplit

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
import requests
from azure.storage.blob import BlobClient, BlobServiceClient
from google.cloud import storage
from requests.exceptions import RequestException
from urllib3.exceptions import RequestError

from video_processing_engine.utils.paths import downloads
from video_processing_engine.vars import dev


def filename_from_url(public_url: str) -> str:
  """Returns filename from public url.

  Args:
    public_url: Url of the file.

  Returns:
    Extracted filename from it's url.

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


def fetch_confirm_token(response: requests.Response):
  """Don't know what this is, hence docstring not updated yet."""
  # TODO(xames3): Update the docstring accordingly.
  for k, v in response.cookies.items():
    if k.startswith('download_warning'):
      return v
  else:
    return None

def download_from_google_drive(shareable_url: str,
                               filename: str,
                               download_path: str = downloads
                               ) -> Optional[bool]:
  """Downloads file from the shareable url.

  Downloads file from shareable url and saves it in downloads folder.

  Args:
    shareable_url: Url of the file.
    filename: Filename for the downloaded file.
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
  # You can find the reference code here:
  # https://stackoverflow.com/a/39225272
  try:
    file_id = shareable_url.split('https://drive.google.com/open?id=')[1]
    session = requests.Session()
    response = session.get(dev.DRIVE_DOWNLOAD_URL,
                           params={'id': file_id},
                           stream=True)
    token = fetch_confirm_token(response)
    if token:
      response = session.get(dev.DRIVE_DOWNLOAD_URL,
                             params={'id': file_id, 'confirm': token},
                             stream=True)
    # Write file to the disk.
    with open(os.path.join(download_path, filename), 'wb') as file:
      for chunk in response.iter_content(dev.CHUNK_SIZE):
        if chunk:
          file.write(chunk)
      return True
  except (RequestError, RequestException):
    return None


def download_from_gcs(bucket_name: str,
                      source_blob_name: str,
                      filename: str,
                      download_path: str = downloads) -> Optional[bool]:
  """Download file from Google Cloud Storage.

  Download file from Google Cloud Storage and store it in downloads
  folder.

  Args:
    bucket_name: Bucket name on GCS.
    source_blob_name: Blob to download from GCS.
    filename: Filename for the downloaded file.
    download_path: Path (default: ./downloads/) for saving file.

  Returns:
    Boolean value if the file is downloaded or not.
  """
  # You can find the reference code here:
  # https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/storage/cloud-client/storage_download_file.py
  try:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(os.path.join(download_path, filename))
    return True
  except Exception:
    return None


def generate_connection_string(account_name: str,
                               account_key: str,
                               protocol: Optional[str] = 'https') -> str:
  """Generates the connection string for Microsoft Azure."""
  connection_string = (f'DefaultEndpointsProtocol={protocol};'
                       f'AccountName={account_name};AccountKey={account_key};'
                       'EndpointSuffix=core.windows.net')
  return BlobServiceClient.from_connection_string(conn_str=connection_string)


def download_from_azure(account_name: str,
                        account_key: str,
                        container_name: str,
                        blob_name: str,
                        filename: str,
                        download_path: str = downloads) -> Optional[bool]:
  """Download file from Microsoft Azure.

  Download file from Microsoft Azure and store it in downloads folder.

  Args:
    connection_string: Azure connection string/url for that file.
    container_name: Container from which blob needs to be downloaded.
    blob_name: Blob to download from Microsoft Azure.
    filename: Filename for the downloaded file.
    download_path: Path (default: ./downloads/) for saving file.

  Returns:
    Boolean value if the file is downloaded or not.
  """
  # You can find the reference code here:
  # https://pypi.org/project/azure-storage-blob/
  try:
    connection_string = generate_connection_string(account_name, account_key)
    blob = BlobClient.from_connection_string(conn_str=connection_string,
                                             container_name=container_name,
                                             blob_name=blob_name)
    with open(os.path.join(download_path, filename), 'wb') as file:
      data = blob.download_blob()
      data.readinto(file)
      return True
  except Exception:
    return None


def download_using_ftp(username: str,
                       password: str,
                       public_address: str,
                       remote_file: str,
                       download_path: str = downloads) -> Optional[bool]:
  """Download/fetch/transfer file using OpenSSH via FTP.

  Fetch file from remote machine to store it in downloads folder.

  Args:
    username: Username of the remote machine.
    password: Password of the remote machine.
    public_address: Remote server IP address.
    remote_file: Remote file to be downloaded/transferred.
    download_path: Path (default: ./downloads/) for saving file.

  Returns:
    Boolean value if the file is downloaded or not.
  """
  # You can find the reference code here:
  # https://stackoverflow.com/a/56850195
  try:
    os.system(f'sshpass -p {password} scp -o StrictHostKeyChecking=no '
              f'{username}@{public_address}:{remote_file} {download_path}')
    return True
  except OSError:
    return None
