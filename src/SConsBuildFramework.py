# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import datetime
import fnmatch
import glob
import sbfIVersionControlSystem
import os
import platform
import re
import string
import tempfile
import time

from collections import OrderedDict
from os.path import splitext
from sbfFiles import *
from sbfRC import resourceFileGeneration

from sbfAllVcs import *
from sbfConfiguration import configurePATH
from sbfEmscripten import *
from sbfQt import *
from sbfSubversion import anonymizeUrl, removeTrunkOrTagsOrBranches
from sbfPackagingSystem import PackagingSystem
from sbfTools import getPathsForTools, getPathsForRuntime, prependToPATH, appendToPATH
from sbfUI import askQuestion
from sbfUses import UseRepository, generateAllUseNames, uses
from sbfUtils import *
from sbfVersion import printSBFVersion, computeVersionNumber, getVersionNumberString2, extractVersion, splitLibsName, splitUsesName, splitDeploymentPrecond

# To be able to use SConsBuildFramework.py without SCons
import __builtin__
try:
	from SCons.Environment import *
	from SCons.Options import *
	from SCons.Script import *
except ImportError as e:
	if not hasattr(__builtin__, 'SConsBuildFrameworkQuietImport'):
		print ('sbfWarning: unable to import SCons.[Environment,Options,Script]')

# To be able to use sbfUses.py without SCons
try:
	from SCons.Tool.MSCommon.vc import cached_get_installed_vcs
except ImportError as e:
	pass


# MS Visual C++ version dictionnaries

clYearToVersionNum = OrderedDict( [	('2003'		, '7.1'),
									('2005Exp'	, '8.0Exp'),
									('2005'		, '8.0'),
									('2008Exp'	, '9.0Exp'),
									('2008'		, '9.0'),
									('2010Exp'	, '10.0Exp'),
									('2010'		, '10.0'),
									('2012Exp'	, '11.0Exp'),
									('2012'		, '11.0'),
									('2013Exp'	, '12.0Exp'),
									('2013'		, '12.0') ] )

clVersionNumToYear = getSwapDict( clYearToVersionNum )

def getInstalledCLVersionNum():
	return sorted(cached_get_installed_vcs())

def getInstalledCLYear():
	return sorted(map( lambda x: clVersionNumToYear.get(x, x), getInstalledCLVersionNum() ))

def printInstalledCL():
	print ('The installed versions of Visual C++ are'),
	for year in getInstalledCLYear():
		versionNum = clYearToVersionNum.get(year, year)
		print ('{} ({})'.format( year, versionNum )),
	print

def createBlowfishShareBuildCommand( key ):
	"""create Blowfish share build command"""
	shareBuildCommand = (	'blowfish_1-0_${MYPLATFORM}_${CCVERSION}${sbf_my_FullPostfix}.exe encrypt ' + key + ' ${SOURCE} ${TARGET}',
							'${SOURCE}.encrypted', 'Encrypt $SOURCE.file' )
	return shareBuildCommand


def getSConsBuildFrameworkOptionsFileLocation( SCONS_BUILD_FRAMEWORK ):
	""" @return the full path to the SConsBuildFramework.options file.
		@remark SConsBuildFramework.options from your home directory or SConsBuildFramework.options from $SCONS_BUILD_FRAMEWORK."""
	homeSConsBuildFrameworkOptions = os.path.expanduser('~/.SConsBuildFramework.options')

	if os.path.isfile(homeSConsBuildFrameworkOptions):
		# Reads from your home directory.
		return homeSConsBuildFrameworkOptions
	else:
		# Reads from $SCONS_BUILD_FRAMEWORK directory.
		return join( SCONS_BUILD_FRAMEWORK, 'SConsBuildFramework.options' )


def sbfPrintCmdLine( cmd, target, src, env ):
#	print ("beginning=%s" % cmd[:20])

	if cmd.startswith( 'sbf' ) :
		if cmd.startswith( 'sbfNull' ) :
			return
		else:
			return
	elif cmd.startswith( ('link /', 'link @', 'lib /', 'lib @' ) ) : # ('link /nologo', 'lib /nologo')
		print ('Linking %s' % str(os.path.basename(target[0].abspath)))
	elif cmd.startswith( 'mt /') : # 'mt /nologo'
		print ('Embedding manifest into %s' % str(os.path.basename(target[0].abspath)))
	else:
		print cmd


###### Functions for print action ######
def printEmptyLine(target = None, source = None, env = None) :
	print ''

def printBuild( target, source, localenv ) :
	# echo -e "\033[34m test" gives a blue "test"
	return '\n' + stringFormatter( localenv, 'Build {0}'.format(localenv['sbf_projectPathName']) )

def printInstall( target, source, localenv ) :
	return stringFormatter(localenv, "Install %s files to %s" % (localenv['sbf_projectPathName'], localenv.sbf.myInstallDirectory) )

def printDeps( target, source, localenv ) :
	return stringFormatter(localenv, "Install %s dependencies to %s" % (localenv['sbf_projectPathName'], localenv.sbf.myInstallDirectory) )

def printMrproper( target, source, localenv ) :
	return stringFormatter( localenv, "Mrproper %s files to %s" % (localenv['sbf_projectPathName'], localenv.sbf.myInstallDirectory) )

def printGenerate( target, source, localenv ) :
	return "Generating %s" % str(os.path.basename(target[0].abspath)) # @todo '\n' usage ?



###### Options : validators and converters ######
def passthruValidator( key, val, env ):
	#print ('passthruValidator: %s' % val)
	pass


def passthruConverter( val ):
	#print ('passthruConverter: %s' % val)

	list_of_values = convertToList( val )

	#print ('passthruConverter: %s' % list_of_values)

	return list_of_values



### Name manipulation ###
def expandNameOfLibrary( sbf, lib ):
	libSplitted = splitLibsName( lib )
	if len(libSplitted[1])==0:
		# no version information supplied
		return '{}{}{}'.format( libSplitted[0], sbf.my_Platform_myCCVersion, sbf.my_PostfixLinkedToMyConfig )
	else:
		# version information supplied
		return '{}_{}{}{}'.format( libSplitted[0], libSplitted[1], sbf.my_Platform_myCCVersion, sbf.my_PostfixLinkedToMyConfig )

def computeLibsExpanded( sbf, libs ):
	"""@return (libsExpanded, True if 'sbf' is in libs (False otherwise))
	Example: computeLibsExpanded( sbf, ['sbf 0-2'] ) returns (['sbf_0-2_win_cl11-0Exp], True)"""

	libsExpanded = []
	containsSbfLibrary = False

	for lib in libs:
		containsSbfLibrary = containsSbfLibrary or lib.startswith('sbf')
		libsExpanded.append( expandNameOfLibrary(sbf, lib) )
	return (libsExpanded, containsSbfLibrary)

###
def isLaunchProject( lenv ):
	return lenv['sbf_launchProject'] == lenv['sbf_project']

def updateParentProjects( lenv, parentProjects ):
	# Part inherited
	if parentProjects is None:
		lenv['sbf_parentProjects'] = []
	else:
		lenv['sbf_parentProjects'] = parentProjects

	# Updates using 'deploymentType' of the current project
	if lenv['deploymentType'] in ['standalone', 'embedded']: # do nothing for 'none' project
		lenv['sbf_parentProjects'].append( lenv )
		if len(lenv['sbf_parentProjects'])>1:
			project1 = lenv['sbf_parentProjects'][0]['sbf_project']
			project2 = lenv['sbf_parentProjects'][1]['sbf_project']
			raise SCons.Errors.UserError( "Encountered the following two projects '{0}' and '{1}' with deploymentType different to none. It's forbidden in the same build.".format(project1, project2) )
		#else nothing to do
	# else nothing to do

	# Debug
	#print self.myProject + ' owned by',
	#for project in lenv['sbf_parentProjects']:
	#	print project['sbf_project'],
	#print



### SHARE BUILD HELPERS ###
def computeFiltersAndCommand( lenv ):
	"""Computes filters and command.
	@todo shareBuild	=	( filters, 'blowfish' ) => shareBuild	=	[( filters, 'blowfish' ),...]"""
	filters = lenv['shareBuild'][0]
	command = lenv['shareBuild'][1]
	if len(filters) > 0:
		if isinstance(command, str):
			if command in lenv['userDict']:
				command = lenv['userDict'][command]
			else:
				if lenv.GetOption('verbosity'): print ("Skip share build stage, because userDict['{0}'] is not defined.".format( command ))
				filters = []
				command = ('','','')
		#else nothing to do
	return filters, command

def applyFilters( files, filters ):
	"""Uses 'filters' to split the 'files' list into two subset of the list.
	The first one contains the list of files that match at least one filter. The second one contains all others files.
	@return (matchingFiles, nonMatchingFiles)."""
	matchingFiles		= []
	nonMatchingFiles	= []
	if len(filters) > 0:
		filters = [ (os.path.dirname(getNormalizedPathname(filter)), os.path.basename(filter)) for filter in filters ]
		for file in files:
			fileSplitted = os.path.split(file)
			for (directoryFilter, fileFilter) in filters:
				if	fnmatch.fnmatch(fileSplitted[0], directoryFilter) and \
					fnmatch.fnmatch(fileSplitted[1], fileFilter):
					matchingFiles.append( file )
					break
			else:
				nonMatchingFiles.append( file )
	else:
		nonMatchingFiles = files
	return matchingFiles, nonMatchingFiles


def buildFilesFromShare( files, sbf, projectEnv, command ):
	"""Adds share build stage in 'build' target
	@return the list of files to install in 'share'"""

	if len(files)==0:
		return []

	lenv = projectEnv.Clone()

	# list of files to install in 'share'
	outputs = []
	for file in files:
		inputFile = join(sbf.myProjectPathName, file)
# @todo check ${SOURCE}
		outputFile = command[1].replace('${SOURCE}', file, 1)
		outputFile = outputFile.replace('share', join(sbf.myProjectBuildPath, sbf.myProject, 'share'), 1 )
		if len(command)==3:
			Alias( 'build', lenv.Command(outputFile, inputFile, Action(command[0], command[2]) ) )
		else:
			Alias( 'build', lenv.Command(outputFile, inputFile, command[0]) )
		outputs.append( outputFile )
	return outputs


### INSTALLATION HELPERS ###
def computeInstallDirectories( lenv, myInstallDirectory ):
	"""Computes the desired installation directories.
	@return the computed installation directories, i.e. the list containing the given installation directory,
	the 'local/standalone/parentProjectVersion' for project 'lenv' having a parent project with a standalone 'deploymentType',
	the 'local/standalone/parentProjectVersionRequired/packages/projectVersion for project 'lenv' having a parent project with an embedded 'deploymentType' and 'deploymentPrecond',
	the 'local/packages/projectVersion' for project 'lenv' having a parent project with en embedded 'deploymentType' and no 'deploymentPrecond'."""
	installDirectories = [myInstallDirectory]
	if len(lenv['sbf_parentProjects']) == 0:
		# no parent project
		pass
	else:
		for parentEnv in lenv['sbf_parentProjects']:
			deploymentType = parentEnv['deploymentType']
			if deploymentType == 'standalone':
				subdir = '{0}_{1}'.format( parentEnv['sbf_project'], parentEnv['version'] )
				installDirectories.append( join( myInstallDirectory, 'standalone', subdir ) )
			elif deploymentType == 'embedded':
				packageSubdir = '{0}_{1}'.format( parentEnv['sbf_project'], parentEnv['version'] )
				if len(parentEnv['deploymentPrecond'])==0:
					installDirectories.append( join( myInstallDirectory, 'packages', packageSubdir ) )
				else:
					(name, operator, version) = splitDeploymentPrecond(parentEnv['deploymentPrecond'])
					standaloneSubdir = '{0}_{1}'.format( name, version )
					installDirectories.append( join( myInstallDirectory, 'standalone', standaloneSubdir, 'packages', packageSubdir ) )
			else:
				assert( False )
	return installDirectories


def removeAllFilesRO( directory ):
	if os.path.exists( directory ):
		# 'directory' is existing, so i have to remove all files from it manually (because of read-only chmod).
		oFiles = []
		searchAllFiles( directory, oFiles )
		for file in oFiles:
			if os.path.exists(file):
				os.chmod( file, 0744 )
				os.remove( file )
			#else nothing to do
	# else nothing to do

def installRO( target, source, env ):
	src = str(source[0])
	dst = str(target[0])
	dir = os.path.dirname( dst )
	if not os.path.exists(dir):
		os.makedirs( dir )
	else:
		if os.path.exists(dst):
			os.chmod( dst, 0744 )
	shutil.copyfile(src, dst) 
	os.chmod( dst, 0444 )
	return 0


### DEPS ###
def getStdlibs( lenv, searchPathList ):
	stdlibs = []
	# Processes the 'stdlibs' project option
	for stdlib in lenv.get( 'stdlibs', [] ):
		filename = splitext(stdlib)[0] + lenv['SHLIBSUFFIX']
		pathFilename = searchFileInDirectories( filename, searchPathList )
		if pathFilename:
			if lenv.GetOption('verbosity'): print('Found standard library {0}', pathFilename)
			stdlibs.append( pathFilename )
		else:
			print("Standard library {0} not found (see 'stdlibs' project option of {1}).".format(filename, lenv['sbf_project']) )
	return stdlibs


def getDepsFiles( lenv, baseSearchPathList, forced = False ):
	def collectDepsFilesForPackage( pakSystem, useName, useVersion, lenv, depsFiles ):
		"""@param depsFiles		files of package (useName,useVersion) are appended to depsFiles"""
		if pakSystem.isInstalled( useName ):
			# installed
			oPakInfo = {}
			oRelDirectories = []
			oRelFiles = []
			pakSystem.loadPackageInfo( useName, oPakInfo, oRelDirectories, oRelFiles )
			if oPakInfo['version'] != useVersion:
				raise SCons.Errors.UserError( '{0} {1} is installed, but {2} is needed.'.format(useName, oPakInfo['version'], useVersion))
			if lenv.GetOption('verbosity'):	print ( 'Collecting all files found in installed package {0} {1}'.format(oPakInfo['name'], oPakInfo['version']) )
			for relFile in oRelFiles:
				absFile = join( lenv.sbf.myInstallDirectory, relFile )
				depsFiles.append( (absFile, relFile) )
		else:
			# not installed
			raise SCons.Errors.UserError( '{0} {1} is NOT installed.'.format(useName, useVersion))

	depsFiles = []
	licensesFiles = []
	sbf = lenv.sbf

	if forced or (lenv['deploymentType'] in ['standalone', 'embedded']):
		allDeps = sbf.getAllDependencies( lenv )
		allUses = sbf.getAllUses( lenv )
		if lenv.GetOption('verbosity'): print ('\nallDeps\n{0}\nallUses\n{1}\n'.format(allDeps, allUses))

		# 'stdlibs'
		for project in allDeps:
			localEnv = sbf.getEnv( project )
			# stdlibs
			stdlibs = getStdlibs( localEnv, baseSearchPathList )
			if len(stdlibs)>0:
				print stdlibs
				assert(False) # not yet implemented, @todo deprecated ?

		pakSystem = PackagingSystem(sbf, verbose=False)

		# Processes external dependencies (i.e. 'uses')
		# For each external dependency, do
		for useNameVersion in allUses:
			# Retrieves use, useName and useVersion
			useName, useVersion, use = UseRepository.gethUse( useNameVersion )
			if lenv.GetOption('verbosity'): print ("Processing uses='{}'...".format(useNameVersion))

			if use:
				### RUNTIME PACKAGE ###
				if use.hasRuntimePackage( useVersion ):
					allUseNames = [useName + '-runtime']
					if lenv['config'] == 'release':
						allUseNames.append( useName + '-runtime-release' )
					else:
						allUseNames.append( useName + '-runtime-debug' )
					for useName in allUseNames:
						collectDepsFilesForPackage( pakSystem, useName, useVersion, lenv, depsFiles )
				else:
				### NO RUNTIME PACKAGE ###
				### LIBS ###
					if use.getPackageType() == 'None':
						# nothing to do
						if lenv.GetOption('verbosity'): print ("No files for uses='{0}'...".format(useNameVersion))
					elif use.getPackageType() in ['NoneAndNormal', 'Normal']:
						# Retrieves LIBS of incoming dependency
						libs = use.getLIBS( useVersion )
						if libs and len(libs) == 2:
							# Computes the search path list where libraries could be located
							searchPathList = baseSearchPathList[:]
							libpath = use.getLIBPATH( useVersion )
							if libpath and (len(libpath) == 2): searchPathList.extend( libpath[1] )

							# For each library, do
							if lenv.GetOption('verbosity') and len(libs[1])==0: print ("No files for uses='{0}'...".format(useNameVersion))
							for file in libs[1]:
								filename = file + lenv['SHLIBSUFFIX']
								pathFilename = searchFileInDirectories( filename, searchPathList )
								if pathFilename:
									if lenv.GetOption('verbosity'):	print ("Found library {0} for uses='{1}'.".format(pathFilename, useName))
									splitPathFilename = os.path.split(pathFilename)
									depsFiles.append( (pathFilename, join('bin', splitPathFilename[1])) )
								else:
									raise SCons.Errors.UserError( "File {0} not found for uses='{1}'.".format(filename, useName) )
						else:
							raise SCons.Errors.UserError("Uses=[\'{0}\'] not supported on platform {1}.".format(useNameVersion, sbf.myPlatform) )
					else:
						# getPackageType() returns an unexpected value
						assert( False )

				### LICENSE ###
				if use.getPackageType() == 'None':
					# nothing to do
					pass
				elif use.getPackageType() == 'NoneAndNormal':
					# Retrieves license files of incoming dependency
					licenses = use.getLicenses( useVersion )
					for i, licenseSource in enumerate(licenses):
						licenseTarget = 'license.{0}{1}.{2}.txt'.format( useName, useVersion, i )
						licensesFiles.append( (licenseTarget, licenseSource) )
				elif use.getPackageType() == 'Normal':
					# Retrieves license files of incoming dependency from package
					if pakSystem.isInstalled( useName ):
						# installed
						oPakInfo = {}
						oRelDirectories = []
						oRelFiles = []
						pakSystem.loadPackageInfo( useName, oPakInfo, oRelDirectories, oRelFiles )
						if oPakInfo['version'] != useVersion:
							raise SCons.Errors.UserError( '{0} {1} is installed, but {2} is needed.'.format(useName, oPakInfo['version'], useVersion))
						if lenv.GetOption('verbosity'):	print ( 'Collecting license files found in installed package {0} {1}'.format(oPakInfo['name'], oPakInfo['version']) )
						for relFile in oRelFiles:
							licensePrefix = 'license' + os.sep
							if relFile.find(licensePrefix) == 0:
								#print 'FOUND', (os.path.basename(relFile), join( sbf.myInstallExtPaths[0], relFile ) )
								licensesFiles.append( (os.path.basename(relFile), join(sbf.myInstallExtPaths[0], relFile) ) )
					else:
						raise SCons.Errors.UserError( '{0} {1} is NOT installed.'.format(useName, useVersion))
				else:
					# getPackageType() returns an unexpected value
					assert( False )
			else:
				raise SCons.Errors.UserError("Uses=[\'{0}\'] not supported on platform {1}.".format(useNameVersion, sbf.myPlatform) )
	# do nothing for 'none' project

	return depsFiles, licensesFiles


