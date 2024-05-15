#!/usr/bin/python3

from datetime import datetime, timedelta
import pandas as pd
from neuralprophet import NeuralProphet, set_log_level
from definitions import *
from operator import itemgetter


def train(history_data,future_data):
    # Obtain components to predict
    components = getComponents()
    if not components: 
        return 'Train module not executed: not components to train'

    # Adding importation data timeline
    curr = datetime.now().replace(hour=0,minute=0, second=0, microsecond=0)
    hist = curr - timedelta(days=int(history_data))

    # Once we have the data to make the requests, we obtain the history of data from the assigned date until today at 00:00
    df = []
    for comp in components:
        dataCPU,dataRAM = getResources(comp,curr,hist)
        # Parseamos los datos a un Pandas Dataframe
        df.append(pd.DataFrame(dataCPU,columns=['ds','y']))
        df.append(pd.DataFrame(dataRAM,columns=['ds','y']))
    if not df:
        return 'Train module not executed: insufficient data'
    
    #Now that the data is in the correct format, we can train and validate a NeuralProphet model
    p = int(future_data) * 96
    resources = []

    for data in df:
        data.drop_duplicates(subset='ds',keep='first', inplace=True)
        res = []
        m = NeuralProphet()
        metrics = m.fit(data,freq='15T')
        #Create forecast
        future = m.make_future_dataframe(data, periods=p)
        forecast = m.predict(future)
        res.append(forecast['yhat1'].tolist())
        res.append(forecast['ds'].tolist())
        resources.append(res)

    data = []

    for i in range(0,len(resources),2):
        for j in range(len(resources[i][0])):
            dict = {
                'enabler_id' : components[int(i/2)]['enabler_id'],
                'component_id': components[int(i/2)]['id'],
                'timestamp': resources[i][1][j].to_pydatetime(),
                'cpu' : max(0,int(resources[i][0][j])),
                'ram' : max(0,int(resources[i+1][0][j])),
                'real' : 0
            }
            data.append(dict)

    sorted_data = sorted(data, key=itemgetter('timestamp','enabler_id','component_id')) 
    setMetrics(sorted_data)

    return 'Train module executed successfully'