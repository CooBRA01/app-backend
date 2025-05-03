import os
import django
import pika
import json
from django.db import transaction
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')
django.setup()

from products.models import Product


params = pika.URLParameters(os.getenv('RABBITMQ_URL'))

def get_connection():
    while True:
        try:
            return pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logger.info(f"Received {properties.content_type} event: {data}")
        with transaction.atomic():
            if properties.content_type == 'product_created':
                Product.objects.create(id=data['id'], title=data['title'], image=data['image'])
                logger.info("Product created in DB")
            elif properties.content_type == 'product_updated':
                product = Product.objects.get(id=data['id'])
                product.title = data['title']
                product.image = data['image']
                product.save()
                logger.info("Product updated in DB")
            elif properties.content_type == 'product_deleted':
                Product.objects.filter(id=data['id']).delete()
                logger.info("Product deleted from DB")
            elif properties.content_type == 'product_liked':
                product = Product.objects.get(id=data['id'])
                product.likes += 1
                product.save()
                logger.info(f"Updated likes for product {product.id}: {product.likes}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def consume():
    while True:
        try:
            connection = get_connection()
            channel = connection.channel()
            channel.queue_declare(queue='main')
            channel.basic_consume(queue='main', on_message_callback=callback, auto_ack=True)
            logger.info('Started Consuming')
            channel.start_consuming()
        except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelError) as e:
            logger.error(f"Connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    consume()