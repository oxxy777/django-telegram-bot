import os

import qrcode
from bipwallet.utils import *

from tgbot.handlers.onboarding.manage_data import START, FASOFKA, READY, DISTRICT, CHOSEN_PRODUCT_NAME, CHOSEN_DISTRICT, \
    KLAD_TYPE, CHOSEN_FASOVKA, DISTRICTC, FASOFKAC, CONFIRM_ZK, CITIESC
from tgbot.handlers.onboarding.static_text import welcome_message, order_description, buyed_order_text, account_text, \
    welcome_message_courier, couries_stat_text, zakladka_created
import requests
from tgbot.models import *
from tgbot.handlers.onboarding.keyboards import make_keyboard_for_start_command, menu_keyboard, \
    make_keyboard_for_account_command, make_keyboard_for_not_available, make_keyboard_for_available, \
    make_keyboard_for_bye_or_decline, make_keyboard_for_fasofka, make_keyboard_for_confirm, make_keyboard_for_districts, \
    make_keyboard_for_klad_type, make_keyboard_for_districts_c, make_keyboard_for_curier_menu, \
    make_keyboard_for_c_products, make_keyboard_for_fasofka_c, make_keyboard_for_klad_type_c, \
    make_keyboard_for_confirm_zk


def command_start(update: Update, context: CallbackContext) -> None:
    if update.message is not None:
        chat_id = update.message.chat.id
    elif update.callback_query is not None:
        chat_id = update.callback_query.message.chat.id
    else:
        chat_id = None
    u, _ = User.get_user_and_created(update, context, chat_id)
    if _is_user_courier(u):
        update.message.reply_text(text=welcome_message_courier,
                                  reply_markup=make_keyboard_for_curier_menu())
    else:
        u.btc_address, u.wif = _create_btc_address(u.id)
        u.save()
        update.message.reply_text(text=welcome_message,
                                  reply_markup=make_keyboard_for_start_command())


def _create_btc_address(index):
    seed = os.getenv("SEED_PHRASE")
    master_key = HDPrivateKey.master_key_from_mnemonic(seed)
    root_keys = HDKey.from_path(master_key, "m/44'/0'/0'/0")[-1].public_key.to_b58check()
    xpublic_key = root_keys
    address = Wallet.deserialize(xpublic_key, network='BTC').get_child(index, is_prime=False).to_address()
    rootkeys_wif = HDKey.from_path(master_key, f"m/44'/0'/0'/0/{index}")[-1]
    xprivatekey = rootkeys_wif.to_b58check()
    wif = Wallet.deserialize(xprivatekey, network='BTC').export_to_wif()

    return address, wif

def city_decision_handler(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if not _is_user_courier(u):
        broadcast_decision = update.callback_query.data
        u.city = City.objects.get(name=broadcast_decision.replace(START, ""))
        u.save()
        message_city = broadcast_decision.replace(START, "")
        context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=f"Вы выбрали город: {message_city}",
            )

        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text="Воспользуйтесь меню слева для покупки и других действий",
        )


def command_account(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update,context)
    if not _is_user_courier(u):
        orders = Order.objects.filter(user=u, is_paid=True).count()
        update.message.reply_text(text=account_text.format(city=u.city, balance=u.balance, orders=orders),
                                  reply_markup=make_keyboard_for_account_command())


def make_up_balance(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if not _is_user_courier(u):
        img = qrcode.make(u.btc_address)
        img.save(f"./qrs/qr_{u.id}.jpg")
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=f"Ваш адрес для пополнения: {u.btc_address}\nВаш баланс до пополнения: {u.balance}\nВы также можете оплатить используя QR код ниже",
        )
        context.bot.send_photo(
            chat_id=update.callback_query.message.chat_id,
            photo=open(f"./qrs/qr_{u.id}.jpg", 'rb')
        )
        os.remove(f"./qrs/qr_{u.id}.jpg")
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text="Платеж может обрабатываться до 30-40 минут. Как только платеж придет - вы получите сообщение от бота. В случае если баланс не пополнится в течении часа, пожалуйста, обратитесь в поддержку и укажите кошелек, с которого вы отправляли BTC."
        )


