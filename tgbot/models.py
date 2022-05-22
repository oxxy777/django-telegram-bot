from __future__ import annotations

from typing import Union, Optional, Tuple

from django.db import models
from django.db.models import QuerySet, Manager
from telegram import Update
from telegram.ext import CallbackContext

from tgbot.handlers.utils.info import extract_user_data_from_update
from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager


KlAD_CHOICES = [
    ('SNOW', 'Снежный прикоп'),
    ('MAGNET', 'Магнит'),
    ('HIDE', 'Тайник'),
    ('GROUND', 'Прикоп'),
    ('OTHER', 'Другой')
]


class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class City(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название города")

    def __str__(self):
        return f"{self.name}"


class User(CreateUpdateTracker):
    user_id = models.PositiveBigIntegerField(verbose_name="Телеграм id")
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    language_code = models.CharField(max_length=8, help_text="Telegram client's lang", **nb)
    deep_link = models.CharField(max_length=64, **nb)
    chat_id = models.IntegerField(verbose_name="id чата")

    is_blocked_bot = models.BooleanField(default=False)

    is_admin = models.BooleanField(default=False)

    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()

    city = models.ForeignKey(City, verbose_name="Город", on_delete=models.SET_NULL, null=True)
    balance = models.FloatField(default=0.00)  # BTC
    btc_address = models.CharField(max_length=34, verbose_name="Дочерний BTC адрес") # уникальный дочерний адрес нашего бтц кошелька
    wif = models.CharField(max_length=255, verbose_name="Wallet import format")
    transactions = models.IntegerField(default=0)

    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.user_id}'

    @classmethod
    def get_user_and_created(cls, update: Update, context: CallbackContext, chat_id) -> Tuple[User, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = extract_user_data_from_update(update, chat_id)
        u, created = cls.objects.update_or_create(user_id=data["user_id"], defaults=data)

        if created:
            # Save deep_link to User model
            if context is not None and context.args is not None and len(context.args) > 0:
                payload = context.args[0]
                if str(payload).strip() != str(data["user_id"]).strip():  # you can't invite yourself
                    u.deep_link = payload
                    u.save()

        return u, created

    @classmethod
    def get_user(cls, update: Update, context: CallbackContext) -> User:
        if update.message is not None:
            chat_id = update.message.chat.id
        elif update.callback_query is not None:
            chat_id = update.callback_query.message.chat.id
        else:
            chat_id = None
        u, _ = cls.get_user_and_created(update, context, chat_id)
        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(user_id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()

    @property
    def invited_users(self) -> QuerySet[User]:
        return User.objects.filter(deep_link=str(self.user_id), created_at__gt=self.created_at)

    @property
    def tg_str(self) -> str:
        if self.username:
            return f'@{self.username}'
        return f"{self.first_name} {self.last_name}" if self.last_name else f"{self.first_name}"


class Support(CreateUpdateTracker):
    user = models.ForeignKey(User, verbose_name="Репортер", on_delete=models.CASCADE)
    text = models.TextField()
    is_solved = models.BooleanField(default=False, verbose_name="Проблема решена")


class Courier(CreateUpdateTracker):
    telegram_id = models.PositiveBigIntegerField(unique=True, verbose_name="Telegram id курьера")
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="Город")

    def __str__(self):
        return f"{self.telegram_id}"


class District(models.Model):
    district_name = models.CharField(verbose_name="Название района", max_length=255)
    city = models.ForeignKey(City, verbose_name="Город в котором находится район", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.district_name}"


class Fasovka(models.Model):
    grams = models.FloatField(verbose_name="Фасовка в граммах", unique=True)
    def __str__(self):
        return f"{self.grams}"


class Product(models.Model):
    name = models.CharField(verbose_name="Название товара", max_length=255, unique=True)
    related_fasovka = models.ManyToManyField(Fasovka, related_name="related_products", blank=True, default=None, through="ProductToFasovka", verbose_name="Доступные фасовки")
    is_available = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"


class Zakladka(CreateUpdateTracker):
    courier = models.ForeignKey(Courier, verbose_name="Курьер", on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, verbose_name="Город", on_delete=models.CASCADE)
    district = models.ForeignKey(District, verbose_name="Район", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="Название товара", on_delete=models.CASCADE)
    fasovka = models.ForeignKey(Fasovka, verbose_name="Фасовка", on_delete=models.CASCADE)
    is_taken = models.BooleanField(default=False, verbose_name="Заказано")
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")
    description = models.TextField(verbose_name="Описание")
    image = models.ImageField(verbose_name="Изображение", upload_to="images")
    klad_type = models.CharField(max_length=6, choices=KlAD_CHOICES, default="GROUND", verbose_name="Тип клада")

    def __str__(self):
        return f"Закладка: {self.product} Фасовка: {self.fasovka} Товар: {self.product} Город: {self.city} Район: {self.district} Координаты: {self.latitude}/{self.longitude}, Тип клада: {self.klad_type}"


class ProductToFasovka(models.Model):
    fasovka = models.ForeignKey(Fasovka, on_delete=models.CASCADE, verbose_name="Фасовка")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    price = models.FloatField(null=True, blank=True, verbose_name="Цена в рублях") # рубли

    def __str__(self):
        return f"Продукт: {self.product}, Фасовка: {self.fasovka}, Цена: {self.price}"


class Order(CreateUpdateTracker):
    user = models.ForeignKey(User, verbose_name="Клиент", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="Товар")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, verbose_name="Город")
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, verbose_name="Район")
    fasovka = models.ForeignKey(Fasovka, on_delete=models.SET_NULL, null=True, verbose_name="Фасовка")
    zakladka = models.ForeignKey(Zakladka, verbose_name="Закладка", on_delete=models.CASCADE, null=True, blank=True)
    price = models.FloatField(verbose_name="Цена") # btc
    is_paid = models.BooleanField(verbose_name="Оплата прошла", default=False)
    klad_type = models.CharField(max_length=6, choices=KlAD_CHOICES, default="GROUND", verbose_name="Тип клада")

    def __str__(self):
        return f"ЗАКАЗ: Продукт: {self.product}, Фасовка: {self.fasovka}, Цена: {self.price}, Тип клада: {self.klad_type}"


class TempZakladkaForCourier(models.Model):
    courier = models.ForeignKey(Courier, verbose_name="Курьер", on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, verbose_name="Город", on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey(District, verbose_name="Район", on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, verbose_name="Название товара", on_delete=models.CASCADE, null=True, blank=True)
    fasovka = models.ForeignKey(Fasovka, verbose_name="Фасовка", on_delete=models.CASCADE, null=True, blank=True)
    latitude = models.FloatField(verbose_name="Широта", null=True, blank=True)
    longitude = models.FloatField(verbose_name="Долгота", null=True, blank=True)
    description = models.TextField(verbose_name="Описание", null=True, blank=True)
    image = models.ImageField(verbose_name="Изображение", upload_to="images", null=True, blank=True)
    klad_type = models.CharField(max_length=6, choices=KlAD_CHOICES, default="GROUND", verbose_name="Тип клада", null=True, blank=True)
