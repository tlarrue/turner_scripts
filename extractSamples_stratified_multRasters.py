
''''
This is a script to extract & save sample points from multiple rasters.

inputs (in form of a parameter file):
-rasterPath (of raster with clipped extent)
-bandNum
-numSamples (for each bin)
-bins (ex.0-10,11-20,20-30) INCLUSIVE
-searchPath (to find addition rasters, extent doesnt matter)
-bandNum_rest
-outputPath

outputs:
-csv with random coordinates and values

example:
python extractSamples_statified_multRasters.py ./params/test_param_file.txt
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
			elif title.lower() == 'numsamples':
				numSamples = int(var)
			elif title.lower() == 'bins':
				listOfRanges = var.split(',')
				bins = [i.split('-') for i in listOfRanges] 
				bins = [(int(j[0]),int(j[1])) for j in bins] #list of tuples
			elif title.lower() == 'searchpath':
				searchPath = var
				rasterPaths_nonExtent = glob.glob(searchPath)
			elif title.lower() == 'bandnum_rest':
				bandNums_nonExtent = [int(var)]*len(rasterPaths_nonExtent)
			elif title.lower() == 'outputpath': 
				outputPath = var
	txt.close()
	return rasterPath_extent, bandNum_extent, numSamples, bins, rasterPaths_nonExtent, bandNums_nonExtent, outputPath

def extractSampleCoords(rasterPath_extent, bandNum_extent, numStrat, bins, rasterPaths_nonExtent, bandNums_nonExtent, outputPath):
	#open clipped raster
	ds_extent = gdal.Open(rasterPath_extent)
	(upper_left_x, x_size, x_rotation, upper_left_y, y_rotation, y_size) = ds_extent.GetGeoTransform()
	band = ds_extent.GetRasterBand(bandNum_extent) 
	bandArray = band.ReadAsArray()
	noData = band.GetNoDataValue()

	bands = [bandNum_extent] + bandNums_nonExtent
	rasters = [rasterPath_extent] + rasterPaths_nonExtent

	#get candidate coordinates from clipped raster
	all_sample_values = [[] for r in rasters]
	all_x = []
	all_y = []
	print "BINS: ", bins
	for bind,bin in enumerate(bins):
		(y_index, x_index) = np.where((bandArray >= bin[0]) & (bandArray <= bin[1]))

		x_coords = x_index * x_size + upper_left_x + (x_size / 2) #add half the cell size to center the point
		y_coords = y_index * y_size + upper_left_y + (y_size / 2) 

		#extract random coords
		print "Extracting random samples for Bin " + str(bind+1) + " ..."
		sample_indeces = np.random.choice(range(len(x_coords)), numStrat[bind], replace=False)
        	all_x.extend(list(x_coords[sample_indeces]))
        	all_y.extend(list(y_coords[sample_indeces]))


        	for rind,raster in enumerate(rasters):
        		ds = gdal.Open(raster)
        		transform = ds.GetGeoTransform()
        		samples = []
        		for sind,s in enumerate(sample_indeces):
        			samples.append(vf.extract_kernel(ds,x_coords[s],y_coords[s],1,1,bands[rind],transform)[0][0])
        		all_sample_values[rind].extend(samples)

    	#save data
    	print "Saving Data..."
    	labels = ['X', 'Y'] + [os.path.splitext(os.path.basename(i))[0].upper() for i in rasters]
    	sample_array = np.zeros(np.sum(numStrat),dtype=[(l,'f8') for l in labels]) #structured array
	sample_array['X'] = all_x
	sample_array['Y'] = all_y
    	#sample_array['X'] = np.array(all_x).flatten()
    	#sample_array['Y'] = np.array(all_y).flatten()
    	for ind,label in enumerate(labels[2:]):
		sample_array[label] = all_sample_values[ind]
        	#sample_array[label] = np.array(all_sample_values[ind]).flatten()
   	np.savetxt(outputPath, sample_array, delimiter=",", comments="", header=",".join(i for i in sample_array.dtype.names), fmt='%s')
    
    	print " Done!"


def main(paramFile):
    	rasterPath_extent, bandNum_extent, numSamples, bins, rasterPaths_nonExtent, bandNums_nonExtent, outputPath = getTxt(paramFile)
	percents = [.16, .35, .42, .07]
    	numStrat = [int(i*numSamples) for i in percents]
    	print numStrat
    	extractSampleCoords(rasterPath_extent, bandNum_extent, numStrat, bins, rasterPaths_nonExtent, bandNums_nonExtent, outputPath)

if __name__ == '__main__':
	args = sys.argv
	if os.path.exists(args[1]):
		main(args[1])
	else:
		sys.exit('\nParameter File Not Found. Exiting.')