### RUN ###
def searchExecutable( lenv, nodeList ):
	for node in nodeList:
		if node.suffix == lenv['PROGSUFFIX']:
			return node


### ZIP/NSIS ###
from sbfNSIS import initializeNSISInstallDirectories, configureZipAndNSISTargets


### INFO FILE ###
from sbfInfo import configureInfofileTarget, configureInfoTarget


###### Toolchains ######
# @todo move into sbfToolchains.py
def removeOption( env, key, option = '-c' ):
	"""Remove first occurrence of ' option ' from env[key]"""
	newValue = env[key].replace(' {} '.format(option), ' ', 1)
	env[key] = newValue

### MSVC ###
# export SCONS_MSCOMMON_DEBUG=ms.log
# HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.0A\InstallationFolder

def createEnvMSVC( sbf, tmpEnv, myTools ):
	myTools += ['msvc', 'mslib', 'mslink']

	dictTranslator = { 'x86-32' : 'x86', 'x86-64' : 'x86_64' }
	targetArch = dictTranslator[ tmpEnv['targetArchitecture'] ]
	if tmpEnv['clVersion'] != 'highest':
		myMsvcVersion = tmpEnv['clVersion']
		myMsvcYear = clVersionNumToYear.get(myMsvcVersion, myMsvcVersion)
		# Tests existance of the desired version of cl
		if myMsvcVersion not in getInstalledCLVersionNum():
			print ('sbfError: MS Visual C++ desired version is not installed in the system.')
			print ('Requested version is Visual C++ {}({}).'.format(myMsvcYear, myMsvcVersion))
			printInstalledCL()
			print ("See 'clVersion' option in SConsBuildFramework.options to fix the problem.")
			Exit(1)
	else:
		myMsvcVersion = None

	return Environment( options = sbf.mySBFOptions, tools = myTools, TARGET_ARCH = targetArch, MSVC_VERSION = myMsvcVersion )

def setupMSVC( sbf ):
	# Extracts version number
	# Step 1 : Extracts x.y (without Exp if any)
	ccVersion				=	sbf.myEnv['MSVS_VERSION'].replace('Exp', '', 1)
	# Step 2 : Extracts major and minor version
	splittedCCVersion		=	ccVersion.split( '.', 1 )
	# Step 3 : Computes version number
	sbf.myCCVersionNumber	= computeVersionNumber( splittedCCVersion )
	# Constructs myCCVersion ( clMajor-Minor[Exp] )
	sbf.myIsExpressEdition = sbf.myEnv['MSVS_VERSION'].find('Exp') != -1
	sbf.myCCVersion = sbf.myCC + getVersionNumberString2( sbf.myCCVersionNumber )
	if sbf.myIsExpressEdition:
		# Adds 'Exp'
		sbf.myCCVersion += 'Exp'
	sbf.myEnv['CCVERSION'] = sbf.myCCVersion

	if sbf.myCCVersionNumber >= 12.0:
		sbf.myMSVSIDE = sbf.myEnv.WhereIs( 'devenv.exe' )
	elif sbf.myCCVersionNumber >= 11.0:
		sbf.myMSVSIDE = sbf.myEnv.WhereIs( 'WDExpress' )
	else:
		sbf.myMSVSIDE = sbf.myEnv.WhereIs( 'VCExpress' )

	sbf.myMSVCVARS32 = sbf.myEnv.WhereIs( 'vcvars32.bat' )
	if sbf.myMSVCVARS32:
		sbf.myVCVARSALL = sbf.myEnv.WhereIs( 'vcvarsall.bat', join( dirname(sbf.myMSVCVARS32), '..' ) )
	else:
		sbf.myVCVARSALL = None
	# Assuming that the parent directory of cl.exe is the root directory of MSVC (i.e. C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC)
	sbf.myMSVC = dirname( sbf.myEnv.WhereIs( 'cl.exe' ) )
	sbf.myMSBuild = sbf.myEnv.WhereIs( 'msbuild.exe' )

#			print sbf.myEnv.WhereIs( 'signtool.exe' )

	if sbf.myEnv.GetOption('verbosity'):
		print 'Visual C++ version {0} installed.'.format( sbf.myEnv['MSVS_VERSION'] )
		if sbf.myMSVSIDE and len(sbf.myMSVSIDE)>0:
			print ("Found {0} in '{1}'.".format(basename(sbf.myMSVSIDE), sbf.myMSVSIDE))
		else:
			print ('Visual C++ IDE (VCExpress.exe, WDExpress.exe or devenv.exe) not found.')

		if sbf.myMSVCVARS32 and len(sbf.myMSVCVARS32)>0:
			print ("Found vcvars32.bat in '{0}'.".format(sbf.myMSVCVARS32))
		else:
			print ('vcvars32.bat not found.')

		if sbf.myVCVARSALL and len(sbf.myVCVARSALL)>0:
			print ("Found vcvarsall.bat in '{0}'.".format(sbf.myVCVARSALL))
		else:
			print ('vcvarsall.bat not found.')

		if sbf.myMSVC and len(sbf.myMSVC)>0:
			print ("Found MSVC in '{0}'.".format(sbf.myMSVC))
		else:
			print ('MSVC not found.')

		if sbf.myMSBuild and len(sbf.myMSBuild)>0:
			print ("Found MSBuild in '{0}'.".format(sbf.myMSBuild))
		else:
			print ('MSBuild not found.')

def configureMSVC(sbf, lenv):
	# Useful for cygwin 1.7
	# The Microsoft linker requires that the environment variable TMP is set.
	if not os.getenv('TMP'):
		lenv['ENV']['TMP'] = sbf.myBuildPath
		if GetOption('verbosity') : print ('TMP sets to {}'.format(sbf.myBuildPath))

	# Adds support of Microsoft Manifest Tool for Visual Studio 2005 (cl8) and up
	if sbf.myCCVersionNumber >= 8.000000 :
		lenv['WINDOWS_INSERT_MANIFEST'] = True

	# 64 bits support
	if sbf.myArch == 'x86-64':
		lenv.Append( LINKFLAGS = '/MACHINE:X64' )
		lenv.Append( ARFLAGS = '/MACHINE:X64' )

	# Compiler/linker command line flags
	if sbf.myCCVersionNumber >= 11.000000:
		#if sbf.myConfig == 'release' and lenv['generateDebugInfoInRelease']:
			# @remark add /d2Zi+ undocumented flags in Visual C++ (at least 2012) to improve debugging experience in release configuration (local variable, inline function...)
			# see http://randomascii.wordpress.com/2013/09/11/debugging-optimized-codenew-in-visual-studio-2012/
			#lenv.Append( CXXFLAGS = ['/d2Zi+'] )
		lenv.Append( LINKFLAGS = '/MANIFEST' )
		lenv.Append( CXXFLAGS = ['/GS-', '/EHsc'] )
		if sbf.myCCVersionNumber >= 12.0: lenv.Append( CXXFLAGS = ['/FS'] )
	elif sbf.myCCVersionNumber >= 10.000000 :
		lenv.Append( LINKFLAGS = '/MANIFEST' )
		lenv.Append( CXXFLAGS = ['/GS-', '/EHsc'] )
	elif sbf.myCCVersionNumber >= 9.000000 :
		lenv.Append( LINKFLAGS = '/MANIFEST' )
		lenv.Append( CXXFLAGS = ['/GS-', '/EHsc'] )
		#lenv.Append( CXXFLAGS = ['/MP'] )
	elif sbf.myCCVersionNumber >= 8.000000 :
		# /GX is deprecated in Visual C++ 2005
		lenv.Append( CXXFLAGS = ['/GS-', '/EHsc'] ) # @todo FIXME : '/GS-' for SOFA !!!
	elif sbf.myCCVersionNumber >= 7.000000 :
		lenv.Append( CXXFLAGS = '/GX' )
		if sbf.myConfig == 'release' :
			lenv.Append( CXXFLAGS = '/Zm600' )

	# /TP : Specify Source File Type (C++) => adds by SCons
	# /GR : Enable Run-Time Type Information
	lenv.AppendUnique( CXXFLAGS = '/GR' )

	lenv.AppendUnique( CXXFLAGS = '/bigobj' ) # see C1128

	# Defines
	lenv.Append( CXXFLAGS = ['/DWIN32', '/D_WINDOWS', '/DNOMINMAX'] )
	# bullet uses _CRT_SECURE_NO_WARNINGS,_CRT_SECURE_NO_DEPRECATE,_SCL_SECURE_NO_WARNINGS
	lenv.Append( CXXFLAGS = ['/D_CRT_SECURE_NO_WARNINGS', '/D_CRT_SECURE_NO_DEPRECATE', '/D_SCL_SECURE_NO_WARNINGS'] )

	#lenv.Append( CXXFLAGS = ['/wd4251'] ) # see in MSDN C4251

	#lenv.Append( CXXFLAGS = ['/D_BIND_TO_CURRENT_VCLIBS_VERSION=1'] )
	#lenv.Append( CXXFLAGS = ['/MP{0}'.format(sbf.myNumJobs)] )

	if sbf.myConfig == 'release' :							### @todo use /Zd in release mode to be able to debug a little.
		lenv.Append( CXXFLAGS = ['/DNDEBUG'] )
		lenv.Append( CXXFLAGS = ['/MD', '/O2'] )			# /O2 <=> /Og /Oi /Ot /Oy /Ob2 /Gs /GF /Gy
		#lenv.Append( CXXFLAGS = ['/GL'] )
		if lenv['generateDebugInfoInRelease']:
			lenv.Append( CXXFLAGS = ['/Oy-'] ) # Disabled frame-pointer omission (help debugging)
			lenv['CCPDBFLAGS'] = ['/Zi', '"/Fd${PDB}"']
	else:
		lenv.Append( CXXFLAGS = ['/D_DEBUG', '/DDEBUG'] )
		# /Od : Disable (Debug)
		lenv.Append( CXXFLAGS = ['/MDd', '/Od'] )
		# Enable Function-Level Linking
		lenv.Append( CXXFLAGS = ['/Gy'] )
		lenv['CCPDBFLAGS'] = ['/Zi', '"/Fd${PDB}"']

		# /Yd is deprecated in Visual C++ 2005; Visual C++ now supports multiple objects writing to a single .pdb file,
		# use /Zi instead (Microsoft Visual Studio 2008/.NET Framework 3.5).

		# /Zi : Produces a program database (PDB) that contains type information and symbolic debugging information
		# for use with the debugger. The symbolic debugging information includes the names and types of variables,
		# as well as functions and line numbers. Using the /Zi instead may yield improved link-time performance,
		# although parallel builds will no longer work. You can generate PDB files with the /Zi switch by overriding
		# the default $CCPDBFLAGS variable
		# /ZI : Produces a program database in a format that supports the Edit and Continue feature.
		# /Gm : Enable Minimal Rebuild.

	# Warnings
	if sbf.myWarningLevel == 'normal' :		### @todo it is dependent of the myConfig. Must be changed ? yes, do it...
		lenv.Append( CXXFLAGS = '/W3' )
	else:
		# /Wall : Enables all warnings
		lenv.Append( CXXFLAGS = ['/W4', '/Wall'] )

### gcc ###
def createEnvGCC( sbf, tmpEnv, myTools ):
	# @todo takes care of tmpEnv['targetArchitecture'], TARGET_ARCH = targetArch ?
	return Environment( options = sbf.mySBFOptions, tools = myTools )

def setupGCC(sbf):
	# Extracts version number
	# Step 1 : Extracts x.y.z
	ccVersion				=	sbf.myEnv['CCVERSION']
	# Step 2 : Extracts major and minor version
	splittedCCVersion		=	ccVersion.split( '.', 2 )
	if len(splittedCCVersion) !=  3 :
		raise SCons.Errors.UserError( "Unexpected version schema for gcc compiler (expected x.y.z) : %s " % ccVersion )
	# Step 3 : Computes version number
	sbf.myCCVersionNumber = computeVersionNumber( splittedCCVersion[:2] )
	# Constructs myCCVersion ( gccMajor-Minor )
	sbf.myCCVersion = sbf.myCC + getVersionNumberString2( sbf.myCCVersionNumber )

def configureGCC(sbf, lenv):
	lenv['CXX'] = lenv.WhereIs('g++')											### FIXME: remove me
																				### myCxxFlags += ' -pedantic'
	if ( sbf.myConfig == 'release' ) :
		lenv.Append( CXXFLAGS = ['-DNDEBUG', '-O3'] )
	else:
		lenv.Append( CXXFLAGS = ['-D_DEBUG', '-DDEBUG', '-g', '-O0'] )
		### profiling myCxxFlags += ' -pg', mpatrol, leaktracer

	# process myWarningLevel, adds always -Wall option.
	lenv.Append( CXXFLAGS = '-std=c++11' )
	lenv.Append( CXXFLAGS = '-msse2' )
	lenv.Append( CXXFLAGS = '-Wall' )
	lenv.Append( CXXFLAGS = '-Wno-deprecated' )
	# @todo remove me
	lenv.Append( CXXFLAGS = '-fpermissive' )
#		lenv.Append( CXXFLAGS = '-fvisibility=hidden' )
	lenv.Append( CXXFLAGS = '-fvisibility-inlines-hidden' )
#		lenv.Append( CXXFLAGS = '-fvisibility-ms-compat' )
#		lenv.Append( LINKFLAGS = '-Wl,-rpath=%s' % os.path.join( sbf.myInstallDirectory, 'lib' ) )
	lenv.Append( LINKFLAGS = '-Wl,-rpath=.' )

### emcc ###
# helpers for emcc
def emccAppend( lenv, value ):
	"""	@brief Append to CXXFLAGS and LINKFLAGS the given value
		@param value	value to add lenv.Append( CXXFLAGS/LINKFLAGS = value )"""
	lenv.Append( CXXFLAGS = value )
	lenv.Append( LINKFLAGS = value )

def emccAppendSettings( lenv, value ):
	"""	@brief Append to CXXFLAGS and LINKFLAGS the given value
		@param value	adds -s value (could be "DEMANGLE_SUPPORT=1")"""
	lenv.Append( CXXFLAGS = ['-s', value] )
	lenv.Append( LINKFLAGS = ['-s', value] )

def createEnvEMCC( sbf, tmpEnv, myTools ):
	myTools += ['mingw']

	emscriptenSCons = getEmscriptenSCons()
	if not emscriptenSCons or not exists(emscriptenSCons):
		if 'updateemscripten' in sbf.myBuildTargets:
			# Creates an environment to continue the construction of SConsBuildFramework.
			# Installation/update of emscripten occurs after.
			return Environment( options = sbf.mySBFOptions, tools = myTools )
		else:
			print ("sbfError: emscripten is not installed and/or configured. Try 'sbf updateEmscripten' to resolve this problem.")
			Exit(1)

	myEnv = Environment( options = sbf.mySBFOptions, tools = myTools )
	myEnv.Tool('emscripten', toolpath=[emscriptenSCons])
	# Previous line configure CC with EMSCRIPTEN_ROOT/emcc. The following lines reduces the length of the command lines
	# by removing EMSCRIPTEN_ROOT (it is in PATH).
	myEnv.Replace(CC     = 'emcc'    )
	myEnv.Replace(CXX    = 'emcc'    )
	myEnv.Replace(LINK   = 'emcc'    )
	myEnv.Replace(AR     = 'emar'    )
	arcomWithoutSOURCES = myEnv['ARCOM'].replace('$SOURCES', '')
	myEnv.Replace( ARCOM  = "{arcom} ${{TEMPFILE('$SOURCES')}}".format(arcom=arcomWithoutSOURCES) )
	myEnv.Replace( RANLIB = 'emranlib')

	removeOption( myEnv, 'CCCOM' )
	removeOption( myEnv, 'CXXCOM' )
	removeOption( myEnv, 'SHCCCOM' )
	removeOption( myEnv, 'SHCXXCOM' )

	if tmpEnv['printCmdLine'] == 'less':
		myEnv.Replace(CXXCOMSTR		= "${SOURCE.file}")
		myEnv.Replace(SHCXXCOMSTR	= "${SOURCE.file}")
		myEnv.Replace(LINKCOMSTR	= "Linking ${TARGET.file}")
		myEnv.Replace(ARCOMSTR		= "Archiving ${TARGET.file}")

	# BEGIN	: FOR DEBUGGING
	#myEnv['ENV']['EMCC_DEBUG'] = 1
	# END	: FOR DEBUGGING

	#
	configureEmscripten( myEnv, myEnv.GetOption('verbosity') )
	return myEnv

def setupEMCC(sbf):
	sbf.myEnv['CC'] = basename(sbf.myEnv['CC'])
	sbf.myCC = sbf.myEnv['CC']

	# Extracts version number of emscripten
	# Step 1 : Extracts x.y.z
	ccVersion = basename(getEmscriptenRoot())
	if ccVersion == 'master':
		# 'ccVersion' has to be modified manually using informations from $SCONS_BUILD_FRAMEWORK\runtime\emsdk\clang\fastcomp\src\emscripten-version.txt
		ccVersion = '1.33.0'
	# Step 2 : Extracts major and minor version
	splittedCCVersion = ccVersion.split( '.', 2 )
	if len(splittedCCVersion) !=  3:
		raise SCons.Errors.UserError( "Unexpected version schema for emscripten compiler (expected x.y.z) : {} ".format( ccVersion ) )
	# Step 3 : Computes version number
	sbf.myCCVersionNumber = computeVersionNumber( splittedCCVersion[:2] )
	# Constructs myCCVersion ( gccMajor-Minor )
	sbf.myCCVersion = sbf.myEnv['CC'] + getVersionNumberString2( sbf.myCCVersionNumber )
	sbf.myEnv['CCVERSION'] = sbf.myCCVersion

def configureEMCC(sbf, lenv):
	"""	CPPDEFINES=__EMSCRIPTEN__ (defined by emcc)
		For CXXFLAGS, see https://github.com/kripken/emscripten/blob/master/src/settings.js
		"""

	#CCFLAGS
	#CXXFLAGS, ARFLAGS, LINKFLAGS

	lenv.Append( CXXFLAGS = ['-std=c++11'] )

