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


while True:
  consume(file=__file__)
