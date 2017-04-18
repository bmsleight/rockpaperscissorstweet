# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from bot.management.commands._botcommands import *
from bot.tweepycredentials import *
from django.db.models import Q

import tweepy

from django.template.loader import render_to_string

#~/rockpaperscissorstweet/rps$ celery -A rps worker -l info

#Just to make the below look nicer
def trigger(command_list, text):
    return any(command in text.lower() for command in command_list)

#Process Text to find confederate_screen_name and hashtext
def checkConfederate(text):
    confederate_screen_name = ''
    hashtext = ''
    if text.count('@') > 1:
        for word in text.rstrip().split(' '):
            if word: # word not ''
                if word[0] == '@' and word.lower() != BOTHANDLE:
                    confederate_screen_name = word[1:] # drop @
                if word[0] == '#':
                    hashtext = hashtext + ' ' + word
    return (confederate_screen_name, hashtext)

############## Incoming from Twitter Stream Non-Blcoking ###############

@shared_task
def processTaskInComing(user_id, screen_name, text, dm):
    if BOTHANDLE in text.lower() or dm:
        # Was mentioned in message (or a DM) so wake up!
        print('Was in message UID: ', user_id, 'Screen_name: ', screen_name, 'Text: ', text)
        # Commands
        challege_commands = ['start', 'fight', 'duel']
        optout_commands = ['optout']
        selection_commands = ['rock', 'paper', 'scissors']
        selection_commands_short = ['r', 'p', 's', 'R', 'P', 'S']
        # Tests
        if trigger(optout_commands, text):
            optOut(screen_name)
        elif trigger(challege_commands, text):
            challege(screen_name, text)
        elif trigger(selection_commands, text) and dm:
            selectedRPSLong(screen_name, text)
        elif text.lower() in selection_commands_short and dm:
            selectedRPS(screen_name, text)

@shared_task
def processNewTwitterFollow(screen_name):
    print('New twitter follow from: ', screen_name)
    if screen_name.lower() != BOTHANDLE[1:].lower():
        try:
            player = Player.objects.get(screen_name__iexact=screen_name)
            player.followed_by = True
            player.optout = False
            player.save()
        except Player.DoesNotExist:
            player = Player(screen_name=screen_name, optout=False, followed_by=True)
        if not player.following:
            chain = create_friendship.s(screen_name) | processCheckGamesNewFollower.s(screen_name)
            chain()
        else:
            checkGamesNewFollower(screen_name)

@shared_task
def processCheckGamesNewFollower(screen_name):
    checkGamesNewFollower(screen_name)

############## Other Tasks Spawned from the Non-Blockers ###############


def optOut(screen_name):
    print('Opt out Command for: ', screen_name)
    try:
        player = Player.objects.get(screen_name__iexact=screen_name)
    except Player.DoesNotExist:
        raise CommandError('Player "%s" does not exist' % screen_name)
    player.optout = True
    player.save()

def checkGamesNewFollower(screen_name):
    try:
        player = Player.objects.get(screen_name__iexact=screen_name)
        try:
            games = Game.objects.filter(
                Q(bot_has_issued_challege=False), 
                Q(player_instigator=player) | Q(player_confederate=player) 
                )
            for game in games:
                if game.player_instigator.followed_by and game.player_confederate.followed_by:
                    issueChallegeByDM(game)
        except Game.DoesNotExist:
            pass # Just following no games yet
    except Player.DoesNotExist:
        print('checkGamesNewFollower - Player.DoesNotExist')

def issueChallegeByDM(game):
    game.bot_has_issued_challege = True
    game.save()
    directMessage(screen_name=game.player_instigator.screen_name, template='dm-challege.txt', other_screen_name=game.player_confederate.screen_name)
    directMessage(screen_name=game.player_confederate.screen_name, template='dm-challege.txt', other_screen_name=game.player_instigator.screen_name)    

