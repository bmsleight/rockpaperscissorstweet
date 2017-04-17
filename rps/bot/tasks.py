# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from bot.management.commands._botcommands import *
from bot.tweepycredentials import *

import tweepy

#Just to make the belwo look nicer
def trigger(command_list, text):
    return any(command in text.lower() for command in command_list)

@shared_task
def processTaskInComing(user_id, screen_name, text, dm):
    if BOTHANDLE in text.lower() or dm:
        # Was mentioned in message (or a DM) so wake up!
        print('Was in message UID: ', user_id, 'Screen_name: ', screen_name, 'Text: ', text)
        # Commands
        challege_commands = ['start', 'challege' 'settle', 'fight', 'duel']
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
        elif text.lower() in optout_commands and dm:
            selectedRPS(screen_name, text)

@shared_task
def processNewTwitterFollow(screen_name):
    newTwitterFollow(screen_name)

@shared_task
def processCheckGamesNewFollower(screen_name):
    checkGamesNewFollower(screen_name)

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



def optOut(screen_name):
    print('Opt out Command for: ', screen_name)
    try:
        player = Player.objects.get(screen_name=screen_name)
    except Player.DoesNotExist:
        raise CommandError('Player "%s" does not exist' % screen_name)
    player.optout = True
    player.save()

def newTwitterFollow(screen_name):
    print('New twitter follow from: ', screen_name)
    if screen_name.lower() != BOTHANDLE[1:]:
        try:
            player = Player.objects.get(screen_name=screen_name)
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

def checkGamesNewFollower(screen_name):
    try:
        player = Player.objects.get(screen_name=screen_name)
        games = Game.objects.filter(player_instigator=player, bot_has_issued_challege=False)
        for game in games:
            if game.player_confederate.followed_by:
                #If other party follows - then both follows so send out challege
                issueChallegeByDM(game)
        games = Game.objects.filter(player_confederate=player, bot_has_issued_challege=False)
        for game in games:
            if game.player_instigator.followed_by:
                #If other party follows - then both follows so send out challege
                issueChallegeByDM(game)
    except Player.DoesNotExist:
        print('checkGamesNewFollower - Player.DoesNotExist')

def issueChallegeByDM(game):
    game.bot_has_issued_challege = True
    game.save()
    directMessage(game.player_instigator.screen_name, template='dm-challege.txt')
    directMessage(game.player_confederate.screen_name, template='dm-challege.txt')    


def challege(screen_name, text):
    print('Challege Command for: ', screen_name)
    # First check for have at least one other player (confederate) mentioned
    (confederate_screen_name, hashtext) = checkConfederate(text)
    if confederate_screen_name:
        # We have a confederate
        (new_i, player_instigator) = newPlayer(screen_name)
        (new_c, player_confederate) = newPlayer(confederate_screen_name)
        if new_i:
            atMessage(screen_name, 'need-to-follow-to-player.txt')
        if new_c:
            atMessage(confederate_screen_name, 'need-to-follow-to-player.txt')
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
    try:
        player = Player.objects.get(screen_name=screen_name)
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
        player = Player.objects.get(screen_name=screen_name)
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

def selectedRPS(screen_name, text):
    print('Selected rps')


def atMessage(screen_name, template):
    print('@: ', screen_name, ' Using template: ', template)

def directMessage(screen_name, template):
    print('DM to: ', screen_name, ' Using template: ', template)
    # delay and kargs

def checkConfederate(text):
    confederate_screen_name = ''
    hashtext = ''
    if text.count('@') > 1:
        for word in text.rstrip().split(' '):
            if word: # word not ''
                if word[0] == '@' and word.lower() != BOTHANDLE:
                    confederate_screen_name = word[1:].lower() # drop @
                if word[0] == '#':
                    hashtext = hashtext + ' ' + word
    return (confederate_screen_name, hashtext)