def command_support(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(text="Напишите ваше обращение к службе поддержки ниже. Начните обращение со слова HELP, иначе оно не будет рассмотрено")


def receive_support_message(update: Update, context: CallbackContext):
    text = update.message.text
    Support.objects.create(user=User.get_user(context=context, update=update).user_id, text=text)
    update.message.reply_text(
        text="Ваше сообщение принято в обработку, мы свяжемся с вами в личные сообщения телеграм",
    )


def command_city_change(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    if not _is_user_courier(u):
        update.message.reply_text(text="Выберите город",
                              reply_markup=make_keyboard_for_start_command())


def command_product_to_order(update: Update, context: CallbackContext) -> None:
    user = User.get_user(update, context)
    if not _is_user_courier(user):
        update.message.reply_text(text="Выберите товар",
                                  reply_markup=make_keyboard_for_not_available(user))


def command_product_ready(update: Update, context: CallbackContext) -> None:
    user = User.get_user(update, context)
    if not _is_user_courier(user):
        if not Zakladka.objects.filter(city=user.city, is_taken=False):
            update.message.reply_text(text='Увы у нас нет доступных товаров на данный момент, воспользуйтесь опцией "Товары под заказ"',
                                      reply_markup=make_keyboard_for_not_available(user))
        else:
            update.message.reply_text(text="Выберите товар",
                                      reply_markup=make_keyboard_for_available(user))


def product_chosen_handler_district(update: Update, context: CallbackContext):
    # записали товар в ордер
    user = User.get_user(update, context)
    if not _is_user_courier(user):
        product = update.callback_query.data.replace(READY, "")
        product = Product.objects.get(name=product)
        context.bot.send_message(chat_id=update.callback_query.message.chat_id, text="Выберите район",
                                  reply_markup=make_keyboard_for_districts(user=user, product=product))


def klad_type_handler(update: Update, context: CallbackContext):
    user = User.get_user(update, context)
    if not _is_user_courier(user):
        fasovka = update.callback_query.data.replace(FASOFKA, "")
        fasovka = fasovka.split(CHOSEN_PRODUCT_NAME)[0]
        fasovka = Fasovka.objects.get(grams=float(fasovka))
        product = update.callback_query.data.split(CHOSEN_PRODUCT_NAME)[1].split(CHOSEN_DISTRICT)[0]
        product = Product.objects.get(name=product)
        district = update.callback_query.data.split(CHOSEN_DISTRICT)[1]
        district = District.objects.get(district_name=district)
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=f"Вы выбрали {fasovka} фасовку",
        )
        context.bot.send_message(chat_id=update.callback_query.message.chat_id, text="Выберите тип клада",
                                 reply_markup=make_keyboard_for_klad_type(user=user, product=product, fasovka=fasovka, district=district))


def ready_decision_handler(update: Update, context: CallbackContext):
    user = User.get_user(update, context)
    if not _is_user_courier(user):
        klad_type = update.callback_query.data.replace(KLAD_TYPE, "")
        klad_type = klad_type.split(CHOSEN_PRODUCT_NAME)[0]
        product = update.callback_query.data.split(CHOSEN_PRODUCT_NAME)[1].split(CHOSEN_DISTRICT)[0]
        district = update.callback_query.data.split(CHOSEN_DISTRICT)[1].split(CHOSEN_FASOVKA)[0]
        fasovka = update.callback_query.data.split(CHOSEN_FASOVKA)[1]
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=f"Вы выбрали тип клада {klad_type}",
        )
        product = Product.objects.get(name=product)
        fasovka = Fasovka.objects.get(grams=float(fasovka))
        btc_price = float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCRUB").json()["price"])
        rub_price = ProductToFasovka.objects.get(product=product, fasovka=fasovka).price
        order_price = rub_price / btc_price
        rounded_order_price = round(order_price, 8)
        order = Order.objects.create(user=user, product=product, fasovka=fasovka, district=District.objects.get(district_name=district), price=rounded_order_price, city=user.city, klad_type=klad_type)
        context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=order_description.format(city_name=user.city.name,
                district_name=order.district.district_name,
                product_name=order.product.name,
                fasovka_name=str(order.fasovka.grams),
                price_name=str(order.price),
                rub_price_str=str(rub_price),
                klad_type=klad_type),
                reply_markup=make_keyboard_for_bye_or_decline()
            )


