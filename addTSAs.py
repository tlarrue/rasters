#!/usr/bin/env python
'''
Add TSA.
Insert TSA info into CSV of coordinates. 
tsa_ref_mask is a mosaic of TSA no buffer masks for region of interest.

Usage:
	addTSAs.py <sourceCsv> <outputCsv> <tsa_ref_mask>
	addTSAs.py (-h | --help)

Options:
	-h --help		Show this screen.
'''
import docopt, sys, os, gdal
import numpy as np
import validation_funs as vf

def main(tsa_ref_mask, inputPath, outputPath):
	#read input CSV
	print "\nReading Input CSV data..." 
	inputFile = open(inputPath, 'rb')
	inputData = np.genfromtxt(inputFile, delimiter=',', names=True, case_sensitive=False, dtype=None) #structured array of strings
	inputFile.close()

	#find TSA for each coord
	print "\nExtracting TSAs..."
	ds = gdal.Open(tsa_ref_mask)
	transform = ds.GetGeoTransform()

	tsas = np.zeros(inputData.size)
	for ind,x in enumerate(inputData['X']):
		y = inputData['Y'][ind]
		tsas[ind] = vf.extract_kernel(ds,x,y,1,1,1,transform)[0][0]

	#save data
	print "\nSaving Data..."
	labels = list(inputData.dtype.names)
	yind = labels.index('Y')
	labels.insert(yind+1, 'TSA')
	outputData = np.zeros(inputData.size, dtype=[(l,'f8') for l in labels]) #structured array
	for field in inputData.dtype.names: outputData[field] = inputData[field]
	outputData['TSA'] = tsas
	np.savetxt(outputPath, outputData, delimiter=",", comments="", header=",".join(i for i in outputData.dtype.names), fmt='%s')
	print " Done!"


if __name__ == '__main__':

	try:
		#parse arguments, use file docstring as parameter definition
		args = docopt.docopt(__doc__)
		#call main function
		main(args['<tsa_ref_mask>'], args['<sourceCsv>'], args['<outputCsv>'])

	#handle invalid options
	except docopt.DocoptExit as e:
		print e.message