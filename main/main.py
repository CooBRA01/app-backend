from flask import Flask, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dataclasses import dataclass
import requests
import pika
import json
from sqlalchemy.exc import IntegrityError
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql://django_user:password123@db:3306/main'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
CORS(app)

db = SQLAlchemy(app)

params = pika.URLParameters('amqps://sskvkcet:icvRyBC3ePJd1DkZV39TbFcdj9YXRxiW@leopard.lmq.cloudamqp.com/sskvkcet')

def get_connection():
    while True:
        try:
            connection = pika.BlockingConnection(params)
            return connection
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

@dataclass
class Product(db.Model):
    id: int
    title: str
    image: str
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(200))
    image = db.Column(db.String(200))

@dataclass
class ProductUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='user_product_unique'),)

@app.route('/api/products')
def index():
    try:
        products = Product.query.all()
        return jsonify([{'id': p.id, 'title': p.title, 'image': p.image} for p in products])
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        abort(500, f"Failed to fetch products: {str(e)}")

@app.route('/api/products/<int:id>/like', methods=['POST'])
def like(id: int):
    try:
        logger.info(f"Processing like for product {id}")
        req = requests.get('http://host.docker.internal:8000/api/user', timeout=5)
        req.raise_for_status()
        json_data = req.json()
        logger.debug(f"Received user data: {json_data}")

        if 'error' in json_data:
            logger.warning(f"User API error: {json_data['error']}")
            abort(400, json_data['error'])

        user_id = json_data.get('id')
        if not user_id:
            logger.warning("No user ID in response")
            abort(400, 'Invalid user data: user ID not found')

        existing_like = ProductUser.query.filter_by(user_id=user_id, product_id=id).first()
        if existing_like:
            logger.info(f"User {user_id} already liked product {id}")
            return jsonify({'message': 'You already liked this product'}), 400

        product_user = ProductUser(user_id=user_id, product_id=id)
        db.session.add(product_user)
        try:
            db.session.commit()
            logger.info(f"Added like from user {user_id} to product {id}")
        except IntegrityError:
            db.session.rollback()
            logger.info(f"Duplicate like attempt by user {user_id} for product {id}")
            return jsonify({'message': 'You already liked this product'}), 400

        publish('product_liked', {'id': id})
        return jsonify({'message': 'Liked!'}), 200  # Match frontend expectation

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch user data: {e}")
        abort(500, f'Failed to fetch user data: {str(e)}')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in like endpoint: {e}")
        abort(500, f'An error occurred: {str(e)}')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')