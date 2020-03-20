import pika

from video_processing_engine.core.turntable import spin


def pika_connect():
    credentials = pika.PlainCredentials('', '')
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='', credentials=credentials, virtual_host=''))
    channel = connection.channel()
    channel.queue_declare(queue='')
    return channel


channel = pika_connect()


def compute(msg):
    spin(msg)


def callback(ch, method, properties, body):
    print("[x] Received %r" % body)
    compute(body)


channel.basic_consume(
    queue='test-vpe', on_message_callback=callback, auto_ack=True)

print('[*] Waiting for messages. To exit press CTRL+C')

def consume():
  global channel
  try:
    channel.start_consuming()
  except Exception as e:
    channel = pika_connect()
    consume()

consume()
