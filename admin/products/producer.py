import pika
import json
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

params = pika.URLParameters('amqps://sskvkcet:icvRyBC3ePJd1DkZV39TbFcdj9YXRxiW@leopard.lmq.cloudamqp.com/sskvkcet')

def get_connection():
    while True:
        try:
            return pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}. Retrying in 5 seconds...")
            time.sleep(5)

connection = get_connection()
channel = connection.channel()

def publish(method: str, body: dict):
    global connection, channel
    try:
        properties = pika.BasicProperties(content_type=method)
        channel.basic_publish(exchange='', routing_key='main', body=json.dumps(body), properties=properties)
        logger.info(f"Published {method} event: {body}")
    except (pika.exceptions.StreamLostError, pika.exceptions.ConnectionClosed):
        logger.warning("RabbitMQ connection lost. Reconnecting...")
        connection = get_connection()
        channel = connection.channel()
        properties = pika.BasicProperties(content_type=method)
        channel.basic_publish(exchange='', routing_key='main', body=json.dumps(body), properties=properties)
        logger.info(f"Republished {method} event: {body}")