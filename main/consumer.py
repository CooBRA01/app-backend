import pika
import json
import time
from main import app, Product, db
import os


params = pika.URLParameters(os.getenv('RABBITMQ_URL'))

def callback(ch, method, properties, body):
    with app.app_context():
        data = json.loads(body)
        print(f"Received {properties.content_type} event: {data}")
        try:
            if properties.content_type == 'product_created':
                product = Product(id=data['id'], title=data['title'], image=data['image'])
                db.session.add(product)
                db.session.commit()
            elif properties.content_type == 'product_updated':
                product = Product.query.get(data['id'])
                if product:
                    product.title = data['title']
                    product.image = data['image']
                    db.session.commit()
            elif properties.content_type == 'product_deleted':
                product = Product.query.get(data)
                if product:
                    db.session.delete(product)
                    db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error processing message: {e}")

def consume():
    while True:
        try:
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue='main')
            channel.basic_consume(queue='main', on_message_callback=callback, auto_ack=True)
            print('Started Consuming')
            channel.start_consuming()
        except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelError) as e:
            print(f"Connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    consume()