from django.shortcuts import render, redirect
from django.views import View
from django.db.models import OuterRef, Subquery, F, ExpressionWrapper, DecimalField, Case, When
from django.utils import timezone
from .models import Category, Product, Discount, Cart, WishList
from rest_framework import viewsets, response
from rest_framework.permissions import IsAuthenticated
from .serializers import CartSerializer, WishListSerializer
from django.shortcuts import get_object_or_404


class WishListViewSet(viewsets.ModelViewSet):
    queryset = WishList.objects.all()
    serializer_class = WishListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        wishlist_items = self.get_queryset().filter(product__id=request.data.get('product'))
        if wishlist_items:
            return response.Response({'message': 'Product is already in wishlist'}, status=200)
        else:
            product = get_object_or_404(Product, id=request.data.get('product'))
            wishlist_item = WishList(user=request.user, product=product)
            wishlist_item.save()
            return response.Response({'message': 'Product added to wishlist'}, status=201)

    def update(self, request, *args, **kwargs):
        wishlist_item = get_object_or_404(WishList, id=kwargs['pk'])
        if request.data.get('product'):
            product = get_object_or_404(Product, id=request.data['product'])
            wishlist_item.product = product
            wishlist_item.save()
            return response.Response({'message': 'Product change in wishlist'}, status=201)

    def destroy(self, request, *args, **kwargs):
        wishlist_item = self.get_queryset().get(id=kwargs['pk'])
        wishlist_item.delete()
        return response.Response({'message': 'Product delete from wishlist'}, status=201)


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        ## Можно записать так, для получения товара (проверка что он уже есть в корзине)
        # cart_items = Cart.objects.filter(user=request.user, product__id = request.data.get('product'))
        # Или можно так, так как мы переопределили метод get_queryset
        cart_items = self.get_queryset().filter(product__id=request.data.get('product'))
        # request API передаёт параметры по названиям полей в БД, поэтому ловим product
        if cart_items:  # Если продукт уже есть в корзине
            cart_item = cart_items[0]
            if request.data.get('quantity'):  # Если в запросе передан параметр quantity,
                # то добавляем значение к значению в БД
                cart_item.quantity += int(request.data.get('quantity'))
            else:  # Иначе просто добавляем значение по умолчению 1
                cart_item.quantity += 1
        else:  # Если продукта ещё нет в корзине
            product = get_object_or_404(Product, id=request.data.get('product'))
            # Получаем продукт и проверяем что он вообще существует, если его нет то выйдет ошибка 404
            if request.data.get('quantity'):  # Если передаём точное количество продукта, то передаём его
                cart_item = Cart(user=request.user, product=product, quantity=request.data.get('quantity'))
            else:  # Иначе создаём объект по умолчанию (quantity по умолчанию = 1, так прописали в моделях)
                cart_item = Cart(user=request.user, product=product)
        cart_item.save()  # Сохранили объект в БД
        return response.Response({'message': 'Product added to cart'}, status=201)  # Вернули ответ, что всё прошло успешно

    def update(self, request, *args, **kwargs):
        # Для удобства в kwargs передаётся id строки для изменения в БД, под параметром pk
        cart_item = get_object_or_404(Cart, id=kwargs['pk'])
        if request.data.get('quantity'):
            cart_item.quantity = request.data['quantity']
        if request.data.get('product'):
            product = get_object_or_404(Product, id=request.data['product'])
            cart_item.product = product
        cart_item.save()
        return response.Response({'message': 'Product change in cart'}, status=201)

    def destroy(self, request, *args, **kwargs):
        # В этот раз напишем примерно так как это делает фреймфорк самостоятельно
        cart_item = self.get_queryset().get(id=kwargs['pk'])
        cart_item.delete()
        return response.Response({'message': 'Product delete from cart'}, status=201)


class ShopView(View):
    def get(self, request, id=0):
        category_items = Category.objects.all()

        # Создание запроса на получения всех действующих не нулевых скидок
        discount_value = Case(When(discount__value__gte=0,
                                   discount__date_begin__lte=timezone.now(),
                                   discount__date_end__gte=timezone.now(),
                                   then=F('discount__value')),
                              default=0,
                              output_field=DecimalField(max_digits=10,
                                                        decimal_places=2)
                              )
        # Создание запроса на расчёт цены со скидкой
        price_with_discount = ExpressionWrapper(
            F('price') * (100.0 - F('discount_value')) / 100.0,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )

        if id:
            products = Product.objects.filter(category_id=id)
        else:
            products = Product.objects.all()

        products = products.annotate(
            discount_value=discount_value,
            # Другой способ через запрос в другую таблицу, однако
            # без фильтрации по времени действия скидки
            # discount_value=Subquery(Discount.objects.filter(product_id=OuterRef('id')).values('value')),
            price_before=F('price'),
            price_after=price_with_discount
        ).values('id', 'name', 'image', 'price_before', 'price_after', 'discount_value')

        return render(request, 'store/shop.html', context={'data': products, 'categories': category_items})


class WishListView(View):
    def get(self, request):
        if request.user.is_authenticated:
            # код который необходим для обработчика
            wishlist_items = WishList.objects.filter(user=request.user)
            return render(request, 'store/wishlist.html', context={'data': wishlist_items})
        # Иначе отправляет авторизироваться
        return redirect('login:login')  # from django.shortcuts import redirect


class CartView(View):
    def get(self, request):
        if request.user.is_authenticated:
            cart_data = Cart.objects.filter(user=request.user)
            cart_items = [{'user': item.user,
                           'quantity': item.quantity,
                           'product': item.product,
                           'total': item.product.price * item.quantity} for item in cart_data]
            return render(request, 'store/cart.html', context={'data': cart_items})
        return redirect('login:login')


class ProductSingleView(View):
    def get(self, request, id):
        data = Product.objects.get(id=id)
        return render(request, "store/product-single.html", context={'name': data.name,
                                                                     'description': data.description,
                                                                     'price': data.price,
                                                                     'rating': 5.0,
                                                                     'url': data.image.url})


def add_product(request, section, id, number=0):
    match section:
        case 'cart':
            tab = Cart
        case 'wishlist':
            tab = WishList
    add_prod = tab.objects.filter(user_id=request.user.id, product_id=id)
    if add_prod and section == 'cart':
        add_prod = add_prod[0]
        if number:
            add_prod.quantity += number
        else:
            add_prod.quantity += 1
        add_prod.save()
    if not add_prod:
        add_prod = tab()
        add_prod.user = request.user
        add_prod.product = Product.objects.get(id=id)
        if number and section == 'cart':
            add_prod.quantity = number
        add_prod.save()
    return redirect('store:shop')


def delete_product(request, section, id):
    match section:
        case 'cart':
            tab = Cart
        case 'wishlist':
            tab = WishList
    del_prod = tab.objects.filter(user_id=request.user.id, product_id=id)
    del_prod.delete()
    return redirect('store:' + section)
