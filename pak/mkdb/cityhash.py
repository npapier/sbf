# SConsBuildFramework - Copyright (C) 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Guillaume Brocker
#
# http://code.google.com/p/cityhash/

import os
import re
import shutil
import subprocess

# Version components definition
versionMajor = 1
versionMinor = 1
versionMaint = 0

# Package name and version definition
packageName		= 'cityhash'
packageVersion	= '{0}-{1}-{2}'.format(versionMajor, versionMinor, versionMaint)

# Defines the path to the source files
sourcePath	= '{0}-{1}.{2}.{3}'.format(packageName, versionMajor, versionMinor, versionMaint )

# Defines the content of the SBF project file.
sconsDefaultOptions = """productName = '{name}'
type = 'static'
version	= '{version}'""".format( name=packageName, version=packageVersion)


def patcher():
	def _patcher():
		global io
		global os
		global packageName
		global re
		global sconsDefaultOptions
		global shutil
		global sourcePath
		
		# Creates a new directory tree for the compilation.
		os.makedirs(packageName+'/include')
		os.makedirs(packageName+'/src')
		
		# Creates the SBF project options file
		sconsDefaultoptionsFile = open( packageName+'/default.options', 'w' )
		sconsDefaultoptionsFile.write( sconsDefaultOptions )
		sconsDefaultoptionsFile.close()
		
		# Copy the sconstruct file into the project
		shutil.copy( os.getenv('SCONS_BUILD_FRAMEWORK')+'/template/projectTemplate/sconstruct', packageName )
		
		# Moves include and source files to the right place.
		shutil.move( sourcePath+'/src/city.h', packageName+'/include' )
		###Deactivated###
		#shutil.move( srcPath+'/citycrc.h', includePath )
		shutil.move( sourcePath+'/src/city.cc', packageName+'/src/city.cpp' )
		
		# Patches the 'city.h' file
		with open( packageName+'/include/city.h', 'r+' ) as city_h:
			city_h_lines = city_h.readlines()
			for (i, line) in enumerate(city_h_lines):
				city_h_lines[i] = re.sub('^(uint\d+)', 'extern "C" \\1', line)
			city_h.seek(0)
			city_h.writelines(city_h_lines)
		
		# Patches the city.cpp file
		with open( packageName+'/src/city.cpp', 'r+' ) as city_cpp:
			city_cpp_lines = city_cpp.readlines()
			for (i, line) in enumerate(city_cpp_lines):
				if( re.match('^#include "config.h"', line) ):
					city_cpp_lines[i] = '//' + line
			city_cpp.seek(0)
			city_cpp.writelines(city_cpp_lines)
		
	
	return lambda : _patcher()
	
	
def builder():
	def _builder():
		global os
		global packageName
		global subprocess
		
		owd = os.getcwd()
		nwd = owd + '/' + packageName
		os.chdir(nwd)
		
		installPaths = 'installPaths={0}/{1}/local'.format(owd, packageName)
		subprocess.call(['scons',installPaths,'release'], shell=True)
		subprocess.call(['scons',installPaths,'debug'], shell=True)
		
		os.chdir(owd)

	return lambda : _builder()

descriptor = {
	'name'		: packageName,
	'version'	: packageVersion,
	'urls'		: [ 'http://cityhash.googlecode.com/files/{0}-{1}.{2}.{3}.tar.gz'.format(packageName, versionMajor, versionMinor, versionMaint) ],
	'include'	: [ packageName+'/local/include/*.h' ],	
	'license'	: [ sourcePath+'/COPYING' ],
	'lib'		: [ packageName+'/local/bin/*.lib' ],
	'builds'	: [ patcher(), builder() ]
}
