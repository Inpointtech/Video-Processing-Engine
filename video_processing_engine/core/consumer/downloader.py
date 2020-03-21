import json
import os

import pika

from video_processing_engine.utils.access_update import (
    download_from_azure, download_from_google_drive, download_using_ftp)
from video_processing_engine.utils.aws import access_file_update
from video_processing_engine.utils.paths import downloads


def pika_connect():
  credentials = pika.PlainCredentials('test', 'inpoint20200318')
  connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='159.89.52.183',
                              credentials=credentials,
                              virtual_host='testvm'))
  channel = connection.channel()
  channel.queue_declare(queue='file-transfer-Q')
  return channel


def compute(json_obj):
    json_data = json.loads(json_obj)
    if json_data.get('access_type', None) == 'GCP':
      download_from_google_drive(json_data.get('g_url', None),
                                 json_data.get('stored_filename', None))
    elif json_data.get('access_type', None) == 'Microsoft':
      download_from_azure(json_data.get('azure_account_name', None),
                          json_data.get('azure_account_key', None),
                          json_data.get('azure_container_name', None),
                          json_data.get('azure_blob_name', None),
                          json_data.get('stored_filename', None))
    elif json_data.get('access_type', None) == 'FTP':
      download_using_ftp(json_data.get('remote_username', None),
                         json_data.get('remote_password', None),
                         json_data.get('remote_public_address', None),
                         json_data.get('remote_file', None),
                         json_data.get('stored_filename', None))
    elif json_data.get('access_type', None) == 'S3':
      access_file_update(json_data.get('s3_access_key', None),
                         json_data.get('s3_secret_key', None),
                         json_data.get('s3_url', None),
                         json_data.get('stored_filename', None),
                         json_data.get('s3_bucket_name', None))
    elif json_data.get('access_type', None) == 'FTP TOOL':
      os.path.join(downloads, json_data.get('stored_filename', None))


def callback(channel, method, properties, body):
  print("[x] Received %r" % body)
  compute(body)


channel = pika_connect()
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
