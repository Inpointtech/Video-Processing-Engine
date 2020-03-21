import pika

from video_processing_engine.core.turntable import spin


def pika_connect():
  credentials = pika.PlainCredentials('test', 'inpoint20200318')
  connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='159.89.52.183',
                              credentials=credentials,
                              virtual_host='testvm'))
  channel = connection.channel()
  channel.queue_declare(queue='test-vpe')
  return channel


def compute(json_obj):
    spin(json_obj)


def callback(channel, method, properties, body):
  print("[x] Received %r" % body)
  compute(body)


channel = pika_connect()
channel.basic_consume(queue='test-vpe',
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
