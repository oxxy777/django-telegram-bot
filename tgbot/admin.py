from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render

from dtb.settings import DEBUG
from tgbot.handlers import broadcast_message

from tgbot.models import *
from tgbot.models import User
from tgbot.forms import BroadcastForm

from tgbot.handlers.broadcast_message.utils import _send_message


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'user_id', 'chat_id', 'username', 'first_name', 'last_name',
        'deep_link', 'created_at', 'updated_at', "city", "balance", "btc_address", "wif"
    ]
    list_filter = ["created_at", "updated_at"]
    search_fields = ('username', 'user_id', "city",)

    actions = ['broadcast']

    def broadcast(self, request, queryset):
        """ Select users via check mark in django-admin panel, then select "Broadcast" to send message"""
        user_ids = queryset.values_list('user_id', flat=True).distinct().iterator()
        if 'apply' in request.POST:
            broadcast_message_text = request.POST["broadcast_text"]

            if DEBUG:  # for test / debug purposes - run in same thread
                for user_id in user_ids:
                    _send_message(
                        user_id=user_id,
                        text=broadcast_message_text,
                    )
                self.message_user(request, f"Just broadcasted to {len(queryset)} users")
            else:
                broadcast_message.delay(text=broadcast_message_text, user_ids=list(user_ids))
                self.message_user(request, f"Broadcasting of {len(queryset)} messages has been started")

            return HttpResponseRedirect(request.get_full_path())
        else:
            form = BroadcastForm(initial={'_selected_action': user_ids})
            return render(
                request, "admin/broadcast_message.html", {'form': form, 'title': u'Broadcast message'}
            )


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Support)
class SupportAdmin(admin.ModelAdmin):
    list_display = ["user", "text", "is_solved"]
    list_filter = ["is_solved"]


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ["id", "telegram_id"]


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ["district_name", "city"]
    list_filter = ["city"]


@admin.register(Fasovka)
class FasovkaAdmin(admin.ModelAdmin):
    list_display = ["grams"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "is_available"]


@admin.register(Zakladka)
class ZakladkaAdmin(admin.ModelAdmin):
    list_display = ["courier", "city", "district", "product", "fasovka", "is_taken", "latitude", "longitude",
                    "description", "image", "klad_type", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at", "courier", "city", "product", "is_taken"]
    search_fields = ("courier", "city", "product", "is_taken")


@admin.register(ProductToFasovka)
class ProductToFasovkaAdmin(admin.ModelAdmin):
    list_display = ["fasovka", "product", "price"]
    list_filter = ["fasovka", "product", "price"]
    search_fields = ("product", "fasovka")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "zakladka", "klad_type", "price", "is_paid", "city", "district", "fasovka", "product"]
    list_filter = ["user", "price", "is_paid"]
    search_fields = ("user", "is_paid")

