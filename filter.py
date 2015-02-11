'''
This is a wrapper to create filtered rasters.

INPUTS (in parameter file):
-inputPath
-bandNum
-kernel
-outputPath

OUTPUT:
-saved filtered raster

EXAMPLE:
python filter.py path/to/paramfile.txt
'''

import gdal, os, sys
from scipy import ndimage
from gdalconst import *

def getTxt(file):
	'''reads parameter file & extracts inputs'''
	txt = open(file, 'r')
	next(txt)

	for line in txt:
		if not line.startswith('#'):
			lineitems = line.split(':')
			title = lineitems[0].strip(' \n')
			var = lineitems[1].strip(' \n')

			if title.lower() == 'inputpath':
				inputPath = var
			if title.lower() == 'datatype':
				if var.lower() == 'int16':
					dataType = GDT_Int16
				elif var.lower() == 'int32':
					dataType = GDT_Int32
				elif var.lower() == 'byte':
					dataType = GDT_Byte
			elif title.lower() == 'nodata':
				noData = int(var)
			elif title.lower() == 'bandnumber':
				bandNum = int(var)
			elif title.lower() == 'kernel':
				kernel = int(var)
			elif title.lower() == 'outputpath':
				outputPath = var
	try: #if nodata value not defined, set to none
		noData
	except NameError:
		noData = None
	txt.close()
	return inputPath, dataType, noData, bandNum, kernel, outputPath

def main(paramFile):
	#extract inputs
	inputPath, dataType, noData, bandNum, kernel, outputPath = getTxt(paramFile)

	#open images, read band
	print "Reading raster: ", inputPath, " ..."
	ds = gdal.Open(inputPath)
	band = ds.GetRasterBand(bandNum)
	bandArray = band.ReadAsArray()

	#apply median filter
	print "Applying " + str(kernel) + "X" + str(kernel) + " median filter..."
	bandArray_filtered = ndimage.median_filter(bandArray,kernel)

	#get image attributes
	print "Saving new filtered raster..."
	driver = ds.GetDriver()
	projection = ds.GetProjection()
	transform = ds.GetGeoTransform()
	noData = band.GetNoDataValue()
	cols = ds.RasterXSize
	rows = ds.RasterYSize
		
	#create new image
	outDs = driver.Create(outputPath, cols, rows, 1, dataType)
	if outDs is None:
		print 'Could not create ' + outputPath
		sys.exit(1)
			
	#write the data
	outBand = outDs.GetRasterBand(1)
	outBand.WriteArray(bandArray_filtered)

	#flush data to disk
	outBand.FlushCache()
	if noData:
		outBand.SetNoDataValue(noData)

	#georeference the image and set the projectionr	
	outDs.SetGeoTransform(transform)
	outDs.SetProjection(projection)

	print " Done! \nRaster available here:", outputPath



if __name__ == '__main__':
	args = sys.argv
	if os.path.exists(args[1]):
		main(args[1])
	else:
		sys.exit('\nParameter File Not Found. Exiting.')
