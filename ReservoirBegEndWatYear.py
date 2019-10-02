"""
Created on Wed Oct 2 14:16:37 2019

@author: alesbou
"""

import os
import pandas as pd
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt     
from matplotlib import style
   

#Working inside subdirectory
abspath = os.path.abspath(__file__)
absname = os.path.dirname(abspath)
os.chdir(absname)


def get_CDEC_data(station_id='mil', sensor_num='15', durformat ='H', start_date='1900-01-01', \
    end_date=dt.datetime.today().strftime("%Y-%m-%d"), interpolate = False, listofstations = False):
    
    url = 'http://cdec.water.ca.gov/dynamicapp/req/CSVDataServlet?Stations='+\
    station_id+'&SensorNums='+sensor_num+'&dur_code='+durformat+'&Start='+start_date+'&End='+end_date
    
    a = pd.read_csv(url, engine='python', encoding='utf-8', skiprows = 1,index_col=False, names = ["STATION_ID","DUR_CODE","SENSOR_NUM","SENSOR_TYPE","ACTUAL_DATE","HOUR","VALUE","DATA_FLAG","UNITS"])    
    
   
    a['ACTUAL_DATE']=a['ACTUAL_DATE'].astype(str)
    a['year']=a['ACTUAL_DATE'].str[:4].astype(int)
    a['month']=a['ACTUAL_DATE'].str[4:6].astype(int)
    a['day']=a['ACTUAL_DATE'].str[6:8].astype(int)
    a['HOUR']=a['ACTUAL_DATE'].str[10:11].astype(int)
    a['date'] = pd.to_datetime(a[['year','month','day','HOUR']])
    a.VALUE = pd.to_numeric(a.VALUE, errors=coerce)
    if listofstations == True:    
        a['output']=a.VALUE
        a = a[['date','output']]
        a.rename(columns={'output': station_id + "_" + sensor_num}, inplace=True)
        a = a.set_index(a.date)
        a = a.drop(columns='date',axis=1)
        if len(a)>0:
            a = a.reindex(pd.date_range(a.index[0], a.index[-1], freq=durformat)).fillna(np.nan)
    if interpolate==True:
        if listofstations==False:
            a.VALUE = a.VALUE.interpolate()
        else:
            a = a.interpolate()
    return a

reservoirs=['CLE','SHA', 'ORO', 'FOL', 'NML', 'DNP','EXC', 'MIL', 'PNF', 'ISB', 'PRR' , 'SNL'] #CAS -> I took out castaic because of missing data for this purpose

storageall = []
releaseall = pd.DataFrame()
for reservoir in reservoirs:
    storageall.append(get_CDEC_data(station_id=reservoir,sensor_num='15', durformat = 'D',start_date='1985-10-01', end_date='2019-10-02'))

storagelist = storageall[0]
for i in np.arange(1,len(storageall)):
    storagelist = storagelist.append(storageall[i])
    
storagelist = storagelist.loc[storagelist.day==1]
storagelist = storagelist.loc[storagelist.month==10]
pivot = storagelist.pivot(index='year', columns='STATION_ID' , values = 'VALUE')
pivotinter = pivot.interpolate()
pivotinter = pivot.dropna()

    
pivotinter['sum'] = pivotinter.sum(axis=1)
datafinal = pivotinter['sum']
datafinal = pd.concat([datafinal, datafinal.shift(-1)], axis=1)
datafinal.columns = ['current', 'next']

datafinal2 = datafinal.sort_values('current')
datafinal2 = datafinal2/1000000
datafinal2 = datafinal2.reset_index()

#Plotting
style.use('ggplot')
NUM_COLORS = len(datafinal2)
cm = plt.get_cmap('jet_r')
color = [cm(1.*i/NUM_COLORS) for i in range(NUM_COLORS)]
for i in np.arange(len(datafinal2)):
    plt.scatter(datafinal2.current[i],i, c= color[i])
    plt.text(datafinal2.current[i],i+0.25, str(datafinal2.year[i]+1))
    if datafinal2.next[i] > datafinal2.current[i]:
        plt.scatter(datafinal2.next[i],i,marker='>', c=color[i])
    else:
        plt.scatter(datafinal2.next[i],i,marker='<', c=color[i])
for i in np.arange(len(datafinal2)):
    plt.plot([datafinal2.current[i], datafinal2.next[i]],[i, i], c=color[i])
plt.xlabel('Millions of acre-feet')
plt.yticks(Visible=False)
plt.title("Water stored in California's 12 major reservoirs at the beginning and end of the water year")
