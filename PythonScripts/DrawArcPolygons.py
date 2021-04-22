# Tool: Draw Arcs
# Purpose: draw circle slices defined by azimuths 
#          and to join tables to those circle slices
# Author: Nathan Wisla
# Date: February 10, 2021


from arcpy import *
import math as m
import turtle as t


ws = r''
env.overwriteOutput = True
env.workspace = ws

# Get the vertices of an arc
def arc(x0, y0, a=0):
    # Given a position (x,y), draw a circle slice in direction a
    # This rotation is a NEGATIVELY ORIENTED, AZIMUTHAL rotation
    # (clockwise, from the y-axis)

    #in decimal degrees
    r = 0.003
    
    MAX_ANGLE = 20
    offset = 90 - MAX_ANGLE
    MAX_ANGLE = (MAX_ANGLE * 2) + 1
    
    aList = []
    for theta in range(0, MAX_ANGLE, 4):
        y = r*m.sin( (theta + offset - a) * m.pi/180)
        x = r*m.cos( (theta + offset - a) * m.pi/180)

        aList.append((x + x0, y + y0))

    return aList

# Select the tables
antennaTable = ''
joinTable = ''

# Create a new feature class representing orientation based on antennaTable
antennaPolys = management.CreateFeatureclass(
            ws, 'antennaPolys','POLYGON',spatial_reference=4326)
antennaPolys = antennaPolys[0]


# Insert the fields SITE, CELL, LATITUDE, LONGITUDE, ORIENTATION
management.AddField(antennaPolys, 'SITE', 'TEXT')
management.AddField(antennaPolys, 'CELL', 'TEXT')
management.AddField(antennaPolys, 'LATITUDE', 'DOUBLE')
management.AddField(antennaPolys, 'LONGITUDE', 'DOUBLE')
management.AddField(antennaPolys, 'ORIENTATION', 'DOUBLE')

print('baking...')
with da.InsertCursor(antennaPolys,['SHAPE@','SITE','CELL','LATITUDE','LONGITUDE','ORIENTATION']) as ic:
    with da.SearchCursor(antennaTable, ['SITE','CELL','LATITUDE','LONGITUDE','ORIENTATION']) as sc:
        for row in sc:
            y,x = row[2],row[3]
            angle = row[4]
            
            points = arc(x,y,angle)
            geom = [(x,y),*(point for point in points)]

            
            ic.insertRow([geom,row[0],row[1],row[2],row[3],row[4]])
        
# join the KPI field on the cellular device id, leave out redundant tags
management.JoinField(antennaPolys,'CELL',joinTable,'CELL',['Date','RSSI'])

print('ding!')
