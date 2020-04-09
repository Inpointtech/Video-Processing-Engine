"""Utility for work as a wrapper around Amazon's Boto3 API."""

import logging
import math
import os
from datetime import datetime
from typing import List, Optional, Tuple

import boto3
import pytz
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.utils import calculate_tree_hash

from video_processing_engine.utils.common import file_size as fz
from video_processing_engine.utils.paths import downloads


def create_s3_bucket(access_key: str,
                     secret_key: str,
                     bucket_name: str,
                     log: logging.Logger,
                     region: str = 'ap-south-1') -> bool:
  """Create an S3 bucket.

  Create an S3 bucket in a specified region.
  If a region is not specified, the bucket is created in the S3 default
  region is 'ap-south-1 [Asia Pacific (Mumbai)]'.

  Args:
    access_key: AWS access key.
    secret_key: AWS secret key.
    bucket_name: Bucket to create.
    log: Logger object for logging the status.
    region: Bucket region (default: ap-south-1 [Asia Pacific (Mumbai)]).

  Returns:
    Boolean value, True if bucket created.
  """
  try:
    s3 = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key,
                      region_name=region)
  except (ClientError, NoCredentialsError):
    log.error('Wrong credentials used to access the AWS account.')
    return False
  else:
    location = {'LocationConstraint': region}
    try:
      s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
      log.info('New bucket created on Amazon S3 storage.')
    except:
      log.warning('Bucket already exist, skipped bucket creation.')
    return True


def upload_to_bucket(access_key: str,
                     secret_key: str,
                     bucket_name: str,
                     filename: str,
                     log: logging.Logger,
                     s3_name: str = None) -> Optional[str]:
  """Upload file to S3 bucket.

  Uploads file to the S3 bucket and returns it's public IP address.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    bucket_name: Bucket to upload to.
    filename: Local file to upload.
    log: Logger object for logging the status.
    s3_name: Name (default: None) for the uploaded file.

  Returns:
    Public IP address of the uploaded file.
  """
  try:
    s3 = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)
  except (ClientError, NoCredentialsError):
    log.error('Wrong credentials used to access the AWS account.')
    return None
  else:
    if s3_name is None:
      try:
        s3_name = os.path.basename(filename)
      except FileNotFoundError:
        log.error('File not found.')
        return None
    s3.upload_file(filename, bucket_name, s3_name,
                    ExtraArgs={'ACL': 'public-read',
                               'ContentType': 'video/mp4'})
    log.info(f'{s3_name} file uploaded on to Amazon S3 bucket.')
    return generate_s3_url(bucket_name, s3_name)


def generate_s3_url(bucket_name: str, s3_name: str) -> str:
  """Generate public url.

  Generates public url for accessing the uploaded file.

  Args:
    bucket_name: Bucket where file exists.
    s3_name: File name whose URL is to be fetched.

  Returns:
    String, public url.
  """
  s3_name = s3_name.replace(' ', '+')
  return f'https://{bucket_name}.s3.amazonaws.com/{s3_name}'


def check_file(access_key: str,
               secret_key: str,
               s3_url: str,
               log: logging.Logger,
               bucket_name: str = None) -> Optional[List]:
  """Return boolean status, bucket and filename.

  Checks if the file is available on S3 bucket and returns bucket and
  filename.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    s3_url: Public url for the file.
    log: Logger object for logging the status.
    bucket_name: Bucket (default: None) to search and download from.

  Returns:
    List of boolean status, bucket and filename.
  """
  try:
    s3 = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)
  except (ClientError, NoCredentialsError):
    log.error('Wrong credentials used to access the AWS account.')
    return None
  else:
    if bucket_name is None:
      bucket_name = s3_url.split('//')[1].split('.')[0]
    s3_file = s3_url.split('.amazonaws.com/')[1]
    return ['Contents' in s3.list_objects(Bucket=bucket_name,
                                          Prefix=s3_file),
            bucket_name,
            s3_file]


def access_file(access_key: str,
                secret_key: str,
                s3_url: str,
                log: logging.Logger,
                bucket_name: str = None) -> None:
  """Access file from S3 bucket.

  Access and download file from S3 bucket.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    s3_url: Public url for the file.
    log: Logger object for logging the status.
    bucket_name: Bucket (default: None) to search and download from.

  Notes:
    This function ensures the file exists on the S3 bucket and then
    downloads the same. If the file doesn't exist on S3, it'll return
    None.
  """
  try:
    s3 = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)
  except (ClientError, NoCredentialsError):
    log.error('Wrong credentials used to access the AWS account.')
    return None
  else:
    [*status, bucket, file] = check_file(access_key, secret_key,
                                         s3_url, log, bucket_name)
    if status[0]:
      s3.download_file(bucket, file, save_file(bucket, file))
    else:
      return None