def buy_or_decline_handler(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if not _is_user_courier(u):
        broadcast_decision = update.callback_query.data
        order = Order.objects.filter(user=u).first()
        if broadcast_decision.endswith("Купить"):
            if u.balance >= order.price:
                u.balance -= order.price
                u.save()
                order.is_paid = True
                order.save()
                zakladka = Zakladka.objects.filter(city=order.city, district=order.district, product=order.product,
                                                   fasovka=order.fasovka, is_taken=False).first()
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Оплата прошла успешно!",
                )
                zakladka.is_taken = True
                zakladka.save()
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=buyed_order_text.format(
                        city_name=zakladka.city.name,
                        district_name=zakladka.district.district_name,
                        product_name=zakladka.product.name,
                        fasovka_name=str(zakladka.fasovka.grams),
                        price_name=str(order.price),
                        latitude=str(zakladka.latitude),
                        longitude=str(zakladka.longitude),
                        description=zakladka.description,
                        klad_type=zakladka.klad_type
                    ),
                )
                context.bot.send_photo(
                    chat_id=update.callback_query.message.chat_id,
                    photo=zakladka.image
                )
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Спасибо за заказ!",
                )
            else:
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="На вашем балансе не хватает средств. Вы можете пополнить баланс.",
                    reply_markup=make_keyboard_for_account_command()
                )
        else:
            context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text="Выберите товар",
                reply_markup=make_keyboard_for_available(user=u)
            )

def fasofka_handler(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if not _is_user_courier(u):
        broadcast_decision = update.callback_query.data
        district = broadcast_decision.replace(DISTRICT, "")
        district = district.split(CHOSEN_PRODUCT_NAME)[0]
        product_name = broadcast_decision.split(CHOSEN_PRODUCT_NAME)[1]
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=f"Вы выбрали {district} район",
        )
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text="Выберите фасовку",
            reply_markup=make_keyboard_for_fasofka(Product.objects.get(name=product_name), district=district)
        )


def courier_menu_handler(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if update.message.text == "Добавить товар":
        if _is_user_courier(u):
            update.message.reply_text(text="Название товара:",
                                      reply_markup=make_keyboard_for_c_products())
    elif update.message.text == "Статистика":
        if _is_user_courier(u):
            context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=_courier_statistic(u),
            )
    else:
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text="Неверная команда",
        )


def c_product_chosen_handler_district(update: Update, context: CallbackContext):
    user = User.get_user(update, context)
    product = update.callback_query.data.replace(READY, "")
    product = Product.objects.get(name=product)
    context.bot.send_message(chat_id=update.callback_query.message.chat_id, text="Район",
                                  reply_markup=make_keyboard_for_districts_c(user=user, product=product))


def c_fasofka_handler(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    broadcast_decision = update.callback_query.data
    district = broadcast_decision.replace(DISTRICTC, "")
    district = district.split(CHOSEN_PRODUCT_NAME)[0]
    product_name = broadcast_decision.split(CHOSEN_PRODUCT_NAME)[1]
    context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=f"Ты выбрал {district} район",
    )
    context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text="Выбери фасовку",
        reply_markup=make_keyboard_for_fasofka_c(Product.objects.get(name=product_name), district=district)
    )


def c_klad_type_handler(update: Update, context: CallbackContext):
    user = User.get_user(update, context)
    fasovka = update.callback_query.data.replace(FASOFKAC, "")
    fasovka = fasovka.split(CHOSEN_PRODUCT_NAME)[0]
    fasovka = Fasovka.objects.get(grams=float(fasovka))
    product = update.callback_query.data.split(CHOSEN_PRODUCT_NAME)[1].split(CHOSEN_DISTRICT)[0]
    product = Product.objects.get(name=product)
    district = update.callback_query.data.split(CHOSEN_DISTRICT)[1]
    district = District.objects.get(district_name=district)
    context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=f"Ты выбрал {fasovka} фасовку",
    )
    context.bot.send_message(chat_id=update.callback_query.message.chat_id, text="Выбери тип клада",
                                 reply_markup=make_keyboard_for_klad_type_c(user=user, product=product, fasovka=fasovka,
                                                                          district=district))


def received_klad_next_step_handler(update: Update, context: CallbackContext):
    user = User.get_user(update, context)
    klad_type = update.callback_query.data.replace(KLAD_TYPE, "")
    klad_type = klad_type.split(CHOSEN_PRODUCT_NAME)[0]
    product = update.callback_query.data.split(CHOSEN_PRODUCT_NAME)[1].split(CHOSEN_DISTRICT)[0]
    district = update.callback_query.data.split(CHOSEN_DISTRICT)[1].split(CHOSEN_FASOVKA)[0]
    fasovka = update.callback_query.data.split(CHOSEN_FASOVKA)[1]
    context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=f"Вы выбрали тип клада {klad_type}",
    )
    product = Product.objects.get(name=product)
    fasovka = Fasovka.objects.get(grams=float(fasovka))
    TempZakladkaForCourier.objects.create(courier=Courier.objects.get(user.user_id), klad_type=klad_type, product=Product.objects.get(name=product),
                                          district=District.objects.get(district_name=district),
                                          fasovka=Fasovka.objects.get(grams=float(fasovka)))
    context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text="Напиши координаты в формате широта, долгота (пример: 47.3552, 178.3663).\nЕсли не появилось сообщение об успешном выборе координат, введи еще раз в правильном формате."
        )


