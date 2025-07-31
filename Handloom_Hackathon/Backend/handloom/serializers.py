from rest_framework import serializers
from .models import User, Product, Group, Message, Order

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type', 
                 'phone', 'address', 'profile_picture', 'bio', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 
                 'last_name', 'user_type', 'phone', 'address']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        # Hash the password manually since we're not using AbstractUser
        from django.contrib.auth.hashers import make_password
        validated_data['password'] = make_password(validated_data['password'])
        user = User.objects.create(**validated_data)
        return user

class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.ReadOnlyField(source='seller.username')
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 'seller', 
                 'seller_name', 'image', 'stock_quantity', 'is_available', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class GroupSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source='creator.username')
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'creator', 'creator_name', 
                 'members', 'member_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.members.count()

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.username')
    receiver_name = serializers.ReadOnlyField(source='receiver.username')
    group_name = serializers.ReadOnlyField(source='group.name')
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_name', 'receiver', 'receiver_name', 
                 'group', 'group_name', 'content', 'timestamp', 'is_read']
        read_only_fields = ['id', 'timestamp']

class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.username')
    product_name = serializers.ReadOnlyField(source='product.name')
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_name', 'product', 'product_name', 
                 'quantity', 'total_price', 'status', 'shipping_address', 
                 'order_date', 'updated_at']
        read_only_fields = ['id', 'order_date', 'updated_at'] 