''''
This is a script to extract & save sample points from multiple rasters 
based off a center coordinate and offset.

inputs (in form of a parameter file):
-rasterPath (of raster with clipped extent)
-bandNum
-center
-offset
-searchPath (to find addition rasters, extent doesnt matter)
-bandNum_rest
-outputPath

outputs:
-csv with coordinates and values

example:
python extractSamples_offCenter_multRasters.py ./params/test_param_file.txt
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
				rasterPath_extent = var
			elif title.lower() == 'bandnumber':
				bandNum_extent = int(var)
			elif title.lower() == 'center':
				centerCoords = [float(i) for i in var.split(',')]
			elif title.lower() == 'offset':
				offset = int(var)
			elif title.lower() == 'searchpath':
				searchPath = var
				rasterPaths_nonExtent = glob.glob(searchPath)
			elif title.lower() == 'bandnum_rest':
				bandNums_nonExtent = [int(var)]*len(rasterPaths_nonExtent)
			elif title.lower() == 'outputpath':
				outputPath = var
	txt.close()
	return rasterPath_extent, bandNum_extent,centerCoords, offset, rasterPaths_nonExtent, bandNums_nonExtent, outputPath

def extractSampleCoords(rasterPath_extent, bandNum_extent, centerCoords, offset, rasterPaths_nonExtent, bandNums_nonExtent, outputPath):
	#open clipped raster
	ds_extent = gdal.Open(rasterPath_extent)
	band = ds_extent.GetRasterBand(bandNum_extent) 
	bandArray = band.ReadAsArray()
	noData = band.GetNoDataValue()

	#extract random coords
	bands = [bandNum_extent] + bandNums_nonExtent
	rasters = [rasterPath_extent] + rasterPaths_nonExtent
	print "Extracting samples..."
	
	all_sample_values = np.zeros([len(rasters), offset**2]) 
	for ind,raster in enumerate(rasters):
		ds = gdal.Open(raster)
		transform = ds.GetGeoTransform()
		values, coordinates = vf.extract_kernel_and_coords(ds,centerCoords[0],centerCoords[1],offset,offset,bands[ind],transform)
		all_sample_values[ind,:] = values.flatten()

	#save data
	print "Saving Data..."
	labels = ['X', 'Y'] + [os.path.splitext(os.path.basename(i))[0].upper() for i in rasters]
	sample_array = np.zeros(offset**2,dtype=[(l,'f8') for l in labels]) #structured array
	sample_array['X'] = coordinates[:,:,0].flatten()
	sample_array['Y'] = coordinates[:,:,1].flatten()
	for ind,label in enumerate(labels[2:]):
		sample_array[label] = all_sample_values[ind]
	np.savetxt(outputPath, sample_array, delimiter=",", comments="", header=",".join(i for i in sample_array.dtype.names), fmt='%s')
	print " Done!"


def main(paramFile):
	rasterPath_extent, bandNum_extent, centerCoords, offset, rasterPaths_nonExtent, bandNums_nonExtent, outputPath = getTxt(paramFile)
	extractSampleCoords(rasterPath_extent, bandNum_extent, centerCoords, offset, rasterPaths_nonExtent, bandNums_nonExtent, outputPath)


if __name__ == '__main__':
	args = sys.argv
	if os.path.exists(args[1]):
		main(args[1])
	else:
		sys.exit('\nParameter File Not Found. Exiting.')