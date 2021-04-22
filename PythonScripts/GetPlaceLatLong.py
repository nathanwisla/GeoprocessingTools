#!/usr/bin/python
# Edited on 8 & 9 Jul 2014 by Dave MacLean
# Modified on 25-26 Feb 2019 by Dave M for Geoprocessing and Modelling course
# Modified on 26 Feb 2021 by Nathan Wisla


if __name__ == "__main__":

    # Import modules for time:
    from time import gmtime, strftime, localtime
    import time

    # Import a variety of modules for system, URLs, pattern-finding, & time
    from os import getcwd
    import sys
    from urllib import request
    import re
    import datetime

    strBeginTime = str(strftime('%a, %d %b %Y %X', localtime()))
    root = getcwd() # get to the root directory of the file for printing results
    this = sys.argv[0].split('\\')[-1] #the name of the python file
    print (f'This is the name of the script: {this}')
    print (f'Number of arguments: {len(sys.argv)}')     
    print (f'The arguments are: {str(sys.argv)}')         

    # Script arguments
    if len(sys.argv) > 2:
        strTown = sys.argv[1]
        strCountryName = sys.argv[2]
        strCountryCode = 'blank'
        print ('Country, code, & town: ', strCountryName, strCountryCode, strTown)
    else:   # provide defaults
        
        strTown = 'Rome'
        strCountryName = 'Italy'
        strTown = 'Halifax'
        strCountryName = 'Canada'
        print(f'not enough arguments! Using a default: {strTown}, {strCountryName}')


    
    #
    try:
# determine Lat & Long for a community name:

        # variable for unique URL to this town:
        strFindLatLongURL = f'https://www.travelmath.com/cities/{strTown},+{strCountryName}'
        print ("lat-long URL is: ", strFindLatLongURL)

        # open and read URL:
        aResp = request.urlopen(strFindLatLongURL)

        web_pg = str(aResp.read()) #force a str type, is a byte type
        
        # find lat and long based on unique pattern within HTML:
        pattern = '<strong>[Latong]*itude:</strong> (-*\d*\.\d*)</p>' # find elements in the () parenthesis with the format xxxxxx.xxxxxx

        # actually search the webpage:
        latLong = re.findall(pattern,web_pg) # outputs a list when it finds the regex
        
        if len(latLong) > 1:
            strLat = latLong[0] # found it within first element of group!
            strLong = latLong[1]
            #
        else: # no community found, so provide bogus value ... used to catch problems
            print ('No community found')
            strLat = 'blank'
            strLong = strLat
        print (f'Latitude & longitude are: {strLat}, {strLong}')
    # done with "figure out lat & long from town name"
    except Exception as e:
        print (f'Uh oh, {e}')
##


# Report variables
strResultsTXT = f'{root}\\PlaceLatLong.txt'     # to write a file of results
strTimeStamp = str(datetime.datetime.today())
if strTimeStamp.find(".") >= 1: # format needs to be 2014-08-28 13:21:09  (not with the .650000 (tzinfo) info)
    strTimeStamp = strTimeStamp[0:strTimeStamp.find(".")]


print(f'Writing to file {strResultsTXT}')
outFile = open(strResultsTXT,'w')
outFile.write(f'Latitude and Longitude Results for {strTown}, {strCountryName}\n')
outFile.write(f'{"":-^50}\n')
outFile.write(f'{"Latitude:":<10} {strLat:>10}\n{"Longitude:":<10} {strLong:>10}\n')
outFile.write(f'{"":-^50}\n')
outFile.write(f'This report was printed on: {strTimeStamp}\n')
outFile.close()

print ('all done')