def challege(screen_name, text):
    print('Challege Command for: ', screen_name)
    # First check for have at least one other player (confederate) mentioned
    (confederate_screen_name, hashtext) = checkConfederate(text)
    if confederate_screen_name:
        # We have a confederate
        (new_i, player_instigator) = newPlayer(screen_name)
        (new_c, player_confederate) = newPlayer(confederate_screen_name)
        if new_i or new_c:
            statusMessage(screen_name=screen_name, player_confederate=confederate_screen_name, template='need-to-follow-to-player.txt')
        # If no one has opted out....
        if new_i is not None and new_c is not None:
            newGame(player_instigator, player_confederate, hashtext)
        elif new_i is not None:
            atMessage(screen_name, 'other-player-opted-out.txt')
        elif new_c is not None: # Unlikely but who knows
            atMessage(confederate_screen_name, 'other-player-opted-out.txt')
        # Are both following me and in Players ?
        if not new_i and not new_c and player_instigator.followed_by and player_confederate.followed_by:
            pass # this is checked in newGame()
    else:
        atMessage(screen_name, 'need-to-mention-confederate-player.txt')

def newPlayer(screen_name):
    print('New Player ?: ', screen_name)
    #http://stackoverflow.com/a/42764175/5860978 @bmsleight?
    PERMITTED_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    screen_name = "".join(c for c in screen_name if c in PERMITTED_CHARS)
    try:
        # The player may be lowercase in screen_name but scored correctly in 
        player = Player.objects.get(screen_name__iexact=screen_name)
        if player.optout:
            return (None, None)
        else:
            return (False, player)
    except Player.DoesNotExist:
        player = Player(screen_name=screen_name)
        print(player)
        player.save()
        return (True, player)

def newGame(player_instigator, player_confederate, hashtext, bot_has_issued_challege=False):
    print('New Game', hashtext)
    game = Game(player_instigator=player_instigator, player_confederate=player_confederate, hashtext=hashtext, bot_has_issued_challege=bot_has_issued_challege)
    game.save()
    if not player_instigator.followed_by:
        # This may be wrong - we should check.
        getFriendshipWithMe(player_instigator.screen_name)
    if not player_confederate.followed_by:
        # This may be wrong - we should check.
        getFriendshipWithMe(player_confederate.screen_name)
    if player_instigator.followed_by and player_confederate.followed_by:
        issueChallegeByDM(game)

def updatePlayerFollows(screen_name, following, followed_by):
    # If new follow then newTwitterFollow
    print('Update Player Followes: ', screen_name, following, followed_by)
    try:
        player = Player.objects.get(screen_name__iexact=screen_name)
        old_followed_by = player.followed_by
        player.followed_by = followed_by
        player.following = following
        if not player.following:
            # FIXME incorrectly assume always can create friendship
            #       A lesson for life ? lol
            create_friendship.delay(player.screen_name)
            #Pick up results from twitter stream - but assume for now true
            player.following = True
        player.save()
        if not old_followed_by and player.followed_by:
            # New Followed_by
            checkGamesNewFollower(screen_name)
    except Player.DoesNotExist:
        print('Player DoesNotExist in updatePlayerFollows')

def selectedRPSLong(screen_name, text):
    print('In long form selected rps')
    if text.lower() == 'rock':
        selectedRPS(screen_name, 'R')
    elif text.lower() == 'paper':
        selectedRPS(screen_name, 'P')
    elif text.lower() == 'scissors':
        selectedRPS(screen_name, 'S')        

def selectedRPS(screen_name, text):
    print('Selected rps')
    rpc = text.upper()
    # Select the right game
    try:
        player = Player.objects.get(screen_name__iexact=screen_name)
    except Player.DoesNotExist:
        print('selectedRPS - Player somehow does not exist') 
    try:
        game = Game.objects.filter(
            Q(bot_has_issued_challege=True), 
            Q(settled=False),
            Q(player_instigator=player) | Q(player_confederate=player) 
            )[0]
        if game.player_instigator == player:
            game.instigator_rpc = rpc
        if game.player_confederate == player:
            game.confederate_rpc = rpc
        game.save()
        if game.instigator_rpc != 'N' and game.confederate_rpc != 'N':
            processGameWhoWon(game)        
    except Game.DoesNotExist:
        directMessage(screen_name=screen_name, template='dm-no-game-in-progress.txt')
    except IndexError:
        print('IndexError') 