#	To uncomment to ease debugging
#	emccAppendSettings( lenv, 'DEMANGLE_SUPPORT=1' )

	#emccAppendSettings( lenv, 'EMTERPRETIFY=1' )
	#emccAppendSettings( lenv, 'EMTERPRETIFY_ASYNC=1' )
	#emccAppendSettings( lenv, 'EMTERPRETIFY_WHITELIST=[\\"_readFromSocket\\"]' )
	#emccAppendSettings( lenv, 'EMTERPRETIFY_ADVISE=1' )

	emccAppendSettings( lenv, 'ALLOW_MEMORY_GROWTH=1' )
	#	defaultTotalMemory = 1024 * 1024 * 16		# 16 MB
	#	emccAppendSettings( lenv, 'TOTAL_MEMORY={}'.format(defaultTotalMemory) )

	#emccAppendSettings( lenv, 'INLINING_LIMIT=1' )

	#emccAppendSettings( lenv, 'ERROR_ON_UNDEFINED_SYMBOLS=1' )

	if sbf.myConfig == 'release':
		#To re-enable exceptions in optimized code, run emcc with -s DISABLE_EXCEPTION_CATCHING=0
		emccAppendSettings(lenv, 'DISABLE_EXCEPTION_CATCHING=0')
		#emccAppendSettings(lenv, 'DISABLE_EXCEPTION_CATCHING=1')
		emccAppend( lenv, ['-DNDEBUG', '-O3'] )

		#emccAppendSettings(lenv, 'OUTLINING_LIMIT=20000')
		#emccAppendSettings(lenv, 'INLINING_LIMIT=1')
		#emccAppend( lenv, '--llvm-lto 1' )
	else:
		emccAppend( lenv, 'ASSERTIONS=1' )
		emccAppend( lenv, ['-D_DEBUG', '-DDEBUG', '-g', '-O2', '--profiling-funcs'] )

	# process myWarningLevel, adds always -Wall option.
	#lenv.Append( CXXFLAGS = '-Wall' )
	lenv.Append( CXXFLAGS = '-Wno-warn-absolute-paths' )
	lenv.Append( LINKFLAGS = '-Wno-warn-absolute-paths' )

	lenv['OBJSUFFIX'] = lenv['SHOBJSUFFIX'] = '.o'
	lenv['LIBSUFFIX'] = lenv['SHLIBSUFFIX'] = '.a'

	lenv['_LIBFLAGS'] = ' -Wl,--start-group {} -Wl,--end-group '.format( lenv['_LIBFLAGS'] )


	#-s GL_ASSERTIONS=1 and -s GL_DEBUG=1 and -s LEGACY_GL_EMULATION=1
	# @todo verbose mode -v

	# lenv.Prepend( CXXFLAGS = '--bind' )
	# lenv.Prepend( LINKFLAGS = '--bind' )
	# lenv.Prepend( SHLINKFLAGS = '--bind' ) 

### call Object(), Program(), StaticLibrary(), SharedLibrary()... ###
def setupBuildingRulesSConsDefault(sbf, lenv, objFiles, objProject, installInBinTarget):
	"""	@param lenv		SCons environment to be configured to build the project (using SCons api)
		@param ...
		@return objFiles, installInBinTarget, lenv modified using SCons api, lenv['sbf_src'], lenv['sbf_bin_debuginfo']
	"""
	filesFromSrc = sbf.getFiles( 'src', lenv )
	lenv['sbf_src'] = filesFromSrc

	if sbf.myType in ['exec', 'static']:
		# Compiles source files
		for srcFile in filesFromSrc:
			objFile = (splitext(srcFile)[0]).replace('src', sbf.myProjectBuildPathExpanded, 1 )
			# Object is a synonym for the StaticObject builder method.
			objFiles.append( lenv.Object( objFile, join(sbf.myProjectPathName, srcFile) ) )
		# Creates executable or static library
		if sbf.myType == 'exec':
			# executable
			projectTarget = lenv.Program( objProject, objFiles )
		else:
			# static library
			projectTarget = lenv.StaticLibrary( objProject, objFiles )
	elif sbf.myType == 'shared':
		# Compiles source files
		for srcFile in filesFromSrc:
			objFile = (splitext(srcFile)[0]).replace('src', sbf.myProjectBuildPathExpanded, 1 )
			objFiles.append( lenv.SharedObject( objFile, join(sbf.myProjectPathName, srcFile) ) )
		# Creates shared library
		projectTarget = lenv.SharedLibrary( objProject, objFiles )

		if sbf.myPlatform == 'win':
			# filter *.exp file
			filteredProjectTarget = []				# @todo uses comprehension list
			for elt in projectTarget:
				if splitext(elt.name)[1] != '.exp':
					filteredProjectTarget.append(elt)
			projectTarget = filteredProjectTarget
		# else no filtering
	else:
		assert( sbf.myType == 'none' )
		projectTarget = None

	if projectTarget:
		# Installation part
		installInBinTarget.extend( projectTarget )
		# projectTarget is not deleted before it is rebuilt.
		lenv.Precious( projectTarget )

		# @todo /PDBSTRIPPED:pdb_file_name
		# Generating debug informations
		if sbf.myPlatform == 'win':
			if lenv['generateDebugInfoInRelease'] or sbf.myConfig == 'debug':
				# PDB Generation. Static library don't generate pdb.
				if sbf.myType in ['exec', 'shared']:
					lenv['PDB'] = objProject + '.pdb'
					lenv.SideEffect( lenv['PDB'], projectTarget )
					# it is not deleted before it is rebuilt.
					lenv.Precious( lenv['PDB'] )
					lenv['sbf_bin_debuginfo'] = lenv['PDB']
				# else nothing to do
			# else nothing to do
		# else nothing to do
	return projectTarget

# var INCLUDE_FULL_LIBRARY = 0; // Whether to include the whole library rather than just the
# // functions used by the generated code. This is needed when
# // dynamically loading modules that make use of runtime
# // library functions that are not used in the main module.
# // Note that this includes js libraries but *not* C. You will
# // need the main file to include all needed C libraries. For
# // example, if a library uses malloc or new, you will need
# // to use those in the main file too to link in dlmalloc.

# var LINKABLE = 0; // If set to 1, this file can be linked with others, either as a shared
# // library or as the main file that calls a shared library. To enable that,
# // we will not internalize all symbols and cull the unused ones, in other
# // words, we will not remove unused functions and globals, which might be
# // used by another module we are linked with.
# // BUILD_AS_SHARED_LIB > 0 implies this, so it is only important to set this to 1
# // when building the main file, and *if* that main file has symbols that
# // the library it will open will then access through an extern.
# // LINKABLE of 0 is very useful in that we can reduce the size of the
# // generated code very significantly, by removing everything not actually used.

# var RUNNING_JS_OPTS = 0; // whether js opts will be run, after the main compiler
# var RUNNING_FASTCOMP = 1; // whether we are running the fastcomp backend
def setupBuildingRulesEmscripten(sbf, lenv, objFiles, objProject, installInBinTarget):
	filesFromSrc = sbf.getFiles( 'src', lenv )
	lenv['sbf_src'] = filesFromSrc

	if lenv['embindStage']:
		embindEnv = lenv.Clone()
		emccAppend( embindEnv, ['--bind'] )

		if lenv['config'] == 'release':
			# @todo with -O2, the js file seems to be not usable.
			emccAppend( embindEnv, ['-O1'] )

	for (setting, value) in lenv['emccSettings'].iteritems():
		if lenv.GetOption('verbosity'):	print ('Adding emcc settings {}={}'.format(setting, value))
		emccAppendSettings(lenv, '{}={}'.format(setting, value))

	# build each files
	bcFiles = []
	if sbf.myType in ['exec', 'static']:
		# Compiles source files
		for srcFile in filesFromSrc:
			bcFile = splitext(srcFile)[0].replace('src', sbf.myProjectBuildPathExpanded, 1 )
			bcFiles.append( bcFile )
			objFiles.append( lenv.StaticObject(bcFile, join(sbf.myProjectPathName, srcFile)) )
	elif sbf.myType == 'shared':
		# Compiles source files
		for srcFile in filesFromSrc:
			bcFile = splitext(srcFile)[0].replace('src', sbf.myProjectBuildPathExpanded, 1 )
			bcFiles.append( bcFile )
			objFiles.append( lenv.SharedObject(bcFile, join(sbf.myProjectPathName, srcFile)) )
	else:
		assert( sbf.myType == 'none' )
		projectTarget = None

	# 'share'
	filesFromShare = sbf.getFiles('share', lenv)
	if len(filesFromShare)>0:
		shareDir = join(sbf.myProjectPathName, 'share')
	else:
		shareDir = None

	# Generate executable (html and js) or library (static or shared)
	if sbf.myType == 'exec':
		# Creates executable (.js)
		emccAppendSettings( lenv, 'LINKABLE=0' )
		projectTarget = lenv.Program( objProject + '.js', bcFiles )
		lenv.SideEffect( objProject + '.js.mem', objProject + '.js')
		projectTarget.append( File(objProject + '.js.mem') )

		# Creates executable (.html)
		projectTarget.extend( lenv.Program( objProject + '.html', bcFiles ) )
		lenv.SideEffect( objProject + '.html.mem', objProject + '.html' )
		projectTarget.append( File(objProject + '.html.mem') )


		# @todo --preload-file
		#lenv.Append(LINKFLAGS = '--preload-file {}@/'.format(objProject + '.html.mem'))
		if shareDir:
			lenv.Append(LINKFLAGS = '--embed-file {}@/share'.format(shareDir))
			#projectTarget.append( File(objProject + '.data') )
	elif sbf.myType == ['static', 'shared']:
		# Appending all generated bytecodes
		emccAppendSettings( lenv, 'EXPORT_ALL=1' )
		emccAppendSettings( lenv, 'LINKABLE=1' )
		projectTarget = lenv.StaticLibrary( objProject, bcFiles )
		if lenv['embindStage']:	projectTarget.extend( embindEnv.Program( objProject + '.js', bcFiles ) )
	#elif sbf.myType == 'shared':
	#	# Appending all generated bytecodes
	#	projectTarget = lenv.StaticLibrary( objProject, bcFiles )
	#	if lenv['embindStage']:	projectTarget.extend( embindEnv.Program( objProject + '.js', bcFiles ) )

	if projectTarget:
		# Installation part
		installInBinTarget.extend( projectTarget )

	return projectTarget

### toolchains registry ###
# clang status http://clang.llvm.org/cxx_status.html
# by default, at least C++98, C++ exceptions and C++ RTTI
# C++11 (see http://clang.llvm.org/docs/LanguageExtensions.html#cxx11)
#def createEnvForToolchain( sbf, tmpEnv, myTools ):
#	return Environment()

#def setupToolchain( sbf ):
#	"""	Have to initialize self.myCCVersionNumber and self.myCCVersion
#		Ensure that myEnv['CCVERSION'] is correct"""

#def configureToolchain( sbf, env ):
	#env['ARFLAGS'... CXXFLAGS, LINKFLAGS...] = ...

registryToolchains = {
	'msvc'		: [createEnvMSVC,	setupMSVC,	configureMSVC,	setupBuildingRulesSConsDefault],
	'gcc'		: [createEnvGCC,	setupGCC,	configureGCC,	setupBuildingRulesSConsDefault],
	'emcc'		: [createEnvEMCC,	setupEMCC,	configureEMCC,	setupBuildingRulesEmscripten] }

###### SConsBuildFramework main class ######
class SConsBuildFramework :

	# targets
	mySbfTargets					= set( ['sbfcheck', 'sbfpak', 'sbfconfigure', 'sbfunconfigure', 'sbfconfiguretools', 'sbfunconfiguretools'] )
	mySvnTargets					= set( ['svnadd', 'svncheckout', 'svnclean', 'svnrelocate', 'svnstatus', 'svnupdate'] )
	mySvnBranchOrTagTargets			= set( ['svnmktag', 'svnremotemkbranch'] )
	myInformationsTargets			= set( ['info', 'infofile'] )
	myBuildingTargets				= set( ['pakupdate', 'all', 'clean', 'mrproper'] )
	myTestTargets					= set( ['test'] ) # @todo test_clean and test_mrproper
	myRunTestTargets				= set( ['onlyruntest', 'runtest'] )
	myRunTargets					= set( ['onlyrun', 'run'] )
	myVCProjTargets					= set( ['vcproj', 'vcproj_clean', 'vcproj_mrproper'] )
	myDoxTargets					= set( ['dox', 'dox_clean', 'dox_mrproper'] )
	# @todo 'zipruntime', 'zipdeps', 'zipdev', 'zipsrc', 'zip', 'zip_clean', 'zip_mrproper', 'nsis_clean', 'nsis_mrproper'
	myZipTargets					= set( ['portable', 'zipportable', 'dbg', 'zipdbg', 'nsis'] )
	myEmscriptenTargets  			= set( ['updateemscripten'] )

	myTargetsHavingToBuildTest		= myTestTargets | myRunTestTargets
	myTargetsHavingToBuildTest.add('pakupdate')

	myTargetsWhoNeedDeps			= set( ['deps', 'portable', 'zipportable', 'nsis'] )
	myTargetsAllowingWeakReading	= set( ['svncheckout', 'svnupdate'] )

	myAllTargets = mySbfTargets | mySvnTargets | mySvnBranchOrTagTargets | myInformationsTargets | myBuildingTargets | myTestTargets | myRunTestTargets | myRunTargets | myVCProjTargets | myDoxTargets | myZipTargets | myEmscriptenTargets

	# Command-line options
	myCmdLineOptionsList			= ['debug', 'release']
	myCmdLineOptions				= set( myCmdLineOptionsList )


	# sbf environment
	mySCONS_BUILD_FRAMEWORK			= ''
	mySbfLibraryRoot				= ''

	# SCons environment
	myCurrentToolChain				= None
	myEnv							= None
	myCurrentLocalEnv				= None			# contains the lenv of the current project

		# lenv['sbf_*'] listing
		#
		# sbf_projectPathName
		# sbf_projectPath
		# sbf_project
		# sbf_parentProjects
		# sbf_libsExpanded

		# sbf_version_major
		# sbf_version_minor
		# sbf_version_maintenance
		# sbf_version_postfix
		# sbf_my_FullPostfix

		# sbf_projectGUID
		#@todo completes this list

	# Options for SConsBuildFramework
	mySBFOptions					= None

	# Options for project
	myProjectOptions				= None

	# Global attributes from command line
	myBuildTargets					= set()		# 'all' if no target is specified, without command line options (like 'debug'...)
	myCurrentCmdLineOptions			= set()
	#myGHasCleanOption				= False

	# Globals attributes

	# haveToBuildTest
	# tryVcsCheckout
	# tryVcsUpdate

	# tryVcsClean
	# tryVcsAdd

	# tryVcsStatus
	# tryVcsRelocate
	# tryVcsMkTag
	# tryVcsRemoteMkBranch

	# tryVcsOperation

	myCurrentTime					= None			# time.localtime()
	myTimePostFix					= ''
	myDate							= ''
	myTime							= ''
	myDateTime						= ''
	myDateTimeForUI					= ''
	myVcs							= None
	myPlatform						= ''			# 'win' | 'posix' | 'cygwin' | 'darwin'
	myArch							= ''			# 'x86-32' | 'x86-64'. See targetArchitecture option.
	myCC							= ''			# 'cl', 'gcc'
	myCCVersionNumber				= 0				# 8.000000 for cl8-0, 4.002001 for gcc 4.2.1
	myIsExpressEdition				= False			# True if Visual Express Edition, False otherwise
	myCCVersion						= ''			# cl8-0Exp
	myMSVSIDE						= ''			# location of VCExpress (example: C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\IDE\VCExpress.exe).
	# @todo replace myMSVCVARS32 by myVCVARSALL
	myMSVCVARS32					= ''			# location of vcvars32.bat (example C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC\bin\vcvars32.bat).
	myVCVARSALL						= ''			# location of vcvarsall.bat (example C:\Program Files (x86)\Microsoft Visual Studio 11.0\VC\vcvarsall.bat)
	myMSVC							= ''			# root directory of Microsoft Visual Studio C++ (i.e. C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC)
	myMSBuild						= ''			# location of msbuild.exe (i.e. C:\Windows\Microsoft.NET\Framework\v4.0.30319\msbuild.exe)
	my_Platform_myCCVersion			= ''
	my_Platform_myArch_myCCVersion	= ''

	# Global attributes from .SConsBuildFramework.options or computed from it
	myNumJobs						= 1
	myCompanyName					= ''
	mySvnUrls						= {}
	mySvnCheckoutExclude			= []
	mySvnUpdateExclude				= []
	myInstallPath					= []
	myPublishPath					= ''
	myBuildPath						= ''
	mySConsignFilePath				= None
	myCachePath						= ''
	myCacheOn						= False
	myConfig						= ''	# 'debug' or 'release'
	myWarningLevel					= ''
	# Computed from .SConsBuildFramework.options
	myInstallExtPaths				= []
	myInstallDirectory				= ''
	myInstallDirectories			= []
	myDepsInstallDirectories		= []
	myNSISInstallDirectories		= []
	myIncludesInstallPaths			= []
	myLibInstallPaths				= []
	myIncludesInstallExtPaths		= []
	myLibInstallExtPaths			= []
	myGlobalCppPath					= []
	myGlobalLibPath					= []

	#@todo use env and lenv or at least copy in env
	# Project local attributes from default.options
	myVcsUse						= ''
	myDefines						= []
	myType							= ''
	myVersion						= ''
	myProjectPostfix				= ''
	myPostfix						= ''
	myDeps							= []
	myUses							= []
	myLibs							= []
	myStdlibs						= []

	# Project local attributes
	myProjectPathName				= ''	# d:\Dev\SrcLib\vgsdk\dependencies\gle
	myProjectPath					= ''	# d:\Dev\SrcLib\vgsdk\dependencies
	myProject						= ''	# gle
	myProjectBuildPath				= ''
	myVersionMajor					= None
	myVersionMinor					= None
	myVersionMaintenance			= None
	myVersionPostfix				= None
	myPostfixLinkedToMyConfig		= ''
	my_PostfixLinkedToMyConfig		= ''
	myFullPostfix					= ''
	my_FullPostfix					= ''

	myProjectBuildPathExpanded		= ''	# c:\temp\sbf\build\gle\0-3\win_x86-32_cl7-1\debug
	mySubsystemNotDefined			= None	# True if LINKFLAGS contains '/SUBSYSTEM:'

	# List of projects that have been already parsed by scons
	myParsedProjects				= OrderedDict() # { (projectName, env),...} 
	myParsedProjectsSet				= set()			# set([projectnameinlowercase,...]) a set of parsed projects in lower case
	myFailedVcsProjects				= set()			# set([projectName, ...])
	# @todo checks usage of myBuiltProjects instead of myParsedProjects
	myBuiltProjects					= OrderedDict()

	# see getAllUses()
	myImplicitUsesSet				= set()			# set( ['swig', 'python'] )
	myImplicitUses					= []			# ['swigX-Y-Z', pythonX-Y-Z]

	# Used by mktag
	myBranchSvnUrls				= OrderedDict() # OrderedDict([(projectPathName, url@rev),...])
	#lenv['myBranchesOrTags']	= 'tags' or 'branches' or None
	#lenv['myBranchOrTag']		= 'tag' or 'branch' or None
	#lenv['myBranch']			= None or env['svnDefaultBranch'] or '2.0' for example.

	def createEnvForToolchain(self):
		# Constructs SCons environment.
		tmpEnv = Environment( options = self.mySBFOptions, tools=[] )

		# Processes 'stages' option of SConsBuildFramework.options
		if tmpEnv['PLATFORM'] == 'win32':
			# Replace defaultCC by msvc on windows platform
			defaultCC = 'msvc'
		else:
			# Replace defaultCC by gcc on posix platform
			defaultCC = 'gcc'
		tmpEnv['stages'] = map( lambda x: defaultCC if x == 'defaultCC' else x, tmpEnv['stages'] )

		# Creates self.myEnv with desired toolchain initialized
		myTools = ['textfile']
		for stage in tmpEnv['stages']:
			if stage in registryToolchains:
				self.myCurrentToolChain = registryToolchains[stage]
				self.myEnv = self.myCurrentToolChain[0]( self, tmpEnv, myTools )
				break
		else:
			print ("sbfError: Unable to found any compiler toolchains in stages={}".format(tmpEnv['stages']))
			print ("'stages' option could be found in SCONS_BUILD_FRAMEWORK/SConsBuildFramework.options")
			Exit( 1 )

	def configureCommandLine(self):
		# Configures command line max length
		if self.myEnv['PLATFORM'] == 'win32':
			#self.myEnv['MSVC_BATCH'] = True # @todo wait improvement in SCons (better control of scheduler => -j8 and /MP8 => 8*8 processes !!! ).
			# @todo adds windows version helpers in sbf
			winVerTuple	= sys.getwindowsversion()
			winVerNumber= computeVersionNumber( [winVerTuple[0], winVerTuple[1]] )
			if winVerNumber >= 5.1 :
				# On computers running Microsoft Windows XP or later, the maximum length
				# of the string that you can use at the command prompt is 8191 characters.
				# XP version is 5.1
				self.myEnv['MAXLINELENGTH'] = 7680
				# On computers running Microsoft Windows 2000 or Windows NT 4.0,
				# the maximum length of the string that you can use at the command
				# prompt is 2047 characters.

		# Configures command line output
		#self.myEnv['LINKCOMSTR'] = "Linking $TARGET"#'sbfLN'#print_cmd_line
		#self.myEnv['SHLINKCOMSTR'] = "Linking $TARGET"#'sbfShLN' #print_cmd_line
		#self.myEnv.Replace(LINKCOMSTR = "Linking... ${TARGET.file}")
		#self.myEnv.Replace(SHLINKCOMSTR = "$LINKCOMSTR")
		#self.myEnv.Replace(ARCOMSTR = "Creating archive... ${TARGET.file}")
		if self.myEnv['printCmdLine'] == 'less' :
			self.myEnv['PRINT_CMD_LINE_FUNC'] = sbfPrintCmdLine
			if self.myEnv['PLATFORM'] == 'win32' :
				# cl prints always source filename. The following line (and 'PRINT_CMD_LINE_FUNC'), gets around this problem to avoid duplicate output.
				if self.myCC == 'cl':
					self.myEnv['CXXCOMSTR']		= 'sbfNull'
					self.myEnv['SHCXXCOMSTR']	= 'sbfNull'

					self.myEnv['RCCOMSTR'] = 'Compiling resource ${SOURCE.file}'
