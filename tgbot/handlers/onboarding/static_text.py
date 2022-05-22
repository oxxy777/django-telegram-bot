start_created = "Sup, {first_name}!"
start_not_created = "Welcome back, {first_name}!"
unlock_secret_room = "Congratulations! You've opened a secret room👁‍🗨. There is some information for you:\n" \
           "<b>Users</b>: {user_count}\n" \
           "<b>24h active</b>: {active_24}"
github_button_text = "GitHub"
secret_level_button_text = "Secret level🗝"

welcome_message = """
Привет! 
Добро пожаловать в наш магазин

Если вдруг вы не найдете то, что вам подходит
Для начала выбери город:
"""

order_description = """
Детали вашего заказа:

Город: {city_name}
Район: {district_name}
Название продукта: {product_name}
Фасовка: {fasovka_name}
Тип клада: {klad_type}

Цена: {price_name}BTC ({rub_price_str} рублей)

Оплата только в BTC
"""

buyed_order_text = """
Ваша покупка:

Город: {city_name}
Район: {district_name}
Название продукта: {product_name}
Фасовка: {fasovka_name}
Тип клада: {klad_type}

Цена: {price_name} BTC

Координаты (широта, долгота): {latitude}, {longitude}

Описание товара:
{description}

"""

account_text = """
Аккаунт

Город: {city}
Баланс: {balance}
Выполненных заказов: {orders}
"""

welcome_message_courier = """
Привет

Для добавления товара жми "Добавить товар".
Для просмотра статистики жми "Статистика".
Клиентские кнопки отключены кроме смены города. Для покупки воспользуйся другим аккаунтом.
"""

couries_stat_text = """
Работаешь с: {date_create}
Закладок сделано: {zk_count}
Последняя закладка: {zk}
"""

zakladka_created = """
Закладка:

Город: {city_name}
Район: {district_name}
Название продукта: {product_name}
Фасовка: {fasovka_name}
Тип клада: {klad_type}
Координаты (широта, долгота): {latitude}, {longitude}

Описание товара:
{description}
"""