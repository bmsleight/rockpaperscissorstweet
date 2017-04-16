#Bot Commands

from django.core.management.base import BaseCommand, CommandError
from bot.models import Player, Game

def optOut(screen_name):
    print('Opt out Command for: ', screen_name)
    try:
        player = Player.objects.get(screen_name=screen_name)
    except Player.DoesNotExist:
        raise CommandError('Player "%s" does not exist' % screen_name)
    player.optout = True
    player.save()
