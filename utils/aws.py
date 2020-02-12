"""Utility for working with AWS using boto3."""

import os
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from video_processing_engine.utils.paths import downloads


def create_s3_bucket(access_key: str,
                     secret_key: str,
                     bucket_name: str,
                     region: Optional[str] = 'ap-south-1') -> bool:
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

  Examples:
    >>> from video_processing_engine.utils.aws import create_s3_bucket
    >>>
    >>> create_s3_bucket('test_access_key',
    ...                  'test_secret_key',
    ...                  'test_bucket_name')
    True
    >>>
  """
  try:
    s3 = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key,
                      region_name=region)
  except (ClientError, NoCredentialsError):
      return False
  else:
    location = {'LocationConstraint': region}
    s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
    return True


def upload_to_bucket(access_key: str,
                     secret_key: str,
                     bucket_name: str,
                     filename: str,
                     s3_name: Optional[str] = None) -> Optional[str]:
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

  Examples:
    >>> from utils.s3_config import upload_to_bucket
    >>>
    >>> upload_to_bucket('test_access_key',
    ...                  'test_secret_key',
    ...                  'test_bucket_name')
    ...                  'test_file_to_upload.py')
    >>> True
    https://test_bucket_name.s3.amazonaws.com/test_file_to_upload.py
  """
  try:
    s3 = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)
  except (ClientError, NoCredentialsError):
    return None
  else:
    if s3_name is None:
      try:
        s3_name = os.path.basename(filename)
      except FileNotFoundError:
        return None
      else:
        s3.upload_file(filename, bucket_name, s3_name,
                       ExtraArgs={'ACL': 'public-read'})
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
               bucket_name: Optional[str] = None) -> Optional[List]:
  """Return boolean value depending on file's existence."""
  try:
    s3 = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)
  except (ClientError, NoCredentialsError):
    return None
  else:
    if bucket_name is None:
      bucket_name = s3_url.split('//')[1].split('.')[0]
    s3_file = s3_url.split('.amazonaws.com/')[1]
    return ['Contents' in s3.list_objects(Bucket=bucket_name, Prefix=s3_file),
            bucket_name,
            s3_file]


def access_file(access_key: str,
                secret_key: str,
                s3_url: str,
                bucket_name: Optional[str] = None) -> None:
  """Access file from S3 bucket.

  Access and download file from S3 bucket.

  Args:
    access_key: AWS access key.
    secret_key: AWS saccess_key: str,
    s3_url: Public url for the file.
    bucket_name: Bucket to search and download from.

  Note:
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


def save_file(bucket_name: str, filename: str) -> str:
  """Save S3 file.

  Create a directory with bucket name and save the file in it.

  Args:
   bucket_name: Bucket to search and download from.
   filename: File to download and save.

  Returns:
    String path where the downloaded file needs to be saved.

  Note:
    If the `./downloads/` folder doesn't exists, it creates one and
    proceeds further with it.
  """
  if not os.path.isdir(os.path.join(downloads, bucket_name)):
    os.makedirs(os.path.join(downloads, bucket_name))
  return os.path.join(os.path.join(downloads, bucket_name), filename)
