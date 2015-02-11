
'''
This is a script to split sample points into test & training sets,
then fit to RMA regression model, then test with test set.

INPUTS (in parameter file):
-samplePointsCsv
-targetField
-predictFields
-percentTraining
-outputPath

OUTPUTS:
-csv of results

EXAMPLE:
python rmaRegression.py ./params/test_param_file.txt
'''

import sys, os, gdal
import numpy as np
import cPickle as pickle
from sklearn import linear_model
from sklearn.cross_decomposition import CCA
from scipy.stats.stats import pearsonr
from numpy.lib.recfunctions import append_fields
from sklearn.metrics import mean_squared_error

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

def transformCCA(x_train, y_train, x_test):
	'''Find 1-D array of training & testing predictors using Canonical Correlation Analysis'''
	cca = CCA(n_components=1, copy=True)
	cca.fit(x_train,y_train)
	x_train_reduced = cca.transform(x_train, copy=True)
	x_test_reduced = cca.transform(x_test, copy=True)
	return x_train_reduced, x_test_reduced, cca

def linearFunc(B, x):
	'''Linear function y = m*x + b'''
	# B is a vector of the parameters.
	# x is an array of the current x values.
	# Return an array in the same format as y passed to Data or RealData.
	return B[0] + B[1]*x
        
def fitRMARegression(x_train_reduced, y_train):
    '''Find RMA parameters & calculate RMSE'''
    slope = np.std(y_train)/ np.std(x_train_reduced)
    if (pearsonr(x_train_reduced, y_train)[0]) < 0.0:
        slope = -1 * slope
    intercept = np.mean(y_train) - np.mean(x_train_reduced)*slope
    B = [intercept,slope]
    
    predictions = linearFunc(B,x_train_reduced)
    mse = mean_squared_error(y_train, predictions)
    training_rmse = np.sqrt(mse)
    return B, training_rmse

def testRMARegression(RMAparams, errTerm, x_test_reduced, y_test):
    '''Applies RMA model to test set, and returns residuals, MSE, & RMSE'''
    predictions = linearFunc(RMAparams, x_test_reduced)
    residuals = predictions - y_test
    mse = mean_squared_error(y_test, predictions)
    rmse = np.sqrt(mse)
    return predictions, residuals, mse, rmse

def main(paramFile):
	inputPath, targetField, predictFields, percentTraining, outputPath = getTxt(paramFile)

	#extract csv data
	print "\nExtracting Input CSV data..." 
	inputFile = open(inputPath, 'rb')
	inputData = np.genfromtxt(inputFile, delimiter=',', names=True, case_sensitive=False, dtype=None) #structured array of strings
	inputFile.close()
	print inputData.dtype.names

	print "\nSplitting Sets..."
	trainSet, testSet = splitTrainingSets(inputData, targetField, predictFields, percentTraining)
	print "Training Set: ", len(trainSet.target), "pts; ", "Testing Set: ", len(testSet.target), "pts."
    
	print "\nApplying Canonical Correlation Analysis..."
	training_ccaindex, testing_ccaindex, cca_model = transformCCA(trainSet.data, trainSet.target, testSet.data)
	trainSet.reducedData = training_ccaindex.flatten()
	testSet.reducedData = testing_ccaindex.flatten()

	print "\nTraining RMA Model..."
	RMAparams, errTerm = fitRMARegression(trainSet.reducedData, trainSet.target)

	print "\nSaving CCA Model..."
	outpath_cca = os.path.splitext(outputPath)[0] + "_CCAmodel"
	with open(outpath_cca, 'w+') as f:
		pickle.dump(cca_model, f)

	print "\nPredicting with new RMA Model..."
	predictions, residuals, mean_sq_err, rmse = testRMARegression(RMAparams, errTerm, testSet.reducedData, testSet.target)
	print "Mean Square Error: ", mean_sq_err

	#save results
	print "\nSaving results..."
	labels = ['X', 'Y', 'CCA_INDEX', 'TARGET', 'PREDICTION', 'RESIDUALS', 'MEAN_SQ_ERR', 'RMSE', 'INTERCEPT', 'SLOPE', 'ERR_TERM']
	model_array = np.zeros(len(testSet.target)+1,dtype=[(l,'f8') for l in labels]) #structured array
	model_array['X'][:trainSet.x.size] = trainSet.x
	model_array['Y'][:trainSet.y.size] = trainSet.y
	model_array['CCA_INDEX'][:testSet.reducedData.size] = testSet.reducedData
	model_array['TARGET'][:testSet.target.size] = testSet.target
	model_array['PREDICTION'][:predictions.size] = predictions
	model_array['RESIDUALS'][:residuals.size] = residuals
	model_array['MEAN_SQ_ERR'][0] = mean_sq_err
	model_array['RMSE'][0] = rmse
	model_array['INTERCEPT'][0] = RMAparams[0]
	model_array['SLOPE'][0] = RMAparams[1]
	model_array['ERR_TERM'][0] = errTerm
	np.savetxt(outputPath, model_array, delimiter=",", comments="", header=",".join(i for i in model_array.dtype.names), fmt='%s')

	print "\n\n Done!"



if __name__ == '__main__':
	args = sys.argv
	if os.path.exists(args[1]):
		main(args[1])
	else:
		sys.exit('\nParameter File Not Found. Exiting.')


