'''
Train & Test a random forest model.

INPUTS (in parameter file):
-samplePointsCSV (binned samples)
-targetField 
-percentTraining 
-outputPath_model
-outputPath_confusion

OUTPUTS:
-pickled RF model
-confusion matrix as CSV

EXAMPLE:
python rfTrainTest.py /path/to/paramfile.txt
'''
import sys, os, gdal
import cPickle as pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
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
			elif title.lower() == 'outputpath_model':
				outputPath_model = var
			elif title.lower() == 'outputpath_confusion':
				outputPath_confusion = var
	txt.close()
	return inputPath, targetField, predictFields, percentTraining, outputPath_model, outputPath_confusion

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

def fitRF(x_train, y_train):
	'''Find 1-D array of training & testing predictors using Canonical Correlation Analysis'''
	rf = RandomForestClassifier(n_estimators=50, oob_score=True)
	rf = rf.fit(x_train,y_train)
	return rf, rf.oob_score_

def fitRFregress(x_train,y_train):
	rf = RandomForestRegressor(n_estimators=50, max_features='sqrt', oob_score=True)
	rf = rf.fit(x_train,y_train)
	return rf, rf.oob_score_

def predictRF(rf, x_test):
	predictions = rf.predict(x_test)
	voting_scores = rf.predict_proba(x_test)
	return predictions, voting_scores

def calcAccuracy(y_test, predictions, classes):
	cm = confusion_matrix(y_test, predictions, labels=classes)
	numPred = np.sum(cm,axis=0).astype('f8')
	numTruth = np.sum(cm,axis=1).astype('f8')
	dtypes = [(' ', 'a25')] + [(str(i),'f8') for i in classes] + [('No. Truth', 'a25'), ('Producers Accuracy', 'f8')] #horizontal labels
	full_cm = np.zeros(cm.shape[0]+2, dtype=dtypes) #structured array
	full_cm[' '] = [str(i) for i in classes] + ['No. Predictions', 'Users Accuracy'] #vertical labels
	totalCorrect = 0
	for ind,i in enumerate(classes):
		numCorrect = float(cm[ind,ind])
		totalCorrect += numCorrect
		full_cm[str(i)] = list(cm[:,ind]) + [numPred[ind], numCorrect/numPred[ind]]
		full_cm['Producers Accuracy'][ind] = numCorrect/numTruth[ind] 
	full_cm['No. Truth'] = list(numTruth.astype('a25')) + [str(np.sum(cm)), 'Overall']
	full_cm['Producers Accuracy'][-2:] = [None,totalCorrect/np.sum(cm).astype('f8')]

	return full_cm


def main(paramFile):
    inputPath, targetField, predictFields, percentTraining, outputPath_model, outputPath_confusion = getTxt(paramFile)

    #extract csv data
    print "\nExtracting Input CSV data..." 
    inputFile = open(inputPath, 'rb')
    inputData = np.genfromtxt(inputFile, delimiter=',', names=True, case_sensitive=False, dtype=None) #structured array of strings
    inputFile.close()

    print "\nSplitting Sets..."
    print inputData.size
    trainSet, testSet = splitTrainingSets(inputData, targetField, predictFields, percentTraining)
    print "Training Set: ", len(trainSet.target), "pts; ", "Testing Set: ", len(testSet.target), "pts."
    print "Training Set 1st: ", trainSet.data[0], "Test Set 1st: ", testSet.data[0]

    print "\nTraining Random Forest Model..."
    rfModel, oobScore = fitRF(trainSet.data, trainSet.target)
    print "OOB:", oobScore
    
    print "\nSaving Random Forest Model..."
    with open(outputPath_model, 'w+') as f:
        pickle.dump(rfModel, f)

	#TEMPORARY!
    # print "\nExtracting Random Forest Model..."
    # with open(outputPath_model, 'rb') as f:
    #     rfModel = pickle.load(f)

	print "\nPredicting with Random Forest Model..."
	predictions, voting_scores = predictRF(rfModel, testSet.data)

	print "Saving Predictions..."
	labels = list(inputData.dtype.names) + ['VOTES_'+str(i) for i in rfModel.classes_] + ['PREDICTION']
	predictionData = np.zeros(inputData.size, dtype=[(l,'f8') for l in labels])
	for field in inputData.dtype.names:
		predictionData[field] = inputData[field]
	start = inputData.size - predictions.size
	for ind,i in enumerate(rfModel.classes_):
		predictionData['VOTES_'+str(i)][start:] = (voting_scores[:,ind]*100).astype(int)
	predictionData['PREDICTION'][start:] = predictions
	outputPath_predictions = os.path.splitext(inputPath)[0] + '_predictions.csv'
	np.savetxt(outputPath_predictions, predictionData, delimiter=",", comments="", header=",".join(i for i in predictionData.dtype.names), fmt='%s')

	print "Saving Confusion Matrix..."
	confusion = calcAccuracy(testSet.target, predictions, rfModel.classes_)
	np.savetxt(outputPath_confusion, confusion, delimiter=",", comments="", header=",".join(i for i in confusion.dtype.names),  fmt='%s')
	print " Done!"


if __name__ == '__main__': 
	args = sys.argv
	if os.path.exists(args[1]):
		main(args[1])
	else:
		sys.exit('\nParameter File Not Found. Exiting.')