def access_file_update(access_key: str,
                       secret_key: str,
                       s3_url: str,
                       file_name: str,
                       log: logging.Logger,
                       bucket_name: str = None) -> Tuple:
  """Access file from S3 bucket.

  Access and download file from S3 bucket.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    s3_url: Public url for the file.
    log: Logger object for logging the status.
    bucket_name: Bucket to search and download from.

  Notes:
    This function ensures the file exists on the S3 bucket and then
    downloads the same. If the file doesn't exist on S3, it'll return
    None.
  """
  try:
    s3 = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)
  except (ClientError, NoCredentialsError):
    log.error('Wrong credentials used to access the AWS account.')
    return None, '[e] Error while downloading file'
  else:
    [*status, bucket, file] = check_file(access_key, secret_key,
                                         s3_url, log, bucket_name)
    if status[0]:
      s3.download_file(bucket,
                       file,
                       os.path.join(downloads, f'{file_name}.mp4'))
      log.info(f'File "{file_name}.mp4" downloaded from Amazon S3 storage.')
      if fz(os.path.join(downloads, f'{file_name}.mp4')).endswith('KB'):
        log.error('Unusable file downloaded since file size is in KBs.')
        return None, '[w] Unusable file downloaded.'
      return True, os.path.join(downloads, f'{file_name}.mp4')
    else:
      log.error('File download from Amazon S3 failed because of poor network '
                'connectivity.')
      return None, '[e] Error while downloading file'


def save_file(bucket_name: str, filename: str) -> str:
  """Save S3 file.

  Create a directory with bucket name and save the file in it.

  Args:
    bucket_name: Bucket to search and download from.
    filename: File to download and save.

  Returns:
    String path where the downloaded file needs to be saved.

  Notes:
    If the `./downloads/` folder doesn't exists, it creates one and
    proceeds further with it.
  """
  if not os.path.isdir(os.path.join(downloads, bucket_name)):
    os.makedirs(os.path.join(downloads, bucket_name))
  return os.path.join(os.path.join(downloads, bucket_name), filename)


def copy_file_from_bucket(access_key: str,
                          secret_key: str,
                          customer_bucket_name: str,
                          customer_obj_key: str,
                          bucket_name: str,
                          log: logging.Logger,
                          bucket_obj_key: str = None) -> Optional[bool]:
  """Copy an object from one S3 bucket to another.

  Copies an object/file from one S3 bucket to another considering we
  have access.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    customer_bucket_name: Bucket name from where we need to fetch file.
    customer_obj_key: Object/File name to be fetched.
    bucket_name: Target bucket name where to dump the fetched file.
    log: Logger object for logging the status.
    bucket_obj_key: Object name to be renamed in destination bucket.

  Notes:
    This function assumes that the files from 'customer_bucket_name'
    are publicly available.
  """
  try:
    s3 = boto3.resource('s3',
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key)
  except (ClientError, NoCredentialsError):
    log.error('Wrong credentials used to access the AWS account.')
    return None
  else:
    copy_source = {
        'Bucket': customer_bucket_name,
        'Key': customer_obj_key
    }
    s3.meta.client.copy(copy_source, bucket_name, bucket_obj_key)
    return True


def create_glacier_vault(access_key: str,
                         secret_key: str,
                         account_id: str,
                         vault_name: str,
                         log: logging.Logger,
                         region: str = 'ap-south-1') -> bool:
  """Create a S3 Glacier vault.

  Create a S3 Glacier vault for archiving data in a specified region.
  If a region is not specified, the bucket is created in the S3 default
  region is 'ap-south-1 [Asia Pacific (Mumbai)]'.

  Args:
    access_key: AWS access key.
    secret_key: AWS secret key.
    account_id: AWS account ID.
    vault_name: Vault to create.
    log: Logger object for logging the status.
    region: Bucket region (default: ap-south-1 [Asia Pacific (Mumbai)]).

  Returns:
    Boolean value, True if the vault is created.
  """
  try:
    glacier = boto3.resource('glacier',
                             aws_access_key_id=access_key,
                             aws_secret_access_key=secret_key,
                             region_name=region)
  except (ClientError, NoCredentialsError):
    log.error('Wrong credentials used to access the AWS account.')
    return False
  else:
    glacier.Vault(account_id, vault_name).create()
    log.info('Vault created on Amazon S3 Glacier.')
    return True


