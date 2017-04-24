from __future__ import absolute_import, unicode_literals
import os

from celery import shared_task
import datetime
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rps.settings')
django.setup()

from bot.models import Player

############# Tweepy Reverse leacky bucket  ############################
@shared_task()
def periodicUpdateRate():
    now = datetime.datetime.now()
    print('Now: ', now)
    for p in Player.objects.all():
        print(p.screen_name)
    
