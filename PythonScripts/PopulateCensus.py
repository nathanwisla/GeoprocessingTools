#===================================================================
# Name    : PopulateCensus.py
# Purpose : to select multiple fields from census data, make a new
#           shapefile with all relevant fields in them so they are
#           relativized and ready to perform analysis with.
# Author  : Nathan Wisla
# Date    : February 19, 2021
#===================================================================
# NOTE: Must be run in Python 3.7 or newer due to dictionaries becoming ordered
# SCROLL DOWN TO ENTER THE FIELDS YOU WISH TO POPULATE

import arcpy

# use cursors to create relative tables for selected fields in
# a dissemination area dataset

ws = 'ENTER WORKSPACE HERE'
arcpy.env.workspace = ws
arcpy.env.overwriteOutput = True
spatialRef = arcpy.Describe('dissemination_areas').spatialReference

EXCL_QUERY = '''HH > 0 AND ECYBASHPOP > 0 AND ECYHOMEPOP > 0''' # change this to omit denominators for relative variables that may be zero
clipFile = 'ENTER CLIPPING POLYGON NAME HERE'


def GetCrits(inDict):

    masterList = []
    indices = []
    loc = 0
    for key in inDict:
        fieldVar = inDict[key]['VARS']
        if fieldVar != None:
            if len(fieldVar) > 1:
                indices.append(loc)
            loc += len(fieldVar)
            
            for item in fieldVar:
                masterList.append(item)
                
    indices.append(loc)
    
    return masterList, indices


def cr_fc(name, pairs):
    disArea = arcpy.management.CreateFeatureclass(
    ws, name,'POLYGON',spatial_reference=spatialRef)

    disArea = disArea[0]
    # populate the feature class created
    for pair in pairs:
        arcpy.management.AddField(disArea,pair[0],pair[1])
    return disArea

       
def relativize(aList):
    return sum(aList[:-1])/aList[-1]


