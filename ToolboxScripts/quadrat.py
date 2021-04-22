import arcpy, os
from tkinter import *

class Quadrat():

    def __init__(self, workspace, dataset, studyArea, side, significance, chkOpt, useScratch=True):
        '''Quadrat()
               workspace    - The workspace that all tasks will be done in
               dataset      - The point dataset that will be operated on
               studyArea    - The shapefile that will be operated within
               side         - The quadrat side length
               significance - The significance statistic (1, 5, 10)
               chkOpt       - Select whether or not to used an optimized quadrat
        '''
        self.root = workspace
        self.dataset = dataset
        self.studyArea = studyArea
        self.quadSideLength = side
        self.significance = significance * 0.01 
        self.chkOpt = True if chkOpt == 'true' else False # Really, esri?
        
        # Get the file name of the dataset without the . extension (is called a few times)
        self.filename = os.path.basename(dataset).split('.')[0]
        self.areaname = os.path.basename(studyArea).split('.')[0]
        self.wsroot = os.path.basename(workspace)
        # SET ENVIRONMENT==============================================
        self.SetEnv()
        self.ws = arcpy.env.scratchFolder if useScratch else arcpy.env.workspace
        # =============================================================
        self.pointCount = self.GetPoints()
        self.area, self.areaMsg = self.GetArea()
        self.optSize, self.optSizeMsg = self.GetOptQuadrat()
        self.quadSideLength = self.GetQuadLength()

        # =============================================================
        # Build data layers
        # =============================================================
        self.fishnetClip = self.BuildFishnet()      
        self.intersected = self.BuildIntersect()
        self.intersectFreq = self.BuildFreqTable_intersect()
        self.frequencyFreq = self.BuildFreqTable_freq()

        # =============================================================
        # Summarize statistics
        # =============================================================        
        self.quadCount, self.quadCountMsg = self.GetQuadCount()    
        self.nonEmptyCount, self.nonEmptyMsg = self.GetNonEmptyQuadCount()
        self.emptyCount, self.emptyMsg = self.GetEmptyQuadCount()
        self.lambda_, self.lambdaMsg = self.GetLambda()
        self.variance, self.varianceMsg = self.GetVariance()
        self.t, self.tMsg = self.GetTTest()
        self.crit = self.GetCritValues()
        self.pointPattern, self.pointPatternMsg = self.GetPointPattern(self.crit)
        self.SetParameters()
        
# ==================================================================================
# ARCPY BUILDERS
# ==================================================================================

    def BuildIntersect(self):
        ''' BuildIntersect() -> ouputPath
            builds an intersect between the dataset points and the fishnet.
            returns output path of the intersect
        '''
        outputName = f'{self.ws}{os.sep}intersected_{self.filename}_{int(self.quadSideLength)}.shp'
        arcpy.analysis.Intersect([self.dataset, self.fishnetClip],outputName)
        return outputName
    

    def BuildFishnet(self):
        '''BuildFishnet() -> outputPath (clipped fishnet)
           Builds and then clips a fishnet around the study area.
        '''
        desc = arcpy.Describe(self.studyArea)
        ext = desc.extent
        cellsize = self.quadSideLength

        origin = f'{ext.XMin - (cellsize/2)} {ext.YMin - (cellsize/2)}'
        orientation = f'{ext.XMin - (cellsize/2)} {ext.YMax + (cellsize/2)}'
        opposite = f'{ext.XMax + (cellsize/2)} {ext.YMax + (cellsize/2)}'

        # The fishnet file name creates a different file name for each
        # point file and each quadrat size, adding them to the filename
        name = f'{self.ws}{os.sep}fishnet_{self.filename}_{int(cellsize)}.shp'

        fishnet = arcpy.management.CreateFishnet(\
            name,\
            origin,\
            orientation,\
            cellsize,\
            cellsize,\
            '0',\
            '0',\
            opposite,\
            'false',\
            '',\
            'POLYGON'\
            )
        
        fishnetClip  = f'{self.ws}{os.sep}fishnetClip_{self.filename}_{int(cellsize)}.shp'

        arcpy.analysis.Clip(fishnet,studyArea,fishnetClip)

        return fishnetClip


    def BuildFreqTable_intersect(self):
        '''BuildFreqTable_intersect() -> outputPath
           Builds the frequency table that describes the intersect between the dataset and the fishnet.
        '''
        intersectFreq = f'{self.ws}{os.sep}freq_{int(self.quadSideLength)}.dbf'
        arcpy.analysis.Frequency(self.intersected, intersectFreq, ['FID_fishne'])
        return intersectFreq
        

    def BuildFreqTable_freq(self):
        '''BuildFreqTable_freq() -> outputPath
           Builds the frequency table describing the frequency of quadrats that have x points.
        '''
        frequencyFreq = f'{self.ws}{os.sep}freq2_{int(self.quadSideLength)}.dbf'
        arcpy.analysis.Frequency(self.intersectFreq, frequencyFreq,['FREQUENCY'])
        return frequencyFreq

