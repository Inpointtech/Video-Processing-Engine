"""Utility to fetch files from Google Drive, Azure and FTP."""

import logging
import os
from datetime import datetime
from typing import List, Tuple
from urllib.parse import unquote, urlsplit

import pytz
import requests
from azure.storage.blob import BlobClient, ContainerClient
from requests.exceptions import RequestException
from urllib3.exceptions import RequestError

from video_processing_engine.core.process.concate import concate_videos
from video_processing_engine.core.process.stats import video_file_extensions
from video_processing_engine.utils.boto_wrap import access_limited_files
from video_processing_engine.utils.common import file_size as fz
from video_processing_engine.utils.logs import log
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
  if (os.path.basename(basename) != basename
      or unquote(os.path.basename(url_path)) != basename):
    raise ValueError('[e] URL has invalid characters. Cannot parse the same.')
  return basename


def download_from_url(public_url: str,
                      filename: str = None,
                      download_path: str = downloads) -> Tuple:
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
      return True, os.path.join(download_path, filename)
  except (RequestError, RequestException):
    return None, '[e] Error while downloading file'


def fetch_confirm_token(response: requests.Response):
  """Don't know what this is, hence docstring not updated yet."""
  # TODO(xames3): Update the docstring accordingly.
  for k, v in response.cookies.items():
    if k.startswith('download_warning'):
      return v
  else:
    return None


def download_from_google_drive(shareable_url: str,
                               file_name: str,
                               log: logging.Logger,
                               download_path: str = downloads) -> Tuple:
  """Downloads file from the shareable url.

  Downloads file from shareable url and saves it in downloads folder.

  Args:
    shareable_url: Url of the file.
    file_name: Filename for the downloaded file.
    log: Logger object for logging the status.
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
    with open(os.path.join(download_path, f'{file_name}.mp4'), 'wb') as file:
      for chunk in response.iter_content(dev.CHUNK_SIZE):
        if chunk:
          file.write(chunk)
    log.info(f'File "{file_name}.mp4" downloaded from Google Drive.')
    if fz(os.path.join(download_path, f'{file_name}.mp4')).endswith('KB'):
      log.error('Unusable file downloaded since file size is in KBs.')
      return None, '[w] Unusable file downloaded.'
    return True, os.path.join(download_path, f'{file_name}.mp4')
  except (RequestError, RequestException):
    log.error('File download from Google Drive failed because of poor network '
              'connectivity.')
    return None, '[e] Error while downloading file'


def generate_connection_string(account_name: str,
                               account_key: str,
                               protocol: str = 'https') -> str:
  """Generates the connection string for Microsoft Azure."""
  connection_string = (f'DefaultEndpointsProtocol={protocol};'
                       f'AccountName={account_name};AccountKey={account_key};'
                       'EndpointSuffix=core.windows.net')
  return connection_string


def download_from_azure(account_name: str,
                        account_key: str,
                        container_name: str,
                        blob_name: str,
                        file_name: str,
                        log: logging.Logger,
                        download_path: str = downloads) -> Tuple:
  """Download file from Microsoft Azure.

  Download file from Microsoft Azure and store it in downloads folder.

  Args:
    account_name: Azure account name.
    account_key: Azure account key.
    container_name: Container from which blob needs to be downloaded.
    blob_name: Blob to download from Microsoft Azure.
    file_name: Filename for the downloaded file.
    log: Logger object for logging the status.
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
    with open(os.path.join(download_path, f'{file_name}.mp4'), 'wb') as file:
      data = blob.download_blob()
      data.readinto(file)
    log.info(f'File "{file_name}.mp4" downloaded from Microsoft Azure.')
    if fz(os.path.join(download_path, f'{file_name}.mp4')).endswith('KB'):
      log.error('Unusable file downloaded since file size is in KBs.')
      return None, '[w] Unusable file downloaded.'
    return True, os.path.join(download_path, f'{file_name}.mp4')
  except Exception:
    log.error('File download from Microsoft Azure failed because of poor '
              'network connectivity.')
    return None, '[e] Error while downloading file'


def get_blob_url(account_name: str,
                 container_name: str,
                 blob_name: str) -> str:
  """Get blob URL."""
  return (f'https://{account_name}.blob.core.windows.net/{container_name}'
          f'/{blob_name}')


def download_using_ftp(username: str,
                       password: str,
                       public_address: str,
                       remote_file: str,
                       file_name: str,
                       log: logging.Logger,
                       download_path: str = downloads) -> Tuple:
  """Download/fetch/transfer file using OpenSSH via FTP.

  Fetch file from remote machine to store it in downloads folder.

  Args:
    username: Username of the remote machine.
    password: Password of the remote machine.
    public_address: Remote server IP address.
    remote_file: Remote file to be downloaded/transferred.
    file_name: Filename for the downloaded file.
    log: Logger object for logging the status.
    download_path: Path (default: ./downloads/) for saving file.

  Returns:
    Boolean value if the file is downloaded or not.
  """
  # You can find the reference code here:
  # https://stackoverflow.com/a/56850195
  try:
    os.system(f'sshpass -p {password} scp -o StrictHostKeyChecking=no '
              f'{username}@{public_address}:{remote_file} {download_path}')
    log.info(f'File "{file_name}.mp4" transferred successfully')
    if fz(os.path.join(download_path, f'{file_name}.mp4')).endswith('KB'):
      log.error('Unusable file transferred since file size is in KBs.')
      return None, '[w] Unusable file transferred.'
    return True, os.path.join(download_path, f'{file_name}.mp4')
  except OSError:
    log.error('File transfer via FTP failed because of poor network '
              'connectivity.')
    return None, '[e] Error while transferring file'


