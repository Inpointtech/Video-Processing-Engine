import pika
from datetime import datetime
import time

from video_processing_engine.core.turntable import spin


def pika_connect():
    # credentials = pika.PlainCredentials('rajtest', 'asdfgh')
    credentials = ''
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='192.168.0.103', credentials=credentials, virtual_host='testvm'))
    channel = connection.channel()
    channel.queue_declare(queue='test-vpe')
    return channel


channel = pika_connect()


def compute(msg):
    # t = datetime.now()
    # print("1 : ", t, "msg  : ", type(msg))
    # time.sleep(10)
    spin(msg)
    # 'rajtest', 'asdfgh'
    # print("2 : ", datetime.now())
    # print("consume time  : ", datetime.now()-t)


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    compute(body)


channel.basic_consume(
    queue='test-vpe', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')

def consume():
  global channel
  try:
    channel.start_consuming()
  except Exception as e:
    channel = pika_connect()
    consume()

consume()
