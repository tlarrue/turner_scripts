
'''
This is a script to split sample points into test & training sets,
then fit to linear regression.

INPUTS (in parameter file:
-samplePointsCsv
-targetField
-predictFields
-percentTraining
-outputPath

OUTPUTS:
-csv of results
'''

import sys, os, gdal
import numpy as np
from sklearn import linear_model

class Struct:
    def __init__(self, **entries): 
        self.__dict__.update(entries)

def getTxt(file):
	'''reads parameter file & extracts inputs'''
	txt = open(file, 'r')
	next(txt)

	for line in txt:
		if not line.startswith('#'):
			lineitems = line.split(':')
			title = lineitems[0].strip(' \n')
			var = lineitems[1].strip(' \n')

			if title.lower() == 'samplepointscsv':
				inputPath = var
			elif title.lower() == 'targetfield':
				targetField = var.upper()
			elif title.lower() == 'predictfields':
				predictFields = var.split(',')
			elif title.lower() == 'percenttraining':
				percentTraining = float(var)
			elif title.lower() == 'outputpath':
				outputPath = var
	txt.close()
	return inputPath, targetField, predictFields, percentTraining, outputPath

def splitTrainingSets(inputData, targetField, predictFields, percentTraining):
	totalPoints = len(inputData[targetField])
	numTraining = int((percentTraining/100.)*totalPoints)

	data = inputData[[i for i in predictFields]][:numTraining]
	data_noTuples = [list(x) for x in data]
	data_as_array = np.array(data_noTuples)
	trainingDict = {'target': np.array(inputData[targetField][:numTraining]),
					'data': data_as_array,
					'x': np.array(inputData['X'][:numTraining]),
					'y': np.array(inputData['Y'][:numTraining])}

	data = inputData[[i for i in predictFields]][numTraining:]
	data_noTuples = [list(x) for x in data]
	data_as_array = np.array(data_noTuples)				
	testingDict = {'target': np.array(inputData[targetField][numTraining:]),
					'data': data_as_array,
					'x': np.array(inputData['X'][numTraining:]),
					'y': np.array(inputData['Y'][numTraining:])}
	return Struct(**trainingDict), Struct(**testingDict)

def fitLinearRegression(x_train, y_train):
	regr = linear_model.LinearRegression()
	regr.fit(x_train, y_train)
	return regr

def testLinearRegression(x_test, y_test, regr):
	'''returns mean squared & R squared values'''
	predictions = regr.predict(x_test)
	mean_sq_error = np.mean((predictions-y_test)**2)
	r_sq = regr.score(x_test, y_test)
	return predictions, mean_sq_error, r_sq

def main(paramFile):
	inputPath, targetField, predictFields, percentTraining, outputPath = getTxt(paramFile)

	#extract csv data
	print "\nExtracting Input CSV data..." 
	inputFile = open(inputPath, 'rb')
	inputData = np.genfromtxt(inputFile, delimiter=',', names=True, case_sensitive=False, dtype=None) #structured array of strings
	inputFile.close()

	print "\nSplitting Sets..."
	trainSet, testSet = splitTrainingSets(inputData, targetField, predictFields, percentTraining)
	print "Training Set: ", len(trainSet.target), "pts; ", "Testing Set: ", len(testSet.target), "pts."
	print "\nTraining Model..."
	regressionModel = fitLinearRegression(trainSet.data, trainSet.target)
	print "\nPredicting with new Linear Regression Model..."
	predictions, mean_sq_error, r_sq = testLinearRegression(testSet.data, testSet.target, regressionModel)
	print "R Squared Value: ", r_sq

	#save results
	print "\nSaving results..."
	coeffs = regressionModel.coef_
	labels = ['X', 'Y', 'TARGET', 'PREDICTION', 'MEAN_SQ_ERROR', 'R_SQ', 'INTERCEPT'] + ['COEFF'+str(i+1) for i in range(len(coeffs))]
	model_array = np.zeros(len(testSet.target),dtype=[(l,'f8') for l in labels]) #structured array
	model_array['X'] = testSet.x
	model_array['Y'] = testSet.y
	model_array['TARGET'] = testSet.target
	model_array['PREDICTION'] = predictions
	model_array['MEAN_SQ_ERROR'][0] = mean_sq_error
	model_array['R_SQ'][0] = r_sq
	model_array['INTERCEPT'][0] = regressionModel.intercept_
	for ind,i in enumerate(labels[7:]):
		model_array[i][0] = coeffs[ind]
	np.savetxt(outputPath, model_array, delimiter=",", comments="", header=",".join(i for i in model_array.dtype.names), fmt='%s')
	print "\n\n Done!"

if __name__ == '__main__':
	args = sys.argv
	if os.path.exists(args[1]):
		main(args[1])
	else:
		sys.exit('\nParameter File Not Found. Exiting.')