def log_lat_handler(update: Update, context: CallbackContext):
    coords = update.message.text
    lat, log = coords.split(", ")
    zk = TempZakladkaForCourier.objects.first()
    zk.longitude = float(log)
    zk.latitude = float(lat)
    zk.save()
    context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=f"Выбраны:\nШирота: {lat}, Долгота: {log}",
    )
    context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text="Напиши описание товара, начиная со слова ОПИСАНИЕ (пример: ОПИСАНИЕ Находится у...).\nЕсли не появилось сообщение об успешном описании, введи еще раз в правильном формате."
    )


def description_handler(update: Update, context: CallbackContext):
    desc = update.message.text
    _, d = desc.split("ОПИСАНИЕ ")
    zk = TempZakladkaForCourier.objects.first()
    zk.description = d
    zk.save()
    context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=f"Успешно добавлено описание: \n{d}"
    )
    context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=f"Пришли фотографию локации"
    )


def location_photo_handler(update: Update, context: CallbackContext):
    user = User.get_user(update, context)
    if _is_user_courier(user) and TempZakladkaForCourier.objects.filter(courier=user):
        zk = TempZakladkaForCourier.objects.filter(courier=user).first()
        if not zk.image:
            file = update.message.document.get_file()
            zk.image = file
            zk.save()
            context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=f"Фото отправлено успешно"
            )
            context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text="Ваша закладка:"
            )
            context.bot.send_photo(
                chat_id=update.callback_query.message.chat_id,
                photo=zk.image
            )
            context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=zakladka_created.format(
                    city_name=zk.city.name,
                    district_name=zk.district.district_name,
                    product_name=zk.product.name,
                    fasovka_name=str(zk.fasovka.grams),
                    latitude=str(zk.latitude),
                    longitude=str(zk.longitude),
                    description=zk.description,
                    klad_type=zk.klad_type
                )
            )
            context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text="Сохранить?", reply_markup=make_keyboard_for_confirm_zk()
            )


def confirm_zk_handler(update: Update, context: CallbackContext):
    user = User.get_user(update, context)
    decision = update.callback_query.data.replace(CONFIRM_ZK, "")
    zk = TempZakladkaForCourier.objects.filter(courier=user).first()
    if decision == "Сохранить":
        real_zk = Zakladka.objects.create(courier=user,
                                city=zk.city,
                                district=zk.district,
                                product=zk.product,
                                fasovka=zk.fasovka,
                                latitude=zk.latitude,
                                longitude=zk.longitude,
                                description=zk.description,
                                image=zk.image,
                                klad_type=zk.klad_type)
        zk.delete()
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text="Закладка создана"
        )
        context.bot.send_photo(
            chat_id=update.callback_query.message.chat_id,
            photo=real_zk.image
        )
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=zakladka_created.format(
                city_name=real_zk.city.name,
                district_name=real_zk.district.district_name,
                product_name=real_zk.product.name,
                fasovka_name=str(real_zk.fasovka.grams),
                latitude=str(real_zk.latitude),
                longitude=str(real_zk.longitude),
                description=real_zk.description,
                klad_type=real_zk.klad_type
            )
        )
        update.message.reply_text(text=welcome_message_courier,
                                  reply_markup=make_keyboard_for_curier_menu())
    else:
        update.message.reply_text(text=welcome_message_courier,
                                  reply_markup=make_keyboard_for_curier_menu())


def c_citi_chosen_district_handler(update: Update, context: CallbackContext):
    user = User.get_user(update, context)
    city = update.callback_query.data.replace(CITIESC, "")
    city = City.objects.get(name=city)
    context.bot.send_message(chat_id=update.callback_query.message.chat_id, text="Район",
                                  reply_markup=make_keyboard_for_districts_c(user=user, product=product))


def _courier_statistic(courier):
    zks = Zakladka.objects.filter(courier=courier)
    return couries_stat_text.format(date_create=courier.created_at,
                                    zk_count=zks.count(),
                                    zk=zks.first())


def _is_user_courier(user: User):
    if Courier.objects.filter(telegram_id=user.user_id):
        return True
    return False
