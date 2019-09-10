from django.shortcuts import render
from django.http import JsonResponse
from .models import *
from django.views.decorators.csrf import csrf_exempt
from django.http import QueryDict
import json
import smtplib
from django.db import transaction


def home(request):
    try:
        reset_data()
        return render(request, "home.html", {"all_products": [product.id for product in Product.objects.all()]})
    except Exception as e:
        print(e)


def all_orders(request):
    return JsonResponse({"all_orders": [product.id for product in Order.objects.all()]})


def get_product(request):
    print("123", request.GET)
    return JsonResponse({"products": [product.to_json() for product in Product.objects.all()]})


def post_product(request):
    json_data = json.loads(request.body)
    qty, product_id, customer_id, vip = json_data['qty'], json_data['id'], json_data['customer_id'], json_data['vip']

    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product_id)
        if product.stock_pcs >= qty and ((not product.vip) or vip):
            product.stock_pcs -= qty
            order = Order()
            order.product = product
            order.qty = qty
            order.customer_id = customer_id
            product.save()
            order.save()
            return JsonResponse({"order_id": order.id, "stock_pcs": product.stock_pcs, "success": True})
        else:
            return JsonResponse({"success": False})


@csrf_exempt
def product_api(request):
    api_dict = {"GET": get_product, "POST": post_product}
    return api_dict[request.method](request)


def get_order(request):
    order_id = request.GET["order_id"]
    order = Order.objects.filter(id=order_id)[0]
    return JsonResponse(
        {"customer_id": order.customer_id, "order_id": order.id, "qty": order.qty, "price": order.product.price,
         "product_id": order.product.id, "shop_id": order.product.shop.name})


def delete_order(request):
    order_id = QueryDict(request.body)["order_id"]
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(id=order_id)
        if not order.exists():
            return JsonResponse({"success": False})
        product = Product.objects.select_for_update.get(id=order.product_id)
        order.delete()
        product.stock_pcs += order.qty
        product.save()
        return JsonResponse({"product_id": order.product.id, "stock_pcs": order.product.stock_pcs, "success": True})


@csrf_exempt
def order_api(request):
    api_dict = {"GET": get_order, "DELETE": delete_order}
    return api_dict[request.method](request)


def get_top3(request):
    result = {}
    for product in Product.objects.all():
        orders = Order.objects.filter(product_id=product.id)
        result[product.id] = sum(order.qty for order in orders)
    result = sorted(list(result.items()), key=lambda p: -p[1])[0:3]
    return JsonResponse(dict(result))