#				else:
#					self.myEnv['CXXCOMSTR']		= '${SOURCE.file}'
#					self.myEnv['SHCXXCOMSTR']	= 'sbfNull'
#			else:
#				self.myEnv['CXXCOMSTR']		= "${SOURCE.file}"
#				self.myEnv['SHCXXCOMSTR']	= "${SOURCE.file}"

			self.myEnv['INSTALLSTR'] = "Installing ${SOURCE.file}"

	def addCommandLineOptions(self):
		# Analyses command line options
		AddOption(	'--nd', '--nodeps',
					action	= 'store_true',
					dest	= 'nodeps',
					default	= False,
					help	= "do not follow project dependencies specified by 'deps' project option." )

		AddOption(	'--nx', '--noexclude',
					action	= 'store_true',
					dest	= 'noexclude',
					default	= False,
					help	= "do not exclude project(s) specified by 'projectExclude' sbf option." )

		AddOption(	"--weak-localext",
					action	= "store_true",
					dest	= "weak_localext",
					#default	= True,
					help	= "Disables SCons scanners for localExt directories." )

		AddOption(	"--no-weak-localext",
					action	= "store_false",
					dest	= "weak_localext",
					default	= True,
					help	= "See --weak-localext option" )

		AddOption(	"--wp", "--weak-publishing",
					action	= 'store_true',
					dest	= 'weakPublishing',
					default	= False,
					help	= "See --weak-publishing" )

		# AddOption(	"--optimize",
					# type	= "int",
					# #action	= "store",
					# #dest	= "optimize",
					# default	= 1,
					# help	= "todo documentation" )
		#print env.GetOption("optimize")
		#print env.GetOption("weak_localext")
		#if env.GetOption("optimize") == 0 :
		#	env.SetOption("weak_localext", 0 )

		AddOption(	'--fast',
					action	= 'store_true',
					default	= False,
					help	= "Speed up the SCons 'thinking' about what must be built before it starts the build. The drawback of this option is that SCons will not rebuild correctly the project in several rare cases." # this comment is duplicated in Help()
					)

		AddOption(	"--accurate",
					action	= "store_true",
					default	= False,
					help	= "See 'decider' SConsBuildFramework option."
					)

		# @todo Each instance of '--verbose' on the command line increases the verbosity level by one, so if you need more details on the output, specify it twice.
		AddOption(	"--verbose",
					action	= "store_true",
					dest	= "verbosity",
					default	= False,
					help	= "Shows details about the results of running sbf. This can be especially useful when the results might not be obvious." )

	def updateEnvFromCommandLineOptions(self, env ):
		env['nodeps'] = GetOption('nodeps')
		env['exclude'] = not GetOption('noexclude')
		if GetOption('fast'):
			env['decider'] = 'fast'
		if GetOption('accurate'):
			env['decider'] = 'accurate'

	def configureDateTime( self ):
		# myCurrentTime, myDate, myTime, myDateTime, myDateTimeForUI
		self.myCurrentTime = time.localtime()

		self.myTimePostFix = time.strftime( self.myEnv['postfixTimeFormat'], self.myCurrentTime )

		self.myDate	= time.strftime( '%Y-%m-%d', self.myCurrentTime )
		self.myTime	= time.strftime( '%Hh%Mm%Ss', self.myCurrentTime )

		# format compatible with that specified in the RFC 2822 Internet email standard.
		# self.myDateTime	= str(datetime.datetime.today().strftime("%a, %d %b %Y %H:%M:%S +0000"))
		self.myDateTime	= '{0}_{1}'.format( self.myDate, self.myTime )
		self.myDateTimeForUI = time.strftime( '%d-%b-%Y %H:%M:%S', self.myCurrentTime )

	def configureVCS(self):
		# Sets the vcs subsystem (at this time only svn is supported).
		if isSubversionAvailable:
			self.myVcs = Subversion( self )
		else:
			self.myVcs = sbfIVersionControlSystem.IVersionControlSystem()

	def startupMessage(self):
		# Prints sbf version, date and time at sbf startup
		if self.myEnv.GetOption('verbosity') :
			printSBFVersion()
			print ( "SConsBuildFramework path is '{}'".format(self.mySCONS_BUILD_FRAMEWORK) )
			print ( 'started {}'.format(self.myDateTimeForUI) )
			print ( "Host computer is a {} {} with a processor '{}'".format(platform.system(), platform.machine(), platform.processor() ) )

	def processTargetsAndOptions(self):
		self.myProjectOptionsWeakReading = len(self.myBuildTargets - self.myTargetsAllowingWeakReading) == 0

		# Tests which target(s) is given
		self.haveToBuildTest = len( self.myBuildTargets & self.myTargetsHavingToBuildTest ) > 0

		# 	User wants a vcs checkout or update ?
		self.tryVcsCheckout = 'svncheckout' in self.myBuildTargets
		if self.tryVcsCheckout and len(self.myEnv['svnUrls']) == 0:
			# Checks validity of 'svnUrls' option.
			raise SCons.Errors.UserError("Unable to do any svn checkout, because option 'svnUrls' is empty.")
		#
		self.tryVcsUpdate = 'svnupdate' in self.myBuildTargets
		#
		self.tryVcsClean = 'svnclean' in self.myBuildTargets
		self.tryVcsAdd = 'svnadd' in self.myBuildTargets
		# 	User wants a vcs status or relocate ?
		self.tryVcsStatus = 'svnstatus' in self.myBuildTargets
		self.tryVcsRelocate = 'svnrelocate' in self.myBuildTargets
		# User wants a vcs mktag or svnremotemkbranch ?
		self.tryVcsMkTag = 'svnmktag' in self.myBuildTargets
		self.tryVcsRemoteMkBranch = 'svnremotemkbranch' in self.myBuildTargets

		self.tryVcsOperation = self.tryVcsCheckout# or self.tryVcsUpdate
		self.tryVcsOperation = self.tryVcsOperation or self.tryVcsStatus or self.tryVcsRelocate
		self.tryVcsOperation = self.tryVcsOperation or self.tryVcsMkTag or self.tryVcsRemoteMkBranch

		# 'clean' and 'mrproper'
		#self.myGHasCleanOption = env.GetOption('clean')
		# Sets clean=1 option if needed.
		if (	'clean' in self.myBuildTargets or
				'mrproper' in self.myBuildTargets	) :
			# target clean or mrproper
			if len(self.myBuildTargets) != 1 :
				raise SCons.Errors.UserError(	"'clean' and 'mrproper' special targets must be used without any others targets.\nCurrent specified targets: %s"
												% convertToString(self.myBuildTargets) )
			else :
				self.myEnv.SetOption('clean', 1)

		# Analyses command line options
		# and
		# Processes special targets used as shortcuts for sbf options
		# This 'hack' is useful to 'simulate' command-line options. But without '-' or '--'

		# Overrides the 'config' option, when one of the special targets, named 'debug' and 'release', is specified
		# at command line.
		if ('debug' in self.myCurrentCmdLineOptions) and ('release' in self.myCurrentCmdLineOptions) :
			raise SCons.Errors.UserError("Targets 'debug' and 'release' have been specified at command-line. Chooses one of both.")
		if 'debug' in self.myCurrentCmdLineOptions:
			self.myEnv['config'] = 'debug'
		elif 'release' in self.myCurrentCmdLineOptions:
			self.myEnv['config'] = 'release'

	def configurePlatformAndArch(self):
		# myPlatform, myArch, 
		if self.myEnv['PLATFORM'].startswith('win'):
			self.myPlatform = 'win'
		else:
			self.myPlatform	= self.myEnv['PLATFORM']
		self.myEnv['MYPLATFORM'] = self.myPlatform

		self.myArch = self.myEnv['targetArchitecture']
		self.myEnv['TARGETARCHITECTURE'] = self.myArch

	def initializeGlobalsFromEnv( self, lenv ) :
		"""Initialize global attributes"""

		# Updates myNumJobs, myCompanyName, mySvnUrls, mySvnCheckoutExclude and mySvnUpdateExclude
		self.myNumJobs				= lenv['numJobs']

		self.myCompanyName			= lenv['companyName']

		self.mySvnUrls				= lenv['svnUrls']
		self.mySvnCheckoutExclude	= lenv['svnCheckoutExclude']
		self.mySvnUpdateExclude		= lenv['svnUpdateExclude']

		# Updates myInstallPath, myInstallExtPaths and myInstallDirectory
		self.myInstallPath = getNormalizedPathname( lenv['installPath'] )
		self.myInstallExtPaths = [self.myInstallPath + 'Ext' + self.my_Platform_myArch_myCCVersion]

		if ( len(self.myInstallPath) > 0 ):
			self.myInstallPath += self.my_Platform_myArch_myCCVersion
			self.myInstallDirectory = self.myInstallPath
			if not os.path.exists(self.myInstallDirectory):
				print ( 'Creates directory : {0}'.format(self.myInstallDirectory) )
				os.makedirs( self.myInstallDirectory )
		else:
			print 'sbfError: empty installPaths'
			Exit( 1 )

		# Updates myPublishPath
		self.myPublishPath = lenv['publishPath']
		if lenv['publishOn'] and len(self.myPublishPath)==0:
			print ("sbfError: sbf option named 'publishPath' is empty.")
			Exit( 1 )
		if lenv.GetOption('verbosity'):	print ( "Publish path is '{}'".format(self.myPublishPath) )

		# Updates myBuildPath, mySConsignFilePath, myCachePath, myCacheOn, myConfig and myWarningLevel
		self.myBuildPath = getNormalizedPathname( lenv['buildPath'] )
		if lenv.GetOption('verbosity'):	print ( "Build path is '{}'".format(self.myBuildPath) )

		# SCons signatures configuration (i.e. location of .sconsign file)
		if lenv['SConsignFilePath'] == 'buildPath' :
			# Explicitly stores signatures in directory given by 'buildPath' option in a file named '.sconsign.dblite'
			self.mySConsignFilePath = self.myBuildPath
		else :
			# Explicitly stores signatures in directory given by 'SConsignFilePath' option in a file named '.sconsign.dblite'
			self.mySConsignFilePath = getNormalizedPathname( lenv['SConsignFilePath'] )

		if not os.path.isabs( self.mySConsignFilePath ) :
			print 'sbfError: SConsignFilePath option = %s' % self.mySConsignFilePath
			print 'sbfError: SConsignFilePath option is not an absolute path name.'
			Exit(1)

		self.myEnv.SConsignFile( os.path.join(self.mySConsignFilePath, '.sconsign') )

		self.myCachePath	= getNormalizedPathname( lenv['cachePath'] )
		self.myCacheOn		= lenv['cacheOn']
		if (self.myCacheOn == True) and \
		(len( self.myCachePath ) > 0 ) :
			lenv.CacheDir( self.myCachePath )
			if lenv.GetOption('verbosity') :
				print 'sbfInfo: Use cache ', self.myCachePath
		else :
			if lenv.GetOption('verbosity') :
				print 'sbfInfo: Don\'t use cache'

		self.myConfig		= lenv['config']
		self.myWarningLevel	= lenv['warningLevel']

		if self.myConfig == 'debug':
			self.myPostfixLinkedToMyConfig = 'D'
			self.my_PostfixLinkedToMyConfig = '_' + self.myPostfixLinkedToMyConfig
		else : # release
			self.myPostfixLinkedToMyConfig = ''
			self.my_PostfixLinkedToMyConfig = ''

		### use myInstallPath and myInstallExtPaths to update myIncludesInstallPaths, myLibInstallPaths,
		### myIncludesInstallExtPaths, myLibInstallExtPaths, myGlobalCppPath and myGlobalLibPath
		self.myIncludesInstallPaths	+=	[ os.path.join(self.myInstallPath, 'include') ]
		#self.myLibInstallPaths		+=	[ os.path.join(element, 'lib') ]
		self.myLibInstallPaths		+=	[ os.path.join(self.myInstallPath, 'bin') ]

		for element in self.myInstallExtPaths:
			self.myIncludesInstallExtPaths	+=	[ os.path.join(element, 'include') ]
			self.myLibInstallExtPaths		+=	[ os.path.join(element, 'lib') ]

		#
		if self.myEnv.GetOption('weak_localext') :
			self.myGlobalCppPath = self.myIncludesInstallPaths
			for element in self.myIncludesInstallExtPaths :
				self.myEnv.Append( CCFLAGS = ['${INCPREFIX}' + element] )
		else:
			self.myGlobalCppPath = self.myIncludesInstallPaths + self.myIncludesInstallExtPaths

		self.myGlobalLibPath = self.myLibInstallPaths + self.myLibInstallExtPaths

	def configureDeciderAndNumJobs( self ):
		# Option 'fast'
		if self.myEnv['decider'] == 'fast':
			#self.myEnv.Decider('timestamp-newer') # similar to make			# 30.8, 17.9
			#self.myEnv.Decider('timestamp-match') # similar to make			# 31.65, 17.7

			# The drawback of MD5-timestamp is that SCons will not detect if a file's content 
			# has changed but its timestamp is the same, as might happen in an automated script
			# that runs a build, updates a file, and runs the build again, all within a single 
			# second.
			self.myEnv.Decider('MD5-timestamp')									# 29.8, 17.9

			# implicit-cache instructs SCons to not rebuild "correctly" in the following cases:
			# - SCons will ignore any changes that may have been made to search paths (like $CPPPATH or $LIBPATH,).
			#	This can lead to SCons not rebuilding a file if a change to $CPPPATH would normally cause a different,
			#	same-named file from a different directory to be used.
			# - SCons will not detect if a same-named file has been added to a directory that is earlier in the search 
			#	path than the directory in which the file was found last time.
			# =>	So obviously the only way to defeat implicit-cache is to change CPPPATH such that the set of files 
			#		included changes without touching ANY files in the entire include tree (from mailing list).
			self.myEnv.SetOption('implicit_cache', 1)							# 11.57, 11.4
			# @todo --implicit-deps-changed ?
			# @todo target incr with --implicit-deps-unchanged => incremental build
			self.myEnv.SetOption('max_drift', 1)								# 11.57, 11.3
		else:
			self.myEnv.Decider('MD5')											# 34, 19.3

		# option num_jobs
		self.myEnv.SetOption( 'num_jobs', self.myNumJobs )

	def configureToolchain( self, lenv ):
		### @todo moves defines(-Dxxxx) from platform specific methods into this one.
		# configure toolchain
		self.myCurrentToolChain[2]( self, lenv )

		if sys.platform == 'darwin':
			lenv.Append( CXXFLAGS = '-D__MACOSX__' )
			#self.myCxxFlags += ' -D__MACOSX__'
		elif ( sys.platform.find( 'linux' ) != -1 ):
			lenv.Append( CXXFLAGS = ['-D__linux','-DPOSIX'] )
			#self.myCxxFlags += ' -D__linux'

		lenv.Append( CPPPATH = self.myGlobalCppPath )
		lenv.Append( LIBPATH = self.myGlobalLibPath )

	def updatePATH( self, env ):
		# 	Adds localExt/bin (i.e. external tools like swig, moc...)
		if GetOption('verbosity'):	print
		toPrepend = [ join(self.myInstallExtPaths[0], 'bin') ]
		prependToPATH( env, toPrepend, GetOption('verbosity') )

		#	Adds rsync, ssh, 7z, nsis, graphviz and doxygen.
		toAppend = getPathsForTools(GetOption('verbosity'))
		if GetOption('verbosity'):	print
		appendToPATH( env, toAppend, GetOption('verbosity') )

		#	Adds local/bin
		appendToPATH( env, [ join(self.myInstallDirectory, 'bin') ], GetOption('verbosity') )

		if GetOption('verbosity'):	print

	def generateHelp(self, env):
		Help("""
Type:
SBF related targets
 'scons sbfCheck' to check availability and version of sbf components and tools.
 'scons sbfPak' to launch sbf packaging system.
 'scons sbfConfigure' to add several paths to environment variable $PATH (windows platform only).
 'scons sbfUnconfigure' to remove paths installed by 'sbfConfigure' except sbf runtime paths.
						It removes all non existing path in $PATH too.
 'scons sbfConfigureTools' to add several paths to environment variable $PATH (windows platform only).
 'scons sbfUnconfigureTools' to remove paths installed by 'sbfConfigureTools'.

svn related targets
 'scons svnAdd' to add files and directories used by sbf (i.e. all sources, configuration files and directory 'share').
 'scons svnCheckout' to check out a working copy from a repository.
 'scons svnClean' to clean up recursively the working copy.
 'scons svnRelocate' to update your working copy to point to the same repository directory, only at a different URL.
	Typically because an administrator has moved the repository to another server, or to another URL on the same server or to change the access method (http <=> https or svn <=> svn+ssh)
 'scons svnStatus' to print the status of working copy files and directories.
 'scons svnUpdate' to update your working copy.

 'scons svnMkTag' to create tag locally and used revision from working copy. But any local modifications are ignored. See 'svnDefaultBranch' option.
 'scons svnRemoteMkBranch' to create a a branch directly on the repository from a local tag file.

informations related target
 'scons info' to print informations about the current project, its dependencies and external packages needed.
 'scons infoFile' to generate info.sbf file for the starting project only.
	This file is generated in root of the project and intalled in the local/share directory of the project.

build related targets
 'scons pakUpdate' to automatically install/upgrade/downgrade any external package(s) needed.
 'scons' or 'scons all' to build your project and all its dependencies in the current 'config' (debug or release). 'All' is the default target.
 'scons clean' to clean intermediate files (see buildPath option).
 'scons mrproper' to clean installed files (see installPaths option). 'clean' target is also executed, so intermediate files are cleaned.

test related targets
 'scons test' to build the test project found optionally in the 'test' sub-directory of each project. The project embedding this 'test' sub-directory is automatically built too.
 'scons onlyRunTest' to launch the test program (if any and available), but without trying to build it.
 'scons runTest' to launch the test program (if any), but firstly build the test (see 'test' target).

run related targets
 'scons onlyRun' to launch the executable (if any and available), but without trying to build the project.
 'scons run' to launch the executable (if any), but firstly build the project.

visual studio related targets
 'scons vcproj' to build Microsoft Visual Studio project (.vcproj) and solution (.sln) files.
 'scons vcproj_clean' or 'scons vcproj_mrproper'

doxygen related targets
 'scons dox' to generate doxygen documentation.
 'scons dox_clean' or 'scons dox_mrproper'

packaging related targets
 'scons zipRuntime'		@toredo
 'scons zipDeps'		@toredo
 'scons portable' to create a portable package of your project and all its dependencies.
 'scons zipPortable' to create a zip file of the portable package created by 'scons portable'.
 'scons dbg' to create a package containing all pdb files on Windows platform of your project (@todo and all its dependencies).
 'scons zipDbg' to create a zip file of the package created by 'scons dbg'.
 'scons zipDev'			@toredo
 'scons zipSrc'			@toredo
 'scons zip'			@toredo
 'scons nsis' to create an nsis installation program.
 'scons zip_clean' and 'scons zip_mrproper'		@toredo
 'scons nsis_clean' and 'scons nsis_mrproper'	@toredo

emscripten related target
 'updateEmscripten'		to install/update emscripten installed in SConsBuildFramework/runtime/emsdk directory

Command-line options:

debug      A shortcut for config=debug. See 'config' option for additionnal informations.
release    A shortcut for config=release. See 'config' option for additionnal informations.

--nodeps or --nd     Do not follow project dependencies specified by 'deps' project option.
--noexclude or --nx  Do not exclude project(s) specified by 'projectExclude' sbf option.

--weak-localext		Disables SCons scanners for localext directories.
--no-weak-localext	See --weak-localext

--weak-publishing or --wp   rsync is used for publishing. Weak publishing means '--delete' option is
							no more given to rsync command.
							Intermediate files are no more cleaned for 'nsis' and zip related targets
							and redistributables coming from 'uses' are no more installed.
							So publishing is faster with this option.
							Tips: Do the first publishing of the day without --weak-publishing and the following with it.

--verbose       Shows details about the results of running sbf. This can be especially useful
				when the results might not be obvious.

--fast          Speed up the SCons 'thinking' about what must be built before it starts the
				build. The drawback of this option is that SCons will not rebuild correctly
				the project in several rare cases.
				See 'decider' SConsBuildFramework option.
--accurate      see --fast


SConsBuildFramework options:
""")
		Help( self.mySBFOptions.GenerateHelpText(env) )


	def __init__( self, initializeOptions = True ) :
		"""Constructor"""

		# Retrieves and normalizes SCONS_BUILD_FRAMEWORK
		self.mySCONS_BUILD_FRAMEWORK = getNormalizedPathname( join(__file__, '../..') )
		#self.mySCONS_BUILD_FRAMEWORK = os.getenv('SCONS_BUILD_FRAMEWORK')
		#if not self.mySCONS_BUILD_FRAMEWORK:
		#	raise SCons.Errors.UserError( "The SCONS_BUILD_FRAMEWORK environment variable is not defined." )
		#self.mySCONS_BUILD_FRAMEWORK = getNormalizedPathname( self.mySCONS_BUILD_FRAMEWORK )

		# Sets the root directory of sbf library
		self.mySbfLibraryRoot = join( self.mySCONS_BUILD_FRAMEWORK, 'lib/sbf' )

		# Reads SConsBuildFramework configuration file
		currentSConsBuildFrameworkOptions = getSConsBuildFrameworkOptionsFileLocation( self.mySCONS_BUILD_FRAMEWORK )
		self.mySBFOptions = self.readSConsBuildFrameworkOptions( currentSConsBuildFrameworkOptions )

		# Retrieves all targets (normalized in lower case)
		self.myBuildTargets = [str(buildTarget).lower() for buildTarget in BUILD_TARGETS]
		SCons.Script.BUILD_TARGETS[:] = self.myBuildTargets
		self.myBuildTargets = set(self.myBuildTargets)
		self.myCurrentCmdLineOptions = self.myBuildTargets & self.myCmdLineOptions
		self.myBuildTargets = self.myBuildTargets - self.myCurrentCmdLineOptions
		if len(self.myBuildTargets)==0:	self.myBuildTargets = set(['all'])

		self.addCommandLineOptions()

		#
		self.createEnvForToolchain()
		#print self.myEnv.Dump()
		#Exit()

		self.updateEnvFromCommandLineOptions( self.myEnv )

		self.configureCommandLine()
		self.configureDateTime()
		self.configureVCS()

		self.startupMessage()

		# Alias/Default
		tmp = list(self.myBuildTargets)[0]
		Alias( tmp )
		Alias( list(self.myCurrentCmdLineOptions), tmp )
		Default('all')

		self.processTargetsAndOptions()
		self.configurePlatformAndArch()

		if 'updateemscripten' in self.myBuildTargets: return		# @todo move closer to the beginning of this method

		# myCC
		self.myCC = self.myEnv['CC']

		# myCCVersionNumber, myCCVersion
		self.myCurrentToolChain[1](self)

		# my_Platform_myCCVersion and my_Platform_myArch_myCCVersion
		self.my_Platform_myCCVersion = '_{}_{}'.format( self.myPlatform, self.myCCVersion )
		self.my_Platform_myArch_myCCVersion = '_{}_{}_{}'.format( self.myPlatform, self.myArch, self.myCCVersion )

		#
		self.initializeGlobalsFromEnv( self.myEnv )

		if initializeOptions:	self.configureDeciderAndNumJobs()

		### configure toolchain
		self.configureToolchain( self.myEnv )
		#print self.myEnv.Dump() Exit()

		self.updatePATH( self.myEnv )
		self.generateHelp( self.myEnv )


	def initializeProjectFromEnv( self, lenv ):
		"""Initialize project from lenv"""

		self.myVcsUse			= lenv['vcsUse']
		self.myDefines			= lenv['defines']
		self.myType				= lenv['type']
		self.myVersion			= lenv['version']
		self.myProjectPostfix	= lenv['projectPostfix']
		self.myPostfix			= lenv['postfix']
		self.myDeps				= lenv['deps']
		self.myUses				= lenv['uses']
		self.myLibs				= lenv['libs']
		self.myStdlibs			= lenv['stdlibs']


	###### Initialize project ######
	def initializeProject( self, lenv ):
		#print ('initializeProject %s' % lenv['sbf_projectPathName'])

		# Already done in method buildProject(), but must be redone (because of recursiv call to buildProject())
		self.myProjectPathName	= lenv['sbf_projectPathName']
		self.myProjectPath		= lenv['sbf_projectPath']
		self.myProject			= lenv['sbf_project']

		# 'productName'
		if len(lenv['productName'])==0:
			lenv['productName'] = self.myProject

		# changes current directory
		os.chdir( self.myProjectPathName )

		# @todo partial move to __init__()
		if os.path.isabs(self.myBuildPath):
			self.myProjectBuildPath = self.myBuildPath
		else :
			self.myProjectBuildPath = join( self.myProjectPathName, self.myBuildPath )

		# processes myVersion
		extractedVersion = extractVersion( self.myVersion )

		self.myVersionMajor = int(extractedVersion[0])
		self.myVersionMinor = int(extractedVersion[1])
		if extractedVersion[2]:
			self.myVersionMaintenance = int(extractedVersion[2])
		else:
			self.myVersionMaintenance = 0
		if extractedVersion[3]:
			self.myVersionPostfix = extractedVersion[3]
		else:
			self.myVersionPostfix = ''
		lenv['sbf_version_major']		= self.myVersionMajor
		lenv['sbf_version_minor']		= self.myVersionMinor
		lenv['sbf_version_maintenance']	= self.myVersionMaintenance
		lenv['sbf_version_postfix']		= self.myVersionPostfix

		### @todo not good if more than one config must be built
		if len(self.myPostfix) > 0:
			self.myFullPostfix = self.myPostfix + self.my_PostfixLinkedToMyConfig
		else :
			self.myFullPostfix = self.myPostfixLinkedToMyConfig

		#@todo function to add '_' if not empty
		if len(self.myFullPostfix) > 0:
			self.my_FullPostfix = '_' + self.myFullPostfix
		else :
			self.my_FullPostfix = ''
		lenv['sbf_my_FullPostfix']		= self.my_FullPostfix

		###
		lenv.Prepend( CPPPATH = os.path.join(self.myProjectPathName, 'include') )

		### expands myProjectBuildPathExpanded
		self.myProjectBuildPathExpanded = join( self.myProjectBuildPath, self.myProject + self.myProjectPostfix, self.myVersion, '{}_{}_{}'.format(self.myPlatform, self.myArch, self.myCCVersion), self.myConfig )
		if len(self.myPostfix) > 0:
			self.myProjectBuildPathExpanded += '_' + self.myPostfix


	def configureProject( self, lenv, type ):

		### configures compiler and linker flags.
		self.configureProjectCxxFlagsAndLinkFlags( lenv, type )
		### configures CPPDEFINES with myDefines
		lenv.Append( CPPDEFINES = self.myDefines )
		# configures lenv['LIBS'] with lenv['stdlibs']
		lenv.Append( LIBS = lenv['stdlibs'] )
		# configures lenv['LIBS'] with lenv['libs']
		lenv.Append( LIBS = lenv['sbf_libsExpanded'] )
		# Configures lenv[*] with lenv['test']
		if lenv['test'] != 'none':
			lenv['uses'].append( lenv['test'] )
		# Configures lenv[*] with lenv['uses']
		uses( self, lenv, lenv['uses'] )




	###### Reads the main configuration file (i.e. configuration of sbf) ######
	# @todo
	def readSConsBuildFrameworkOptions( self, file ) :

		myOptions = Variables( file )
		myOptions.AddVariables(
			BoolVariable( 'queryUser', "Sets to False to assume default answer on all queries. Disables most of the normal user queries during sbf execution.", True ),

			('numJobs', 'Allow N jobs at once. N must be an integer equal at least to one.', 1 ),
			EnumVariable(	'decider',
							"Specifies the method used to decide if a target is up-to-date or must be rebuilt. Chooses among 'fast' or 'accurate'",
							'fast',
							allowed_values = ( 'fast', 'accurate' ) ),
			('outputLineLength', 'Sets the maximum length of one single line printed by sbf.', 79 ),
			EnumVariable(	'printCmdLine', "Sets to 'full' to print all command lines launched by sbf, and sets to 'less' to hide command lines and see only a brief description of each command.",
							'less',
							allowed_values = ( 'full', 'less' ) ), # @todo silent

			('companyName', 'Sets the name of company that produced the project. This is used on win32 platform to embedded in exe, dll or lib files additional informations.', '' ),

			('pakPaths', "Sets the list of paths from which packages can be obtained. No matter what is specified by this options, the first implicit path where packages are searched would be 'installPath/../sbfPak'.", [] ),

			('svnUrls', 'A dictionnary... @todo doc ... The list of subversion repositories used, from first to last, until a successful checkout occurs.', {}),
			('svnDefaultBranch', 'svnMkTag and svnRemoteMkBranch asks user the name of the tag/branch to use. This option sets the default choice suggested to user.', '1.0'),
			('projectExclude', 'The list of projects excludes from any sbf operations. All projects not explicitly excluded will be included. The project from which sbf was initially invoked is never excluded. The unix filename pattern matching is used by the list.', []),
			('weakLocalExtExclude', 'The list of packages (see \'uses\' project option for a complete list of available packages) excludes by the --weak-localext option.'
			' --weak-localext could be used to disables SCons scanners for localExt directories.'
			' All packages not explicitly excluded will be included.', []),
			('svnCheckoutExclude', 'The list of projects excludes from subversion checkout operations. All projects not explicitly excluded will be included. The unix filename pattern matching is used by the list.', []),
			('svnUpdateExclude', 'The list of projects excludes from subversion update operations. All projects not explicitly excluded will be included. The unix filename pattern matching is used by the list.', []),

			EnumVariable(	'targetArchitecture', 'Sets the target architecture for Visual Studio compiler or gcc, i.e. the architecture (32 or 64 bits) of the binaries generated by the compiler.',
							'x86-32',
							allowed_values = ( 'x86-32', 'x86-64' ) ),
# @todo stages=[test, nsis, dox...] ?
			('stages', 'The list of stages that have to be execute during a build. Allowed values are defaultCC (replace be cl on win platform and gcc for posix platform), cl, gcc, emcc and swig', ['defaultCC', 'swig']),
			EnumVariable(	'clVersion', 'MS Visual C++ compiler (cl.exe) version using the following version schema : x.y or year. Use the special value \'highest\' to select the highest installed version.',
							'highest',
							allowed_values = ( '7.1', '8.0Exp', '8.0', '9.0Exp', '9.0', '10.0Exp', '10.0', '11.0Exp', '11.0', '12.0Exp', '12.0', 'highest' ),
							map=clYearToVersionNum ),

			('installPath', "The given path would be used as a destination path for target named 'install'. This directory is similar to unix '/usr/local'. It is also the basis of localExt directory (ex: localExt_win32_cl10-0Exp ).", '$SCONS_BUILD_FRAMEWORK/../local'),

			('postfixTimeFormat', "A string controlling the format of the date/time postfix (used by 'nsis' and 'zip' targets). Default time format is '%Y-%m-%d' producing for example the date 2012-04-12. Adds '%Hh%Mm%Ss' to append for example 10h40m21s. See python documentation on time.strftime() for additionnal informations.", '%Y-%m-%d' ),

			('publishPath', 'The result of a target, typically copied in installPaths[0], could be transfered to another host over a remote shell using rsync. This option sets the destination of publishing (see rsync for destination syntax).', ''),
			BoolVariable('publishOn', 'Sets to True to enabled the publishing. See \'publishPath\' option for additional informations.', False),

			PathVariable(	'buildPath',
							'The build directory in which to build all derived files. It could be an absolute path, or a relative path to the project being build)',
							'$SCONS_BUILD_FRAMEWORK/../build',
							PathVariable.PathAccept),
			(	'SConsignFilePath',
				'Stores signatures (.sconsign.dblite file) in the specified absolute path name. If SConsignFilePath is not defined or is equal to string \'buildPath\' (the default value), the value of \'buildPath\' option is used.',
				'buildPath' ),
			PathVariable('cachePath', 'The directory where derived files will be cached. The derived files in the cache will be shared among all the builds using the same cachePath directory.', '', PathVariable.PathAccept),
			BoolVariable('cacheOn', 'Sets to True to use the build cache system (see cachePath option), False (the default) to disable it.', False),

			EnumVariable(	'config', "Sets to 'release' to build the production program/library. Or sets to 'debug' to build the debug version.",
							'release',
							allowed_values=('debug', 'release'),
							map={}, ignorecase=1 ),
			('configFlags', "The list of strings available inside project configuration file to adjust its behavior (usage in default.options: SConsEnvironment.sbf.myEnv['configFlags']).", []),
			BoolVariable(	'generateDebugInfoInRelease', 'The purpose of this option is to be able to fix bug(s) occurring only in release build and/or when no debugger is attached.'
							'Typically, a release build does not contain any debug informations. '
							'But sets this option to true to add the debugging informations for executable and libraries in release build, false otherwise (the default value).',
							False ),
			EnumVariable(	'warningLevel', 'Sets the level of warnings.', 'normal',
							allowed_values=('normal', 'high'),
							map={}, ignorecase=1 ),

			(	'userDict', "a python dictionnary containing any user data and that could be made available in any project configuration file (i.e. default.options).\nExample:\n	from SCons.Script.SConscript import SConsEnvironment\n	print SConsEnvironment.sbf.myEnv['userDict'].",
				{} )
		)
		return myOptions


	###### Reads a configuration file for a project ######
	def readProjectOptions( self, file, weakReading = False ):
		"""@param weakReading		True to read the minimum number of variables (only 'vcsUse', 'deps' and 'customBuild')"""

		myOptions = Variables( file )
		myOptions.AddVariables(
			EnumVariable(	'vcsUse', "'yes' if the project use a versioning control system, 'no' otherwise.", 'yes',
							allowed_values=('yes', 'no'),
							map={}, ignorecase=1 ),
			('deps', 'Specifies list of dependencies to others projects. Absolute path is forbidden.', []),
			('customBuild',	"A dictionnary containing { target : pyScript, ... } to specify a python script for a target. Python script is executed during 'thinking stage' of SConsBuildFramework if its associated target have to be built. Script has access to SCONS_BUILD_FRAMEWORK environment variable and lenv, the SCons environment for the project. Python 'sys.path' is adjusted to allow direct 'import' of python script from the root directory of the project.", {})
		)

		if not weakReading:
			myOptions.AddVariables(
				('description', "Description of the project to be presented to users. This is used on win32 platform to embedded in exe, dll or lib files additional informations.", '' ),
				('productName', 'Name of the product to be presented to users. This information is used by nsis installation program. Default value (i.e. empty string) means that project name is used instead.', ''),

				#EnumVariable(	'vcsUse', "'yes' if the project use a versioning control system, 'no' otherwise.", 'yes',
				#				allowed_values=('yes', 'no'),
				#				map={}, ignorecase=1 ),

				BoolVariable(	'embindStage',
								"True to enable the generation of javascript binding from EMSCRIPTEN_BINDINGS(). See documentation of embind in emscripten site.",
								False ),
				(	'emccSettings',
					"A python dictionnary containing emscripten settings to append to CXXFLAGS and LINKFLAGS. An item of the dictionnary contains (key=name of settings, value=value of settings). For example ('TOTAL_MEMORY', 1024 * 1024 * 16) to add -s TOTAL_MEMORY=16777216.",
					{} ),
				('defines', 'The list of preprocessor definitions given to the compiler at each invocation (same effect as #define xxx).', ''),
				EnumVariable(	'type', "Specifies the project/target type. 'exec' for executable projects, 'static' for static library projects, 'shared' for dynamic library projects, 'none' for meta or headers only projects.",
								'none',
								allowed_values=('exec', 'static','shared','none'),
								map={}, ignorecase=1 ),

				('version', "Sets the project version. The following version schemas must be used : major-minor-[postfix] or major-minor-maintenance[-postfix]. For example '1-0', '1-0-RC1', '1-0-1' or '0-99-technoPreview'", '0-0'),
				('projectPostfix', "Adds a postfix to the project name (for project named 'glo' and projectPostfix='ES2', the target filename would be gloES2_0-3_win_cl12-0.dll)", ''),
				('postfix', 'Adds a postfix to the target name.', ''),
				BoolVariable('generateInfoFile', 'Sets to true enabled the generation of info.sbf file, false to disable it.', False ),

				#('deps', 'Specifies list of dependencies to others projects. Absolute path is forbidden.', []),

				# 'Available packages:{}\nAlias: {}'.format( convertToString(UseRepository.getAllowedValues()), convertDictToString(UseRepository.getAlias()))
				(	'uses',
					'Specifies a list of packages to configure for compilation and link stages.\n',
					[] ),

				('libs', 'The list of libraries used during the link stage that have been compiled with SConsBuildFramework.', []),
				('stdlibs', 'The list of standard libraries used during the link stage.', []),
				EnumVariable(	'test', 'Specifies the test framework to configure for compilation and link stages.', 'none',
								allowed_values=('none', 'gtest'), ignorecase=1 ),


				('shareExclude', "The list of Unix shell-style wildcards to exclude files from 'share' directory", []),
				('shareBuild', "Defines the build stage for files from 'share' directory. The following schemas must be used for this option : ( [filters], command ).\n@todo Explains filters and command.", ([],('','',''))),

				BoolVariable(	'console',
								'True to enable Windows character-mode application and to allow the operating system to provide a console. False to disable the console. This option is specific to MS/Windows executable.',
								True ),

				(	'runParams',
					"The list of parameters given to executable by targets 'run' and 'onlyRun'. To specify multiple parameters at command-line uses a comma-separated list of parameters, which will get translated into a space-separated list for passing to the launching command.",
					[],
					passthruValidator, passthruConverter ),

				(	'runTestParams',
					"The list of parameters given to executable by targets 'runTest' and 'onlyRunTest'. To specify multiple parameters at command-line uses a comma-separated list of parameters, which will get translated into a space-separated list for passing to the launching command.",
					[],
					passthruValidator, passthruConverter ),

				EnumVariable(	'deploymentType', "Specifies where the project and its dependencies have to be installed in root of the installation directory and/or in sub-directory 'packages' of the installation directory.",
								'none', allowed_values=('none', 'standalone', 'embedded'), ignorecase=1 ),

				(	'deploymentPrecond', '', ''	),


				(	'nsis', "A dictionnary to customize generated nsis installation program. Key 'autoUninstall' sets to True to uninstall automatically previous version if needed, otherwise it writes 'launch=commandLine' in 'Uninstall' section of the feedback file. Key 'installDirFromRegKey' set to true to tell the installer to check a string in the registry and use it for the install dir if that string is valid, false to do nothing (only for standalone). Key 'ensureNewInstallDir' to ensure that the installation directory is always a newly created directory (by appending a number if needed to the chosen directory name). Key 'actionOnVarDirectory' to allow 'leave' untouch the 'var' directory, to 'remove' the 'var' directory during the uninstall stage, 'autoMigration' to move the 'var' directory during installation and 'manualMigration' to write 'varDirectory=pathOfVar' in 'Import' section of the feedback file. Key 'moveLogFileIntoVarDirectory' to move log file into 'var' directory. Key 'copySetupFileIntoVarDirectory' to copy installation program file into 'var' directory. Key 'customPointInstallationValidation' to add nsis code after the copying of all files during installation and before migration of var/packages directories, autoUninstall and registry updating. The variable $installationValidation have to be used to validate (==0) to invalidate (!=0) the installation. Invalidate an installation to abort the installation, nevertheless uninstall.exe is created to be able to clean installed files.",
					{	'autoUninstall'						: True,
						'installDirFromRegKey'				: True,
						'ensureNewInstallDir'				: False,
						'actionOnVarDirectory'				: 'leave',
						'moveLogFileIntoVarDirectory'		: False,
						'copySetupFileIntoVarDirectory'		: False,
						'customPointInstallationValidation'	: ''
					} )
			)

		return myOptions


	###### Reads a configuration file for a project ######
	###### Updates environment (self.myProjectOptions and lenv are modified).
	# Returns true if config file exists, false otherwise.
	# @todo error reporting in the function (remove error reporting from caller).
	def readProjectOptionsAndUpdateEnv( self, lenv, configDotOptionsFile = 'default.options' ):
		configDotOptionsPathFile = join(self.myProjectPathName, configDotOptionsFile)
		retVal = os.path.isfile(configDotOptionsPathFile)
		if retVal:
			# update lenv with config.options
			self.myProjectOptions = self.readProjectOptions( configDotOptionsPathFile, self.myProjectOptionsWeakReading )
			if self.myProjectOptionsWeakReading:
				self.myProjectOptions.Update( lenv )
				projectOptionsVariables = OrderedDict([
					('description'	, ''),
					('productName'	, ''),
					('embindStage'	, ''),
					('emccSettings'	, ''),
					('defines'		, ''),
					('type'			, 'none'),
					('version'		, '0-0'),
					('projectPostfix', ''),
					('postfix'		, ''),
					('generateInfoFile'	, False),
					('uses'			, []),
					('libs'			, []),
					('stdlibs'		, []),
					('test'			, 'none'),
					('shareExclude'	, []),
					('shareBuild'	, ([],('','',''))),
					('console'		, True),
					('runParams'		, []),
					('runTestParams'	, []),
					('deploymentType', 'none'),
					('deploymentPrecond'	, ''),
					('nsis'			, {}) ])
				for (key,val) in projectOptionsVariables.items():
					lenv[key] = val
			else:
				self.myProjectOptions.Update( lenv )
		#else:
		#	pass
		return retVal


	def processUsesRequirements( self, lenv ):
		"""Adding requirements for each element of 'uses'"""
		usesToProcess = lenv['uses'][:]
		for useNameVersion in usesToProcess:
			# Retrieves use, useName and useVersion
			useName, useVersion, use = UseRepository.gethUse( useNameVersion )

			# Retrieves use object for incoming dependency
			if use:
				requirements = use.getRequirements( useVersion )
				if requirements:
					for requirement in requirements:
						reqName, reqVersion = splitUsesName( requirement )
						requirement = reqName + reqVersion
						if requirement not in lenv['uses']:
							lenv['uses'].append(requirement)
							usesToProcess.append(requirement)
						#else do nothing
				# else nothing to do
			else:
				raise SCons.Errors.UserError("Uses=[\'{}\'] not supported on platform {}.".format(useNameVersion, self.myPlatform) )



	###### Configures CxxFlags & LinkFlags ######



	# @todo incremental in release, but not for portable app and nsis
	def configureProjectCxxFlagsAndLinkFlagsMSVC( self, lenv, type ):
		if self.myCC != 'cl':				# @todo not very cute
			assert( False )
			return

		# Linker flags
		if self.myConfig == 'release':
			# To ensure that the final release build does not contain padding or thunks, link non incrementally.
			lenv.Append( LINKFLAGS = '/INCREMENTAL:NO' )
