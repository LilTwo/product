from django.db import models
import pandas as pd


# Create your models here.
class Shop(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.id}, {self.name}"


class Product(models.Model):
    stock_pcs = models.IntegerField()
    price = models.IntegerField()
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    vip = models.BooleanField()

    def __str__(self):
        return f"{self.stock_pcs}, {self.price}, {self.shop}, {self.vip}"

    def to_json(self):
        result = {key: getattr(self, key) for key in vars(self) if key != "_state"}
        result['shop_id'] = self.shop.name
        return result


class Order(models.Model):
    qty = models.IntegerField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer_id = models.IntegerField()


def prepare_shop(df):
    shops = set(df['shop_id'])
    for shop in shops:
        shop_obj = Shop()
        shop_obj.name = shop
        shop_obj.save()


def prepare_Product(df):
    for product_id, product in df.iterrows():
        product_obj = Product()
        product_obj.id = product_id
        product_obj.stock_pcs = product['stock_pcs']
        product_obj.shop = Shop.objects.filter(name=product['shop_id'])[0]
        product_obj.vip = product['vip']
        product_obj.price = product['price']
        product_obj.save()


def reset_data():
    df = pd.read_csv("data.csv", index_col=0)
    Shop.objects.all().delete()
    Product.objects.all().delete()
    Order.objects.all().delete()

    prepare_shop(df)
    prepare_Product(df)
