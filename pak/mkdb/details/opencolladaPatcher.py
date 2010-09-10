#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os
import re
import sys

# locate sbf and add it to sys.path
sbf_root = os.getenv('SCONS_BUILD_FRAMEWORK')
if not sbf_root:
	raise StandardError("SCONS_BUILD_FRAMEWORK is not defined")
sbf_root_normalized	= os.path.normpath( os.path.expandvars( sbf_root ) )
sys.path.append( sbf_root_normalized )

#
from src.sbfFiles import searchFiles

def patchVCPROJ( filename ):
	"""Patches vcproj named filename (WholeProgramOptimization="1" => WholeProgramOptimization="0")."""

	# Reads filename
	with open( filename ) as file:
		lines = file.readlines()

	# Patches
	# WholeProgramOptimization="1" replaced by WholeProgramOptimization="0"
	wholeProgramOptimizationNumRE = re.compile( r'^(\s+WholeProgramOptimization=")1("\s)$' )
	# WholeProgramOptimization="true" replaced by WholeProgramOptimization="false"
	wholeProgramOptimizationBoolRE = re.compile( r'^(\s+WholeProgramOptimization=")true("\s)$' )	
	for (i, line) in enumerate(lines):
		matchObject = wholeProgramOptimizationNumRE.match(line)
		if matchObject:
			matchList = matchObject.groups()
			print ("PATCH line:{0}".format(line)),
			newLine = matchList[0] + '0' + matchList[1] + '\n'
			print ("USING line:%s" % newLine )
			lines[i] = newLine

		matchObject = wholeProgramOptimizationBoolRE.match(line)
		if matchObject:
			matchList = matchObject.groups()
			print ("PATCH line:{0}".format(line)),
			newLine = matchList[0] + 'false' + matchList[1] + '\n'
			print ("USING line:%s" % newLine )
			lines[i] = newLine			
		#else:
		#	print ("IGNORE line:", line)

	# Writes filename
	with open( filename, 'w' ) as file:
		# Writes modifications
		file.writelines( lines )



#
directory = os.path.join( sbf_root, 'pak', 'var', 'build', 'opencollada' + '768', 'opencollada' )

vcprojFiles = []
searchFiles( directory, vcprojFiles, allowedFilesRe = r".*[.]vcproj" )

# Patches each found vcproj file
for vcprojFile in vcprojFiles:
	patchVCPROJ( vcprojFile )