#			lenv.Append( LINKFLAGS = '/LTCG' )
			if lenv['generateDebugInfoInRelease']:
				lenv.Append( LINKFLAGS = [ '/DEBUG' ] )
		else:
			# By default, the linker runs in incremental mode.
			lenv.Append( LINKFLAGS = [ '/DEBUG', '/INCREMENTAL' ] )

		#
		if type == 'exec':
			# Subsystem
			self.mySubsystemNotDefined = str(lenv['LINKFLAGS']).upper().find( '/SUBSYSTEM:' ) == -1

			if self.mySubsystemNotDefined:
				if lenv['console']:
					# subsystem sets to console to output debugging informations.
					lenv.Append( LINKFLAGS = ['/SUBSYSTEM:CONSOLE'] )
				else:
					# subsystem sets to windows.
					lenv.Append( LINKFLAGS = ['/SUBSYSTEM:WINDOWS', '/entry:mainCRTStartup'] )

			# /GA : Results in more efficient code for an .exe file for accessing thread-local storage (TLS) variables.
			lenv.Append( CXXFLAGS = '/GA' )

		elif type == 'shared':
			lenv.Append( CXXFLAGS = '/D_USRDLL' )

	def configureProjectCxxFlagsAndLinkFlags( self, lenv, type, skipDefinesInCXXFLAGS = False ):
		if self.myCC == 'cl':
			self.configureProjectCxxFlagsAndLinkFlagsMSVC( lenv, type )
		elif self.myCC in ['gcc', 'emcc']:
			pass
		else:
			raise SCons.Errors.UserError("Unknown compiler {}.".format(self.myCC))

		# Adds to command-line several defines with version number informations.
		lenv.Append( CPPDEFINES = [
						("COMPANY_NAME",	"\\\"%s\\\"" % self.myCompanyName ),
						("MODULE_NAME",		"\\\"%s\\\"" % lenv['sbf_project'] ),
						("MODULE_VERSION",	"\\\"%s\\\"" % lenv['version'] ),
						("MODULE_MAJOR_VER",	"%s" % self.myVersionMajor ),
						("MODULE_MINOR_VER",	"%s" % self.myVersionMinor ),
						("MODULE_MAINT_VER",	"%s" % self.myVersionMaintenance ),
						("MODULE_POSTFIX_VER",	"%s" % self.myVersionPostfix ),
#						("MODULE_MAJOR_VER",	"%s" % lenv['sbf_version_major'] ),
#						("MODULE_MINOR_VER",	"%s" % lenv['sbf_version_minor'] ),
#						("MODULE_MAINT_VER",	"%s" % lenv['sbf_version_maintenance'] ),
#						("MODULE_POSTFIX_VER",	"%s" % lenv['sbf_version_postfix'] ),
						 ] )
		if lenv['projectPostfix']:
			lenv.Append( CPPDEFINES = ("MODULE_POSTFIX",	"\\\"%s\\\"" % lenv['projectPostfix'] ) )

		if skipDefinesInCXXFLAGS:
			return

		# Completes myCxxFlags with some defines
		if self.myType == 'static':
			lenv.Append( CXXFLAGS = ' -D' + self.myProject.upper() + '_STATIC ' )
		elif self.myType == 'shared':
			lenv.Append( CXXFLAGS = ' -D' + self.myProject.upper() + '_SHARED ' )
			# @todo remove me
			lenv.Append( CXXFLAGS = ' -D' + self.myProject.upper() + '_EXPORTS ' )


	###################################################################################
	def doVcsCheckoutOrOther( self, lenv ):
		"""Do a vcs checkout, status, relocate, tag/branch related targets."""

		if not self.tryVcsOperation:
			return

		# What must be done for this project ?
		#existanceOfProjectPathName	tryVcsCheckout		action
		#True						True 				env (checkout and env, if lenv['vcsUse'] == 'yes' and not already checkout from vcs)
		#True						False				env
		#False						True				vcsCheckout env
		#False						False				return

		# Tests existance of project path name
		existanceOfProjectPathName = os.path.isdir(self.myProjectPathName)
		if not existanceOfProjectPathName :
			if self.tryVcsCheckout:
				self.vcsCheckout( lenv )
			else:
				return
