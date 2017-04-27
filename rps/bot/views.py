from django.shortcuts import render

from graphos.sources.simple import SimpleDataSource
from graphos.renderers.gchart import LineChart

def chart(request):
    data =  [
            ['Year', 'Sales', 'Expenses'],
            [2004, 1000, 400],
            [2005, 1170, 460],
            [2006, 660, 1120],
            [2007, 1030, 540]
        ]
    # DataSource object
    data_source = SimpleDataSource(data=data)
    # Chart object
    chart = LineChart(data_source)
#    chart = LineChart(data_source, options={ 
#     'backgroundColor': {
#        'fill':'black'     
#        },    
#    })
    context = {'chart': chart}
    return render(request, 'chart.html', context)
