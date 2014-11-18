# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os, collections
from os.path import dirname, exists, isdir, isfile, join
from sbfArchives import extractArchive
from sbfFiles import createDirectory, copy, getNormalizedPathname
from sbfTools import appendToPATH
from sbfUtils import download, extractFilenameFromUrl


def getEmscriptenUrl():
	return 'https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.25.0-portable-64bit.zip'


# Configuration file related functions
def getEmscriptenConfigurationPathFilename():
	return os.path.expanduser('~/.emscripten')

def readEmscriptenConfiguration():
	"""@brief Returns a dictionary containing symbol(s) from ~/.emscripten"""
	dotEmscripten = getEmscriptenConfigurationPathFilename()
	emscriptenConfig = {}
	if exists(dotEmscripten):
		execfile( dotEmscripten, {}, emscriptenConfig )
	return emscriptenConfig


def getEmscriptenRoot():
	emscriptenConfig = readEmscriptenConfiguration()
	return emscriptenConfig.get( 'EMSCRIPTEN_ROOT', None )

def getEmscriptenSCons():
	emscriptenRoot = getEmscriptenRoot()
	if emscriptenRoot:
		return getNormalizedPathname( join(emscriptenRoot, 'tools/scons/site_scons/site_tools/emscripten') )


# Installation related functions
# @todo remove emscripten (i.e. sbf removeEmscripten)
def getEmscriptenInstallationDirectory():
	return getNormalizedPathname( join(__file__, '../../runtime/emsdk') )

def isEmscriptenInstalled():
	return exists( getEmscriptenInstallationDirectory() )

def installEmscripten( sbf ):
	assert( not isEmscriptenInstalled() )
	url = getEmscriptenUrl()
	filename = extractFilenameFromUrl( url )
	emsdkRoot = getEmscriptenInstallationDirectory()

	createDirectory( emsdkRoot )

	# Try to retrieve emsdk from pakPaths or download it from the web
	for path in sbf.myEnv['pakPaths']:
		if exists( join(path,filename) ):
			copy( filename, filename, path, emsdkRoot, True )
			break
	else:
		download( url, join(emsdkRoot, filename) )
	extractArchive( join(emsdkRoot, filename), emsdkRoot, sbf.myEnv.GetOption('verbosity') )


# Configuration function
def configureEmscripten( env, verbose, ignoreEmscriptenConfigurationFile = False ):
	if verbose:		print ('\nConfiguration of emscripten tools...')

	# Add emscripten root to PATH
	appendToPATH( env, [getEmscriptenInstallationDirectory()], verbose )

	# Add HOME to environment (HOME is needed to retrieve/create .emscripten configuration file)
	if verbose:	print ('Adding HOME={}'.format(os.path.expanduser('~')))
	env['ENV']['HOME'] = os.path.expanduser('~')

	# Add NUMBER_OF_PROCESSORS to environment (NUMBER_OF_PROCESSORS is needed for multiprocessing.cpu_count() on windows)
	if env['PLATFORM'].startswith('win'):
		numProcessors = os.getenv('NUMBER_OF_PROCESSORS', 1)
		if verbose:	print ('Adding NUMBER_OF_PROCESSORS={}'.format( numProcessors ))
	env['ENV']['NUMBER_OF_PROCESSORS'] = numProcessors

	# Configure env from value retrieved by reading ~/.emscripten
	if not ignoreEmscriptenConfigurationFile:
		emConfig = readEmscriptenConfiguration()
		toAppend = set()
		for (key, value) in emConfig.iteritems():
			if isinstance(value, str):
				if isfile(value):
					toAppend.add( dirname(value) )
				elif isdir(value):
					toAppend.add( value )
				#else nothing to do
				if verbose:	print ('Adding {}={}'.format(key, value))
				env[key] = value
			else:
				if verbose:	print ('ignore:{}'.format(key))
		# Add toAppend to PATH
		appendToPATH( env, list(toAppend), verbose )

		env['ENV']['EMSCRIPTEN'] = emConfig['EMSCRIPTEN_ROOT']
		if verbose:	print ('Adding {}={}'.format('EMSCRIPTEN', emConfig['EMSCRIPTEN_ROOT']))
		if verbose:	print ('Configuration of emscripten tools is successful.\n')
# @todo missing PATH += d:\localExt_win_x86-32_cl11-0Exp\bin\emsdk\git\1.8.3\bin;d:\localExt_win_x86-32_cl11-0Exp\bin\emsdk\git\1.8.3\cmd