#				print stringFormatter( lenv, "project %s in %s" % (self.myProject, self.myProjectPath) )
#				print "sbfWarning: Unable to find project", self.myProject, "in directory", self.myProjectPath
#				print "sbfInfo: target svnCheckout have not been specified."
#				print "sbfInfo: None of targets svnCheckout or", self.myProject + "_svnCheckout have been specified."
#				self.myFailedVcsProjects.add( self.myProject )
#				return
		else:
			successful = self.readProjectOptionsAndUpdateEnv( lenv )
			if successful:
				if lenv['vcsUse'] != 'yes':
					if lenv.GetOption('verbosity'): print ("Skip project {0} in {1}, because 'vcsUse' option sets to no.".format(self.myProject, self.myProjectPath))
					return

				if self.tryVcsCheckout:
					projectURL = self.myVcs.getUrl( self.myProjectPathName )
					if projectURL:
						print stringFormatter( lenv, "project {0} in {1}".format(self.myProject, self.myProjectPath) )
						if lenv.GetOption('verbosity'):
							print "sbfInfo: Already checkout from %s using svn." % projectURL
							print "sbfInfo: Uses 'svnUpdate' to get the latest changes from the repository."
						print
					else:
						self.vcsCheckout( lenv )
				elif self.tryVcsStatus:
					self.vcsStatus( lenv )
				elif self.tryVcsRelocate:
					self.vcsRelocate( lenv )
				# vcsMkTag
				elif self.tryVcsMkTag:
					self.vcsMkTag( lenv )
				# tryVcsRemoteMkBranch
				elif self.tryVcsRemoteMkBranch:
					pass
					#self.vcsRemoteMkBranch( lenv )
				else:
					assert( False )
					#else nothing to do
			else:
				raise SCons.Errors.UserError("Unable to find 'default.options' file for project {0} in directory {1}.".format(self.myProject, self.myProjectPath) )


	def doVcsUpdate( self, lenv ):
		# User wants a vcs update ?
		if self.tryVcsUpdate:
			if lenv['vcsUse'] == 'yes' :
				self.vcsUpdate( lenv )
				self.readProjectOptionsAndUpdateEnv( lenv )
			else:
				if lenv.GetOption('verbosity'):	print ("Skip project {} in {}, because 'vcsUse' option sets to no.".format(self.myProject, self.myProjectPath))
		# else nothing to do.


	def doVcsCleanOrAdd( self, lenv ):
		# a vcs cleanup ?
		if self.tryVcsClean:
			if lenv['vcsUse'] == 'yes' :
				self.vcsClean( lenv )
			else:
				if lenv.GetOption('verbosity'):
					print ("Skip project {0} in {1}, because 'vcsUse' option sets to no.".format(self.myProject, self.myProjectPath))

		# a vcs add ?
		if self.tryVcsAdd:
			if lenv['vcsUse'] == 'yes':
				self.vcsAdd( lenv )
			else:
				if lenv.GetOption('verbosity'):
					print ("Skip project {0} in {1}, because 'vcsUse' option sets to no.".format(self.myProject, self.myProjectPath))


	###################################################################################
	def vcsOperation( self, lenv, vcsOperation, opDescription ):

		# Checks if vcs operation of this project has already failed
		if self.myProject not in self.myFailedVcsProjects :
			print stringFormatter( lenv, "vcs {0} project {1} in {2}".format(opDescription, self.myProject, self.myProjectPath) )

			successful = vcsOperation( self.myProjectPathName, self.myProject )

			if successful:
				print
				return successful
			else:
				self.myFailedVcsProjects.add( self.myProject )
				print ( "sbfWarning: Unable to do vcs operation in directory {0}\n".format( self.myProjectPathName ) )
				return successful
		else:
			print
			return False


	def _vcsCheckoutOrUpdate( self, lenv, vcsOperation, opDescription, excludeList ):
		# Checks if this project have to skip vcs operation
		if self.matchProjectInList( self.myProjectPathName, excludeList ):
			if lenv.GetOption('verbosity'):
				print stringFormatter( lenv, "vcs {0} project {1} in {2}".format( opDescription, self.myProject, self.myProjectPath ) )
				print ("sbfInfo: Exclude from vcs {0}.".format(opDescription))
				print ("sbfInfo: Skip to the next project...\n")
			return
		else:
			return self.vcsOperation( lenv, vcsOperation, opDescription )


	def vcsCheckout( self, lenv ):
		retVal = self._vcsCheckoutOrUpdate( lenv, self.myVcs.checkout, 'checkout', self.mySvnCheckoutExclude )
		return retVal

	def vcsUpdate( self, lenv ):
		retVal = self._vcsCheckoutOrUpdate( lenv, self.myVcs.update, 'update', self.mySvnUpdateExclude )
		return retVal

	def vcsClean( self, lenv ):
		return self.vcsOperation( lenv, self.myVcs.clean, 'clean' )

	def vcsAdd( self, lenv ):
		return self.vcsOperation( lenv, self.myVcs.add, 'add' )

	def vcsStatus( self, lenv ):
		return self.vcsOperation( lenv, self.myVcs.status, 'status' )

	def vcsRelocate( self, lenv ):
		return self.vcsOperation( lenv, self.myVcs.relocate, 'relocate' )

	def vcsMkTag( self, lenv ):
		print stringFormatter( lenv, "project {0} in {1}".format(self.myProject, self.myProjectPath) )
		(url, revision ) = self.myVcs.getUrlAndRevision( self.myProjectPathName )
		self.myBranchSvnUrls[ self.myProject ] = '{0}@{1}'.format(anonymizeUrl(url), revision)



	###### Build a project ######
	def buildProject( self, projectPathName, parentProjects, configureOnly = False ):
		# Normalizes incoming path
		projectPathName = getNormalizedPathname( projectPathName )

		# Initializes basic informations about incoming project
		self.myProjectPathName	= projectPathName
		self.myProjectPath		= os.path.dirname(	projectPathName	)
		self.myProject			= os.path.basename(	projectPathName	)

