"""A subservice for processing video processing engine."""

import pika

from video_processing_engine.core.turntable import spin
from video_processing_engine.utils.logs import log as _log

log = _log(__file__)


def pika_connect():
  credentials = pika.PlainCredentials('test', 'inpoint20200318')
  connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='159.89.52.183',
                              credentials=credentials,
                              virtual_host='testvm'))
  channel = connection.channel()
  channel.queue_declare(queue='local_test-vpe')
  return channel


def compute(json_obj):
  spin(json_obj, log)


def callback(channel, method, properties, body):
  log.info(f'Received: {body}')
  compute(body)


channel = pika_connect()
channel.basic_consume(queue='local_test-vpe',
                      on_message_callback=callback,
                      auto_ack=True)


def consume():
  global channel
  try:
    log.info('Video processing engine consumer started processing this order.')
    channel.start_consuming()
  except Exception:
    log.warning('Video processing engine consumer stopped after processing '
                'time consuming order.')
    channel = pika_connect()
    log.info('Video processing engine consumer restarted.')
    consume()
  except KeyboardInterrupt:
    log.error('Video processing engine consumer interrupted.')
    exit(0)


consume()
