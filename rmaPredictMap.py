'''
OLD VERSION! Need to update to use pickled CCA model.

This is a script to apply CCA/RMA regression model to a map.

INPUTS (in parameter file):
-regressionModelCsv 
	[includes fields: 'CCA_ROTATIONS', 'CCA_X_MEAN', 'CCA_X_STD', 'INTERCEPT', 'SLOPE']
-predictTopDir
-predictionsRasters
	*stack, same # of bands as len(CCA_WEIGHTS)
-ccaOutputDataType
-ccaNoData
-ccaOutputPath
-predictionOutputDataType
-predictionNoData
-predictionOutputPath

OUTPUTS:
-raster of cca indeces
-raster of predictions

EXAMPLE:
python rmaPredictMap.py ./params/test_param_file.txt
'''
import sys, os, gdal
from gdalconst import *
import numpy as np
import cPickle as pickle

class Struct:
	def __init__(self, **entries): 
		self.__dict__.update(entries)

def chooseDataType(var):
	if var.lower() == 'byte':
		return GDT_Byte
	elif var.lower() == 'int16':
		return GDT_Int16
	elif var.lower() == 'int32':
		return GDT_Int32
	elif var.lower() == 'float32':
		return GDT_Float32
	else:
		sys.exit('Data Type not understood. Available Choices: Byte, Int16, Int32')

def getTxt(file):
	'''reads parameter file & extracts inputs'''
	txt = open(file, 'r')
	next(txt)

	for line in txt:
		if not line.startswith('#'):
			lineitems = line.split(':')
			title = lineitems[0].strip(' \n')
			var = lineitems[1].strip(' \n')

			if title.lower() == 'regressionmodelcsv':
				if os.path.exists(var):
					modelCsv = var
				else:
					sys.exit("Cannot Find Regression Model CSV: "+ var)
			elif title.lower() == 'predicttopdir':
				topDir = var
			elif title.lower() == 'predictorrasters':
				rasterList = var.split(';')
				predictorRasters = []
				for i in rasterList:
					if os.path.exists(os.path.join(topDir,i)):
						predictorRasters.append(os.path.join(topDir,i))
					else:
						sys.exit("Cannot Find Predict Raster: "+ i)
			elif title.lower() == 'ccaoutputdatatype':
				dataType_cca = chooseDataType(var)
			elif title.lower() == 'ccanodata':
				nodata_cca = int(var)
			elif title.lower() == 'ccaoutputpath':
				outputPath_cca = var
			elif title.lower() == 'predictionoutputdatatype':
				dataType_prediction = chooseDataType(var)
			elif title.lower() == 'predictionnodata':
				nodata_prediction = int(var)
			elif title.lower() == 'predictionoutputpath':
				outputPath_prediction = var

	txt.close()
	return modelCsv, predictorRasters, dataType_cca, nodata_cca, outputPath_cca, dataType_prediction, nodata_prediction, outputPath_prediction

def linearFunc(B, x):
	'''Linear function y = m*x + b'''
	# B is a vector of the parameters.
	# x is an array of the current x values.
	# Return an array in the same format as y passed to Data or RealData.
	return B[0] + B[1]*x

def extractModel(modelCsv):
	#read regression model csv file
	inputFile = open(modelCsv, 'rb')
	inputData = np.genfromtxt(inputFile, delimiter=',', names=True, case_sensitive=False, dtype=None) #structured array of strings
	inputFile.close()

	#cca model params
	ccaModel = {'sampleMean': np.trim_zeros(np.array(inputData['CCA_X_MEAN']).astype('f8'),'b'),
				'sampleStd': np.trim_zeros(np.array(inputData['CCA_X_STD']).astype('f8'),'b'),
				'rotations': np.trim_zeros(np.array(inputData['CCA_ROTATIONS']).astype('f8'), 'b')}

	#rma regression model params
	rmaModel = [np.array(inputData['INTERCEPT']).astype('f8')[0], np.array(inputData['SLOPE']).astype('f8')[0]]

	return Struct(**ccaModel), rmaModel


def main(paramFile):
	modelCsv, predictorRasters, dataType_cca, nodata_cca, outputPath_cca, dataType_prediction, nodata_prediction, outputPath_prediction = getTxt(paramFile)

	#extract model elements
	ccaModel, rmaParams = extractModel(modelCsv)

	#Read rasters while applying cca model
	print 'Applying CCA Reduction to predictors....'
	for ind,raster in enumerate(predictorRasters):
		print raster
		ds = gdal.Open(raster)
		band = ds.GetRasterBand(1)
		bandArray = band.ReadAsArray()
		if ind == 0:
			(xShape, yShape) = bandArray.shape
			ccaIndex = np.zeros([xShape, yShape])
			noData = band.GetNoDataValue()
			(xNoData, yNoData) = np.where(bandArray == noData)
		#multiply CCA weight to normalized predict data, and sum all of this into one array
		ccaIndex += ((bandArray-ccaModel.sampleMean[ind])/ccaModel.sampleStd[ind])*ccaModel.rotations[ind] 

	print "\nSaving CCA predictor raster..."
	driver = ds.GetDriver()
	projection = ds.GetProjection()
	transform = ds.GetGeoTransform()
	cols = ds.RasterXSize
	rows = ds.RasterYSize
	outDs = driver.Create(outputPath_cca, cols, rows, 1, dataType_cca)
	if outDs is None:
		print 'Could not create ' + outputPath_cca
		sys.exit(1)

	#write the data
	outBand = outDs.GetRasterBand(1)
	outBand.WriteArray(ccaIndex)

	#flush data to disk
	outBand.FlushCache()
	outBand.SetNoDataValue(nodata_cca)

	#georeference the image and set the projection
	outDs.SetGeoTransform(transform)
	outDs.SetProjection(projection)
	print " Done! \nRaster available here:", outputPath_cca

	#predict on reduced array
	print "\nPredicting using RMA model..."
	predictions = linearFunc(rmaParams, ccaIndex)
	(xNegs, yNegs) = np.where(predictions < 0)
	predictions[xNegs, yNegs] = 0
	predictions[xNoData,yNoData] = nodata_prediction 

	#make new map
	print "\nSaving new prediction raster..."
	outDs = driver.Create(outputPath_prediction, cols, rows, 1, dataType_prediction)
	if outDs is None:
		print 'Could not create ' + outputPath_prediction
		sys.exit(1)

	#write the data
	outBand = outDs.GetRasterBand(1)
	outBand.WriteArray(predictions)

	#flush data to disk
	outBand.FlushCache()
	outBand.SetNoDataValue(nodata_prediction)

	#georeference the image and set the projection
	outDs.SetGeoTransform(transform)
	outDs.SetProjection(projection)
	print " Done! \nRaster available here:", outputPath_prediction


if __name__ == '__main__':
	args = sys.argv
	if os.path.exists(args[1]):
		main(args[1])
	else:
		sys.exit('\nParameter File Not Found. Exiting.')