# @todo OPTME Creates self.myExcludeProjects and uses
		# Tests if the incoming project must be ignored
		if self.myEnv['exclude'] and \
		   (self.matchProjectInList(self.myProjectPathName, self.myEnv['projectExclude'])) and \
		   (self.myProject != os.path.basename(GetLaunchDir())) :
			if self.myEnv.GetOption('verbosity') :
				print ( "Ignore project {} in {}".format(self.myProject, self.myProjectPath) )
			return


		# Configures a new environment
		self.myCurrentLocalEnv = self.myEnv.Clone()
		lenv = self.myCurrentLocalEnv

		# used by code printing messages during the different build stage.
		lenv['sbf_projectPathName'	] = self.myProjectPathName
		lenv['sbf_projectPath'		] = self.myProjectPath
		lenv['sbf_project'			] = self.myProject

		if lenv.GetOption('verbosity'): print ( "Reading default.options of project {}...".format(lenv['sbf_project']) )

		# VCS checkout or status or relocate or mkTag/Branch or rmTag/Branch
		self.doVcsCheckoutOrOther( lenv )

		# Tests existance of project path name and updates lenv with 'default.options' configuration file
		if isdir(self.myProjectPathName):
			successful = self.readProjectOptionsAndUpdateEnv( lenv )
			if successful:
				# Adds the new environment
				self.myParsedProjects[self.myProject] = lenv
				self.myParsedProjectsSet.add( self.myProject.lower() )
			else:
				raise SCons.Errors.UserError("Unable to find 'default.options' file for project %s in directory %s." % (self.myProject, self.myProjectPath) )
		else:
			#if strict:
			print ( "sbfError: Unable to find project '{}' in directory '{}'".format( self.myProject, self.myProjectPath ) )
			Exit(1)
			#if not strict
				#print 'sbfWarning: Unable to find project', self.myProject, 'in directory', self.myProjectPath
				#print ('sbfInfo: Skip to the next project...')
				#self.myFailedVcsProjects.add( self.myProject )
				#return


		# VCS update
		self.doVcsUpdate( lenv )


		# Tests project options existance
		if self.myProjectOptions is None:
			# No project options, this is not a project to build.
			return


		# Adds help on project options only for the "first" project ( exclude lib/sbf when automatically added to dependencies ).
		if	( len(self.myParsedProjects) == 1 and lenv['sbf_launchDir'] == self.myProjectPathName ) or\
			( len(self.myParsedProjects) == 2 and lenv['nodeps'] == False ):
			Help("""\n\n\n%s options:\n""" % self.myProject )
			Help( self.myProjectOptions.GenerateHelpText(lenv) )



		#
		updateParentProjects( lenv, parentProjects )

		if isLaunchProject(lenv):	initializeNSISInstallDirectories( self, lenv )


		# Constructs dependencies
		#print "sbfDebug:%s dependencies are %s" % (self.myProject, lenv['deps'])

		# Tests if sbf library must be implicitly built (process lenv['libs'] for that)
		(libsExpanded, buildSbfLibrary) = computeLibsExpanded( self, lenv['libs'])
		lenv['sbf_libsExpanded'] = libsExpanded

		# Builds sbf library
		if buildSbfLibrary and 'sbf' not in self.myParsedProjectsSet:
			if lenv['nodeps'] == False:
				self.buildProject( self.mySbfLibraryRoot, lenv['sbf_parentProjects'], lenv['nodeps'] )
			#else nothing to do
		#else nothing to do

		# Built project dependencies (i.e. 'deps')
		for dependency in lenv['deps']:
			# Checks dependency path
			# dependency is an absolute path
			if os.path.isabs( dependency ): raise SCons.Errors.UserError("Absolute path is forbidden in 'deps' project option.")

			# dependency is a path relative to the directory containing default.options
			normalizedDependency			= getNormalizedPathname( projectPathName + os.sep + dependency )
			incomingProjectName				= os.path.basename(normalizedDependency)
			lowerCaseIncomingProjectName	= incomingProjectName.lower()
			if lowerCaseIncomingProjectName not in self.myParsedProjectsSet:
				# dependency not already encountered
				#print ('buildProject %s' % normalizedDependency)
				if incomingProjectName not in self.myFailedVcsProjects:
					# Built the dependency and takes care of 'nodeps' option by enabling project
					# configuration only (and not the full building process).
					self.buildProject( normalizedDependency, lenv['sbf_parentProjects'], lenv['nodeps'] )
#					if lenv['nodeps'] == False: self.buildProject( normalizedDependency, lenv['sbf_parentProjects'], lenv['nodeps'] )
					# else nothing to do
				#else: nothing to do
			else:
				# A project with the same name (without taking case into account) has been already parsed.
				if incomingProjectName in self.myParsedProjects :
					# A project with the same name has been already parsed (with the same case).
					# Checks path ?
					if self.myParsedProjects[incomingProjectName]['sbf_projectPathName'] != normalizedDependency :
						raise SCons.Errors.UserError("Encountered the following two projects :\n%s and \n%s\nwith the same name (without taking case into account). It's forbidden." % (self.myParsedProjects[incomingProjectName]['sbf_projectPathName'], normalizedDependency) )
					#else: nothing to do (because same path => project already parsed).
						#print "sbfDebug: project %s already parsed." % projectPathName
				else:
					# Exception: A project with the same name has been already parsed, but with a different case
					registeredProjectName = None
					for project in self.myParsedProjects :
						if project.lower() == incomingProjectName.lower() :
							raise SCons.Errors.UserError("The dependency %s, defined in project %s, has already been encountered with a different character case (%s). It's forbidden." % (normalizedDependency, lenv['sbf_projectPathName'], self.myParsedProjects[project]['sbf_projectPathName'] ) )
					else:
						# Must never happened
						raise SCons.Errors.UserError("Internal sbf error.")


		# Initializes the project
		self.initializeProjectFromEnv( lenv )
		self.processUsesRequirements(lenv)

		#
		if self.tryVcsOperation or configureOnly:
			if lenv.GetOption('verbosity'): print ( "Parsing project {}...".format(lenv['sbf_project']) )
			return
		else:
			# Adds the new environment
			self.myBuiltProjects[ lenv['sbf_project'] ] = lenv
			if lenv.GetOption('verbosity'): print ( "Studying project {}...".format(lenv['sbf_project']) )

		# Dumping construction environment (for debugging) : print lenv.Dump() Exit()

		### Starts building stage
		### option 'customBuild' of project
		if len(lenv['customBuild']):
			for target, cmd in lenv['customBuild'].iteritems():
				if target not in self.myBuildTargets:	continue

				### Moves to 'sandbox'
				# Writes cmd in a temporary file
				with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as file:
					file.writelines( cmd )

				# Backups current working directory
				backupCWD = os.getcwd()
				os.chdir( lenv['sbf_projectPathName'] )

				# Adapts sys.path
				sys.path.append( lenv['sbf_projectPathName'] )

				# Executing command, lenv is available to command
				print stringFormatter(lenv, "customBuild '{0}' for project {1}".format( target, lenv['sbf_project']))
				locals = { 'lenv': lenv }
				execfile( file.name, locals  )

				# Process returned value
				if locals['exitCode'] > 0:
					print ('exit code:{0}'.format(locals['exitCode']))
					Exit(locals['exitCode'])
				print

				# Restores state before 'sandbox'
				sys.path.pop()
				os.chdir( backupCWD )

				# Cleaning
				os.remove(file.name)

				### Deferred executing cmd (command line and not python code)
				# Propagating SCONS_BUILD_FRAMEWORK environment variable in command(s)
				#lenv['ENV']['SCONS_BUILD_FRAMEWORK'] = self.mySCONS_BUILD_FRAMEWORK
				#Alias( target, lenv.Command(
				#	'{0}_{1}_print.out'.format(lenv['sbf_project'], target), 'dummy.in',
				#	Action( nopAction, stringFormatter(lenv, "customBuild for project {0} : '{1}'".format(lenv['sbf_project'], cmd)) ) ))
				#Alias( target, lenv.Command(
				#	'{0}_{1}.out'.format(lenv['sbf_project'], target), 'dummy.in', '{cmd}'.format(cmd=cmd), chdir=lenv['sbf_projectPathName'] ) )

		self.initializeProject( lenv )
		self.configureProject( lenv, self.myType )



		### BIN BUILD ###

		# lenv modified: CPPPATH, PDB, Precious(), SideEffect(), Alias(), Clean()
		#
		# installInBinTarget, intallTestInBinTarget
		# lenv['sbf_rc'] =[resource.rc, resource_sbf.rc, project.ico]
		# lenv['sbf_bin_debuginfo']
		# 'myProject_resource_generation' and 'myProject_build' (aliasProjectBuild) targets

		## Processes win32 resource files (resource.rc and resource_sbf.rc)
		objFiles = []
		installInBinTarget = []
		installTestInBinTarget = []

		# @todo generalizes a rc system
		Alias( self.myProject + '_resource.rc_generation' )

		rcPath = join(self.myProjectPathName, 'rc')
		if self.myCC == 'cl': # and self.myPlatform == 'win'
			# Adds project/rc directory to CPPPATH
			if os.path.isdir( rcPath ): lenv.Append( CPPPATH = rcPath )

			# Compiles resource.rc
			rcFile = join(rcPath, 'resource.rc')
			if os.path.isfile( rcFile ):
				# Compiles the resource file
				objFiles += lenv.RES( rcFile )
				lenv['sbf_rc'] = [rcFile]
			else:
				lenv['sbf_rc'] = []

			# Generates resource_sbf.rc file
			sbfRCFile = join(self.myProjectBuildPathExpanded, 'resource_sbf.rc')
# @todo Textfile()
			Alias(	self.myProject + '_resource_generation',
					lenv.Command( sbfRCFile, 'dummy.in', Action( resourceFileGeneration, printGenerate ) ) )
			objFiles += lenv.RES( sbfRCFile )

			# @todo FIXME not very cute, same code in sbfRC
			iconAbsPathFile	= join( rcPath, lenv['sbf_project'] + '.ico' )
			if os.path.isfile( iconAbsPathFile ) :
				lenv['sbf_rc'].append( iconAbsPathFile )
		else:
			lenv['sbf_rc'] = []

		# @todo move to sbfQt.py
		# Qt: rcc on rc/resources.qrc
		rcFile = join(rcPath, 'resources.qrc')
		if os.path.isfile( rcFile ):
			# Compiles the resource file
			inputFile = rcFile
			outputFile = join(self.myProjectBuildPathExpanded, 'qrc_resources.cpp')
			objFiles += lenv.Command( outputFile, inputFile, Action( [['rcc', '-name', self.myProject, '$SOURCE', '-o', '${TARGETS[0]}']] ) )
			lenv['sbf_rc'].append( rcFile )
		#else nothing todo

		## Build source files
		# setup 'pseudo BuildDir' (with OBJPREFIX)
		# @todo use VariantDir()

		filesFromInclude = self.getFiles( 'include', lenv )

		objProject = join( self.myProjectBuildPathExpanded, self.myProject + self.myProjectPostfix ) + '_' + self.myVersion + self.my_Platform_myCCVersion + self.my_FullPostfix

		# Qt: moc stage
		if 'qt' in lenv['uses']:	moc(lenv, getFilesForMoc(filesFromInclude), objFiles)

# @todo Modularization {	alias : ,
#							filesShare, } testModule.execute()
#						swigModule.execute()
#						...

		# Test : aliasProjectTestBuild and filesFromTestShare
		aliasProjectTestBuild = None
		filesFromTestShare = []

		#if False:		# @todo remove this hack for emscripten
		if self.haveToBuildTest and os.path.exists('test'):
			# Add implicit uses for gtest (for all test related targets and pakUpdate)
			if 'gtest' not in self.myImplicitUsesSet:
				self.myImplicitUsesSet.add( 'gtest' )
				self.myImplicitUses.append( 'gtest' )

			#
			filesFromTestShare = self.getFiles( 'share', lenv, 'test' )

			# Configure environment
			testEnv = self.myEnv.Clone()

			testVarDir = join(self.myProjectBuildPathExpanded, '_test')
			testSrcDir = join(self.myProjectPathName, 'test')

			self.readProjectOptionsAndUpdateEnv( testEnv )
			testEnv['sbf_projectPathName'] = join( lenv['sbf_projectPath'], lenv['sbf_project'], 'test' )		# used by printBuild()
			testEnv['sbf_project'] = '{}-test'.format(lenv['sbf_project'])										# used by CPPDEFINES.MODULE_NAME
			self.configureProjectCxxFlagsAndLinkFlags( testEnv, 'exec', skipDefinesInCXXFLAGS=True )

			testEnv.Prepend( CPPPATH = join(testSrcDir, 'include') )

			testEnv['uses'].append( 'gtest' ) # Implicit uses='gtest'
			(libsExpanded, buildSbfLibrary) = computeLibsExpanded( self, testEnv['libs'] )
			uses( self, testEnv, testEnv['uses'] )
			### configures CPPDEFINES with myDefines
			testEnv.Append( CPPDEFINES = self.myDefines )
			testEnv.Prepend( LIBS = objProject )
			testEnv.Append( LIBS = libsExpanded )
			testEnv.Append( LIBS = testEnv['stdlibs'] )

			#
			testEnv.VariantDir( testVarDir, testSrcDir, duplicate = 1 )

			if lenv['type'] not in ['shared', 'static']:
				print ("sbfError: Try to build tests for project '{}'. But only libraries can be tested.".format(self.myProject))
				Exit(1)

			# Compiles test source files
			baseFilename = '{projectName}_{version}{_platform_ccVersion}{_fullPostfix}'.format(projectName=testEnv['sbf_project'] + testEnv['projectPostfix'], version=self.myVersion, _platform_ccVersion=self.my_Platform_myCCVersion, _fullPostfix=self.my_FullPostfix )
			pathFilenameProgram = '{outdir}{sep}{filename}'.format( outdir = testVarDir, sep=os.sep, filename=baseFilename )

			# target projectTest_build
			testTarget = testEnv.Program( pathFilenameProgram, [ join(testVarDir, file) for file in self.getFiles('src', lenv, 'test') ] )
			aliasProjectTestBuild = Alias( self.myProject + '-test_build', testEnv.Command('dummy_build_test_print' + self.myProject, 'dummy.in', Action(nopAction, printBuild)) )
			aliasProjectTestBuild += testTarget

			# file to install
			installTestInBinTarget.append( File(pathFilenameProgram+testEnv['PROGSUFFIX']) )


		# Swig
		def extractModuleName( file ):
			# '%module moduleName' detection
			# or
			# '%module (directors="1") moduleName' detection
			regexDirector = r'(?:\s*[(]\s*directors\s*=\s*"1"\s*[)])?'
			moduleNameRe = re.compile(r'^\s*%module{}\s+([A-Za-z0-9_-]+)\s*'.format(regexDirector))
			with open(file, 'r') as file:
				for line in file:
					matchObject = moduleNameRe.match( line )
					if matchObject:						
						return matchObject.group(1)

		swigFiles = self.getFiles( 'swig', lenv )
		swigTarget = []
		if swigFiles and 'swig' in lenv['stages']:
			# @todo move the code initializing shlibsuffix in SConsBuildFramework initialization stage.
			if self.myPlatform == 'win':
				shlibsuffix = '.pyd'
			else:
				shlibsuffix = '.so'
			# Add implicit uses for swig and python
			if 'swig' not in self.myImplicitUsesSet:
				assert( 'python' not in self.myImplicitUsesSet )
				# swig
				self.myImplicitUsesSet.add( 'swig' )
				self.myImplicitUses.append( 'swig' )
				# python
				self.myImplicitUsesSet.add( 'python' )
				self.myImplicitUses.append( 'python' )

			# configuration postfix
			if self.myConfig == 'debug':
				configPostfix = '_d'
			else:
				configPostfix = ''

			# Configure environment
			swigEnv = lenv.Clone( tools=['swig'] ) # @todo should be self.myEnv.Clone()

			uses( self, swigEnv, 'python' )

			swigVarDir = join(self.myProjectBuildPathExpanded, '_swig')
			swigSrcDir = join(self.myProjectPathName, 'swig')
			swigEnv.VariantDir( swigVarDir, swigSrcDir )

			swigEnv['SWIGPATH'] = swigEnv['CPPPATH'] # project/include, local/include
			if self.myType in ['shared', 'static']: 
				swigEnv.Append(SWIGPATH = self.myIncludesInstallExtPaths[0]) # localExt/include
				if self.myPlatform == 'posix':
					# @todo remove the two following lines only here for linux
					swigEnv.Append(SWIGPATH = join(self.myInstallExtPaths[0], 'bin/Lib/python') ) # localExt/bin/Lib/python
					swigEnv.Append(SWIGPATH = join(self.myInstallExtPaths[0], 'bin/Lib/') ) # localExt/bin/Lib

			# for debug
			# print 'SWIGPATH', swigEnv['SWIGPATH']
			swigEnv['SWIGFLAGS'] = [ '-c++', '-python', '-dirprot' ]
			if swigEnv['printCmdLine'] != 'full':
				swigEnv['SWIGCOMSTR'] = 'Processing swig file ${SOURCE.file}'

			# Processes each file
			for file in swigFiles:
				moduleName = extractModuleName(file)
				if not moduleName:
					raise SCons.Errors.UserError( "Unable to extract module name of swig file {}.".format(join(self.myProjectPathName, file)) )
					#print ("Ignore swig file {}.".format(join(self.myProjectPathName, file)) )
					#continue


				# Creates shared library (_*[_d].pyd)
				baseFilename = '_{moduleName}{configPostfix}'.format( moduleName=moduleName, configPostfix=configPostfix )

				installInBinTarget.append( File(join(swigVarDir, moduleName+'.py')) )
				installInBinTarget.append( File(join(swigVarDir, baseFilename+shlibsuffix)) )
				#installInBinTarget.append( File(join(swigVarDir, baseFilename+'.pyd.manifest')) )
				#installInBinTarget.append( File(join(swigVarDir, baseFilename+'.pdb')) )

				pathFilenameSharedLibrary = '{outdir}{sep}{filename}'.format( outdir = swigVarDir, sep=os.sep, filename=baseFilename )
				tmp = swigEnv.SharedLibrary( pathFilenameSharedLibrary, file.replace('swig', swigVarDir, 1), SHLIBPREFIX = '', SHLIBSUFFIX=shlibsuffix )
				swigEnv.Append( LIBPATH = dirname(objProject) ) # link with the current project
				swigEnv.Append( LIBS = basename(objProject) ) # link with the current project
				swigTarget += tmp
		else:
			swigTarget = None

		# setup building rules of current toolchain
		projectTarget = self.myCurrentToolChain[3](self, lenv, objFiles, objProject, installInBinTarget )

		### target 'myProject_build'
		aliasProjectBuild = Alias( self.myProject + '_build', lenv.Command('dummy_build_print_' + self.myProject, 'dummy.in', Action(nopAction, printBuild)) )
		Alias( self.myProject + '_build', self.myProject + '_resource.rc_generation' )
		Alias( self.myProject + '_build', projectTarget )

		# swig
		if swigTarget:
			Alias( self.myProject + '_build', swigTarget )

		#
		Clean( self.myProject + '_build', self.myProjectBuildPathExpanded )



		### SHARE BUILD ###
		# filters, command
		# filesFromShare, filesFromShareToBuild
		# filesFromShareBuilt

		(filters, command) = computeFiltersAndCommand( lenv )
		(filesFromShareToBuild, filesFromShare) = applyFilters( self.getFiles('share', lenv), filters )
		filesFromShareBuilt = buildFilesFromShare( filesFromShareToBuild, self, lenv, command )



		### DEPS 'BUILD' ###
		# depsFiles, depsLicensesFiles
		# 'deps' only for launch project and if needed
		if isLaunchProject(lenv) and len(self.myBuildTargets & self.myTargetsWhoNeedDeps) > 0:
			depsFiles, depsLicensesFiles = getDepsFiles( lenv, self.myLibInstallExtPaths, isLaunchProject(lenv) )
		else:
			depsFiles = []
			depsLicensesFiles = []

		licensesFiles = self.getFiles( 'license', lenv )



		### INSTALLATION ###

		# self.myInstallDirectories, self.myDepsInstallDirectories
		# installTarget, installTestTarget

		self.myInstallDirectories = computeInstallDirectories(lenv, self.myInstallDirectory)
		self.myInstallDirectories.extend( self.myNSISInstallDirectories )
		#   Don't install deps files in myInstallDirectories[0], because myInstallDirectories[0] is in the PATH.
		self.myDepsInstallDirectories = self.myInstallDirectories[1:]
		# for debugging : print lenv['sbf_project'], self.myInstallDirectories

		# infofile, info, zip* and nsis
		configureInfofileTarget( lenv, isLaunchProject(lenv) )

		if isLaunchProject(lenv):
			configureInfoTarget( lenv )
			configureZipAndNSISTargets(lenv)

		installTarget = []
		installTestTarget = []


		# install libraries and binaries in 'bin'
		# 	from installInBinTarget
		if len(installInBinTarget) > 0:
			for installDir in self.myInstallDirectories:
				installTarget += lenv.Install( join(installDir, 'bin'), installInBinTarget )
		# 	from installTestInBinTarget
		if len(installTestInBinTarget) > 0:
			for installDir in self.myInstallDirectories:
				installTestTarget += lenv.Install( join(installDir, 'bin'), installTestInBinTarget )

		# install dependencies in 'bin' (from depsFiles)
		# depsTarget
		depsTarget = []

		if len(depsFiles) > 0:
			for installDir in self.myDepsInstallDirectories:
				for (absFile, relFile) in depsFiles:
					depsTarget += lenv.InstallAs( join(installDir, relFile), absFile )

		# install licenses files in 'license' (from depsFiles and getFiles())
		if len(depsLicensesFiles) > 0:
			for installDir in self.myDepsInstallDirectories:
				licenseDir = join(installDir, 'license')
				for (licenseTarget, licenseSource) in depsLicensesFiles:
					depsTarget += lenv.InstallAs( join(licenseDir, licenseTarget), licenseSource )

		if len(licensesFiles) > 0:
			for installDir in self.myDepsInstallDirectories:
				licenseDir = join(installDir, 'license')
				for relFile in licensesFiles:
					target = relFile.replace('license', join(licenseDir, self.myProject), 1)
					source = join(self.myProjectPathName, relFile)
					depsTarget += lenv.InstallAs( target, source )

		# install in 'share' (from filesFromShare, filesFromShareBuilt and lenv['sbf_info'])
		for installDir in self.myInstallDirectories:
			shareBaseDir = join(installDir, 'share', self.myProject, self.myVersion)
			for file in filesFromShare:
				installTarget += lenv.InstallAs( file.replace('share', shareBaseDir, 1), join(self.myProjectPathName, file) )
			for fileAbs in filesFromShareBuilt:
				fileRel = fileAbs[ fileAbs.index('share') : ]
				installTarget += lenv.InstallAs( fileRel.replace('share', shareBaseDir, 1), fileAbs )
			for file in lenv.get('sbf_info', []):
				installTarget += lenv.Install( shareBaseDir, file )
			# Test
			shareTestBaseDir = join(installDir, 'share', '{}-test'.format(self.myProject), self.myVersion)
			for file in filesFromTestShare:
				installTestTarget += lenv.InstallAs( file.replace('share', shareTestBaseDir, 1), join(self.myProjectPathName, 'test', file) )

		# install in 'include'
		# installInIncludeTarget
		installInIncludeTarget = filesFromInclude

		#	install swig files (i.e. *.i)
		for swigFile in swigFiles:
			src = join( self.myProjectPathName, swigFile )
			dst = join( self.myInstallDirectory, 'include', swigFile.replace('swig', self.myProject, 1) )
			installTarget += lenv.InstallAs( dst, src )

		# install in 'include'
		if 'mrproper' in self.myBuildTargets:
			removeAllFilesRO( join(self.myInstallDirectory, 'include') )
		elif 'clean' in self.myBuildTargets:
			pass
		else:
			# @todo one Command per directory
			for file in installInIncludeTarget :
				dst = join(self.myInstallDirectory, file)
				src = join(self.myProjectPathName, file)

				# Installing filename.hpp
				lenv.Precious( dst )
				installTarget += lenv.Command( dst, src, Action(installRO, 'Installing {0}'.format(file) ) )



		######	setup targets : myProject_deps myProject_install myProject myProject_clean myProject_mrproper ######
