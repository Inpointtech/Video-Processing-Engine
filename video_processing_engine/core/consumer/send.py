import pika
from datetime import datetime
# connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# channel = connection.channel()

# channel.queue_declare(queue='hello')

# channel.basic_publish(exchange='',
#                       routing_key='hello',
#                       body='Hello World!')
# print(" [x] Sent 'Hello World!'")
# connection.close()


def pika_connect():
    credentials = pika.PlainCredentials('rajtest', 'asdfgh')
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='192.168.0.103', credentials=credentials, virtual_host='testvm'))
    channel = connection.channel()
    channel.queue_declare(queue='test-vpe')
    return channel


channel = pika_connect()


def loopMsgToRBMQ(iter: int):
    global channel
    try:
        for x in range(iter):
            msg = "test iter : %s time is %s" % (x, datetime.now())
            print(x, ">>>>", msg)
            channel.basic_publish(exchange='',
                                  routing_key='test-vpe',
                                  body=msg)
    except Exception as e:
        channel = pika_connect()
