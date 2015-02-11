'''
This is a script to apply a Random Forest Classifier model to a map.

INPUTS (in parameter file):
-rfModelFilePath
-predictionMask
-predictorTopDir
-predictorMaps
	*in same order as predictFields from rfTrainTest, seperated by commas
-outputPath

OUTPUTS:
-raster of predictions

EXAMPLE:
python rfPredictMap.py ./params/test_param_file.txt
'''
import sys, os, gdal
import cPickle as pickle
import numpy as np
from gdalconst import *
import validation_funs as vf

def pathExists(path):
	if os.path.exists(path):
		return path
	else:
		sys.exit("Path Not Valid: '" + path + "'. Exiting.")

def getTxt(file):
	'''reads parameter file & extracts inputs'''
	txt = open(file, 'r')
	next(txt)

	for line in txt:
		if not line.startswith('#'):
			lineitems = line.split(':')
			title = lineitems[0].strip(' \n')
			var = lineitems[1].strip(' \n')

			if title.lower() == 'rfmodelfilepath':
				rfModelFile = pathExists(var)
			elif title.lower() == 'predictionmask':
				predictionMask = pathExists(var)
			elif title.lower() == 'predictortopdir':
				predictorTopDir = pathExists(var)
			elif title.lower() == 'predictormaps':
				map_bases = var.split(',') 
				maps = [os.path.join(predictorTopDir,i.strip(' ')) for i in map_bases]	
				predictorMaps = [pathExists(j) for j in maps]
			elif title.lower() == 'outputpath':
				outputPath = var
	txt.close()
	return rfModelFile, predictionMask, predictorMaps, outputPath

def main(paramFile):
	#extract inputs
	print "\nReading Parameter File..."
	rfModelFile, predictionMask, predictorMaps, outputPath = getTxt(paramFile)

	#extract rfModel
	print "\nExtracting Random Forest Model..."
	with open(rfModelFile, 'rb') as f:
		rfModel = pickle.load(f)

	#open prediction extent mask + extract band & projection info
	print "\nExtracting Projection Info from Prediction Mask..."
	ds = gdal.Open(predictionMask, GA_ReadOnly)
	driver = ds.GetDriver()
	projection = ds.GetProjection()
	transform = ds.GetGeoTransform()
	(upper_left_x, x_size, x_rotation, upper_left_y, y_rotation, y_size) = transform
	cols = ds.RasterXSize
	rows = ds.RasterYSize
	extent_band = ds.GetRasterBand(1)
	extent_bandArray = extent_band.ReadAsArray()
	extent_shape = extent_bandArray.shape
	print "Extent Shape: ", extent_shape
	mid_index = (int(np.floor(extent_shape[0]/2.)), int(np.floor(extent_shape[1]/2.)))
	mid_x_coord = mid_index[1] * x_size + upper_left_x + (x_size / 2) #add half the cell size to center the point
	mid_y_coord = mid_index[0] * y_size + upper_left_y + (y_size / 2)
	print "Midpoint: " , mid_x_coord, mid_y_coord

	#build predictor array
	print "\nReading Predictor Maps..."
	numPredictors = len(predictorMaps)
	for ind, i in enumerate(predictorMaps):
		ds_pm = gdal.Open(i, GA_ReadOnly)
		transform_pm = ds_pm.GetGeoTransform()
		band_pm = ds_pm.GetRasterBand(1)
		bandArray_pm = vf.extract_kernel(ds_pm, mid_x_coord, mid_y_coord, cols, rows, 1, transform_pm) 
		if ind == 0:
			predictor_array = np.zeros((bandArray_pm.flatten().size, numPredictors)) #define array
		predictor_array[:, ind] = bandArray_pm.flatten()

	#predict with RF model & reshape to original extent band array shape
	print "\nPredicting using RF model..."
	mask = extent_bandArray
	mask[np.where(mask != 0)] = 1
	predictions = rfModel.predict(predictor_array)
	votingScores = rfModel.predict_proba(predictor_array) * 100
	predictions_masked = predictions.reshape(extent_shape) * mask
	votingScores_masked = []
	for ind,i in enumerate(rfModel.classes_):
		votingScores_masked.append(votingScores[:,ind].reshape(extent_shape) * mask)

	#save predictions raster
	print "\nSaving new prediction raster..."
	outDs = driver.Create(outputPath, cols, rows, 1+len(rfModel.classes_), GDT_Int16)
	if outDs is None:
		print 'Could not create ' + outputPath
		sys.exit(1)
	#write the data
	outBand = outDs.GetRasterBand(1)
	outBand.WriteArray(predictions_masked)
	#flush data to disk
	outBand.FlushCache()
	outBand.SetNoDataValue(0)

	#write the data
	for i in range(len(rfModel.classes_)):
		outBand = outDs.GetRasterBand(i+2)
		outBand.WriteArray(votingScores_masked[i])
		#flush data to disk
		outBand.FlushCache()
		outBand.SetNoDataValue(255)

	#georeference the image and set the projection
	outDs.SetGeoTransform(transform)
	outDs.SetProjection(projection)
	print " Done! \nRaster available here:", outputPath




if __name__ == '__main__':
	args = sys.argv
	if os.path.exists(args[1]):
		main(args[1])
	else:
		sys.exit('\nParameter File Not Found. Exiting.')