def processGameWhoWon(game):
    draw = False
    if game.instigator_rpc == 'R':
        if game.confederate_rpc == 'R':
            draw = True
        elif game.confederate_rpc == 'P':
            game.instigator_won = False
        elif game.confederate_rpc == 'S':
            game.instigator_won = True
    elif game.instigator_rpc == 'P':
        if game.confederate_rpc == 'R':
            game.instigator_won = True
        elif game.confederate_rpc == 'P':
            draw = True
        elif game.confederate_rpc == 'S':
            game.instigator_won = False
    elif game.instigator_rpc == 'S':
        if game.confederate_rpc == 'R':
            game.instigator_won = False
        elif game.confederate_rpc == 'P':
            game.instigator_won = True
        elif game.confederate_rpc == 'S':
            draw = True
    if draw:
        game.draws = game.draws + 1
        game.instigator_rp = 'N'
        game.confederate_rpc = 'N'
        game.save()
        directMessage(screen_name=game.player_instigator.screen_name, template='dm-draw.txt')
        directMessage(screen_name=game.player_confederate.screen_name, template='dm-draw.txt')        
    else:
        game.settled = True
        game.save()
        messageGameOutCome(
            game.player_instigator.screen_name, game.get_instigator_rpc_display(), 
            game.player_confederate.screen_name, game.get_confederate_rpc_display(),
            game.instigator_won, game.draws, game.hashtext
            )

def messageGameOutCome(
            instigator_screen_name, instigator_rpc, 
            confederate_screen_name, confederate_rpc,
            instigator_won, draws, hashtext):
    if instigator_won:
        statusMessage(
            template='outcome-game-won.txt',
            winner_screen_name=instigator_screen_name,
            winner_rpc = instigator_rpc,
            loser_screen_name=confederate_screen_name,
            loser_rpc=confederate_rpc,
            draws=draws,
            hashtext=hashtext)
    else:
        statusMessage(
            template='outcome-game-won.txt',
            winner_screen_name=confederate_screen_name,
            winner_rpc = confederate_rpc,
            loser_screen_name=instigator_screen_name,
            loser_rpc=instigator_rpc,
            draws=draws,
            hashtext=hashtext)

################# Prep Messages before Tweepy ##########################

def statusMessage(**kwargs):
    rendered = render_to_string(kwargs['template'], context=kwargs)
    print(rendered)
    update_status.delay(rendered[:140])

def atMessage(screen_name, template):
    rendered = render_to_string(template, {'screen_name': screen_name})
    print(rendered)
    update_status.delay(rendered[:140])

def directMessage(**kwargs):
    rendered = render_to_string(kwargs['template'], context=kwargs)
    print(rendered)
    dm.delay(kwargs['screen_name'], rendered)
    # delay and kargs


################# Tweepy Stuff Outgoing ################################

def returnAPI():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.secure = True
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = tweepy.API(auth)
    return api

@shared_task(rate_limit='400/h')  # reduce to 40
def getFriendshipWithMe(screen_name):
    api = returnAPI()    
    friendships = api.show_friendship(source_screen_name=BOTHANDLE,
                                     target_screen_name=screen_name)
    updatePlayerFollows(screen_name, friendships[0].following, friendships[0].followed_by)

@shared_task(rate_limit='40/h')
def create_friendship(screen_name):
    api = returnAPI()    
    api.create_friendship(screen_name=screen_name)

@shared_task(rate_limit='400/h') # reduce to 40
def dm(screen_name, text):
    api = returnAPI()    
    api.send_direct_message(screen_name=screen_name, text=text)

@shared_task(rate_limit='100/h')
def update_status(text):
    api = returnAPI()    
    api.update_status(status=text)
