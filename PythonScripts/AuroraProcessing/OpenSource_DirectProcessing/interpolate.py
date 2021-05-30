#==============================================================================
# Aurora : interpolate.py
# Author : Nathan Wisla
# Purpose: To create a spline interpolated raster image from OVATION Model data
#          from the NOAA, and store the most recent result into a database
# Date   : May 15, 2021
#==============================================================================

from io import BytesIO
from os import remove
from osgeo import gdal, osr
from scipy.interpolate import griddata
from numpy import mgrid, transpose, array
from json import dumps, loads
from urllib import request
from PIL import Image
import datetime
import psycopg2

ROOT = r'C:\inetpub\wwwroot\\'
PNG_DEST = ROOT + 'int.png'
dsn = 'host=localhost dbname=* user=* password=*'
maxRowCount = 500 # Specify maximum allowed rows in database

class Aurora():

    def __init__(self, db_connectString):
        self.outputName = 'temp.tif'
        self.db_connectString = db_connectString
        self.sourceData = self.getJSON()
        self.rowCount = self.getCount()

    def __repr__():
        return self.sourceData

    
    def createSpline(self):
        '''createSpline(outputName, existingPoints, values, allPoints) -> void
                outputName: name of the output geotiff file (.tif)
                existingPoints: points that already exist from the input
                values: values for each existingPoint. Must have same length as existingPoints
                allPoints: x,y grid points that represent every point that needs to be interpolated

                Creates an empty raster that is then filled with interpolated data points
        '''

        outputName = self.outputName
        existingPoints = self.sourceData['coordinates'][:,0:2]
        values = self.sourceData['coordinates'][:,2]
        allPoints = tuple(mgrid[0:360:0.1, -90:90:0.1])
        
        interpolationGrid = griddata(existingPoints,values,allPoints,fill_value=0, method='cubic')
        interpolationGrid = transpose(interpolationGrid)

        pixelWidth = pixelHeight = 0.1
        x_min, x_max, y_min, y_max = -180,180,-90,90
        cols = int((x_max - x_min) / pixelHeight)
        rows = int((y_max - y_min) / pixelWidth)

        driver = gdal.GetDriverByName('GTiff')

        target = driver.Create(outputName,cols,rows,1,gdal.GDT_Byte)
        target.SetGeoTransform((x_min, pixelWidth, 0, y_min, 0, pixelHeight))

        band = target.GetRasterBand(1)
        NDV = 0
        band.SetNoDataValue(NDV)
        band.FlushCache()

        target.GetRasterBand(1).WriteArray(interpolationGrid)

        targetSRS = osr.SpatialReference()
        targetSRS.ImportFromEPSG(4326)
        target.SetProjection(targetSRS.ExportToWkt())
        target = None
        

    def deleteLastRow(self, sizeThreshold):
        '''deleteLastRow(sizeThreshold) -> void
                Deletes the last entry of the database row if there are more
                rows than the size threshold
        '''
        
        if self.rowCount > sizeThreshold:
            print(f'Row count exceeds {sizeThreshold}!\nDeleting oldest row in the database...')
            with psycopg2.connect(dsn) as connection:
                with connection.cursor() as c:
                    c.execute("""DELETE FROM aurorarasters
                                 WHERE forecast_dt = (SELECT MIN(forecast_dt)
                                                      FROM aurorarasters)
                              """)
                    

    def deleteTIF(self):
        '''deleteTIF() -> void
                deletes any file, specifically made to delete a temporary geoTIFF
        '''
        remove(self.outputName)

        
    def instanceExists(self):
        '''instanceExists() -> bool
               Enters the database and checks if the current raster
               already exists
        '''

        dt = self.sourceData['Forecast Time']
        dsn = self.db_connectString
        with psycopg2.connect(dsn) as connection:
            with connection.cursor() as c:
                c.execute(f"""SELECT forecast_dt
                             FROM aurorarasters
                          """)
                tempList = c.fetchall()
                dtList = [tempList[i][0] for i in range(len(tempList))]
                return dt in dtList

    
    def getCount(self):
        '''getCount() -> int
               Retrieves the count of rows in the postgres database
        '''
        
        dsn = self.db_connectString
        with psycopg2.connect(dsn) as connection:
            with connection.cursor() as c:
                c.execute("""SELECT COUNT(*)
                             FROM aurorarasters
                          """)
                return c.fetchall()[0][0]


    def getJSON(self):
        '''getJSON() -> JSON dictionary
                Retrieves a JSON file that contains OVATION model data from NOAA
                and cleans the result:
                    coordinates into a gridded numpy array
                    time strings into datetime instances
        '''
        
        jsonLocation_url = f'https://services.swpc.noaa.gov/json/ovation_aurora_latest.json'
        http = request.urlopen(jsonLocation_url) #returns a bytes datatype
        aurora = http.read()
        aurora = loads(aurora)

        convertTimeFromString = lambda time : datetime.datetime.strptime(aurora[time],'%Y-%m-%dT%H:%M:%S%z')

        # make coordinate groups for each aurora strength value
        aurora['coordinates'] = array(aurora['coordinates'])

        # make observation time and forecast time datetime objects
        times = ('Observation Time','Forecast Time')
        for time in times:
            aurora[time] = convertTimeFromString(time)
        
        return aurora


    



    def insertInto(self, img='rast', useST=True):
        '''insertInto(img, useST) -> void
                Inserts a specified image into a database, if it is a
                GDAL supported format
                img(='rast'): the image column to insert into
                useST(=True): specify if you want to insert the image using
                              ST_FromGDALRaster() or as a raw image
        '''
        formatTime = lambda dt : dt.strftime('%Y-%m-%d %H:%M:%S%z')
        obsDT = formatTime(self.sourceData['Observation Time'])
        forecastDT = formatTime(self.sourceData['Forecast Time'])
        
        dsn = self.db_connectString
        with open(self.outputName,'rb') as f:
            f = psycopg2.Binary(f.read())
            with psycopg2.connect(dsn) as connection:
                with connection.cursor() as c:
                    if useST:
                        c.execute(f"""INSERT INTO
                                  aurorarasters(obs_dt,forecast_dt,{img}) VALUES
                                  ('{obsDT}','{forecastDT}',ST_FromGDALRaster({f}))
                                  """)
                    else:
                        c.execute(f"""INSERT INTO
                                  aurorarasters(obs_dt,forecast_dt,{img}) VALUES
                                  ('{obsDT}','{forecastDT}',{f})
                                  """)



                    
    def producePNG(self,dest):
        '''producePNG() -> void
                Accesses the postgres database and saves a png to the
                specified directory
                dest: path of png file
        '''
        dsn = 'host=localhost dbname=aurora user=postgres password=cogs1234'
        with psycopg2.connect(dsn) as connection:
            with connection.cursor() as c:
                c.execute("""SELECT
                                ST_AsPNG(rast)
                             FROM aurorarasters
                             WHERE forecast_dt = (SELECT MAX(forecast_dt) FROM aurorarasters)
                          """)
                png = c.fetchall()[0][0]
        png = Image.open(BytesIO(png))
        png.save(dest)
        


        

        
                    
    

aurora = Aurora(dsn)
if not aurora.instanceExists():
    print('Creating raster spline...')
    aurora.createSpline()
    print('done!')
    try:
        print('Inserting raster and metadata into database...')
        aurora.insertInto()
        aurora.deleteTIF()
        print('done!')
        aurora.deleteLastRow(maxRowCount)
        aurora.producePNG(PNG_DEST)

        with open(ROOT + 'source.json','w') as file:
            j = {'obs_dt':aurora.sourceData['Observation Time'].strftime('%Y-%m-%d %H:%M:%S%z'),\
                 'forecast_dt':aurora.sourceData['Forecast Time'].strftime('%Y-%m-%d %H:%M:%S%z')}
            j = dumps(j)
            file.write(j)

    except Exception as E:
        print(f'Insert failed: {E}')

else:
    print('Operation skipped: data of this instance already exists!')







