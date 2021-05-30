# Open Source Direct Processing
This script uploads a row of raster data into PostGIS raster, then generates a PNG image that gets saved into any directory.

This script runs **only if** the following packages are installed:
  - GDAL
  - Pillow
  - Psycopg2
  - SciPy

You can install GDAL and SciPy through the Python Anaconda (Conda) download manager, so this file heavily recommends that you use Conda instead of PIP to install packages or you might have a hard time getting GDAL or SciPy onto your Python Environment. 
