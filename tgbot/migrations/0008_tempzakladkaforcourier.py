# Generated by Django 3.2.13 on 2022-05-21 18:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0007_courier_city'),
    ]

    operations = [
        migrations.CreateModel(
            name='TempZakladkaForCourier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.FloatField(blank=True, null=True, verbose_name='Широта')),
                ('longitude', models.FloatField(blank=True, null=True, verbose_name='Долгота')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('image', models.ImageField(blank=True, null=True, upload_to='images', verbose_name='Изображение')),
                ('klad_type', models.CharField(blank=True, choices=[('SNOW', 'Снежный прикоп'), ('MAGNET', 'Магнит'), ('HIDE', 'Тайник'), ('GROUND', 'Прикоп'), ('OTHER', 'Другой')], default='GROUND', max_length=6, null=True, verbose_name='Тип клада')),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tgbot.city', verbose_name='Город')),
                ('courier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tgbot.courier', verbose_name='Курьер')),
                ('district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tgbot.district', verbose_name='Район')),
                ('fasovka', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tgbot.fasovka', verbose_name='Фасовка')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tgbot.product', verbose_name='Название товара')),
            ],
        ),
    ]