# ==================================================================================
# GETTERS
# ==================================================================================  


    def GetArea(self):
        '''GetArea() -> totalArea (sq. m), msg (sq. km)
           Gets the total area of the study area.
        '''
        totalArea = 0

        with arcpy.da.SearchCursor(self.studyArea,['AREA']) as cursor:
            for row in cursor:
                totalArea += row[0]

        totalArea = totalArea
        msg = f'The total area is {totalArea/1000000:.2f} sq. km.\n'
        return totalArea, msg


    def GetCritValues(self):
        '''GetCritValues() -> crit
           Gets the critical values based on the significance chosen.
        '''
        significance = self.significance
        if significance == 0.01:
            crit = 2.58
        elif significance == 0.05:
            crit = 1.96
        elif significance == 0.1:
            crit = 1.645
        return crit
    

    def GetEmptyQuadCount(self):
        '''GetEmptyQuadCount() -> emptyCount, msg
           Gets the total empty quadrats in the study area.
        '''
        emptyCount = self.quadCount - self.nonEmptyCount
        msg = f'The number of empty quadrats is {emptyCount}.\n'
        return emptyCount, msg

    
    def GetLambda(self):
        '''GetLambda() -> lambda, msg
           Gets the lambda value (mean value of points per quadrat).
        '''
        l = self.pointCount / self.quadCount
        msg = f'Lambda = {l:.2f}\n'
        return l, msg
    

    def GetNonEmptyQuadCount(self):
        '''GetNonEmptyQuadCount() -> count, msg
           Gets the total non-empty quadrats in the study area
        '''
        nonEmptyCount = arcpy.management.GetCount(self.intersectFreq)
        nonEmptyCount = int(nonEmptyCount.getOutput(0))
        msg = f'There are {nonEmptyCount} quadrats with points.\n'
        return nonEmptyCount, msg
    

    def GetOptQuadrat(self):
        '''GetOptQuadrat() -> optSize (meters), msg (km)
           Gets the optimal quadrat side length in the study area.
        '''
        optSize = (2 * self.area / self.pointCount) **0.5
        msg = f'The optimal size of the quadrat is {optSize/1000:.2f} km.\n'
        return optSize, msg


    def GetPointPattern(self,crit):
        '''GetEmptyQuadCount(crit) -> pattern, msg
           Gets the pattern classification based on a statistical t-test's critical values.
        '''
        if self.t < -crit:
            pattern = 'regular'
            
        elif self.t > crit:
            pattern = 'clustered'
            
        else:
            pattern = 'random'
        
        msg = f'The data pattern is {pattern}\n'
        return pattern, msg


    def GetPoints(self):
        '''GetPoints() -> pointCount
           Gets the total amount of points in the dataset.
        '''
        pointCount = arcpy.management.GetCount(self.dataset)
        pointCount = int(pointCount.getOutput(0))
        return pointCount
    

    def GetQuadCount(self):
        '''GetQuadCount() -> quadCcount, msg
           Gets the total quadrats in the study area, based on the fishnet.
        '''
        quadCount = arcpy.management.GetCount(self.fishnetClip)
        quadCount = int(quadCount.getOutput(0))
        msg = f'There are {quadCount} quadrats.\n'
        return quadCount, msg

    def GetQuadLength(self):
        '''GetQuadLength() -> optSide
           Selects the quadrat side length depending if the checkbox was marked.
        '''
        side = self.quadSideLength
        optSide = self.optSize
        chkOpt = self.chkOpt
        return optSide if chkOpt else side * 1000


    def GetTTest(self):
        '''GetTTest() -> tScore, msg
           Gets the statistical t-test result for the points in the study area.
        '''
        # Test Statistic T = (variance - lambda)/sqrt(2/(k-1))
        tScore = (self.variance - self.lambda_) / ((2 / (self.quadCount -1)) **0.5)
        msg = f't-score = {tScore:.2f}\n'
        return tScore, msg


    def GetVariance(self):
        '''GetVariance() -> variance, msg
           Gets the variance used to calculate the statistical t-test.
        '''       
        lambda_ = self.lambda_
        variance = ((lambda_) **2) * self.emptyCount

        with arcpy.da.SearchCursor(self.frequencyFreq,['FREQ_GP','FREQUENCY']) as cursor:
            for row in cursor:
                x = row[1]
                fx = row[0]
                variance += ((x - lambda_) **2) * fx

        variance = variance / self.quadCount
        msg = f'Variance = {variance:.2f}\n'
        return variance, msg