## 0. DO NOT CHANGE THE FIRST ENTRY!
## 1. ALL DATA ENTERED NEEDS TO FOLLOW THE DICTIONARY FORMAT AS FOLLOWS:
##         {<field>: {'TYPE':'TEXT'|'DOUBLE'|'LONG'|etc., 'VARS':[]}}
## 2. Add fields that do not need to be relativized after the first entry (place between the separators)
## 3. All variables 'VAR' need to be lists, even if there is only one entry
## 4. All fields that need to be relativized go after the last relativized variable
##      a) The denominator is the last item in each list, and you can sum numerators by
##         putting extra entries before the denominator!
## MUST BE RUN IN PYTHON 3.7 OR NEWER, ELSE THE DICTIONARY WILL BECOME UNORDERED
FIELD_DICT = {
    'SHAPE@'                        :{'TYPE': None   ,'VARS':['SHAPE@']}                   ,\
    ############################################################################################
    'RG_ABBREV'                     :{'TYPE':'TEXT'  ,'VARS':['RG_ABBREV']}                 ,\
    'avgIncome'                     :{'TYPE':'DOUBLE','VARS':['ECYHRIAVG']}                 ,\
    'employmentRate'                :{'TYPE':'DOUBLE','VARS':['ECYACTER']}                  ,\
    ############################################################################################
    'transport_EXP'                 :{'TYPE':'DOUBLE','VARS':['HSTR001S','HH']}             ,\
    'populationChange'              :{'TYPE':'DOUBLE','VARS':['ECYBASHPOP','P5YBASHPOP']}   ,\
    'daytime_POP'                   :{'TYPE':'DOUBLE','VARS':['ECYWORKPOP','ECYHOMEPOP']}   ,\
    'separatedHH_POP'               :{'TYPE':'DOUBLE','VARS':['ECYMARSEP','ECYBASHPOP']}    ,\
    'immig_POP'                     :{'TYPE':'DOUBLE','VARS':['ECYTIMIMGT','ECYBASHPOP']}   ,\
    'vachome_EXP'                   :{'TYPE':'DOUBLE','VARS':['HSSH041','HH']}              ,\
    'HH5Plus_POP'                   :{'TYPE':'DOUBLE','VARS':['ECYHSZ5PER','ECYBASHPOP']}   ,\
    'liveSports_EXP'                :{'TYPE':'DOUBLE','VARS':['HSRE063A','HH']}             ,\
    'packageTrips_EXP'              :{'TYPE':'DOUBLE','VARS':['HSRE074','HH']}              ,\
    'tradeCertificates_POP'         :{'TYPE':'DOUBLE','VARS':['ECYEDAATCD','ECYBASHPOP']}   ,\
    'religious_POP'                 :{'TYPE':'DOUBLE','VARS':['ECYRELCHR','ECYBASHPOP']}    ,\
    'multilingual_POP'              :{'TYPE':'DOUBLE','VARS':['ECYMOTMULT','ECYBASHPOP']}   ,\
    'rent_EXP'                      :{'TYPE':'DOUBLE','VARS':['HSSH004','HH']}              ,\
    'camper_EXP'                    :{'TYPE':'DOUBLE','VARS':['HSRV001E','HH']}             ,\
    'sportswear_EXP'                :{'TYPE':'DOUBLE','VARS':['HSCF001B','HSCM001B','HH']}  ,\
    'cameras_EXP'                   :{'TYPE':'DOUBLE','VARS':['HSRE017','HH']}              ,\
    'airportParking_EXP'            :{'TYPE':'DOUBLE','VARS':['HSRV016','HH']}              ,\
    'publicTransit_EXP'             :{'TYPE':'DOUBLE','VARS':['ECYTRAPUBL','ECYBASHHD']}    ,\
    'hotels_EXP'                    :{'TYPE':'DOUBLE','VARS':['HSSH051','HH']}              ,\
    'theatres_EXP'                  :{'TYPE':'DOUBLE','VARS':['HSRE062','HH']}              ,\
    'recFacilities_EXP'             :{'TYPE':'DOUBLE','VARS':['HSRE070','HH']}              ,\
    'tuition_EXP'                   :{'TYPE':'DOUBLE','VARS':['HSED005','HH']}              ,\
    'workFromNoFixedLocation_EXP'   :{'TYPE':'DOUBLE','VARS':['ECYPOWNFIX','ECYBASHHD']}    ,\
    'occupationArtsSports_POP'      :{'TYPE':'DOUBLE','VARS':['ECYOCCARTS','ECYBASHHD']}    ,\
    'driveway_EXP'                  :{'TYPE':'DOUBLE','VARS':['HSRM005','HH']}              ,\
    'childCare_EXP'                 :{'TYPE':'DOUBLE','VARS':['HSCC002','HH']}
      }

print('gathering critical indices and making lists...')
# Create a list of field definitions for the new attribute table
FIELD_PAIRS = [[field,FIELD_DICT[field]['TYPE']] for field in FIELD_DICT if FIELD_DICT[field]['TYPE'] != None]
# Create the fields and indices that will be going through the search cursor
SEARCH_FIELDS, indices = GetCrits(FIELD_DICT)
# Create fields for the new attribute table
NEW_FIELDS = [field for field in FIELD_DICT]
print('done!')


print(f'creating a new feature class with {len(FIELD_DICT)} variable entries...')
disArea = cr_fc('DA_relative',FIELD_PAIRS)
#disArea = 'DA_relative'
print('feature class created!')




print('baking...')
with arcpy.da.SearchCursor('dissemination_areas',SEARCH_FIELDS,EXCL_QUERY)\
                           as sc:
    with arcpy.da.InsertCursor(disArea,\
                               NEW_FIELDS)\
                               as ic:
        
        for row in sc:
            calculated = []
            

            # read the first index and the second index from the
            # indices list, which will omit the first entries
            for j in range(len(indices) - 1):
                i0 = indices[j]
                i = indices[j+1]

                calculated.append(relativize(row[i0:i]))

            ic.insertRow([*(item for item in row[0:4]),*(item for item in calculated)])

print('cooling...')
print('adding near features...')
arcpy.analysis.Near(disArea, 'shopping_centres')
print('clipping features...')
try:
    arcpy.analysis.Clip(disArea,clipFile,f'DA_{clipFile}')
except:
    print('no clipping feature found! Leaving the entire dissemination area shapefile')
                
print('ding!')        

