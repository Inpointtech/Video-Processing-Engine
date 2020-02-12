"""Utility for generating strings and filename."""

import os
from datetime import datetime
from typing import Optional, Union

from video_processing_engine.utils.hasher import (hash_26, hash_52, hash_2704,
                                                  hash_area, hash_country)


def hash_xy(unique_id: Union[int, str]) -> Optional[str]:
  """Return hashed string code for the double unique ids from aa - ZZ.

  The unique id is fetched from the database and should range from 
  0001 to 2704 values. The hashing is done purely on the ideology of
  python dictionaries.

  Args:
    unique_id: Integer or string value from database.

  Returns:
    Hashed string from hash_2704 dictionary.

  Notes:
    Values greater than 2704 will return None.
  """
  return hash_2704.get(int(unique_id), None)


def hash_x(unique_id: Union[int, str]) -> Optional[str]:
  """Return hashed string code for single unique id from a - Z.

  The unique id is fetched from the database and should range from 
  01 to 52 values. Similar to `hash_xy_id()`, the hashing is done purely
  on the ideology of python dictionaries.

  Args:
    unique_id: Integer or string value from database.

  Returns:
    Hashed string from hash_52 dictionary.

  Notes:
    Values greater than 52 will return None.
  """
  return hash_52.get(int(unique_id), None)


def hash_u(unique_id: Union[int, str]) -> Optional[str]:
  """Return hashed string code for single unique id from A - Z.

  The unique id is fetched from the database and should range from
  01 to 26 values. Similar to `hash_x()`, the hashing is done purely
  on thhash_xye ideology of python dictionaries.

  Args:
    unique_id: Integer or string value from database.

  Returns:
    Hashed string from hash_26 dictionary.

  Notes:
    Values greater than 26 will return None.
  """
  return hash_26.get(int(unique_id), None)


def hash_area_code(area: str) -> Optional[str]:
  """Return hashed string code.

  Args:
    area: Area to be hashed.

  Returns:
    Character representing the area.

  Notes:
    Refer documentation for the area code hashes.

  Raises:
    KeyError: If the key is not found.
    ValueError: If the value is not found.
  """
  try:
    return dict(map(reversed, hash_area.items()))[area]
  except (KeyError, ValueError):
    return None


def hash_country_code(country_code: str) -> str:
  """Return hashed country code."""
  return  hash_country.get(country_code, 'xx')


def hash_timestamp(now: Optional[datetime] = None) -> str:
  """Return converted timestamp.

  Generate 'hashed' timestamp for provided instance in 'MMDDYYHHmmSS'.

  Args:
    now: Current timestamp (default: None).

  Returns:
    Hashed timestamp in MMDDYYHHmmSS.
  """
  if now is None:
    now = datetime.now().replace(microsecond=0)
  return '{:0>2}{:0>2}{:0>2}{}{:0>2}{:0>2}'.format(str(now.month),
                                                   str(now.day),
                                                   str(now.year)[2:],
                                                   hash_u(now.hour),
                                                   str(now.minute),
                                                   str(now.second))


def bucket_name(country_code: str,
                customer_id: Union[int, str],
                contract_id: Union[int, str],
                order_id: Union[int, str],
                store_id: Union[int, str]) -> Optional[str]:
  """Generate an unique bucket name.

  The generated name represents the hierarchy of the stored video.

  Args:
    country_code: 2 letter country code (eg: India -> IN).
    customer_id: Customer Id from customer_id table from 0000 - 9999.
    contract_id: Contract Id from contract_id table from 00 - 99.
    order_id: Order Id from order_id table from 00 - 99.
    store_id: Store Id from store_id table from 000 - 999.

  Returns:
    Unique string name for S3 bucket.

  Raises:
    TypeError: If any positional arguments are skipped.
  """
  try:
    return '{}{:0>4}{:0>2}{:0>2}{:0>3}'.format(hash_country_code(country_code),
                                               int(customer_id),
                                               int(contract_id),
                                               int(order_id),
                                               int(store_id))
  except TypeError:
    return None

def order_name(area_code: str,
               camera_id: Union[int, str],
               timestamp: Optional[datetime] = None) -> Optional[str]:
  """Generate an unique order name.

  Generate an unique string based on order details.

  Args:
    area_code: Area code from area_id table (P -> Parking lot).
    camera_id: Camera Id from camera_id table from 00 - 99.
    timestamp: Current timestamp (default: None) for the file.

  Returns:
    Unique string based on the order details.

  Raises:
    TypeError: If any positional arguments are skipped.
  """
  return '{}{:0>2}{}'.format(hash_area_code(area_code),
                             int(camera_id), hash_timestamp())


def video_type(compress: Optional[bool] = False,
               trim: Optional[bool] = False,
               trim_compress: Optional[bool] = False) -> str:
  """Return type of the video.

  The returned value is generated by conditional checks.

  Args:
    compress: Boolean value (default: False) if video to be compress.
    trim: Boolean value (default: False) if video is to be trimmed.
    trim_compress: Boolean value (default: False) if trimmed video is
                   to be compressed.

  Returns:
    String for video type.
  """
  temp = ['a', 'a', 'a']

  if compress:
    temp[1] = 'c'
  if trim:
    temp[2] = 'n'
    if trim_compress:
      temp[2] = 'c'

  return ''.join(temp)


def filename(bucket: str, order: str, video_type: str) -> str:
  """Return filename without extension."""
  return f'{bucket}{order}{video_type}'
