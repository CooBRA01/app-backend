from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Product, User
from .serializers import ProductSerializer
from django.http import Http404
from .producer import publish
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ProductViewSet(viewsets.ViewSet):
    def list(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            image_path = str(product.image).split('/')[-1]
            publish('product_created', {'id': product.id, 'title': product.title, 'image': f'products/{image_path}'})
            logger.info(f"Created product {product.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Product creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product)
            return Response(serializer.data)
        except Product.DoesNotExist:
            raise Http404

    def update(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product, data=request.data, partial=True)  # Partial for optional image
            if serializer.is_valid():
                serializer.save()
                image_path = str(product.image).split('/')[-1]
                publish('product_updated', {'id': product.id, 'title': product.title, 'image': f'products/{image_path}'})
                logger.info(f"Updated product {product.id}")
                return Response(serializer.data)
            logger.error(f"Product update failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            raise Http404

    def destroy(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
            product.delete()
            publish('product_deleted', {'id': int(pk)})
            logger.info(f"Deleted product {pk}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            raise Http404

class UserAPIView(APIView):
    def get(self, request):
        try:
            users = User.objects.all()
            return Response({'id': users[0].id if users.exists() else 1})
        except Exception as e:
            logger.error(f"Error in UserAPIView: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)