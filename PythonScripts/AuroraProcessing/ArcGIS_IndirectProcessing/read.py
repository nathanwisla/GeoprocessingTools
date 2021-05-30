import datetime
import re
import arcpy

def APinitialize():
    ws = r'S:\GIS\ArcGIS\Private_Projects\Aurora\scratch'
    sr = arcpy.SpatialReference(4326)
    arcpy.env.workspace = ws
    arcpy.env.overwriteOutput = True
    return ws, sr

ws, sr = APinitialize()

ws2 = 'S:\\GIS\\ArcGIS\\Private_Projects\\Aurora\\aurora.sde'
auroraFC = 'aurora.public.aurorastrength'
aurora = arcpy.Describe(ws2 + '\\' + auroraFC)


rasterList = []

for i in range(48):

            
        
    arcpy.management.SelectLayerByAttribute('auroraStrength',\
                                      'NEW_SELECTION',\
                                      f"id = {i + 1}")

##    out_raster = arcpy.sa.Spline("aurora.public.aurorastrength", "strength", 0.1, "REGULARIZED", 0.1, 12)
    
    rasterList.append(out_raster)
#    out_raster.save(r"S:\GIS\ArcGIS\Private_Projects\Aurora\Default.gdb\Spline_auror1")
    break
            
    

