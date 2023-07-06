from django.contrib import admin
from .models import Category, Product, Discount, Cart, WishList

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Discount)
admin.site.register(Cart)
admin.site.register(WishList)

