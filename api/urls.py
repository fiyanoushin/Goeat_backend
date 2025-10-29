from django.urls import path
from .views import (
    RegisterView, LoginView, UserListView, BlockUnblockUserView,
    CategoryListCreateView, ProductListCreateView, ProductDetailView,
    CartView, WishlistView, CreateOrderView, OrderListView, VerifyPaymentView,
    CartItemDetailView, AdminStatsView, AdminUserListView, AdminProductView,
    AdminOrderListView, AdminOrderStatusUpdateView,AdminOrderDetailView
)

urlpatterns = [
   
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),

 
    path('users/', UserListView.as_view()),
    path('users/<int:pk>/block/', BlockUnblockUserView.as_view()),

  
    path('categories/', CategoryListCreateView.as_view()),

   
    path('products/', ProductListCreateView.as_view()),
    path('products/<int:pk>/', ProductDetailView.as_view()),

   
    path('cart/', CartView.as_view()),
    path('cart/<int:pk>/', CartItemDetailView.as_view(), name='cart-item-detail'),
    path('wishlist/', WishlistView.as_view()),

 
    path('orders/create/', CreateOrderView.as_view()),
    path('orders/', OrderListView.as_view()),
    path('orders/verify-payment/', VerifyPaymentView.as_view()),

    path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/<int:pk>/block/', BlockUnblockUserView.as_view(), name='block-user'),
    path('admin/products/<int:pk>/', AdminProductView.as_view(), name='admin-product'),
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-orders'),
    path('admin/orders/<int:pk>/status/', AdminOrderStatusUpdateView.as_view(), name='admin-order-status'),
    path('admin/orders/<int:pk>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),

]
