# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from bot.management.commands._botcommands import optOut

@shared_task
def processTaskInComing(user_id, screen_name, text):
    if '@rpsrobot' in text.lower():
        # Was mentioned in message so wake up!
        print('Was in message UID: ', user_id, 'Screen_name: ', screen_name, 'Text: ', text)
        if 'optout'in text.lower():
            optOut(screen_name)


@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)