#=======================================================================================================================
#	  'scons build' for all myproject_build
#	  'scons install' for all myproject_install
#
#	  'scons build' for all myproject_build
#	  'scons install' for all myproject_install
#	  'scons' or 'scons all' for all myproject (this is the default target)
#	  'scons debug' like target all, but config option is forced to debug
#	  'scons release' like target all but config option is forced to release
#	  'scons clean' for all myproject_clean
#	  'scons mrproper' for all myproject_mrproper
#
#	  'scons myproject_build' or 'myproject_install' or 'myproject' (idem myproject_install) or 'myproject_clean' or 'myproject_mrproper'
#
#     'scons myproject_vcproj' to build a Microsoft Visual Studio project file.
#=======================================================================================================================
		### myProject_deps
		aliasProjectDeps = Alias( self.myProject + '_deps', lenv.Command('dummy_deps_print' + self.myProject, 'dummy.in', Action( nopAction, printDeps ) ) )
		Alias( self.myProject + '_deps', depsTarget )

		### myProject_install
		aliasProjectInstall = Alias( self.myProject + '_install', self.myProject + '_build' )
		Alias( self.myProject + '_install', lenv.Command('dummy_install_print' + self.myProject, 'dummy.in', Action(nopAction, printInstall)) )
		Alias( self.myProject + '_install', installTarget )

		### myProject
		aliasProject = Alias( self.myProject, aliasProjectInstall )

		### myProject_clean
		aliasProjectClean = Alias( self.myProject + '_clean', self.myProject + '_build' )

		### myProject_mrproper
		aliasProjectMrproper = Alias( self.myProject + '_mrproper', aliasProjectInstall )
		# temporary build path
		Clean( self.myProject + '_mrproper', join(self.myProjectBuildPath, self.myProject) )
		# clean 'share'
		for installDir in self.myInstallDirectories:
			shareProjectInstallDirectory = join( installDir, 'share', self.myProject )
			if os.path.exists( shareProjectInstallDirectory ):
				shareProjectInstallEntries = os.listdir( shareProjectInstallDirectory )
				if	len(shareProjectInstallEntries) == 0 or \
					(len(shareProjectInstallEntries) == 1 and shareProjectInstallEntries[0] == self.myVersion):
					Clean( self.myProject + '_mrproper', shareProjectInstallDirectory )
				else:
					Clean( self.myProject + '_mrproper', join(shareProjectInstallDirectory, self.myVersion) )
			# else : nothing to do, no share/myProject directory

		# clean 'include'
		#for installDir in self.myInstallDirectories:
		#	Clean( self.myProject + '_mrproper', join(installDir, 'include', self.myProject) )

		# @todo Improves mrproper (local/doc/myProject directory ?)

# @todo lenv['sbf_*'] used by vcproj target
		### Configures lenv
		lenv['sbf_bin']						= []
		lenv['sbf_include']					= installInIncludeTarget

# @todo unify lenv['sbf_share'] and lenv['sbf_shareBuilt'] in lenv['sbf_share']
		lenv['sbf_share']						= filesFromShare
#		lenv['sbf_shareBuilt']					= filesFromShareBuilt


#		lenv['sbf_lib_object']					= []
#		lenv['sbf_lib_object_for_developer']	= []

		#lenv['sbf_bin_debuginfo'] = lenv['PDB']
		#lenv['sbf_lib_debuginfo'] = lenv['PDB']

		lenv['sbf_files']						= glob.glob( join(self.myProjectPathName, '*.options') )
		lenv['sbf_files'].append( join(self.myProjectPathName, 'sconstruct') )
		#lenv['sbf_info']
		#lenv['sbf_rc']
		# @todo configures sbf_... for msvc/eclipse ?

		for elt in installInBinTarget :
			lenv['sbf_bin'].append( elt.abspath )

# @todo lazy
#		# @todo not very platform independent
#		for elt in installInLibTarget:
#			# @todo must be optimize
#			absPathFilename	= elt.abspath
#			filename		= os.path.split(absPathFilename)[1]
#			filenameExt		= os.path.splitext(filename)[1]
#			if filenameExt == '.lib':
#				lenv['sbf_lib_object_for_developer'].append( absPathFilename )
#			else :
#				lenv['sbf_lib_object'].append( absPathFilename )

		###### special targets: build install deps all clean mrproper ######
		Alias( 'build',		aliasProjectBuild							)
		Alias( 'install',	aliasProjectInstall							)
		Alias( 'test', 		[aliasProjectInstall, aliasProjectTestBuild, installTestTarget])
		Alias( 'deps',		aliasProjectDeps							)
		Alias( 'all',		aliasProject								)
		Alias( 'clean',		aliasProjectClean							)
		Alias( 'mrproper',	[aliasProjectClean, aliasProjectMrproper]	)

		# VCS clean and add
		self.doVcsCleanOrAdd( lenv )


		# Helpers for targets *run*
		def actionCall( runParams ):
			def _actionCall( runParams, target, source, env ):
				# command 'path' and 'exe'
				pathFilename = str(source[0])
				path = dirname(pathFilename)
				exe = basename(pathFilename)
				if env.sbf.myPlatform == 'win':
					cmdEnv = { 'PATH' : os.path.join(env.sbf.myInstallExtPaths[0], 'lib') }
				else:
					cmdEnv = os.environ
					#cmdEnv['LD_LIBRARY_PATH'] = '{}:$LD_LIBRARY_PATH'.format( join(env.sbf.myInstallDirectory, 'bin') ) no more used see -Wl,-rpath option
				return call( [exe] + runParams, path, cmdEnv )
			return lambda target, source, env : _actionCall( runParams, target, source, env )

		def buildPrintMsg( env, executableFilename, runParams ):
			printMsg = '\n' + stringFormatter(env, 'Launching {}'.format(executableFilename))

			if len(runParams):
				cmdParameters = ''
				for param in runParams:
					cmdParameters += ' ' + param
				printMsg += stringFormatter(env, 'with parameters:{}'.format(cmdParameters))
			return printMsg

		# Targets: onlyRun and run
		if len(self.myBuildTargets & self.myRunTargets) > 0:
			executableNode = searchExecutable( lenv, installInBinTarget )
			if executableNode:
				executableFilename	= basename(executableNode.abspath)
				pathForExecutable	= join(self.myInstallDirectory, 'bin')

				printMsg = buildPrintMsg( lenv, executableFilename, lenv['runParams'] )
				Alias( 'onlyrun',	lenv.Command(self.myProject + '_onlyRun.out', join(pathForExecutable, executableFilename),
									Action( actionCall(lenv['runParams']), printMsg ) ) )
				AlwaysBuild('onlyrun')

				Alias( 'run', ['install', 'onlyrun'] )

		# Targets: onlyRunTest and runTest
		if	len(self.myBuildTargets & self.myRunTestTargets)>0 and \
			len(installTestInBinTarget)>0:
			executableFilename = installTestInBinTarget[0].name
			pathForExecutable = join( self.myInstallDirectories[0], 'bin' )

			printMsg = buildPrintMsg( lenv, executableFilename, lenv['runTestParams'] )

			Alias( 'onlyruntest',	lenv.Command(self.myProject + '_onlyRunTest.out', join(pathForExecutable, executableFilename),
									Action( actionCall(lenv['runTestParams']), printMsg ) ) )
			AlwaysBuild('onlyruntest')

			Alias( 'runtest', ['test', 'onlyruntest'] )


	###### Helpers ######

# @todo what == rc => remove lenv['sbf_rc']
	def getFiles( self, what, lenv, path = None ):
		"""	@param what		select what to collect. It could be 'src', 'include', 'share', 'license' and 'swig'
			@param path		path where to look for files ot None to retrieve files from current working directory

		@todo .cpp .cxx .c => config.options global, idem for pruneDirectories, .h .... => config.options global ?"""

		basenameWithDotRe = r"^[a-zA-Z][a-zA-Z0-9_\-]*\."

		if path:
			backupCWD = os.getcwd()
			os.chdir( path )

		files = []
		if what == 'src':
			searchFiles( 'src', files, ['.svn'], basenameWithDotRe + r"(?:cpp|c)$" )
		elif what == 'include':
			searchFiles( 'include', files, ['.svn'], basenameWithDotRe + r"(?:hpp|hxx|inl|h)$" )
		elif what == 'share':
			filesNotFiltered = []
			searchFiles( 'share', filesNotFiltered, ['.svn'], r"^[^_]+.*$" )

			# filtering
			shareExcludeFilters = lenv['shareExclude']
			if len(shareExcludeFilters) > 0:
				for file in filesNotFiltered:
					for filter in shareExcludeFilters:
						if fnmatch.fnmatch(file, filter):
							if lenv.GetOption('verbosity'):
								print ('Exclude file {0}'.format( join(lenv['sbf_projectPathName'], file) ) )
							break
					else:
						files.append( file )
			else:
				files = filesNotFiltered
		elif what == 'license':
			searchFiles( 'license', files, ['.svn'], r"^.*" )
		elif what == 'swig':
			searchFiles( 'swig', files, ['.svn'], basenameWithDotRe + r"(?:i)$" )
		else:
			raise SCons.Errors.UserError("Internal sbf error in getFiles().")

		if path:
			os.chdir( backupCWD )

		return files


	def getAllFiles( self, projectEnv ):
		"""Returns files taking into account by sbf to build the given project. include, share, src, *.options and rc files are returned."""
		return projectEnv['sbf_include'] +projectEnv['sbf_share'] + projectEnv['sbf_src'] +  projectEnv['sbf_files'] + projectEnv['sbf_rc']

	def getAllFiles( self, projectName ):
		"""Returns files taking into account by sbf to build the given project. include, share, src, *.options and rc files are returned."""
		projectEnv = self.getEnv( projectName )
		return projectEnv['sbf_include'] +projectEnv['sbf_share'] + projectEnv['sbf_src'] +  projectEnv['sbf_files'] + projectEnv['sbf_rc']

	### share directory
	def getShareDirectory( self, projectEnv = None ):
		if projectEnv:
			return os.path.join( 'share', projectEnv['sbf_project'], projectEnv['version'] )
		else:
			return os.path.join( 'share', self.myProject, self.myVersion )

	def getShareInstallDirectory( self, projectEnv = None ):
		if projectEnv:
			return os.path.join( self.myInstallDirectory, self.getShareDirectory(projectEnv) )
		else:
			return os.path.join( self.myInstallDirectory, self.getShareDirectory() )

	### Helper for exclusion
	def matchProjectInList( self, project, fnMatchList ):
		for pattern in fnMatchList:
			#print project, pattern, fnmatch.fnmatch( project, pattern )
			if fnmatch.fnmatch( project, pattern ):
				return True
		return False



	def getDepsProjectName( self, lenv, keepOnlyExistingProjects = True ):
		"""@return	a list containing all direct dependencies (deps options) of the project with the given environment.
					The returned list contains only project names (not full path or SCons environment)."""

		if keepOnlyExistingProjects :
			retVal = []
			for dep in lenv['deps']:
				projectName = os.path.basename(getNormalizedPathname(dep))
				if projectName in self.myParsedProjects :		# @todo uses a set()
					retVal.append( projectName )
				#else nothing to do
			return retVal
		else:
			retVal = []
			for dep in lenv['deps']:
				projectName = os.path.basename(getNormalizedPathname(dep))
				retVal.append( projectName )
			return retVal

	def getAllDependencies( self, lenv, addSBFLibrary = True ) :#, keepOnlyExistingProjects = True ):
		"""	Collects recursively all dependencies of the project with the given environment.
			@param addSBFLibrary True to implicitly append the 'sbf' library, False otherwise
			@return a list containing project name of all its dependencies."""
		stackDependencies			= self.getDepsProjectName(lenv) #, keepOnlyExistingProjects)
		recursiveDependenciesSet	= set()
		recursiveDependencies		= []
#		for elt in stackDependencies :
#			if elt not in recursiveDependenciesSet and elt in self.myParsedProjects :
#				recursiveDependenciesSet.add( elt )
#				recursiveDependencies.append( elt )

		while ( len(stackDependencies) > 0 ):
			dependencyName	= stackDependencies.pop(0)
			if dependencyName not in recursiveDependenciesSet:
				# found a new dependency

				# adds to dependecies containers
				recursiveDependenciesSet.add( dependencyName )
				recursiveDependencies.append( dependencyName )

				# adds new dependencies to the stack
				dependencyEnv	= self.myParsedProjects[ dependencyName ]
				stackDependencies += self.getDepsProjectName( dependencyEnv )

		if addSBFLibrary and ('sbf' in self.myParsedProjects): recursiveDependencies.append( 'sbf' )

		# Returns the list
		return recursiveDependencies


	def getAllUses( self, lenv ):
		"""Computes the set of all 'uses' for the project described by lenv and all its dependencies."""

		# The return value containing all 'uses'
		retValUses = set( lenv['uses'] )

		# Retrieves all dependencies
		dependencies = self.getAllDependencies(lenv)

		# Adds 'uses' to return value, for each dependency
		for dependency in dependencies:
			dependencyEnv = self.myParsedProjects[ dependency ]
			retValUses = retValUses.union( set(dependencyEnv['uses']) )

		# Adds implicit uses
		retValUses = retValUses.union( set(self.myImplicitUses) )

		# Returns the computed set
		return retValUses


	def getProjectsRoot( self, lenv ):
		"""	Computes common root of all projects
			Returns the desired path"""
		projectPathNameList = [ lenv['sbf_projectPathName'] ]
		for projectName in self.getAllDependencies(lenv):
			projectPathNameList.append( self.myParsedProjects[projectName]['sbf_projectPathName'] )

		projectsRoot = getNormalizedPathname( os.path.commonprefix( projectPathNameList ) )

		if os.path.exists(projectsRoot):
			return projectsRoot
		else:
			return os.path.dirname(projectsRoot)


	def getEnv( self, projectName ):
		"""Returns the environment for the given project name.
		@pre projectName must be an existing project name"""
		return self.myParsedProjects[ projectName ]

	def getRootProjectEnv( self ):
		"""Returns the environment for the project that has started the scons command."""
		return self.getEnv( self.myEnv['sbf_launchProject'] )
