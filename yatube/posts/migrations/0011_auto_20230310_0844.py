# Generated by Django 2.2.6 on 2023-03-10 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_auto_20230309_2054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(help_text='Текст нового поста', verbose_name='Текст поста'),
        ),
    ]