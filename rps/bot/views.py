from django.shortcuts import render

from .models import Player, Game
from django.db.models import Q

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
    data = [[k,v] for k,v in datadict.items()]    
    data =  [['Selection', 'Number']] + data

    chart_description = 'The number of times a player has won, why not challenge the top winners ?' 
    context = {'data': data, 'bar_chart': True, 'chart_description': chart_description}
    return render(request, 'p_chart.html', context)
