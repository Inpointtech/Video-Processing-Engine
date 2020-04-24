"""A subservice for downloading files."""

import json
import os
import time
from datetime import datetime
from typing import Union

import pika

from video_processing_engine.utils.boto_wrap import access_file_update
from video_processing_engine.utils.common import now
from video_processing_engine.utils.common import seconds_to_datetime as s2d
from video_processing_engine.utils.fetch import (download_from_azure,
                                                 download_from_google_drive,
                                                 download_using_ftp)
from video_processing_engine.utils.logs import log as _log
from video_processing_engine.utils.paths import downloads

log = _log(__file__)


def pika_connect():
  credentials = pika.PlainCredentials('test', 'inpoint20200318')
  connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='159.89.52.183',
                              credentials=credentials,
                              virtual_host='testvm'))
  channel = connection.channel()
  channel.queue_declare(queue='uat_file-transfer-Q')
  return channel


def compute(json_obj: Union[bytes, str]):
  json_data = json.loads(json_obj)
  scheduled = json_data.get('schedule_download', False)
  if scheduled:
    scheduled_time = f'{json_data["start_date"]} {json_data["start_time"]}'
    sleep_interval = datetime.strptime(scheduled_time,
                                       '%Y-%m-%d %H:%M') - now()
    if sleep_interval.seconds <= 0:
      log.error('Scheduled time has passed already.')
      return None
    log.info('Video is scheduled for downloading, the process will suspend '
             f'for {s2d(int(sleep_interval.seconds))}.')
    time.sleep(1.0 + sleep_interval.seconds)
  log.info('Initiate video download.')
  if json_data.get('access_type', None) == 'GCP':
    log.info('Download file via Google Drive.')
    download_from_google_drive(json_data.get('g_url', None),
                                json_data.get('stored_filename', None), log)
  elif json_data.get('access_type', None) == 'Microsoft':
    log.info('Download file via Microsoft Azure.')
    download_from_azure(json_data.get('azure_account_name', None),
                        json_data.get('azure_account_key', None),
                        json_data.get('azure_container_name', None),
                        json_data.get('azure_blob_name', None),
                        json_data.get('stored_filename', None), log)
  elif json_data.get('access_type', None) == 'FTP':
    log.info('Transfer file via FTP.')
    download_using_ftp(json_data.get('remote_username', None),
                        json_data.get('remote_password', None),
                        json_data.get('remote_public_address', None),
                        json_data.get('remote_file', None),
                        json_data.get('stored_filename', None), log)
  elif json_data.get('access_type', None) == 'S3':
    log.info('Download file via Amazon S3 storage.')
    access_file_update(json_data.get('s3_access_key', None),
                        json_data.get('s3_secret_key', None),
                        json_data.get('s3_url', None),
                        json_data.get('stored_filename', None), log,
                        json_data.get('s3_bucket_name', None))
  elif json_data.get('access_type', None) == 'FTP TOOL':
    log.info('Transfer file via TeamViewer (FTP Tool).')
    os.path.join(downloads, json_data.get('stored_filename', None))


def callback(channel, method, properties, body):
  log.info(f'Received: {body}')
  compute(body)


channel = pika_connect()
channel.basic_consume(queue='uat_file-transfer-Q',
                      on_message_callback=callback,
                      auto_ack=True)


def consume():
  global channel
  try:
    log.info('Downloader consumer started.')
    channel.start_consuming()
  except Exception:
    raise Exception
    log.warning('Downloader consumer stopped after downloading huge file.')
    channel = pika_connect()
    log.info('Downloader consumer restarted.')
    consume()
  except KeyboardInterrupt:
    log.error('Downloader consumer interrupted.')
    exit(0)


consume()
