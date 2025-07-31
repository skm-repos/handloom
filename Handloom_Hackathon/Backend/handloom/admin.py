from django.contrib import admin
from .models import User, Product, Group, Message, Order

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'user_type', 'date_joined']
    list_filter = ['user_type', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'price', 'category', 'stock_quantity', 'is_available']
    list_filter = ['category', 'is_available', 'created_at']
    search_fields = ['name', 'description', 'seller__username']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'member_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description', 'creator__username']
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'group', 'content_preview', 'timestamp', 'is_read']
    list_filter = ['is_read', 'timestamp']
    search_fields = ['content', 'sender__username', 'receiver__username']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'product', 'quantity', 'total_price', 'status', 'order_date']
    list_filter = ['status', 'order_date']
    search_fields = ['customer__username', 'product__name']
