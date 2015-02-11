'''
Mosaic US TSA masks.

INPUTS:
-pathrows

OUTPUT:
-mosaiced TSA mask

EXAMPLE:
python mergeMasks.py 43/26-31,42/27-30
'''
import sys, os
import validation_funs as vf

def expandPathRows(sceneSets):
	'''takes in list of scene sets, returns list of 6 digit scene numbers'''
	sceneList = []
	for i in sceneSets:
		scenePart = i.split('/')
		if '-' in scenePart[0]:
			rng = scenePart[0].split('-')
			paths = range(int(rng[0]), int(rng[1])+1)
		else:
			paths = [str(scenePart[0])]

		if '-' in scenePart[1]:
			rng = scenePart[1].split('-')
			rows = range(int(rng[0]), int(rng[1])+1)
		else:
			rows = [str(scenePart[1])]

		for row in rows:
			for path in paths:
				pathRow = str(path) + str(row)
				sceneList.append(pathRow)

	return sceneList

def main(scenes):

	scene_sets = scenes.split(',')
	scenes = [vf.sixDigitTSA(i) for i in expandPathRows(scene_sets)]

	topDir = '/projectnb/trenders/general_files/datasets/spatial_data/us_contiguous_tsa_masks_nobuffer/'
	listOfPaths = [os.path.join(topDir, 'us_contiguous_tsa_nobuffer_{0}.bsq'.format(i)) for i in scenes]
	inputFiles = " ".join(listOfPaths)

	outPath = '/projectnb/trenders/general_files/datasets/spatial_data/orwaidmt_tsa_masks_mosaic.bsq'
	mergeStatement = "gdal_merge.py -o {0} -of ENVI -tap -n 0 -init 0 -a_nodata 0 -ot Int32 {1}".format(outPath, inputFiles)
	print mergeStatement

	os.system(mergeStatement)

if __name__ == '__main__':
	args = sys.argv
	main(args[1])
