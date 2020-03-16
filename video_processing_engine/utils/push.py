"""Utility for pushing files to Azure, GCS and FTP."""

import boto3
# from boto3.s3.connection import S3Connection
import os
from typing import Optional

from azure.storage.blob import BlobClient

from video_processing_engine.utils.access import generate_connection_string, download_from_azure
from video_processing_engine.utils.common import now


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
      return True
  except Exception:
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
    return True
  except OSError:
    return None
