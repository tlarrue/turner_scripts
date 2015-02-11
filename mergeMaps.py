'''
Mosaic all maps in specified directory.
Hardcoded for age maps.

INPUTS (command line):
-topDir
-outPath

OUTPUT:
-mosaiced map

EXAMPLE:
python mergeMaps.py /path/to/maps/ /path/to/mosaic.bsq
'''

import os, sys, glob

def main(topDir, outPath):

	listOfPaths = glob.glob(os.path.join(topDir, '*.bsq'))
	inputFiles = " ".join(listOfPaths)

	mergeStatement = "gdal_merge.py -o {0} -of ENVI -tap -n 0 -init 0 -a_nodata 0 -ot Int16 {1}".format(outPath, inputFiles)
	print mergeStatement

	os.system(mergeStatement)


if __name__ == '__main__':
	args = sys.argv
	main(args[1], args[2])