# ==================================================================================
# SETTERS
# ==================================================================================
    def SetEnv(self):
        '''setEnv()
           Sets the environment and the scratch workspace.
        '''       
        ws = self.root
        arcpy.env.workspace = ws
        arcpy.env.scratchWorkspace = ws

        arcpy.env.overwriteOutput = True
        

    def SetParameters(self):
        '''SetParameters()
           Sets the output parameters of the tool.
        '''
        arcpy.SetParameterAsText(6, self.dataset)
        arcpy.SetParameterAsText(7, self.studyArea)
        arcpy.SetParameterAsText(8, self.fishnetClip)

# ==================================================================================
# toString
# ==================================================================================

    def __repr__(self):
        aStr = f'\n{"":*^50}\n {"The program Quadrat Analysis has started":^50}\n{"":*^50}\n'
        aStr +=\
             f'Workspace: {self.wsroot}\n'\
             f'Point data set: {self.filename}\n'\
             f'Study area: {self.areaname}\n'\
             f'Quadrat side length: {self.quadSideLength}\n'\
             f'Significance level: {self.significance*100}%\n'\
             f'Optimal side length: {self.chkOpt}\n'\
             f'\n{"":*^50}\n{"SUMMARY STATISTICS":*^50}\n{"":*^50}\n'
        aStr += self.areaMsg
        aStr += self.optSizeMsg
        aStr += self.quadCountMsg
        aStr += self.nonEmptyMsg
        aStr += self.emptyMsg
        aStr += self.lambdaMsg
        aStr += self.varianceMsg
        aStr += self.tMsg
        aStr += self.pointPatternMsg
              
        
        return aStr

# =====================================================================================
# OUT OF CLASS TKINTER (ArcGIS Pro was crashing)
# =====================================================================================

def ShowResults(*args):
    '''ShowResults(*args)
       Displays the results of the quadrat operation.
    '''
    descText = \
            [\
            'Point dataset',\
            'Number of points',\
            'Number of quadrats',\
            'Applied quadrat size (km)',\
            'Optimal quadrat size (km)',\
            'Average number of points per quadrat',\
            'Variance',\
            'Test statistic t',\
            'Pattern',\
            'Significance level'\
            ]
            
    window = Tk()
    window.title('Results')
    window.geometry('330x320')
    frame = Frame(window)
    
    # Loop over all arguments in function, only have to create columns
    for i, arg in enumerate(args):
        # Round down all float values with this handy ternary
        arg = f'{arg:.2f}' if isinstance(arg,float) else arg

        lbl1 = Label(frame,background='white',foreground='blue',\
                     text=descText[i],anchor='w')
        lbl1.grid(row=i,column=0,sticky=W+E)

        lbl2 = Label(frame,background='yellow',foreground='red',\
                     text=arg, anchor='w')
        lbl2.grid(row=i,column=1,sticky=W+E)

    button = Button(frame, background='DeepSkyBlue', foreground='red',\
                    text='Exit', font='bold', command=window.destroy)
    button.grid(row=i+1,column=0,columnspan=2,sticky=W+E)
   
    frame.pack()
    window.mainloop()

# =====================================================================================
# Initialize parameters and run script
# =====================================================================================

ws = arcpy.GetParameterAsText(0)
dataset = arcpy.GetParameterAsText(1)
studyArea = arcpy.GetParameterAsText(2)
side = float(arcpy.GetParameterAsText(3))
significance = int(arcpy.GetParameterAsText(4))
chkOpt = arcpy.GetParameterAsText(5)

q = Quadrat(ws,dataset,studyArea,side,significance,chkOpt)

ShowResults(\
            q.filename,\
            q.pointCount,\
            q.quadCount,\
            q.quadSideLength/1000,\
            q.optSize/1000,\
            q.lambda_,\
            q.variance,\
            q.t,\
            q.pointPattern,\
            q.significance\
            )

arcpy.AddMessage(q)
