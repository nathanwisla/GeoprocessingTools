#==============================================================================
# Aurora : get_json.py
# Author : Nathan Wisla
# Purpose: To retrieve the OVATION JSON file from the NOAA website and format
#          as a dictionary for easy cleaning
# Date   : April 1, 2021
#==============================================================================

from urllib import request
import json

def getJSON():
    jsonLocation_url = f'https://services.swpc.noaa.gov/json/ovation_aurora_latest.json'
    http = request.urlopen(jsonLocation_url) #returns a bytes datatype
    aurora = http.read()

    aurora = json.loads(aurora)


    # make coordinate groups for each aurora strength value
    points = aurora['coordinates']
    classifiedMultiPoints = {}

    for x,y,a in points:
        
        if a in classifiedMultiPoints:
            classifiedMultiPoints[a].append([x,y])
        else:
            classifiedMultiPoints[a] = []

    aurora['coordinates'] = classifiedMultiPoints
    return aurora
