from django.shortcuts import render

from .models import Player, Game
from django.db.models import Q

import pygal
from pygal.style import DarkStyle

import operator

def pchart(request):
    data =  [
          ['Task', 'Hours per Day'],
          ['Work',     11],
          ['Eat',      12],
          ['Commute',  2],
          ['Watch TV', 2],
          ['Sleep',    7]
        ]
    # [['Paper', 1], ['Scissors', 1], ['Rock', 1]]

    context = {'data': data, 'pie_chart': True}
    return render(request, 'p_chart.html', context)

def choices(request):
    datadict = {}
    for c in Game.RPS:
        if c[0] != 'N':
            datadict[c[1]] = Game.objects.filter(Q(instigator_rpc=c[0]) | Q(confederate_rpc=c[0]) ).count()
    data = [[k,v] for k,v in datadict.items()]    
    data =  [['Selection', 'Number']] + data
    context = {'data': data, 'pie_chart': True}
    return render(request, 'p_chart.html', context)


def winners(request):
    datadict = {}
    for player in Player.objects.all():
        datadict[player.screen_name] = Game.objects.filter(
            Q(player_instigator=player, instigator_won=True) | Q(player_confederate=player, instigator_won=False) 
            ).count()
    print(datadict)
    data = [[k,v] for k,v in datadict.items()]    
    data =  [['Selection', 'Number']] + data

    chart_description = 'The number of times a player has won, why not challenge the top winners ?' 
    context = {'data': data, 'bar_chart': True, 'chart_description': chart_description}
    return render(request, 'p_chart.html', context)

#http://www.saltycrane.com/blog/2007/12/how-to-sort-table-by-columns-in-python/
def sort_table(table, cols):
    """ sort a table by multiple columns
        table: a list of lists (or tuple of tuples) where each inner list 
               represents a row
        cols:  a list (or tuple) specifying the column numbers to sort by
               e.g. (1,0) would sort by column 1, then by column 0
    """
    for col in reversed(cols):
        table = sorted(table, key=operator.itemgetter(col), reverse=True)
    return table

def dashboard(request):
    pygal.style.DarkStyle.label_font_size = 20 
    pygal.style.DarkStyle.legend_font_size = 20
    pygal.style.DarkStyle.major_label_font_size = 20
    pygal.style.DarkStyle.value_label_font_size = 20
    pygal.style.DarkStyle.tooltip_font_size = 20
    # Winners
    line_chart = pygal.HorizontalBar(style=pygal.style.DarkStyle)
#    line_chart.title = 'Total Number of Wins'
    for player in Player.objects.all():
        line_chart.add(player.screen_name, Game.objects.filter(
            Q(player_instigator=player, instigator_won=True) | Q(player_confederate=player, instigator_won=False) 
            ).count())
    winners_chart = line_chart.render_data_uri()

    # Winners as a percentage
    #  Yes I couls store the resutl form before... but..
    win = []
    lose = []
    players = []
    table = []
    for player in Player.objects.all():
        players.append(player.screen_name)
        wins = (Game.objects.filter(
            Q(player_instigator=player, instigator_won=True) | Q(player_confederate=player, instigator_won=False) 
            ).count())
        loses = (Game.objects.filter(
            Q(player_instigator=player, instigator_won=False) | Q(player_confederate=player, instigator_won=True) 
            ).count())
        total = wins + loses
        win_percent = round(100*wins/total,1)
        lose_percent = round(100*loses/total,1)
        table.append((player.screen_name, wins, loses, win_percent, lose_percent, total))
    leader_data = sort_table(table, (3,1))
    # Ok now we have the leaderboard data in a nice table
    
    # Make into markdown
    leader_md = '| | Win Percentage | Total Wins | \n| - |:-:| -:|\n'
    for d in leader_data[:3]:
        leader_md = leader_md + '| [@' + d[0] + '](http://twitter.com/share?text=Ok%20@' + d[0] + '%20Your%20on%20the%20Leaderboard,%20lets%20duel%20with%20@RPSrobot%20as%20referee%20) |' + str(d[3]) + '|' + str(d[1]) + '| \n'
#<a class="twitter popup" href="http://twitter.com/share?text=This%20is%20so%20easy">Tweet</a>

    # Make into chart
    win = []
    lose = []
    players = []
    for d in reversed(leader_data):
        players.append(d[0])
        win.append(d[3])
        lose.append(d[4])
    line_chart = pygal.HorizontalStackedBar(style=pygal.style.DarkStyle)
    line_chart.x_labels = players
    line_chart.add('Win', win)
    line_chart.add('Lose', lose)
    winners_percentage = line_chart.render_data_uri()

    # Choices
    pie_chart = pygal.Pie(style=pygal.style.DarkStyle)
#    pie_chart.title = 'Choices selected in %'
    not_n = Game.objects.filter(~Q(instigator_rpc ='N')).count() + Game.objects.filter(~Q(confederate_rpc='N')).count()
    for c in Game.RPS:
        if c[0] != 'N':
            pie_chart.add(c[1],round(100*Game.objects.filter(Q(instigator_rpc=c[0]) | Q(confederate_rpc=c[0]) ).count()/not_n, 2) )
    choices_chart = pie_chart.render_data_uri()
    
    return render(request, 'dashboard.html', 
                 context = {'winners_chart': winners_chart, 
                            'choices_chart': choices_chart, 
                            'winners_percentage': winners_percentage, 
                            'leader_md': leader_md})
