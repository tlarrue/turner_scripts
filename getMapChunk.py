
''''
This is a script to extract an array of pixels from a raster, and save as a csv.

inputs (in form of a parameter file):
-rasterPath 
-bandNumber
-center
-offset
-outputPath

outputs:
-csv with array of values

example:
python getMapChunk.py ./params/test_param_file.txt
'''
import sys, os, gdal, glob
import numpy as np
import validation_funs as vf

def getTxt(file):
	'''reads parameter file & extracts inputs'''
	txt = open(file, 'r')
	next(txt)

	for line in txt:
		if not line.startswith('#'):
			lineitems = line.split(':')
			title = lineitems[0].strip(' \n')
			var = lineitems[1].strip(' \n')

			if title.lower() == 'rasterpath':
				rasterPath = var
			elif title.lower() == 'bandnumber':
				bandNum = int(var)
			elif title.lower() == 'center':
				centerCoords = [float(i) for i in var.split(',')]
			elif title.lower() == 'offset':
				offset = int(var)
			elif title.lower() == 'outputpath':
				outputPath = var
	txt.close()
	return rasterPath, bandNum,centerCoords, offset, outputPath

def extractSampleCoords(rasterPath, bandNum, centerCoords, offset, outputPath):
	print "Extracting samples..."
	
	# all_sample_values = np.zeros([len(rasters), offset**2]) 
	ds = gdal.Open(rasterPath)
	transform = ds.GetGeoTransform()
	values = vf.extract_kernel(ds,centerCoords[0],centerCoords[1],offset,offset,bandNum,transform)

	#save data
	print "Saving Data..."
	np.savetxt(outputPath, values, delimiter=",", fmt='%i')
	print " Done!"

def main(paramFile):
	rasterPath, bandNum,centerCoords, offset, outputPath = getTxt(paramFile)
	extractSampleCoords(rasterPath, bandNum, centerCoords, offset, outputPath)


if __name__ == '__main__':
	args = sys.argv
	if os.path.exists(args[1]):
		main(args[1])
	else:
		sys.exit('\nParameter File Not Found. Exiting.')