#==============================================================================
# Aurora : populate.py
# Author : Nathan Wisla
# Purpose: To process the OVATION dictionary produced by get_json.py and to 
#          insert the results into a Postgres - PostGIS database
# Date   : April 8, 2021
#==============================================================================

import psycopg2
import datetime
from get_json import *


aurora = getJSON()
# Get name based on timestamp
forecastTime = datetime.datetime.strptime(\
                        aurora['Forecast Time'],\
                        '%Y-%m-%dT%H:%M:%S%z')
observationTime = datetime.datetime.strptime(\
                        aurora['Observation Time'],\
                        '%Y-%m-%dT%H:%M:%S%z')


obsStr = observationTime.strftime('%Y-%m-%d %H:%M:%S%z')
forecastStr = forecastTime.strftime('%Y-%m-%d %H:%M:%S%z')




for key in aurora['coordinates']:
    
    mpString = 'MULTIPOINT('
    for xy in aurora['coordinates'][key]:
        mpString += f'{xy[0]} {xy[1]},'
    mpString = mpString[:-1] + ')'
    
    aurora['coordinates'][key] = mpString


#==========================================================================


conn = psycopg2.connect(
    host = 'localhost',
    database='aurora',
    user='postgres',
    password='cogs1234')

c = conn.cursor()

print('version:')
c.execute('SELECT * FROM version()')
dbVersion = c.fetchone()
print(dbVersion)

c.execute('SELECT max(id) FROM auroraStrength')

maxid = c.fetchall()[0][0]

if maxid == None:
    maxid = 1
else:
    maxid += 1
    
for key in aurora['coordinates']:
    insert = f'''INSERT INTO auroraStrength VALUES(
        {maxid},'{obsStr}'::timestamptz,'{forecastStr}'::timestamptz,{key},'{aurora['coordinates'][key]}'
        );'''
    print(f'inserting values: {maxid}, {obsStr}, {forecastStr}, {key}')
    c.execute(insert)

c.close()

conn.commit()
print('committed insert to database!')
conn.close()
