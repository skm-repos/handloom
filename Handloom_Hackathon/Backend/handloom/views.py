from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from .models import User, Product, Group, Message, Order
from .serializers import (
    UserSerializer, UserRegistrationSerializer, ProductSerializer,
    GroupSerializer, MessageSerializer, OrderSerializer
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User registered successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        try:
            user = User.objects.get(username=username)
            from django.contrib.auth.hashers import check_password
            if check_password(password, user.password):
                login(request, user)
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data
                })
        except User.DoesNotExist:
            pass
        
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_available=True)
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
    
    @action(detail=True, methods=['post'])
    def place_order(self, request, pk=None):
        product = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        shipping_address = request.data.get('shipping_address')
        
        if not shipping_address:
            return Response({'error': 'Shipping address is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if product.stock_quantity < quantity:
            return Response({'error': 'Insufficient stock'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        total_price = product.price * quantity
        
        order = Order.objects.create(
            customer=request.user,
            product=product,
            quantity=quantity,
            total_price=total_price,
            shipping_address=shipping_address
        )
        
        # Update stock
        product.stock_quantity -= quantity
        if product.stock_quantity == 0:
            product.is_available = False
        product.save()
        
        return Response({
            'message': 'Order placed successfully',
            'order': OrderSerializer(order).data
        }, status=status.HTTP_201_CREATED)

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        group = serializer.save(creator=self.request.user)
        group.members.add(self.request.user)
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        group = self.get_object()
        if request.user in group.members.all():
            return Response({'error': 'Already a member'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        group.members.add(request.user)
        return Response({'message': 'Joined group successfully'})
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        group = self.get_object()
        if request.user not in group.members.all():
            return Response({'error': 'Not a member'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        group.members.remove(request.user)
        return Response({'message': 'Left group successfully'})

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Message.objects.filter(
                Q(sender=user) | Q(receiver=user) | Q(group__members=user)
            ).order_by('-timestamp')
        else:
            # For unauthenticated access, return all messages
            return Message.objects.all().order_by('-timestamp')
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
    
    @action(detail=False, methods=['get'])
    def conversations(self, request):
        user = request.user
        # Get unique conversations (direct messages and group messages)
        conversations = []
        
        # Direct messages
        direct_messages = Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).exclude(group__isnull=False).order_by('-timestamp')
        
        # Group messages
        group_messages = Message.objects.filter(
            group__members=user
        ).order_by('-timestamp')
        
        return Response({
            'direct_messages': MessageSerializer(direct_messages, many=True).data,
            'group_messages': MessageSerializer(group_messages, many=True).data
        })

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.user_type in ['weaver', 'designer']:
                # Sellers can see orders for their products
                return Order.objects.filter(product__seller=user)
            else:
                # Customers can see their own orders
                return Order.objects.filter(customer=user)
        else:
            # For unauthenticated access, return all orders
            return Order.objects.all()
