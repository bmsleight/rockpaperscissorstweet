from django.db import models

# Create your models here.
# rm db.sqlite3 ; python manage.py makemigrations bot ;  python manage.py migrate ; python manage.py creatuperuser

class Player(models.Model):
    screen_name = models.CharField(max_length=15, help_text='screen_name')
    optout = models.BooleanField(default=False)
    following = models.BooleanField(default=False, help_text='@RPSrobot is following screen_name')
    followed_by = models.BooleanField(default=False, help_text='@screen_name is following RPSrobot')
    premium = models.IntegerField(default=10)

    def __str__(self):              # __unicode__ on Python 2
        return self.screen_name

class Game(models.Model):    
    player_instigator = models.ForeignKey(Player, related_name='player_instigator')
    player_confederate = models.ForeignKey(Player, related_name='player_confederate') # Oppersite of instigator
    hashtext = models.CharField(max_length=140, default='', blank=True)
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

    def __str__(self):              # __unicode__ on Python 2
        return self.player_instigator.screen_name + ' vs ' + self.player_confederate.screen_name + ' ' + self.hashtext
