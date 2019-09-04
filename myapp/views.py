from django.shortcuts import render
from django.http import JsonResponse
from .models import *
from django.views.decorators.csrf import csrf_exempt
from django.http import QueryDict
import json
import smtplib


def home(request):
    try:
        reset_data()
        return render(request, "home.html", {"all_products": [product.id for product in Product.objects.all()]})
    except Exception as e:
        print(e)


def all_orders(request):
    return JsonResponse({"all_orders": [product.id for product in Order.objects.all()]})


def get_product(request):
    return JsonResponse({"products": [product.to_json() for product in Product.objects.all()]})


def post_product(request):
    qty, product_id, customer_id, vip = request.POST['qty'], request.POST['id'], request.POST["customer_id"], \
                                        json.loads(request.POST["vip"])
    qty = int(qty)
    product = Product.objects.filter(id=product_id)[0]

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
    try:
        order = Order.objects.filter(id=order_id)[0]
        order.delete()
        order.product.stock_pcs += order.qty
        order.product.save()
        return JsonResponse({"product_id": order.product.id, "stock_pcs": order.product.stock_pcs, "success": True})
    except:
        return JsonResponse({"success": False})


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


def send_status(request):
    gmail_user = 'sender mail'
    gmail_password = 'sender password'

    sent_from = gmail_user
    to = request.GET["email"]
    subject = 'order status'
    body = ''
    for shop in Shop.objects.all():
        products = Product.objects.filter(shop_id=shop.id)
        orders = sum([list(Order.objects.filter(product_id=product.id)) for product in products],[])
        if not orders:
            body += f"shop {shop.name}, no orders\n"
        else:
            body += f"shop {shop.name}, {len(orders)} orders, total money: {sum(order.qty*order.product.price for order in orders)}, total qty: {sum(order.qty for order in orders)}\n"
    email_text = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (sent_from, to, subject, body)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        print("sent")
        return JsonResponse({"success":True})
    except Exception as e:
        print(e)
        return JsonResponse({"success":False})
