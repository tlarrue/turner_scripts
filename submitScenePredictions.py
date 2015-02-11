'''
Script used to automate random forest prediction maps production
for Turner age map project.
'''
import sys, os, subprocess
import validation_funs as vf

QSUB_TEMPLATE = """#!/bin/tcsh
#$ -pe omp 2
#$ -l h_rt=12:00:00
#$ -N {0}
#$ -V
#$ -o {1}
#$ -e {1}
{2}
wait"""  

PARAMFILE_TEMPLATE = """RF Prediction Map for {0}
rfModelFilePath: {1}
predictionMask: {2}
predictorTopDir: {3}
predictorMaps: {4}
outputPath: {5}
"""

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

	for scene in scenes:
		print "\n\nWorking on " + scene + " ....."

		#polygonize TSA masks
		clipRasterDir = '/projectnb/trenders/general_files/datasets/spatial_data/us_contiguous_tsa_masks_nobuffer/'
		clipRaster = os.path.join(clipRasterDir, 'us_contiguous_tsa_nobuffer_' + scene + '.bsq')
		outDir = '/projectnb/trenders/proj/turner/outputs/id_mt_age/forest_mask/OR_WA/clip_boundaries/'
		shapeFile = os.path.join(outDir, scene + '_poly.shp')
		layer = os.path.join(outDir, scene + '_poly.lyr')
		if not os.path.exists(shapeFile):
			poly_statement = 'gdal_polygonize.py {0} -b {1} -f "ESRI Shapefile" {2} {3} {4}'.format(clipRaster, str(1), shapeFile, layer, 'TSA')
			print "\n" + poly_statement
			os.system(poly_statement)

		#clip forest mask with TSA shapefile
		sourceRaster = '/projectnb/trenders/proj/turner/outputs/id_mt_age/forest_mask/ID_MT/IDMTORWA_forestmask.bsq'
		outMask = '/projectnb/trenders/proj/turner/outputs/id_mt_age/forest_mask/OR_WA/tsa_prediction_masks/' + scene + '_forestmask.bsq'
		if not os.path.exists(outMask):
			scene_5digit = "'" + scene[1:] + "'"
			clip_statement = 'gdalwarp {0} {1} -cutline {2} -cwhere "TSA={3}" -crop_to_cutline -of ENVI'.format(sourceRaster, outMask, shapeFile, scene_5digit)
			print "\n" + clip_statement
			os.system(clip_statement)

		#prepare rfPredictMap.py inputs
		rfModelFile = '/projectnb/trenders/proj/turner/outputs/id_mt_age/regression_rf_models/random_forest/troubleshooting/rfmodel_ideal'
		predictionMask = outMask
		predictorTopDir = '/projectnb/trenders/proj/turner/outputs/id_mt_age/history_aspect/ORWA_history/historyvars_5x5median/'
		predictorMaps = ','.join(['OR_WA_histvars_mosaic_b_t_2010_5x5filter.bsq','OR_WA_histvars_mosaic_db_t_2010_5x5filter.bsq','OR_WA_histvars_mosaic_g_t_2010_5x5filter.bsq', 
		'OR_WA_histvars_mosaic_dg_t_2010_5x5filter.bsq', 'OR_WA_histvars_mosaic_nbr_t_2010_5x5filter.bsq', 'OR_WA_histvars_mosaic_dnbr_t_2010_5x5filter.bsq', 
		'OR_WA_histvars_mosaic_w_t_2010_5x5filter.bsq', 'OR_WA_histvars_mosaic_dw_t_2010_5x5filter.bsq', 'ORWAIDMT_aspectNWSE.bsq', 'ORWAIDMT_aspectNESW.bsq'])
		outputPath = '/projectnb/trenders/proj/turner/outputs/id_mt_age/prediction_maps/idealmodel_studyarea_TSAs/' + scene + '_idealmodel_rfpredictions.bsq'

		#write new parameter file
		paramFileName = '/projectnb/trenders/proj/turner/scripts/params/rfmap_ideal_' + scene + '.txt'
		paramContext = PARAMFILE_TEMPLATE.format(scene, rfModelFile, predictionMask, predictorTopDir, predictorMaps, outputPath)
		if not os.path.exists(paramFileName):
			print "\nWriting Parameter File: " + paramFileName + " ..."
			paramFile = open(paramFileName, 'w')
			paramFile.write(paramContext) #write filled-in template context to new files
			paramFile.close()

		#write & submit qub file to cluster
		errorDir = '/projectnb/trenders/proj/turner/scripts/params/error_output_files/'
		jobName = 'rf' + scene
		scriptCall = 'python /projectnb/trenders/proj/turner/scripts/rfPredictMap.py ' + paramFileName
		qsubFileName = '/projectnb/trenders/proj/turner/scripts/params/rfmap_ideal_' + scene + '.sh'
		if not os.path.exists(qsubFileName):
			print "\nWriting Qsub File: " + qsubFileName + " ..."
			qsubContext = QSUB_TEMPLATE.format(jobName, errorDir, scriptCall)
			qsubFile = open(qsubFileName, 'w')
			qsubFile.write(qsubContext) #write filled-in template context to new files
			qsubFile.close()
			subprocess.call('qsub ' + qsubFileName, shell=True)
			print " Submitted Job: " + jobName + "."


if __name__ == '__main__':
	args = sys.argv
	main(args[1])

