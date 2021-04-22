#===================================================================
# Name    : DistanceWithin.py
# Purpose : to select all points within a certain radius of another
#           set of points to create a table with that information
# Author  : Nathan Wisla
# Date    : February 4, 2021
#===================================================================

from arcpy import *


class DistanceWithin():

    def __init__(self, ws, storeFC, custFC, searchDist):
        '''DistanceWithin(ws, storeFC, custFC, searchDist)
           A class that calculates the percent count of all feature classes (custFC)
           within a specified radius of another class (storeFC).
        '''

        self.storeFC = storeFC
        self.custFC = custFC
        self.searchDist = searchDist
        tableName = 'PercentWithinDistance'

        self.SetEnv(ws)

        # ======================================================
        self.percent = self.SelectPercent()
        fields, self.fieldsMsg = self.cr_table(tableName,['DISTANCE_KM','LONG'],['PERCENT','DOUBLE'])
        self.insertMsg = self.InsertInto(tableName, fields, searchDist, self.percent)

        
    def SetEnv(self, ws):
        env.workspace = ws
        env.scratchWorkspace = ws
        env.overwriteOutput = True

    # Calculate the percent of customers within a
    # given distance of a particular store.
    def SelectPercent(self):
        '''SelectPercent() -> percent
           Selects feature classes within a search radius and calculates
               a percentage of the selection with the entire feature class.
        '''
        storeFC = self.storeFC
        custFC = self.custFC
        withinDist = self.searchDist
        # clear any selections that may have been made
        management.SelectLayerByAttribute(custFC,'CLEAR_SELECTION')
        # get the total count first
        total = int(management.GetCount(custFC)[0])

        selection = management.SelectLayerByLocation(\
            custFC,\
            'WITHIN_A_DISTANCE',\
            storeFC,\
            withinDist*1000)

        # get the count of selected features
        selCount = int(management.GetCount(selection)[0])

        return selCount / total * 100


    # create a table to store the data
    # uses *args to insert all fields as pairs:
    #                                   [field name, field datatype]
    def cr_table(self, tableName,*fields):
        '''cr_table(tableName, *fields) -> fields, msg
           Creates a table and populates it with fields inputted as
               pairs of [field name, field datatype]
        '''

        management.CreateTable(ws,tableName)
        msg = f'CREATED TABLE {tableName} WITH FIELDS\n----------------\n'
        
        for field in fields:
            management.AddField(tableName, field[0], field[1])
            msg += f'{field[0]}: {field[1]}\n'

        return [field[0] for field in fields], msg


    # create an insert cursor to make new rows
    # use with__as to create a temporary cursor so it doesn't need to be deleted
    def InsertInto(self, tableName, fields, *rowContents):
        '''InsertInto(tableName, fields, *rowContents) -> msg
           Inserts rows into an empty table, outputs a success message
        '''
        with da.InsertCursor(tableName, fields) as cursor:
            cursor.insertRow(rowContents)
        
        msg = 'Insert successful!\n'
        return msg


    def __repr__(self):
        aStr = ''
        aStr += f'Searching for features in {self.custFC} within \n'\
                f'{self.searchDist} km of selected {self.storeFC}...\n\n'

        aStr += self.fieldsMsg
        aStr += f'Inserting rows... {self.insertMsg}\n'
        aStr += 'script complete!'

        aStr += f'\n\n{self.percent:.2f} percent of the {self.custFC} features were selected\n'\
                f'in this operation.'

        return aStr


#============================================================================
# run the script

ws = GetParameterAsText(0)
storeFC = GetParameterAsText(1)
custFC = GetParameterAsText(2)
searchDist = int(GetParameterAsText(3))

search = DistanceWithin(ws, storeFC, custFC, searchDist)
AddMessage(search)