def upload_to_vault(access_key: str,
                    secret_key: str,
                    account_id: str,
                    vault_name: str,
                    file_name: str,
                    log: logging.Logger = None,
                    archive_name: str = None,
                    region: str = 'ap-south-1') -> Optional[dict]:
  """Upload archive to S3 Glacier.

  Uploads files to S3 Glacier for archival.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    bucket_name: Bucket to upload to.
    file_name: Local file to upload.
    log: Logger object for logging the status.
    s3_name: Name (default: None) for the uploaded file.

  Returns:
    Dictionary/Response of the uploaded archived file.
  """
  # You can find the reference code here:
  # https://stackoverflow.com/a/52602270
  try:
    glacier = boto3.client('glacier',
                           aws_access_key_id=access_key,
                           aws_secret_access_key=secret_key,
                           region_name=region)
  except (ClientError, NoCredentialsError):
    log.error('Wrong credentials used to access the AWS account.')
    return None
  else:
    if archive_name is None:
      try:
        archive_name = os.path.basename(file_name)
      except FileNotFoundError:
        log.error('File not found.')
        return None
    upload_chunk = 2 ** 25
    mp_upload = glacier.initiate_multipart_upload
    mp_part = glacier.upload_multipart_part
    cp_upload = glacier.complete_multipart_upload
    multipart_archive_upload = mp_upload(vaultName=vault_name,
                                         archiveDescription=file_name,
                                         partSize=str(upload_chunk))
    file_size = os.path.getsize(file_name)
    multiple_parts = math.ceil(file_size / upload_chunk)
    with open(file_name, 'rb') as upload_archive:
      for idx in range(multiple_parts):
        min_size = idx * upload_chunk
        max_size = min_size + upload_chunk - 1
        if max_size > file_size:
          max_size = (file_size - min_size) + min_size - 1
        file_part = upload_archive.read(upload_chunk)
        upload_part = mp_part(vaultName=vault_name,
                              uploadId=multipart_archive_upload['uploadId'],
                              range=f'bytes {min_size}-{max_size}/{file_size}',
                              body=file_part)
    checksum = calculate_tree_hash(open(file_name, 'rb'))
    complete_upload = cp_upload(vaultName=vault_name,
                                uploadId=multipart_archive_upload['uploadId'],
                                archiveSize=str(file_size),
                                checksum=checksum)
    log.info(f'"{file_name}" file archived on AWS S3 Glacier.')
    return complete_upload


def access_limited_files(access_key: str,
                         secret_key: str,
                         bucket_name: str,
                         access_from: str,
                         access_to: str,
                         log: logging.Logger,
                         timestamp_format: str = '%Y-%m-%d %H:%M:%S') -> List:
  """Access files from S3 bucket for particular timeframe.

  Access and download file from S3 bucket for particular timeframe.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    bucket_name: Bucket to search and download from.
    access_from: Datetime from when to start fetching files.
    access_to: Datetime till when to fetch files.
    log: Logger object for logging the status.
    timestamp_format: Timestamp format (default: %Y-%m-%d %H:%M:%S)

  Notes:
    This function ensures the files exists on the S3 bucket and then
    downloads the same. If the file doesn't exist on S3, it'll return
    None.
  """
  try:
    s3 = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)
  except (ClientError, NoCredentialsError):
    log.error('Wrong credentials used to access the AWS account.')
    return []
  else:
    limit_from = datetime.strptime(
        access_from, timestamp_format).replace(tzinfo=pytz.UTC)
    limit_till = datetime.strptime(
        access_to, timestamp_format).replace(tzinfo=pytz.UTC)
    bucket_dir = os.path.join(downloads, bucket_name)
    concate_dir = []
    files_with_timestamp = {}
    all_files = s3.list_objects_v2(Bucket=bucket_name)
    for files in all_files['Contents']:
      if files['Key'].endswith('.mp4'):
        files_with_timestamp[files['Key']] = files['LastModified']
    sorted_files = sorted(files_with_timestamp.items(), key=lambda xa: xa[1])
    for file, timestamp in sorted_files:
      if timestamp > limit_from and timestamp < limit_till:
        s3_style_dir = os.path.join(bucket_dir, os.path.dirname(file))
        concate_dir.append(s3_style_dir)
        if not os.path.isdir(s3_style_dir):
          os.makedirs(s3_style_dir)
        s3.download_file(bucket_name, file, os.path.join(s3_style_dir,
                                          os.path.basename(file)))
        log.info(f'File "{file}" downloaded from Amazon S3.')
    return list(set(concate_dir))
