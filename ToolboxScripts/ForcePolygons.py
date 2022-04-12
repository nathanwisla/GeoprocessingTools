# =====================================================================================
# Name    : ForcePolygons.py
# Author  : Nathan Wisla
# Purpose : ForcePolygons is a series of methods that is intended to pull polygons from
#           an unknown spatial reference that could not be moved using the basic "Move
#           To" tool provided by ESRI in ArcGIS Pro. This problem arose from some old 
#           spatial data that was submitted to the BC Gov that had a bad projection; when 
#           I attempted to reproject or even define the projection, the polygons would
#           not appear. This script is intended to take those types of polygons and 
#           force them onto the canvas to be manually placed in ArcGIS Pro.
# Date    : April 12, 2022
# Revised :
# =====================================================================================


import arcpy
from json import loads

class ForcePolygons:
    
    def __init__(self, shape, newX, newY, srid=3005):
        '''ForcePolygons takes a shape that cannot be found on the canvas after projecting or reprojecting, and moves it to a new location on the canvas 
                :param: shape: an ESRI arcpy or arcgis API shape
                :param: newX : rough coordinates representing the center x of the polygon to placed on the canvas
                :param: newY : rough coordinates representing the center y of the polygon to placed on the canvas
                :param: srid : a *projected* spatial reference system, in the same units as the original system
        '''
        self.sr = arcpy.SpatialReference(srid)
        self.OldShape = shape
        self.centroid, self.coords = self.__ExtractCoordinates()
        self.XY = (newX,newY)
        self.NewShape = self.__GeneratePolygon()

    def __repr__(self):
        aStr = ''
        aStr += f'{self.centroid} --> {self.XY}'
        return aStr

    def __GeneratePolygon(self):
        RelativeShape = arcpy.Polygon(self.__RelativizeCoordinates(self.coords))
        RelativeCoords = loads(RelativeShape.JSON)['rings']
        AbsoluteCoords = self.__AbsolutizeCoordinates(RelativeCoords)
        AbsoluteShape = arcpy.Polygon(AbsoluteCoords,self.sr)
        return AbsoluteShape

    def __AbsolutizeCoordinates(self, array):
        '''A recursive method for taking relative coordinates and placing them relative to a new centroid on the canvas.
                array: an iterable of coordinates
        '''
        if self.__is_iterable(array):
            array = list(array)
            coords = []
            
            for i in range(len(array)):
                if self.__is_iterable(array[i]):
                    array[i] = self.__AbsolutizeCoordinates(array[i])
                else:
                    coords.append(array[i] + self.XY[i])
            if coords:
                array = arcpy.Point(*coords)
            else:
                array = arcpy.Array(array)
            
            return array

    def __ExtractCoordinates(self):
        shape = self.OldShape
        if isinstance(shape, arcpy.Polygon):
            centroid = (shape.centroid.X, shape.centroid.Y)
            coords = loads(shape.JSON)['rings']
        else:
            centroid = shape.centroid
            coords = shape.coordinates()
        return centroid, coords 

    def __is_iterable(self, obj):
        try:
            iter(obj)
        except:
            #not iterable
            return False
        else:
            #iterable
            return True
    
    def __RelativizeCoordinates(self, array):
        '''A recursive method for taking coordinates and placing them relative to a centroid
                array: an iterable of coordinates
        '''
        if self.__is_iterable(array):
            array = list(array)
            coords = []
            
            for i in range(len(array)):
                if self.__is_iterable(array[i]):
                    array[i] = self.__RelativizeCoordinates(array[i])
                else:
                    coords.append(array[i] - self.centroid[i])
            if coords:
                array = arcpy.Point(*coords)
            else:
                array = arcpy.Array(array)
            
            return array
    
class Parameters:
    def __init__(self, inputList):
        '''Parameters takes an ordered list or dictionary of ordered parameters, and converts them to arcpy parameters.\n
        Arguments:\n
            :param inputList: a list or dictionary containing parameters as strings.
            If the input is a dictionary, the keys must be integers or strings that can be type cast as an integer.'''

        if isinstance(inputList,dict):
            assert self.__isSimpleKey(inputList)
            for key in inputList:
                self.__dict__[inputList[key]] = self.Parameter(int(key))
        
        elif isinstance(inputList,(list,set)):
            for i, param in enumerate(inputList):
                self.__dict__[param] = self.Parameter(i)
        
    def __isSimpleKey(self, aDict):
        for key in aDict:
            try: 
                int(key)
            except:
                return False
        return True

    def __repr__(self):
        aStr = ''
        for key in self.__dict__:
            aStr += f'key: {key},\nvalue: ({self.__dict__[key]}),\n'
        return aStr.rstrip(',\n')
                
    class Parameter:
        def __init__(self, position):
            self.position = position
            self.value = arcpy.GetParameterAsText(position)

        def __repr__(self):
            return f'parameter number: {self.position}, parameter value: {self.value}'

def Message(*args):
    '''Message(*args) simultaneously prints an Arcpy message and a Python print statement. This action is intended to output the same string regardless 
    of being run through Python or ArcGIS.

    :param: *args
    :returns: void'''
    print(*args)
    
    if len(args) > 1:
        aStr = ''
        for item in args:
            aStr += f'{item}, '
        arcpy.AddMessage(aStr.rstrip(', '))
    else: 
        arcpy.AddMessage(args[0])

params = [
    'old_fc',
    'new_fc',
    'newCenter'
]

params = Parameters(params)
ws = arcpy.env.workspace
sr = arcpy.SpatialReference(3005)
xy = params.newCenter.value.split(' ')# arcgis point parameter object is a text string of X,Y separated by a space.
X,Y = [float(val) for val in xy]


Message('Creating new feature class...')
fc = arcpy.Describe(arcpy.management.CreateFeatureclass(ws,params.new_fc.value.split('\\')[-1],'POLYGON',spatial_reference=sr))

Message('Extracting polygons from old feature class...')
with arcpy.da.SearchCursor(params.old_fc.value, ['SHAPE@']) as sc:
    polygons = [row[0] for row in sc]

# Future: use an update cursor on the old feature class
Message('Moving Polygons to new feature class...')
with arcpy.da.InsertCursor(fc.name, ['SHAPE@']) as ic:
    for polygon in polygons:
        f = ForcePolygons(polygon,X, Y)
        Message(f)
        ic.insertRow([f.NewShape])

Message('Done!')