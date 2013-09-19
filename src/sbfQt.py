# SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os
import re

from os.path import join

# To be able to use SConsBuildFramework.py without SCons
import __builtin__
try:
	from SCons.Script import *
except ImportError as e:
	if not hasattr(__builtin__, 'SConsBuildFrameworkQuietImport'):
		print ('sbfWarning: unable to import SCons.Script')

# Qt : moc
def getFilesForMoc( includeFiles ):
	"""@return the list with all files of includeFiles containing G_OBJECT, i.e. files that have to be processed by moc."""
	retVal = []
	# Q_OBJECT detection
	q_object_search = re.compile(r'^.*Q_OBJECT.*$') 
	for includeFile in includeFiles:
		with open(includeFile, 'r') as file:
			for line in file:
				if q_object_search.search(line):
					retVal.append(includeFile)
					break
	return retVal


def moc( lenv, filesForMoc, objFiles ):
	"""@brief apply moc to filesForMoc using lenv. Add all moc action in objFiles."""
	sbf = lenv.sbf
	for mocFile in filesForMoc:
		inputFile = join(sbf.myProjectPathName, mocFile)
		outputFile = (os.path.splitext(mocFile)[0]).replace('include'+os.sep+sbf.myProject, sbf.myProjectBuildPathExpanded, 1 ) + '_moc.cpp'
		objFiles += lenv.Command( outputFile, inputFile,
			Action( [['moc', '-o', '${TARGETS[0]}', '$SOURCE']] ) )

# Mkpak
def getQMakePlatform( ccVersionNumber ):
	"""Helper for mkpak."""

	qmakeGenerator = {
		8	: 'win32-msvc2005',
		9	: 'win32-msvc2008',
		10	: 'win32-msvc2010',
		11	: 'win32-msvc2012',
		}
	if ccVersionNumber in qmakeGenerator:
		return qmakeGenerator[ccVersionNumber]
	else:
		print >>sys.stderr, "Wrong MSVC version. ."
		print ('Given unsupported MSVC version {}. \nVersion 8.0[Exp], 9.0[Exp], 10.0[Exp] or 11.0[Exp] required.'.format(ccVersionNumber))
		exit(1)
