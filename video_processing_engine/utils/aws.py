"""Utility for working with AWS using boto3."""

import logging
import os
from typing import List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from video_processing_engine.utils.common import file_size as fz
from video_processing_engine.utils.logs import log as _log
from video_processing_engine.utils.paths import downloads


def create_s3_bucket(access_key: str,
                     secret_key: str,
                     bucket_name: str,
                     region: str = 'ap-south-1',
                     log: logging.Logger = None) -> bool:
  """Create an S3 bucket.

  Create an S3 bucket in a specified region.
  If a region is not specified, the bucket is created in the S3 default
  region is 'ap-south-1 [Asia Pacific (Mumbai)]'.

  Args:
    access_key: AWS access key.
    secret_key: AWS secret key.
    bucket_name: Bucket to create.
    region: Bucket region (default: ap-south-1 [Asia Pacific (Mumbai)]).

  Returns:
    Boolean value, True if bucket created.
  """
  log = _log(__file__) if log is None else log
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
                     s3_name: str = None,
                     log: logging.Logger = None) -> Optional[str]:
  """Upload file to S3 bucket.

  Uploads file to the S3 bucket and returns it's public IP address.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    bucket_name: Bucket to upload to.
    filename: Local file to upload.
    s3_name: Name (default: None) for the uploaded file.

  Returns:
    Public IP address of the uploaded file.
  """
  log = _log(__file__) if log is None else log
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
        return None
      else:
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
               bucket_name: str = None,
               log: logging.Logger = None) -> Optional[List]:
  """Return boolean status, bucket and filename.

  Checks if the file is available on S3 bucket and returns bucket and
  filename.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    s3_url: Public url for the file.
    bucket_name: Bucket to search and download from.

  Returns:
    List of boolean status, bucket and filename.
  """
  log = _log(__file__) if log is None else log
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
                bucket_name: str = None) -> None:
  """Access file from S3 bucket.

  Access and download file from S3 bucket.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    s3_url: Public url for the file.
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
    return None
  else:
    [*status, bucket, file] = check_file(access_key, secret_key,
                                         s3_url, bucket_name)
    if status[0]:
      s3.download_file(bucket, file, save_file(bucket, file))
    else:
      return None


def access_file_update(access_key: str,
                       secret_key: str,
                       s3_url: str,
                       file_name: str,
                       bucket_name: str = None,
                       log: logging.Logger = None) -> Tuple:
  """Access file from S3 bucket.

  Access and download file from S3 bucket.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    s3_url: Public url for the file.
    bucket_name: Bucket to search and download from.

  Notes:
    This function ensures the file exists on the S3 bucket and then
    downloads the same. If the file doesn't exist on S3, it'll return
    None.
  """
  log = _log(__file__) if log is None else log
  try:
    s3 = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)
  except (ClientError, NoCredentialsError):
    log.error('Wrong credentials used to access the AWS account.')
    return None, '[e] Error while downloading file'
  else:
    [*status, bucket, file] = check_file(access_key, secret_key,
                                         s3_url, bucket_name)
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
                          bucket_obj_key: str = None,
                          log: logging.Logger = None) -> Optional[bool]:
  """Copy an object from one S3 bucket to another."""
  log = _log(__file__) if log is None else log
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
