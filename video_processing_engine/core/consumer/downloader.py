import json
import os

import pika

from video_processing_engine.utils.access_update import (
    download_from_azure, download_from_google_drive, download_using_ftp)
from video_processing_engine.utils.aws import access_file_update
from video_processing_engine.utils.paths import downloads


def pika_connect():
    credentials = pika.PlainCredentials('', '')
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='', credentials=credentials, virtual_host=''))
    channel = connection.channel()
    channel.queue_declare(queue='')
    return channel


channel = pika_connect()


def compute(json_obj):
    json_data = json.loads(json_obj)
    original_file = 0
    if json_data.get('access_type', None) == 'GCP':
      _, original_file = download_from_google_drive(
          json_data.get('public_url', None),
          json_data.get('stored_filename', None))
    elif json_data.get('access_type', None) == 'Microsoft':
      _, original_file = download_from_azure(
          json_data.get('azure_account_name', None),
          json_data.get('azure_account_key', None),
          json_data.get('azure_container_name', None),
          json_data.get('azure_blob_name', None),
          json_data.get('stored_filename', None))
    elif json_data.get('access_type', None) == 'FTP':
      _, original_file = download_using_ftp(
          json_data.get('remote_username', None),
          json_data.get('remote_password', None),
          json_data.get('remote_public_address', None),
          json_data.get('remote_file', None),
          json_data.get('stored_filename', None))
    elif json_data.get('access_type', None) == 'S3':
      _, original_file = access_file_update(
          json_data.get('s3_access_key', None),
          json_data.get('s3_secret_key', None),
          json_data.get('s3_url', None),
          json_data.get('stored_filename', None),
          json_data.get('s3_bucket_name', None))
    elif json_data.get('access_type', None) == 'FTP TOOL':
      _, original_file = True, os.path.join(downloads,
                                            json_data.get('stored_filename', None))


def callback(ch, method, properties, body):
    print("[x] Received %r" % body)
    compute(body)


channel.basic_consume(queue='file-transfer-Q',
                      on_message_callback=callback,
                      auto_ack=True)

print('[*] Waiting for messages. To exit press CTRL+C')


def consume():
  global channel
  try:
    channel.start_consuming()
  except Exception as e:
    channel = pika_connect()
    consume()


consume()
