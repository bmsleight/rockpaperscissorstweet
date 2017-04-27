from django.contrib import admin

# Register your models here.

from .models import Player
from .models import Game
from .models import Rate

admin.site.register(Player)
admin.site.register(Game)
admin.site.register(Rate)
