'''
Compare raster values. Output confusion matrix.
Currently hard-coded for Turner age map bins.

INPUTS (in parameter file):
-predictionsRaster
-truthRaster
-outputPath

OUTPUT:
-confusion matrix CSV

EXAMPLE:
python compareRasters.py path/to/paramfile.txt
'''
import sys, os, gdal
import numpy as np
from sklearn.metrics import confusion_matrix
import validation_funs as vf

def getTxt(file):
	'''reads parameter file & extracts inputs'''
	txt = open(file, 'r')
	next(txt)

	for line in txt:
		if not line.startswith('#'):
			lineitems = line.split(':')
			title = lineitems[0].strip(' \n')
			var = lineitems[1].strip(' \n')

			if title.lower() == 'predictionsraster':
				predictionsRaster = var
			elif title.lower() == 'truthraster':
				truthRaster = var
			elif title.lower() == 'outputpath':
				outputPath = var
	txt.close()
	return predictionsRaster, truthRaster, outputPath

def main(paramFile):
	predictionsRaster, truthRaster, outputPath = getTxt(paramFile)

	ds = gdal.Open(predictionsRaster)
	band = ds.GetRasterBand(1)
	noData_pred = band.GetNoDataValue()
	(upper_left_x, x_size, x_rotation, upper_left_y, y_rotation, y_size) = ds.GetGeoTransform()
	cols = ds.RasterXSize
	rows = ds.RasterYSize
	predictions = band.ReadAsArray()
	mid_index = (int(np.floor(predictions.shape[0]/2.)), int(np.floor(predictions.shape[1]/2.)))
	mid_x_coord = mid_index[1] * x_size + upper_left_x + (x_size / 2) #add half the cell size to center the point
	mid_y_coord = mid_index[0] * y_size + upper_left_y + (y_size / 2)

	ds_truth = gdal.Open(truthRaster)
	band_truth = ds.GetRasterBand(1)
	noData_truth = band_truth.GetNoDataValue()
	transform_truth = ds_truth.GetGeoTransform()
	observations = vf.extract_kernel(ds_truth, mid_x_coord, mid_y_coord, cols, rows, 1, transform_truth) 

	(xData_pred, yData_pred) = np.where(predictions != noData_pred)
	obs_flat = observations[xData_pred,yData_pred].flatten()
	pred_flat = predictions[xData_pred,yData_pred].flatten()
	
	bins = [(0,60), (61,100), (101,200), (201,1000)]
	bin_names = [45,80,150,250]
	for ind,bin in enumerate(bins):
		index = np.where((obs_flat >= bin[0]) & (obs_flat <= bin[1]))
		obs_flat[index] = bin_names[ind]

	confusion = confusion_matrix(obs_flat.astype(int), pred_flat.astype(int), labels=bin_names)
	print "Saving Confusion Data..."
	np.savetxt(outputPath, confusion, delimiter=",", fmt='%i')
	print " Done!"


if __name__ == '__main__':
	args = sys.argv
	if os.path.exists(args[1]):
		main(args[1])
	else:
		sys.exit('\nParameter File Not Found. Exiting.')