def concate_batch_from_s3(access_key: str,
                          secret_key: str,
                          bucket_name: str,
                          access_from: str,
                          access_to: str,
                          log: logging.Logger,
                          timestamp_format: str = '%Y-%m-%d %H:%M:%S') -> List:
  """Downloads multiple files from S3 and concatenate them.

  Download multiple files from S3 bucket for particular timeframe and
  concatenate them resulting into a single file in each directory.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    bucket_name: Bucket to search and download from.
    access_from: Datetime from when to start fetching files.
    access_to: Datetime till when to fetch files.
    log: Logger object for logging the status.
    timestamp_format: Timestamp format (default: %Y-%m-%d %H:%M:%S)

  Returns:
    List of the concatenated files.
  """
  log.info(f'Downloading files from "{bucket_name}" for range {access_from} '
           f'to {access_to} from Amazon S3.')
  list_of_dirs = access_limited_files(access_key, secret_key, bucket_name,
                                      access_from, access_to, log,
                                      timestamp_format)
  if len(list_of_dirs) > 0:
    log.info('Concatenating files in their subsequent directories.')
    return [concate_videos(idx) for idx in list_of_dirs]
  else:
    log.warning('0 files downloaded. Returning empty list.')
    return []


def batch_download_from_azure(account_name: str,
                              account_key: str,
                              container_name: str,
                              access_from: str,
                              access_to: str,
                              log: logging.Logger,
                              timestamp_format: str = '%Y-%m-%d %H:%M:%S',
                              download_path: str = downloads) -> List:
  """Download multiple files from Microsoft Azure.

  Download multiple files from Azure Blob container for particular
  timeframe.

  Args:
    account_name: Azure account name.
    account_key: Azure account key.
    container_name: Container from which blob needs to be downloaded.
    blob_name: Blob to download from Microsoft Azure.
    file_name: Filename for the downloaded file.
    log: Logger object for logging the status.
    download_path: Path (default: ./downloads/) for saving file.

  Returns:
    List of the directories which hosts the downloaded files.
  """
  # You can find the reference code here:
  # https://pypi.org/project/azure-storage-blob/
  try:
    connection_string = generate_connection_string(account_name, account_key)
    container = ContainerClient.from_connection_string(connection_string,
                                                  container_name=container_name)
    limit_from = datetime.strptime(
        access_from, timestamp_format).replace(tzinfo=pytz.UTC)
    limit_till = datetime.strptime(
        access_to, timestamp_format).replace(tzinfo=pytz.UTC)
    container_dir = os.path.join(downloads, container_name)
    concate_dir = []
    files_with_timestamp = {}
    blobs_list = container.list_blobs()
    for blob in blobs_list:
      if (blob.name).endswith(video_file_extensions):
        files_with_timestamp[blob.name] = blob.creation_time
    sorted_files = sorted(files_with_timestamp.items(), key=lambda xa: xa[1])
    for file, timestamp in sorted_files:
      if timestamp > limit_from and timestamp < limit_till:
        blob_style_dir = os.path.join(container_dir, os.path.dirname(file))
        concate_dir.append(blob_style_dir)
        if not os.path.isdir(blob_style_dir):
          os.makedirs(blob_style_dir)
        download_from_azure(account_name, account_key, container_name,
                            file, os.path.basename(file[:-4]), log,
                            blob_style_dir)
    return list(set(concate_dir))
  except Exception:
    log.error('File download from Microsoft Azure failed because of poor '
              'network connectivity.')
    return []


def concate_batch_from_azure(account_name: str,
                             account_key: str,
                             container_name: str,
                             access_from: str,
                             access_to: str,
                             log: logging.Logger,
                             timestamp_format: str = '%Y-%m-%d %H:%M:%S'
                             ) -> List:
  """Downloads multiple files from Azure and concatenate them.

  Download multiple files from Azure bucket for particular timeframe and
  concatenate them resulting into a single file in each directory.

  Args:
    account_name: Azure account name.
    account_key: Azure account key.
    container_name: Container from which blob needs to be downloaded.
    access_from: Datetime from when to start fetching files.
    access_to: Datetime till when to fetch files.
    log: Logger object for logging the status.
    timestamp_format: Timestamp format (default: %Y-%m-%d %H:%M:%S)

  Returns:
    List of the concatenated files.
  """
  log.info(f'Downloading files "{container_name}" for range {access_from} '
           f'to {access_to} from Microsoft Azure.')
  list_of_dirs = batch_download_from_azure(account_name, account_key,
                                           container_name, access_from,
                                           access_to, log, timestamp_format)
  if len(list_of_dirs) > 0:
    log.info('Concatenating files in their subsequent directories.')
    return [concate_videos(idx) for idx in list_of_dirs]
  else:
    log.warning('0 files downloaded. Returning empty list.')
    return []
