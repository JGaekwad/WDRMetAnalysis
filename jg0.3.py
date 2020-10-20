#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 10:14:05 2020

@author: jason
"""


'''This is code to process hourly measurements of wind speed, widn direction, 
and rainfall rate into a format appropriate for statistical analysis of 
wind driven rain, and also to conduct that analysis and provide the relevant
outputs

Note that the code will need to be altered based on input format, units of measurement,
and similar discrepancies typical of meteorological data sets'''

import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt

#import hourly data

wind=pd.read_csv('InTEST.csv')
#list out all column names
columnNames=list(wind.columns.values)
print(columnNames)

#create new dataframe which only includes useful columns
WDR=wind[['Year','Month','Day','Total Precipitation  [sfc]','Wind Speed  [10 m above gnd]',\
          'Wind Direction  [10 m above gnd]','Wind Gust  [sfc]']]
print(WDR)

#rename columns to simpler names
WDR.rename(inplace=True, columns={'Total Precipitation  [sfc]':'Rainfall rate, mm/hr',\
                                  'Wind Speed  [10 m above gnd]':'Speed, kts',\
                                  'Wind Direction  [10 m above gnd]':'Direction, deg',\
                                  'Wind Gust  [sfc]':'Gust, kts'})

'''note that df WDR is a copy of a slice from the 'wind' df. This is okay as
the WDR df will be used as the base df from here on ''' 

#delete rows which have rainfall rate of zero
#WDR=WDR.loc[WDR['rainfall rate, mm/hr']>0]
WDR=WDR.drop(WDR.index[WDR['Rainfall rate, mm/hr']==0])
print(WDR)

#delete rows which have wind speed of zero
#WDR=WDR.loc[WDR['rainfall rate, mm/hr']>0]
WDR=WDR.drop(WDR.index[WDR['Speed, kts']==0])
print(WDR)

#convert wind speed from kts to m/s
windSpeedConversionFactor=0.51447
WDR['Speed, m/s']=WDR.loc[:,'Speed, kts'].multiply(windSpeedConversionFactor)
WDR['Gust, m/s']=WDR.loc[:,'Gust, kts'].multiply(windSpeedConversionFactor)
print(WDR)

# Calculate gust factor
WDR['Gust factor']=WDR.loc[:,'Gust, m/s'].divide(WDR.loc[:,'Speed, m/s'])

#normalise measured mean wind speed to TC2
TCconv=pd.read_csv('TCconv.csv')
for i,j,k in zip(TCconv['Start'], TCconv['End'], TCconv['Conversion factor']):
    print ('i is ' + str(i) + ' j is ' + str(j) + ' k is ' + str(k))
    WDR.loc[WDR['Direction, deg'].between(i,j, inclusive=True), 'Speed, m/s'].multiply(k)

#convert previously normalised TC2 mean wind speed to site wind speed
Siteconv=pd.read_csv('Siteconv.csv')
for i,j,k in zip(Siteconv['Start'], Siteconv['End'], Siteconv['Conversion factor']):
    print ('i is ' + str(i) + ' j is ' + str(j) + ' k is ' + str(k))
    WDR.loc[WDR['Direction, deg'].between(i,j, inclusive=True), 'Speed, m/s'].multiply(k)

#plot wind speed vs direction (noting that these are all nenzero rain and wind data points)
WDR.plot.scatter(x='Direction, deg', y='Speed, m/s')

#plot hourly mean wind speed against rainfall intensity
WDR.plot.scatter(x='Speed, m/s', y='Rainfall rate, mm/hr')

#import list of wind directions (8 directions)
dirn=pd.read_csv('Directions.csv')

#import list of quantiles to calculate
quantList=pd.read_csv('Quantiles.csv')

#initialise variables and df for iterating through direction
totFreq = pd.DataFrame(columns={'Direction','Frequency', 'Max wind speed, m/s',\
                                'Max rainfall rate, mm/hr', 'Mean wind speed m/s',\
                                'Mean rainfall rate, mm/hr'})
dex=0

#iterate across the 8 wind directions
for l,m,n in zip(dirn['Start'], dirn['End'], dirn['Direction']):
    print ('l is ' + str(l) + ' m is ' + str(m) + ' n is ' + str(n))
    windDirn=WDR.loc[WDR['Direction, deg'].between(l,m, inclusive=False)]

    #calculate the number of entries per direction
    freq=len(windDirn.index)
    ''
    #calculate maxes and means per direction
    dirnMax=windDirn.max()
    dirnMean=windDirn.mean()
    
    #store the frequency with each wind direction
    totFreq=totFreq.append(pd.DataFrame({'Direction': n, 'Frequency': freq,\
                                         'Max wind speed, m/s': dirnMax['Speed, m/s'], \
                                        'Max rainfall rate, mm/hr':dirnMax['Rainfall rate, mm/hr'],\
                                        'Mean wind speed m/s': dirnMean['Speed, m/s'], \
                                        'Mean rainfall rate, mm/hr': dirnMean['Rainfall rate, mm/hr']}, index=[dex]))
    #dex+=1
    
    #export quantiles also
    
    #for loop to iterate through quantiles
    for q in quantList['Quantile']:
        print(q)
        quant=windDirn.quantile(q=q, axis=0)
    
    
    #for loop to calc wind speed and rainfall rain
        listVar=['Rainfall rate, mm/hr', 'Speed, m/s', 'Gust factor']
        for var in listVar:
            #var='Rainfall rate, mm/hr'
            colName=var+' '+str(q)+' percentile'
            totFreq.loc[dex,colName]=quant[var]

    print(totFreq)
    print(n)
    
    dex+=1
    
    
print(totFreq)

#calculate total frequency to calculate percentage (0.01 is to convert to percentage out of 100)
colSum=totFreq.sum(axis=0)
total=colSum['Frequency']
totFreq['Probability']=totFreq['Frequency'].divide(total*0.01)
print(totFreq)

#export table to Exel
totFreq.to_excel('Output.xlsx', sheet_name='Summary', index=False)

#plot wind direciton vs frequeny (noting that these are all nonzero rain and wind data points)
totFreq.plot.bar(x='Direction', y='Probability')



    