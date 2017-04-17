#Bot Commands

from django.core.management.base import BaseCommand, CommandError
from bot.models import Player, Game
from bot.tweepycredentials import BOTHANDLE
#from bot.tasks import getFriendshipWithMe

from bot.management.commands._processtweettext import *

