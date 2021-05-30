# AuroraProcessing
This collection of scripts uploads Aurora forecasts as timestamped point data to a Postgres database.

There are two different methods that I used to process the data:
  1) Using Postgres, then utilizing ArcGIS Pro for batch processing of PostGIS point data. This takes a few steps to complete in several files.
  2) Using Postgres, then directly saving raster images directly utilizing GDAL and PostGIS raster.

Both methods The single file included will generate the most recent forecast for the Aurora.
