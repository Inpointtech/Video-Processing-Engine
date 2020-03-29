"""A subservice for running Video processing engine."""

import pika

from video_processing_engine.core.turntable import spin
from video_processing_engine.utils.logs import log as _log


def pika_connect(**kwargs):
  credentials = pika.PlainCredentials('test', 'inpoint20200318')
  connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='159.89.52.183',
                              credentials=credentials,
                              virtual_host='testvm'))
  channel = connection.channel()
  channel.queue_declare(queue='test-vpe')
  return channel


def compute(json_obj, **kwargs):
  spin(json_obj, **kwargs)


def callback(channel, method, properties, body, **kwargs):
  log = _log(**kwargs)
  log.info(f'Received: {body}')
  compute(body, **kwargs)


channel = pika_connect(file=__file__)
channel.basic_consume(queue='test-vpe',
                      on_message_callback=callback,
                      auto_ack=True)


def consume(**kwargs):
  log = _log(**kwargs)
  global channel
  try:
    log.info('Video processing engine consumer started.')
    channel.start_consuming()
  except Exception:
    log.warning('Video processing engine consumer stopped after processing '
                'time consuming order.')
    channel = pika_connect(**kwargs)
    log.info('Video processing engine consumer restarted.')
    consume(**kwargs)
  except KeyboardInterrupt:
    log.error('Video processing engine consumer interrupted.')
    exit(0)


# while True:
#   consume(file=__file__)

json_obj = {"country_code": "in",
            "customer_id": "0555",
            "contract_id": "44",
            "order_id": "33",
            "store_id": "221",
            "camera_id": "1",
            "area_code": "x",
            "use_stored": False,
            "access_mode": "s3",
            "public_url": "",
            "azure_account_name": "",
            "azure_account_key": "",
            "azure_container_name": "",
            "azure_blob_name": "60 Minute Timer.mp4",
            "remote_username": False,
            "remote_password": False,
            "remote_public_address": False,
            "remote_file": False,
            "s3_access_key": "",
            "s3_secret_key": "",
            "s3_url": "",
            "teamviewer_file": "test.mp4",
            "s3_bucket_name": False,
            "start_time": "17:50:00",
            "end_time": "17:50:30",
            "camera_address": "203.192.197.184",
            "camera_port": "9002",
            "camera_username": "admin",
            "camera_password": "user@1234",
            "timestamp_format": False,
            "select_sample": True,
            "sampling_rate": "5",
            "perform_compression": True,
            "perform_trimming": True,
            "trim_compressed": True,
            "trim_type": "trim_by_factor",
            "compression_ratio": "60",
            "number_of_clips": "24",
            "equal_distribution": True,
            "clip_length": 30,
            "trim_factor": "s",
            "last_clip": False,
            "sample_start_time": "17:40:00",
            "sample_end_time": "17:45:00",
            }

import json

json_obj = json.dumps(json_obj)

compute(json_obj, file=__file__)
