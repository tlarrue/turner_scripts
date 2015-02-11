'''
Script used to experiment with random vs. stratified sampling schemes
to build random forest model for age mapping.
'''

import sys, os
import numpy as np
    
def main(args):
    
    stratPath = args[1] #csv path
    randPath = args[2]  #csv path
    # pctRand_str = args[3]   #0-100
    
    pcts = np.arange(5,80,5)
    for p in pcts:
        print "STARTING ", p
        pctRand = float(p)/100. #decimal
    
        #extract csv data
        print "\nExtracting Input CSV data..." 
        stratFile = open(stratPath, 'rb')
        stratData = np.genfromtxt(stratFile, delimiter=',', names=True, case_sensitive=False, dtype=None) 
        stratFile.close()
        randFile = open(randPath, 'rb')
        randData = np.genfromtxt(randFile, delimiter=',', names=True, case_sensitive=False, dtype=None) 
        randFile.close()
    
        print "\nSplitting Sets..."
        numTraining_strat = stratData.size/2 #original samples
        numTraining_rand = randData.size/2 #original samples
        print numTraining_strat, numTraining_rand 
    
        ind_strat = np.random.choice(range(numTraining_strat), np.floor(numTraining_strat*(1.-pctRand)), replace=False)
        ind_rand = np.random.choice(range(numTraining_rand), np.ceil(numTraining_strat*pctRand), replace=False)
        print ind_strat.size, ind_rand.size
    
        newData = np.zeros(stratData.size, dtype=[(l,'f8') for l in stratData.dtype.names]) #structured array
        newData[numTraining_strat+1:] = randData[-(numTraining_strat):]
        newData[:ind_strat.size] = stratData[ind_strat]
        newData[ind_strat.size:numTraining_strat] = randData[ind_rand]
    
        print "\nSaving new CSV..."
        outDir = os.path.dirname(stratPath)
        outputPath = os.path.join(outDir, 'rfsamples_trainstrat{0}pctrand_testrand.csv'.format(str(p)))
        np.savetxt(outputPath, newData, delimiter=",", comments="", header=",".join(i for i in newData.dtype.names), fmt='%s')
        print " Done! New CSV here: ", outputPath
        
    
if __name__ == '__main__': 
	args = sys.argv
	main(args)