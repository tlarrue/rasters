#!/usr/bin/env python
'''
Intersect Mask.

Usage:
  intersectMask.py <source> <mask> <output> [--src_band=<sb>] [--msk_band=<mb>] [--nodata=<n>] [--datatype=<dt>]
  intersectMask.py -h | --help

Options:
  -h --help     	Show this screen.
  --src_band=<sb>  	Band of source file [default: 1].
  --msk_band=<mb>  	Band of mask file [default: 1].
  --nodata=<n>  	No data value of output.
  --datatype=<dt>  	Data type of output [default: byte].
'''
import docopt, gdal, os, sys
from gdalconst import *
import numpy as np
import validation_funs as vf


def realPath(path):
	if os.path.exists(path):
		return path
	else:
		sys.exit("\nPath Not Valid: '" + path + "'.\n Exiting.")

def maskAsArray(sourcePath, maskPath, src_band=1, msk_band=1):
	'''masks out pixels in a source raster according to 0 pixels in mask raster, outputs numpy array'''
	#extract coordinate info from source
	src = gdal.Open(sourcePath, GA_ReadOnly)
	projection = src.GetProjection()
	driver = src.GetDriver()
	cols = src.RasterXSize
	rows = src.RasterYSize
	transform = src.GetGeoTransform()
	(upper_left_x, x_size, x_rotation, upper_left_y, y_rotation, y_size) = transform
	midInd = (rows/2,cols/2)
	midx = midInd[1] * x_size + upper_left_x + (x_size / 2) #add half the cell size to center the point
	midy = midInd[0] * y_size + upper_left_y + (y_size / 2)

	#read source as array
	srcBand = src.GetRasterBand(src_band)	
	srcBandArray = srcBand.ReadAsArray()

	#read mask as array to the extent of source
	msk = gdal.Open(maskPath, GA_ReadOnly)
	mskTransform = msk.GetGeoTransform()
	mskBand = msk.GetRasterBand(msk_band)
	mskBandArray = vf.extract_kernel(msk, midx, midy, cols, rows, 1, mskTransform) 

	#ensure mask is of 0's & 1's, multiply source & mask
	mskBandArray[np.where(mskBandArray != 0)] = 1
	outBandArray = srcBandArray * mskBandArray

	return outBandArray, transform, projection

def saveArrayAsRaster(outBandArray, transform, projection, outPath, nodata=None, datatype=GDT_Byte):
	'''saves a numpy array as a new raster'''
	print "\nSaving raster..."
	(rows,cols) = outBandArray.shape
	#save new raster
	out = driver.Create(outPath, cols, rows, 1, datatype)
	if out is None:
		print sys.exit('\nCould not create ' + outPath)
	#write the data
	outBand = out.GetRasterBand(1)
	outBand.WriteArray(outBandArray)
	#flush data to disk
	outBand.FlushCache()
	if nodata: outBand.SetNoDataValue(nodata)

	#georeference the image and set the projection
	out.SetGeoTransform(transform)
	out.SetProjection(projection)
	print "\n Done! \nNew raster available here:", outPath

def main(sourcePath, maskPath, outPath, src_band, msk_band, nodata, datatype):

	outBandArray, transform, projection = maskAsArray(sourcePath, maskPath, src_band=src_band, msk_band=msk_band)
	saveArrayAsRaster(outBandArray, transform, projection, outPath, nodata=nodata, datatype=datatype)


if __name__ == '__main__':

	dataTypes = {'byte': GDT_Byte, 'uint16': GDT_UInt16, 'int16': GDT_Int16, 'uint32': GDT_UInt32, 'int32': GDT_Int32,
			 	 'float32': GDT_Float32, 'float64': GDT_Float64}

	try:
		#parse arguments, use file docstring as parameter definition
		args = docopt.docopt(__doc__)

		#call main function if all paths are valid
		outDir = realPath(os.path.dirname(args['<output>']))
		try:
			dt = dataTypes[args['--datatype'].lower()]
			main(realPath(args['<source>']), realPath(args['<mask>']), args['<output>'], int(args['--src_band']), int(args['--msk_band']), args['--nodata'], dt)
		except (TypeError, ValueError) as e:
			sys.exit("\nBand parameter is not an integer.\n Exiting.")
		except KeyError:
			sys.exit("\nData type entry not valid. Choices: {0}\n Exiting.".format(','.join([key for (key,value) in dataTypes.items()])))


	#handle invalid options
	except docopt.DocoptExit as e:
		print e.message