from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model,authenticate
from django.contrib.auth.hashers import check_password
import razorpay

from .models import User, Product, Category, Cart, Wishlist, Order, OrderItem
from .serializers import (
    UserSerializer, ProductSerializer, CategorySerializer,
    CartSerializer, WishlistSerializer, OrderSerializer, OrderItemSerializer
)
from .permissions import IsAdmin

User = get_user_model()


client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))



def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }



class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

           
            send_mail(
                subject="🎉 Welcome to Goeat!",
                message=f"Hi {user.name},\n\nThank you for registering with Goeat. Enjoy your desserts! 🍰",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            send_mail(
                subject="📢 New User Registered",
                message=f"New user registered:\n\nName: {user.name}\nEmail: {user.email}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["fathimafiyanoushin@gmail.com"],
                fail_silently=False,
            )

            return Response(
                {"message": "User registered successfully. Verification email sent.", "user": UserSerializer(user).data},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=401)

       
        if not check_password(password, user.password):
            return Response({"error": "Invalid credentials"}, status=401)

        token = get_tokens_for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "token": token
        }, status=200)


class UserListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        users = User.objects.filter(role='user')
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)


class BlockUnblockUserView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        user = get_object_or_404(User, id=pk)
        user.is_active = not user.is_active
        user.save()
        return Response({'message': f'User {"unblocked" if user.is_active else "blocked"} successfully.'})



class CategoryListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Access denied'}, 403)
        serializer = CategorySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, 201)
        return Response(serializer.errors, 400)



class ProductListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        category = request.GET.get('category')
        products = Product.objects.filter(category__name=category, active=True) if category else Product.objects.filter(active=True)
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Access denied'}, 403)
        serializer = ProductSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, 201)
        return Response(serializer.errors, 400)


class ProductDetailView(APIView):
    def get(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        serializer = ProductSerializer(product, context={'request': request})
        return Response(serializer.data)



class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart_items, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        product_id = request.data.get('product')
        quantity = int(request.data.get('quantity', 1))

        if not product_id:
            return Response({"error": "Product ID required"}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product_id=product_id,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartSerializer(cart_item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        cart_item = get_object_or_404(Cart, id=pk, user=request.user)
        quantity = request.data.get("quantity")
        if quantity is not None:
            cart_item.quantity = quantity
            cart_item.save()
            serializer = CartSerializer(cart_item, context={'request': request})
            return Response(serializer.data)
        return Response({"error": "Quantity not provided"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        cart_item = get_object_or_404(Cart, id=pk, user=request.user)
        cart_item.delete()
        return Response({"message": "Item removed from cart"}, status=status.HTTP_200_OK)



class WishlistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wishlist = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(wishlist, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        product_id = request.data.get('product')
        if not product_id:
            return Response({"error": "Product ID required"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created:
            wishlist_item.delete()
            return Response({"message": "Item removed from wishlist"})
        return Response({"message": "Item added to wishlist"}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        product_id = request.data.get('product')
        if not product_id:
            return Response({"error": "Product ID required"}, status=status.HTTP_400_BAD_REQUEST)
        Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
        return Response({"message": "Item removed from wishlist"})



class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            items = request.data.get('items')
            total = request.data.get('total')

            if not items or not total:
                return Response({"error": "Items and total required"}, status=400)

            total = float(total)
            order = Order.objects.create(user=request.user, total=total, status="pending")

            for item in items:
                product = get_object_or_404(Product, id=item['product'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.get('quantity', 1),
                    price=product.price
                )

            razorpay_order = client.order.create({
                "amount": int(total * 100),
                "currency": "INR",
                "payment_capture": 1
            })

            order.razorpay_order_id = razorpay_order['id']
            order.save()

            return Response({
                "order_id": order.id,
                "razorpay_order_id": razorpay_order['id'],
                "amount": razorpay_order['amount'],
                "currency": razorpay_order['currency']
            }, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": data.get('razorpay_order_id'),
                "razorpay_payment_id": data.get('razorpay_payment_id'),
                "razorpay_signature": data.get('razorpay_signature'),
            })

            order = Order.objects.get(id=data.get('order_id'))
            order.status = "completed"
            order.razorpay_payment_id = data.get('razorpay_payment_id')
            order.save()

            return Response({"message": "Payment verified successfully"})

        except razorpay.errors.SignatureVerificationError:
            return Response({"error": "Invalid signature"}, status=400)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class OrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.all() if request.user.role == 'admin' else Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)


class AdminStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        total_users = User.objects.filter(role='user').count()
        total_products = Product.objects.count()
        total_orders = Order.objects.count()
        total_revenue = Order.objects.filter(status='completed').aggregate(total=Sum('total'))['total'] or 0
        return Response({
            'total_users': total_users,
            'total_products': total_products,
            'total_orders': total_orders,
            'total_revenue': total_revenue
        })


class AdminUserListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        users = User.objects.filter(role='user')
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)


class AdminProductView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def put(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        serializer = ProductSerializer(product, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        product.delete()
        return Response({'message': 'Product deleted successfully'})


class AdminOrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        orders = Order.objects.all().order_by('-created_at')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)


class AdminOrderStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        new_status = request.data.get('status')
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=400)
        order.status = new_status
        order.save()
        return Response(OrderSerializer(order, context={'request': request}).data)

class AdminOrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def delete(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        order.delete()
        return Response({'message': 'Order deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
