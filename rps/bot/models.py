from django.db import models

# Create your models here.

class Player(models.Model):
    screen_name = models.CharField(max_length=15, help_text='screen_name')
    optout = models.BooleanField(default=True)
    retweets = models.BooleanField(default=False)
    following = models.BooleanField(default=False)
    followed_by = models.BooleanField(default=False)
    premium = models.IntegerField(default=10)

class Game(models.Model):    
    player_instigator = models.ForeignKey(Player, related_name='player_instigator')
    player_confederate = models.ForeignKey(Player, related_name='player_confederate') # Oppersite of instigator
    start_status_id = models.BigIntegerField()
    status_content = models.CharField(max_length=186, help_text='140 + 2x15 + 15error + 1error')
    bot_has_issued_challege = models.BooleanField(default=False, help_text='Tweet of So @playerone wants to settle this by #RockPaperScissors')
    RPS = (
        ('N', 'None'),
        ('R', 'Rock'),
        ('P', 'Paper'),
        ('S', 'Scissors'),
    )
    instigator_rpc = models.CharField(max_length=1, choices=RPS, default='N')
    confederate_rpc = models.CharField(max_length=1, choices=RPS, default='N')
    draws = models.IntegerField(default=0)
    settled = models.BooleanField(default=False)
    instigator_won = models.BooleanField(default=False)

