# SConsBuildFramework - Copyright (C) 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os

from src.sbfRsync	import createRsyncAction
from src.SConsBuildFramework import stringFormatter

# To be able to use SConsBuildFramework.py without SCons
import __builtin__
try:
	from SCons.Script import *
except ImportError as e:
	if not hasattr(__builtin__, 'SConsBuildFrameworkQuietImport'):
		print ('sbfWarning: unable to import SCons.[Environment,Options,Script]')


### special doxygen related targets : dox_build dox_install dox dox_clean dox_mrproper ###

def printDoxygenBuild( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Build documentation with doxygen" )

def printDoxygenInstall( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Install doxygen documentation" )


# Creates a custom doxyfile
def doxyfileAction( target, source, env ) :
	sbf = env.sbf

	# Compute inputList, examplePath and imagePath parameters of doxyfile
	inputList	= ''
	examplePath	= ''
	imagePath	= ''
	for projectName in sbf.myParsedProjects :

		localenv = sbf.myParsedProjects[projectName]
		projectPathName	= localenv['sbf_projectPathName']

		newPathEntry	= os.path.join(projectPathName, 'include') + ' '
		if os.path.exists( newPathEntry ) :
			inputList	+= newPathEntry

		newPathEntry	= os.path.join(projectPathName, 'src') + ' '
		if os.path.exists( newPathEntry ) :
			inputList	+= newPathEntry

		newPathEntry	= os.path.join(projectPathName, 'doc') + ' '
		if os.path.exists( newPathEntry ) :
			inputList	+= newPathEntry

		newPathEntry	= os.path.join(projectPathName, 'doc', 'example') + ' '
		if os.path.exists( newPathEntry ) :
			examplePath	+= newPathEntry

		newPathEntry	= os.path.join(projectPathName, 'doc', 'image') + ' '
		if os.path.exists( newPathEntry ) :
			imagePath	+= newPathEntry

	# Create a custom doxyfile
	import shutil

	targetName = str(target[0])
	sourceName = str(source[0])

	print 'Generating {}'.format( targetName )

	shutil.copyfile(sourceName, targetName)			# or env.Execute( Copy(targetName, sourceName) )

	with open( targetName, 'a' ) as file:
		file.write( '\n### Added by SConsBuildFramework\n' )
		file.write( 'PROJECT_NAME		= "%s"\n'					% sbf.myProject )
		file.write( 'PROJECT_NUMBER		= "%s generated at %s"\n'	% (sbf.myVersion, sbf.myDateTime) )
		file.write( 'OUTPUT_DIRECTORY	= "%s"\n'					% (targetName + '_build') )
		file.write( 'INPUT				= %s\n'						% inputList )
		#FIXME: FILE_PATTERNS, EXCLUDE, EXCLUDE_PATTERNS
		file.write( 'EXAMPLE_PATH		= %s\n'				% examplePath )
		file.write( 'IMAGE_PATH			= %s\n'				% imagePath )

		file.write( 'ENABLED_SECTIONS	= %s\n'				% sbf.myProject )


# Synchronizes files from source to target.
# target should be yourDestinationPath/dummy.out
# Recursively copy the entire directory tree rooted at source to the destination directory (named by os.path.dirname(target)).
# Remark : the destination directory would be removed before the copying occurs (even if not empty, so be carefull).
def syncAction( target, source, env ) :

	import shutil

	sourcePath		= str(source[0])
	destinationPath	= os.path.dirname(str(target[0]))

	print 'Copying %s at %s' % (sourcePath, destinationPath)

	if ( os.path.ismount(destinationPath) ) :
		print 'sbfError: Try to use %s as an installation/desinstallation directory. Stop action to prevent any unwanted file destruction'
		return None

	shutil.rmtree( destinationPath, True )

	if ( os.path.isdir( os.path.dirname(destinationPath) ) == False ):
		os.makedirs( os.path.dirname(destinationPath) )
	shutil.copytree( sourcePath, destinationPath )




def configureDoxTarget( env ):
	# @todo improves output message
	sbf = env.sbf

	if (	('dox_build' in sbf.myBuildTargets) or
			('dox_install' in sbf.myBuildTargets) or
			('dox' in sbf.myBuildTargets) or
			('dox_clean' in sbf.myBuildTargets) or
			('dox_mrproper' in sbf.myBuildTargets)	):

		if (	('dox_clean' in sbf.myBuildTargets) or
				('dox_mrproper' in sbf.myBuildTargets)	):
			env.SetOption('clean', 1)

		#@todo use other doxyfile(s). see doxInputDoxyfile
		doxInputDoxyfile		= os.path.join(sbf.mySCONS_BUILD_FRAMEWORK, 'doxyfile')
		doxOutputPath			= os.path.join(sbf.myBuildPath, 'doxygen', sbf.myProject, sbf.myVersion )
		doxOutputCustomDoxyfile	= os.path.join(doxOutputPath, 'doxyfile.sbf')

		doxBuildPath			= os.path.join(doxOutputPath, 'doxyfile.sbf_build')
		doxInstallPath			= os.path.join(sbf.myInstallDirectory, 'doc', sbf.myProject, sbf.myVersion)

		# target dox_build
		commandGenerateDoxyfile = env.Command( doxOutputCustomDoxyfile, doxInputDoxyfile, Action(doxyfileAction, printDoxygenBuild) )
		env.Alias( 'dox_build', commandGenerateDoxyfile	)
		commandCompileDoxygen = env.Command( 'dox_build.out', 'dummy.in', 'doxygen ' + doxOutputCustomDoxyfile )
		env.Alias( 'dox_build', commandCompileDoxygen )
		env.AlwaysBuild( [commandGenerateDoxyfile, commandCompileDoxygen] )
		env.Depends( commandCompileDoxygen, commandGenerateDoxyfile )

		# target dox_install
		dox_install_cmd = env.Command( os.path.join(doxInstallPath,'dummy.out'), Dir(os.path.join(doxBuildPath, 'html')), Action(syncAction, printDoxygenInstall) )
		env.Alias( 'dox_install', [ 'dox_build', dox_install_cmd ] )
		env.AlwaysBuild( dox_install_cmd )
		env.Depends( dox_install_cmd, 'dox_build' )

		# target dox
		env.Alias( 'dox', 'dox_install' )
		if env['publishOn'] :
			rsyncAction = createRsyncAction( env, 'doc_%s_%s' % (sbf.myProject, sbf.myVersion), Dir(os.path.join(doxBuildPath, 'html')), 'dox' )
			env.Depends( rsyncAction, 'dox_install' )

		# target dox_clean
		env.Alias( 'dox_clean', 'dox' )
		env.Clean( 'dox_clean', doxOutputPath )

		# target dox_mrproper
		env.Alias( 'dox_mrproper', 'dox_clean' )
		env.Clean( 'dox_mrproper', doxInstallPath )
