"""Utility for upload files to Azure, GCS and FTP."""

import os
from typing import Optional

from azure.storage.blob import BlobClient

from video_processing_engine.utils.access import generate_connection_string
from video_processing_engine.utils.logs import log

log = log(__file__)


def push_to_azure(account_name: str,
                  account_key: str,
                  container_name: str,
                  filename: str) -> Optional[bool]:
  """Upload file to Microsoft Azure.

  Upload file to Microsoft Azure.

  Args:
    account_name: Azure account name.
    account_key: Azure account key.
    container_name: Container where the file needs to be uploaded.
    filename: File to upload.

  Returns:
    Boolean value if the file is uploaded or not.
  """
  # You can find the reference code here:
  # https://pypi.org/project/azure-storage-blob/
  try:
    blob_name = os.path.basename(filename)
    connection_string = generate_connection_string(account_name, account_key)
    blob = BlobClient.from_connection_string(conn_str=connection_string,
                                             container_name=container_name,
                                             blob_name=blob_name)
    with open(filename, 'rb') as file:
      blob.upload_blob(file)
    log.info(f'File "{os.path.basename(filename)}" uploaded to '
             'Microsoft Azure.')
    return True
  except Exception:
    log.error('File upload to Microsoft Azure failed because of poor '
              'network connectivity.')
    return None


def push_to_client_ftp(username: str,
                       password: str,
                       public_address: str,
                       file_path: str,
                       remote_path: str) -> Optional[bool]:
  """Upload/push file using OpenSSH via FTP.

  Push file from current machine to a remote machine.

  Args:
    username: Username of the remote machine.
    password: Password of the remote machine.
    public_address: Remote server IP address.
    file_path: File to be pushed onto remote machine.
    remote_path: Remote path where the file is to be transferred.

  Returns:
    Boolean value if the file is uploaded or not.
  """
  # You can find the reference code here:
  # https://stackoverflow.com/a/56850195
  try:
    os.system(f'sshpass -p {password} scp -o StrictHostKeyChecking=no '
              f'{file_path} {username}@{public_address}:{remote_path}')
    log.info(f'File "{os.path.basename(file_path)}" transferred successfully.')
    return True
  except OSError:
    log.error('File transfer via FTP failed because of poor network '
              'connectivity.')
    return None
