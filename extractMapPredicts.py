'''
Extract Map Predictions.
Extract values from a raster corresponding to X,Y coordinates from input CSV.

INPUTS (command line):
-inputPath [CSV with X,Y columns]
-predictionMap [path to raster of predictions]
-outputPath

OUTPUT:
-new CSV with 'MAP_PREDICTION' column added

EXAMPLE:
python exractMapPredicts.py path/to/original.csv path/to/predictMap.bsq path/to/new.csv
'''



import sys, os, gdal
import numpy as np
import validation_funs as vf

def main(inputPath, predictionMap, outputPath):
	#read input CSV
	print "\nReading Input CSV data..." 
	inputFile = open(inputPath, 'rb')
	inputData = np.genfromtxt(inputFile, delimiter=',', names=True, case_sensitive=False, dtype=None) #structured array of strings
	inputFile.close()

	#find prediction for each coord
	print "\nExtracting Predictions..."
	ds = gdal.Open(predictionMap)
	transform = ds.GetGeoTransform()

	predictions = np.zeros(inputData.size)
	for ind,x in enumerate(inputData['X']):
		y = inputData['Y'][ind]
		try:
			predictions[ind] = vf.extract_kernel(ds,x,y,1,1,1,transform)[0][0]
		except:
			continue

		#save data
	print "\nSaving Data..."
	labels = list(inputData.dtype.names) + ['MAP_PREDICTION']
	outputData = np.zeros(inputData.size, dtype=[(l,'f8') for l in labels]) #structured array
	for field in inputData.dtype.names:
		outputData[field] = inputData[field]
	outputData['MAP_PREDICTION'] = predictions
	np.savetxt(outputPath, outputData, delimiter=",", comments="", header=",".join(i for i in outputData.dtype.names), fmt='%s')
	print " Done!"


if __name__ == '__main__':
	args = sys.argv
	main(args[1], args[2], args[3])