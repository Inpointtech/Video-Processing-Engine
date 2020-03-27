import pika

from video_processing_engine.core.turntable import spin
from video_processing_engine.utils.logs import log

log = log(__file__)


def pika_connect():
  credentials = pika.PlainCredentials('test', 'inpoint20200318')
  connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='159.89.52.183',
                              credentials=credentials,
                              virtual_host='testvm'))
  channel = connection.channel()
  channel.queue_declare(queue='test-vpe')
  log.info('Pika connection established.')
  return channel


def compute(json_obj):
  spin(json_obj)


def callback(channel, method, properties, body):
  log.info(f'Received: {body}')
  compute(body)


channel = pika_connect()
channel.basic_consume(queue='test-vpe',
                      on_message_callback=callback,
                      auto_ack=True)


def consume():
  global channel
  try:
    channel.start_consuming()
  except Exception:
    log.warning('Video processing engine consumer stopped after processing '
                'time consuming order.')
    channel = pika_connect()
    log.info('Video processing engine consumer restarted.')
    consume()


while True:
  consume()
