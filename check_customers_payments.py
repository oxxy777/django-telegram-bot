import os

import django
import requests
import time

from tgbot.dispatcher import bot

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dtb.settings')
    django.setup()
    from tgbot.models import User

    def checked_balance(user):
        # Адрес кошелька пользователя
        wallet = user.btc_address

        url = f'https://blockchain.info/rawaddr/{wallet}'
        x = requests.get(url)
        wallet = x.json()
        if user.transactions < len(wallet["txs"]):
            for tx in wallet["txs"][:2]: # последние две
                user.balance += tx["amount"] # или что тут будет?
                user.transactions += 1
            user.save()
            bot.send_message(chat_id=user.chat_id, text=f"Ваш баланс пополнен и составляет {user.balance} BTC\nУдачных покупок!")
        # print('Итоговый баланс:' + str(wallet['final_balance']))
        # print('Транзакции:' + str(wallet['txs']))

    while True:
        users = User.objects.all()
        for user in users:
            checked_balance(user)
        time.sleep(180)