"""Utility to access and download files."""

import os
from typing import Optional
from urllib.parse import unquote, urlsplit

import requests
from azure.storage.blob import BlobClient
from google.cloud import storage
from google.oauth2 import service_account
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
                      filename: str = None,
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


def download_from_gcs(type_of_account: str,
                      project_id: str,
                      private_key_id: str,
                      bucket_name: str,
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
  # service_account_info = json.loads(
  #     'service_account.json', encoding='utf-8')
  # print(service_account_info)
  # credentials = service_account.Credentials.from_service_account_json(
  #     'service_account.json')
  # client = storage.Client.from_service_account_json(
  #     '/home/xames3/Desktop/video_processing_engine/video_processing_engine/utils/service_account.json')
  # bucket = client.bucket(bucket_name)
  # blob = bucket.blob(source_blob_name)
  # blob.download_to_filename(os.path.join(download_path, filename))
  json_obj = {
      "type": "service_account",
      "project_id": "video-processing-engine-beta",
      "private_key_id": "e4f054133ce1012a1abce276400911481cd2a31e",
      "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCurZioOVUq9x9s\nBzTeFj0s2ao3BF86ri4uqyPAAwyvqDnC9lSEbwkY8bfnxMUBZmtbwZmnLbxt69Yu\ncgQi1n4ElYgw5AVvF1Kgptk5O3kyxfK23Z+VtoGx54vZDU374Gek/HfSBLQT7DTI\nYc03toNLR4lFLSKJt0PfzXiso2CJBYlt1dEeePWfZKwv+4u5k394XRhLEjQTkeBN\nJ5SFCpA0DY7lTlRyurfOoL8gOJBu9zrMYMsJ3P3px4TTDJ9HUYIcG2YNMxkHfqBr\nkorSDdIeGu5K1xSPNWVDgqxWWiip/pA1QBrY2p3n4gWNqlDyDZpJY2x3YpGJdtrz\n/x5UQ7U7AgMBAAECggEAFMAFdD0J9iZ7YpYBPJKau3MIlSwyncy8KrS6H0tIHK5u\nB3rDSSTMNAeJfQGdv3qprTGJ2FdcB24ZDX+40w9KKARACe1vDHvSR8hE4gIZIHlt\nnuB5M8va4JssvIt9OeW174jtjj1wdjS8g8NDzBGlIMeuMaauGtBHl/9CDbauDIix\nNmdY3khaGsJl0x1oxc+x735cvBXpKBTOoS6TAXTJekTINlJ3y1UWagZwQnKwN3L3\nQrxtkYcL/zyNl5/EN97yf+3RFf9WR7OFfnEF5YlVOBI3T/z5NZpfig8jlWJ+0Wvn\nL0FkxWwNy+XnEVWfZTpYWGoxnJgnZicCq7vE7nS/PQKBgQDoeUF/w2JZyZsuCgiV\nyAugpCijDzEqYfaNpBe+c943kcjrMa44XfjvqWmnKcCPLj2h2r/6vg2fPK8JJfyI\nIpUZ0L2qlv49OaalfYCPtG7g++E1wyzy3o7V3cPzkN2hv0LsPTdryWhc4Hh+EWUD\n27ZPMrzWX5k5q6Vlpf0sarW7dQKBgQDAWwTg5DsUaeA06tK4+2WPT79ooWUroRyR\neQ0n0Z37M0jnZ4ia/omSM9eQgTnZu92yNTUlARtfaYTyr1YgIetFHnygGorDDYc5\nVnT4PfFdqAjBnYnxjV6wh4KRiSNR0as3qGp/wjcbTuYeZl1FUiGCvAd8fU3eG19s\n9fnmTuOH7wKBgQClAlyBiXfn73gcZ7bMSiAmuB64DvKA+OP+ibjo0Gms2+fXOX5G\nOD2YL5H0u2gYuWO53QFjwz78BiDfx3zGTHW0yzu1OFPhtWgaE0kLt7D0NRUYCh9/\njIWqPCz4V51ZT976vED4Ww+ezR35rfMbl/qBoKv1JgomqzVNP1LDEkNIeQKBgH13\nIPB7jZmcEZUSkc38lFrs3mGl3DKgDN1KQu11CYG/Cs99NZo7aopFbFaiI5TEuC80\nC20OksciMYiGGzwsQ6Q65XkctuPRICGjJfqBlLzNDKEVW9OFrXyhduXsuG/2vaI5\nJPYePQl/5hNwG2hK0PbQJGXr6W11F0IgExdI35pbAoGAPNKZnabqi0KnEioAAc3r\nmWDvMJ3tIqPaRd+eWKLoiyCqcLUw4gG6/7596WZqFX/Agkep9umeHR1p+6LWvJEL\n4lfJ0SXqQw4qKvzn+gBO2zhFdrqABVb0tUU0FtspCOR8CLjOJDGSRxheEGUIDntg\nEsGsxDjL+t+aTZBSaSQSgYk=\n-----END PRIVATE KEY-----\n",
      "client_email": "video-processing-engine-servic@video-processing-engine-beta.iam.gserviceaccount.com",
      "client_id": "115726406834255702972",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/video-processing-engine-servic%40video-processing-engine-beta.iam.gserviceaccount.com"
  }
  from oauth2client.service_account import ServiceAccountCredentials
  try:
    # credentials_dict = {
    #     'type': 'service_account',
    #     'client_id': os.environ['BACKUP_CLIENT_ID'],
    #     'client_email': os.environ['BACKUP_CLIENT_EMAIL'],
    #     'private_key_id': os.environ['BACKUP_PRIVATE_KEY_ID'],
    #     'private_key': os.environ['BACKUP_PRIVATE_KEY'],
    # }


    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        json_obj
    )
    client = storage.Client(credentials=credentials, project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(os.path.join(download_path, filename))
    return True
  except Exception as err:
    print(err)
    return None


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
                        filename: str,
                        download_path: str = downloads) -> Optional[bool]:
  """Download file from Microsoft Azure.

  Download file from Microsoft Azure and store it in downloads folder.

  Args:
    account_name: Azure account name.
    account_key: Azure account key.
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


