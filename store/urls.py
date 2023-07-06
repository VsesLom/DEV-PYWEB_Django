from django.urls import path
from .views import ShopView, CartView, WishListView, ProductSingleView, CartViewSet, WishListViewSet, add_product, delete_product
from rest_framework import routers


cart_router = routers.DefaultRouter()
cart_router.register(r'cart', CartViewSet)

wish_router = routers.DefaultRouter()
wish_router.register(r'wishlist', WishListViewSet)

app_name = 'store'

urlpatterns = [
    path('', ShopView.as_view(), name='shop'),
    path('category/<int:id>/', ShopView.as_view(), name='category'),
    path('product/<int:id>/', ProductSingleView.as_view(), name='product'),
    path('cart/', CartView.as_view(), name='cart'),
    path('<str:section>/add/<int:id>/', add_product, name='add_cart'),
    path('<str:section>/delete/<int:id>/', delete_product, name='delete_cart'),
    path('wishlist/', WishListView.as_view(), name='wishlist'),
    path('<str:section>/add/<int:id>/', add_product, name='add_wishlist'),
    path('<str:section>/delete/<int:id>/', delete_product, name='delete_wishlist'),
]
