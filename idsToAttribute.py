'''
Convert raster of ID's to raster of attribute from CSV file.
Used with image segmentation. 
This version using np.vectorize.

INPUTS (command line):
-csv
-raster of ID's
-attribute name
-no data value
-outputPath

OUTPUTS:
-raster of attributes

EXAMPLE:
python idsToAttribute.py /path/to/input.csv AGE_DOM /path/to/idRaster.bsq 0 /path/to/attrRaster.bsq
'''

import csv, gdal, sys
import numpy as np
from gdalconst import *

def lookup(d, key, default):
	try:
		value = d[key]
	except KeyError:
		value = default
	return value

def main(args):

	inputCsv = args[1]
	attribute = args[2]
	idRaster = args[3]
	noData = float(args[4])
	outputPath = args[5]

	#get lookup dictionary of attributes
	print "\nReading CSV data..."
	csvfile = open(inputCsv, 'r')
	data = list(csv.DictReader(csvfile))
	csvfile.close()
	pairs = {int(i['ID']): float(i[attribute]) for i in data}

	#read raster of ids
	print "\nOpening ID Raster..."
	ds = gdal.Open(idRaster)
	band = ds.GetRasterBand(1)
	idArray = band.ReadAsArray()

	#convert array to attribute values
	print "\nConverting Raster to Attribute..."
	vlookup = np.vectorize(lookup)
	attributeArray = vlookup(pairs, idArray, noData)

	#save new raster
	print "\nSaving Converted Raster..."
	driver = ds.GetDriver()
	projection = ds.GetProjection()
	transform = ds.GetGeoTransform()
	cols = ds.RasterXSize
	rows = ds.RasterYSize
	outDs = driver.Create(outputPath, cols, rows, 1, GDT_Int16)
	if outDs is None:
		print 'Could not create ' + outputPath
		sys.exit(1)

	#write the data
	outBand = outDs.GetRasterBand(1)
	outBand.WriteArray(attributeArray)

	#flush data to disk
	outBand.FlushCache()
	outBand.SetNoDataValue(noData)

	#georeference the image and set the projection
	outDs.SetGeoTransform(transform)
	outDs.SetProjection(projection)
	print " Done! \nRaster available here:", outputPath


if __name__ == '__main__':
	args = sys.argv
	main(args)








