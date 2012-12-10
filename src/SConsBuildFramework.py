# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, 2010, 2011, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import datetime
import fnmatch
import glob
import sbfIVersionControlSystem
import os
import re
import string
import tempfile
import time

from collections import OrderedDict

from sbfFiles import *
from sbfRC import resourceFileGeneration

from sbfAllVcs import *
from sbfQt import *
from sbfSubversion import anonymizeUrl, removeTrunkOrTagsOrBranches
from sbfPackagingSystem import PackagingSystem
from sbfTools import getPathsForTools, getPathsForRuntime, prependToPATH, appendToPATH
from sbfUI import askQuestion
from sbfUses import getPathsForSofa
from sbfUses import UseRepository, usesValidator, usesConverter, uses
from sbfUtils import *
from sbfVersion import printSBFVersion, extractVersion, splitLibsName, splitUsesName, splitDeploymentPrecond

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


def createBlowfishShareBuildCommand( key ):
	"""create Blowfish share build command
	@todo version and platform"""
	shareBuildCommand = (	'blowfish_1-0_${PLATFORM}_${CCVERSION}${sbf_my_FullPostfix}.exe encrypt ' + key + ' ${SOURCE} ${TARGET}',
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



### ###
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
	"""
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

def buildFilesFromShare( files, lenv, command ):
	"""Adds share build stage in 'build' target
	@return the list of files to install in 'share'"""

	sbf = lenv.sbf

	# list of files to install in 'share'
	outputs = []
	for file in files:
		inputFile = join(sbf.myProjectPathName, file)
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

		# Processes external dependencies (i.e. 'uses')
		# For each external dependency, do
		for useNameVersion in allUses:
			# Extracts name and version of incoming external dependency
			useName, useVersion = splitUsesName( useNameVersion )
			if lenv.GetOption('verbosity'): print ("Processing uses='{0}'...".format(useNameVersion))

			# Retrieves use object for incoming dependency
			use = UseRepository.getUse( useName )
			if use:
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
				elif use.getPackageType() == 'Full':
					pakSystem = PackagingSystem(lenv.sbf, verbose=False)
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
							absFile = join( sbf.myInstallExtPaths[0], relFile )
							depsFiles.append( (absFile, relFile) )
					else:
						raise SCons.Errors.UserError( '{0} {1} is NOT installed.'.format(useName, useVersion))
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
					pakSystem = PackagingSystem(lenv.sbf, verbose=False)
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
				elif use.getPackageType() == 'Full':
					# nothing to do
					pass
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


###### SConsBuildFramework main class ######
class SConsBuildFramework :

	# targets
	mySbfTargets					= set( ['sbfcheck', 'sbfpak', 'sbfconfigure', 'sbfunconfigure', 'sbfconfiguretools', 'sbfunconfiguretools'] )
	mySvnTargets					= set( ['svnadd', 'svncheckout', 'svnclean', 'svnrelocate', 'svnstatus', 'svnupdate'] )
	mySvnBranchOrTagTargets			= set( ['svnmktag', 'svnremotemkbranch'] )
	myInformationsTargets			= set( ['info', 'infofile'] )
	myBuildingTargets				= set( ['pakupdate', 'all', 'clean', 'mrproper'] )
	myRunTargets					= set( ['onlyrun', 'run'] )
	myVCProjTargets					= set( ['vcproj', 'vcproj_clean', 'vcproj_mrproper'] )
	myDoxTargets					= set( ['dox', 'dox_clean', 'dox_mrproper'] )
	# @todo 'zipruntime', 'zipdeps', 'zipdev', 'zipsrc', 'zip', 'zip_clean', 'zip_mrproper', 'nsis_clean', 'nsis_mrproper'
	myZipTargets					= set( ['portable', 'zipportable', 'dbg', 'zipdbg', 'nsis'] )

	myTargetsWhoNeedDeps			= set( ['deps', 'portable', 'zipportable', 'nsis'] )

	myAllTargets = mySbfTargets | mySvnTargets | mySvnBranchOrTagTargets | myInformationsTargets | myBuildingTargets | myRunTargets | myVCProjTargets | myDoxTargets | myZipTargets

	# Command-line options
	myCmdLineOptionsList			= ['debug', 'release']
	myCmdLineOptions				= set( myCmdLineOptionsList )

	# sbf environment
	mySCONS_BUILD_FRAMEWORK			= ''
	mySbfLibraryRoot				= ''

	# SCons environment
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

	# Options instances
	mySBFOptions					= None
	myProjectOptions				= None

	# Global attributes from command line
	myBuildTargets					= set()		# 'all' if no target is specified, without command line options (like 'debug'...)
	myCurrentCmdLineOptions			= set()
	#myGHasCleanOption				= False

	# Globals attributes

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
	myPlatform						= ''			# 'win32' | 'cygwin' | 'posix' | 'darwin'
	myCC							= ''			# 'cl', 'gcc'
	myCCVersionNumber				= 0				# 8.000000 for cl8-0, 4.002001 for gcc 4.2.1
	myIsExpressEdition				= False			# True if Visual Express Edition, False otherwise
	myCCVersion						= ''			# cl8-0Exp
	myMSVSIDE						= ''			# location of VCExpress (example: C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\IDE\VCExpress.exe).
	myMSVCVARS32					= ''			# location of vcvars32.bat (example C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC\bin\vcvars32.bat).
	myMSVC							= ''			# root directory of Microsoft Visual Studio C++ (i.e. C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC)
	my_Platform_myCCVersion			= ''


	# Global attributes from .SConsBuildFramework.options or computed from it
	myNumJobs						= 1
	myCompanyName					= ''
	mySvnUrls						= {}
	mySvnCheckoutExclude			= []
	mySvnUpdateExclude				= []
	myInstallPaths					= []
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

	myProjectBuildPathExpanded		= ''	# c:\temp\sbf\build\gle\0-3\win32\cl7-1\debug
	mySubsystemNotDefined			= None	# True if LINKFLAGS contains '/SUBSYSTEM:'

	# List of projects that have been already parsed by scons
	myParsedProjects				= OrderedDict() # { (projectName, env),...} 
	myParsedProjectsSet				= set()			# set([projectnameinlowercase,...]) a set of parsed projects in lower case
	myFailedVcsProjects				= set()			# set([projectName, ...])
	# @todo checks usage of myBuiltProjects instead of myParsedProjects
	myBuiltProjects					= OrderedDict()

	# Used by mktag
	myBranchSvnUrls				= OrderedDict() # OrderedDict([(projectPathName, url@rev),...])
	#lenv['myBranchesOrTags']	= 'tags' or 'branches' or None
	#lenv['myBranchOrTag']		= 'tag' or 'branch' or None
	#lenv['myBranch']			= None or env['svnDefaultBranch'] or '2.0' for example.

	###### Constructor ######
	def __init__( self, initializeOptions = True ) :

		# Retrieves and normalizes SCONS_BUILD_FRAMEWORK
		self.mySCONS_BUILD_FRAMEWORK = os.getenv('SCONS_BUILD_FRAMEWORK')
		if self.mySCONS_BUILD_FRAMEWORK == None:
			raise SCons.Errors.UserError( "The SCONS_BUILD_FRAMEWORK environment variable is not defined." )
		self.mySCONS_BUILD_FRAMEWORK = getNormalizedPathname( os.getenv('SCONS_BUILD_FRAMEWORK') )

		# Sets the root directory of sbf library
		self.mySbfLibraryRoot = os.path.join( self.mySCONS_BUILD_FRAMEWORK, 'lib', 'sbf' )

		currentSConsBuildFrameworkOptions = getSConsBuildFrameworkOptionsFileLocation( self.mySCONS_BUILD_FRAMEWORK )
		self.mySBFOptions = self.readSConsBuildFrameworkOptions( currentSConsBuildFrameworkOptions )

		# Constructs SCons environment.
		tmpEnv = Environment( options = self.mySBFOptions, tools=[] )

		myTools = ['textfile']
		if tmpEnv['PLATFORM'] == 'win32':
			myTools += ['msvc', 'mslib', 'mslink', 'mssdk']

			myTargetArch = 'x86'
			if tmpEnv['clVersion'] != 'highest':
				myMsvcVersion = tmpEnv['clVersion']
				# Tests existance of the desired version of cl
				if myMsvcVersion not in cached_get_installed_vcs():
					print ('sbfError: clVersion sets to {0}'.format(myMsvcVersion))
					print ('The installed versions of cl are {0}'.format(sorted(cached_get_installed_vcs())))
					Exit(1)
			else:
				myMsvcVersion = None

			self.myEnv = Environment( options = self.mySBFOptions, tools = myTools, TARGET_ARCH = myTargetArch, MSVC_VERSION = myMsvcVersion )


			pathFromEnv = os.environ['PATH'] ### @todo uses getInstallPath() on win32 to FIXME not very recommended
			if pathFromEnv != None:
				self.myEnv['ENV']['PATH'] += pathFromEnv
		else:
			self.myEnv = Environment( options = self.mySBFOptions, tools = myTools )


		# Configures command line max length
		if self.myEnv['PLATFORM'] == 'win32':
			#self.myEnv['MSVC_BATCH'] = True # @todo wait improvement in SCons (better control of scheduler => -j8 and /MP8 => 8*8 processes !!! ).
			# @todo adds windows version helpers in sbf
			winVerTuple	= sys.getwindowsversion()
			winVerNumber= self.computeVersionNumber( [winVerTuple[0], winVerTuple[1]] )
			if winVerNumber >= 5.1 :
				# On computers running Microsoft Windows XP or later, the maximum length
				# of the string that you can use at the command prompt is 8191 characters.
				# XP version is 5.1
				self.myEnv['MAXLINELENGTH'] = 7680
				# On computers running Microsoft Windows 2000 or Windows NT 4.0,
				# the maximum length of the string that you can use at the command
				# prompt is 2047 characters.

		# Configures command line output
		if self.myEnv['printCmdLine'] == 'less' :
			self.myEnv['PRINT_CMD_LINE_FUNC'] = sbfPrintCmdLine
			if self.myEnv['PLATFORM'] == 'win32' :
				# cl prints always source filename. The following line (and 'PRINT_CMD_LINE_FUNC'), gets around this problem to avoid duplicate output.
				self.myEnv['CXXCOMSTR']		= 'sbfNull'
				self.myEnv['SHCXXCOMSTR']	= 'sbfNull'

				self.myEnv['RCCOMSTR'] = 'Compiling resource ${SOURCE.file}'
			else:
				self.myEnv['CXXCOMSTR']		= "$SOURCE.file"
				self.myEnv['SHCXXCOMSTR']	= "$SOURCE.file"

			self.myEnv['INSTALLSTR'] = "Installing ${SOURCE.file}"
		#self.myEnv['LINKCOMSTR'] = "Linking $TARGET"#'sbfLN'#print_cmd_line
		#self.myEnv['SHLINKCOMSTR'] = "Linking $TARGET"#'sbfShLN' #print_cmd_line
		#self.myEnv.Replace(LINKCOMSTR = "Linking... ${TARGET.file}")
		#self.myEnv.Replace(SHLINKCOMSTR = "$LINKCOMSTR")
		#self.myEnv.Replace(ARCOMSTR = "Creating archive... ${TARGET.file}")

# @todo uses UnknownVariables()
#		#
#		unknown = self.mySBFOptions.UnknownVariables()
#		print "Unknown variables:", unknown.keys()
#		if unknown:
#			print "Unknown variables:", unknown.keys()
#			Exit(1)

		# Analyses command line options
		AddOption(	'--nd', '--nodeps',
					action	= 'store_true',
					dest	= 'nodeps',
					default	= False,
					help	= "do not follow project dependencies specified by 'deps' project option." )
		self.myEnv['nodeps'] = GetOption('nodeps')

		AddOption(	'--nx', '--noexclude',
					action	= 'store_true',
					dest	= 'noexclude',
					default	= False,
					help	= "do not exclude project(s) specified by 'projectExclude' sbf option." )
		self.myEnv['exclude'] = not GetOption('noexclude')

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
		#print self.myEnv.GetOption("optimize")
		#print self.myEnv.GetOption("weak_localext")
		#if self.myEnv.GetOption("optimize") == 0 :
		#	self.myEnv.SetOption("weak_localext", 0 )

		AddOption(	'--fast',
					action	= 'store_true',
					default	= False,
					help	= "Speed up the SCons 'thinking' about what must be built before it starts the build. The drawback of this option is that SCons will not rebuild correctly the project in several rare cases." # this comment is duplicated in Help()
					)
		if self.myEnv.GetOption('fast'):
			self.myEnv['decider'] = 'fast'

		AddOption(	"--accurate",
					action	= "store_true",
					default	= False,
					help	= "See 'decider' SConsBuildFramework option."
					)
		if self.myEnv.GetOption('accurate'):
			self.myEnv['decider'] = 'accurate'

		# @todo Each instance of '--verbose' on the command line increases the verbosity level by one, so if you need more details on the output, specify it twice.
		AddOption(	"--verbose",
					action	= "store_true",
					dest	= "verbosity",
					default	= False,
					help	= "Shows details about the results of running sbf. This can be especially useful when the results might not be obvious." )

		# @todo FIXME : It is disabled, because it doesn't work properly
		# Log into a file the last scons outputs (stdout and stderr) for a project
		#myProject = os.path.basename( os.getcwd() )
		#logCommand = "tee " + os.path.join( env['buildPath'], myProject + "_sbf.log")
		#sys.stderr = sys.stdout = open( os.path.join( env['buildPath'], myProject + "_sbf.log"), 'w' )# or
		#sys.stdout = sys.stderr = os.popen(logCommand, "w")

		# myCurrentTime, myDate, myTime, myDateTime, myDateTimeForUI
		self.myCurrentTime = time.localtime()

		self.myTimePostFix = time.strftime( self.myEnv['postfixTimeFormat'], self.myCurrentTime )

		self.myDate	= time.strftime( '%Y-%m-%d', self.myCurrentTime )
		self.myTime	= time.strftime( '%Hh%Mm%Ss', self.myCurrentTime )

		# format compatible with that specified in the RFC 2822 Internet email standard.
		# self.myDateTime	= str(datetime.datetime.today().strftime("%a, %d %b %Y %H:%M:%S +0000"))
		self.myDateTime	= '{0}_{1}'.format( self.myDate, self.myTime )
		self.myDateTimeForUI = time.strftime( '%d-%b-%Y %H:%M:%S', self.myCurrentTime )

		# Sets the vcs subsystem (at this time only svn is supported).
		if isSubversionAvailable:
			self.myVcs = Subversion( self )
		else:
			self.myVcs = sbfIVersionControlSystem.IVersionControlSystem()

		# Prints sbf version, date and time at sbf startup
		if self.myEnv.GetOption('verbosity') :
			printSBFVersion()
			print 'started', self.myDateTimeForUI

		# Retrieves all targets (normalized in lower case)
		self.myBuildTargets = [str(buildTarget).lower() for buildTarget in BUILD_TARGETS]
		SCons.Script.BUILD_TARGETS[:] = self.myBuildTargets
		self.myBuildTargets = set(self.myBuildTargets)
		self.myCurrentCmdLineOptions = self.myBuildTargets & self.myCmdLineOptions
		self.myBuildTargets = self.myBuildTargets - self.myCurrentCmdLineOptions
		if len(self.myBuildTargets)==0:	self.myBuildTargets = set(['all'])

		tmp = list(self.myBuildTargets)[0]
		Alias( tmp )
		Alias( list(self.myCurrentCmdLineOptions), tmp )
		Default('all')

		# Tests which target is given
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


		# myPlatform, myCC, myCCVersionNumber, myCCVersion and my_Platform_myCCVersion
		# myPlatform = win32 | cygwin | posix | darwin				@todo TOTHINK: posix != linux and bsd ?, env['PLATFORM'] != sys.platform
		self.myPlatform	= self.myEnv['PLATFORM']

		# myCC, myCCVersionNumber, myCCVersion and my_Platform_myCCVersion
		if self.myEnv['CC'] == 'cl' :
			# Sets compiler
			self.myCC				=	'cl'
			# Extracts version number
			# Step 1 : Extracts x.y (without Exp if any)
			ccVersion				=	self.myEnv['MSVS_VERSION'].replace('Exp', '', 1)
			# Step 2 : Extracts major and minor version
			splittedCCVersion		=	ccVersion.split( '.', 1 )
			# Step 3 : Computes version number
			self.myCCVersionNumber	= self.computeVersionNumber( splittedCCVersion )
			# Constructs myCCVersion ( clMajor-Minor[Exp] )
			self.myIsExpressEdition = self.myEnv['MSVS_VERSION'].find('Exp') != -1
			self.myCCVersion = self.myCC + self.getVersionNumberString2( self.myCCVersionNumber )
			if self.myIsExpressEdition:
				# Adds 'Exp'
				self.myCCVersion += 'Exp'
			self.myEnv['CCVERSION'] = self.myCCVersion

			self.myMSVSIDE = self.myEnv.WhereIs( 'VCExpress' )
			self.myMSVCVARS32 = self.myEnv.WhereIs( 'vcvars32.bat' )
			# Assuming that the parent directory of cl.exe is the root directory of MSVC (i.e. C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC)
			self.myMSVC = os.path.dirname( self.myEnv.WhereIs( 'cl.exe' ) )

			if self.myEnv.GetOption('verbosity'):
				print 'Visual C++ version {0} installed.'.format( self.myEnv['MSVS_VERSION'] )
				if self.myMSVSIDE and len(self.myMSVSIDE)>0:
					print ("Found VCExpress.exe in '{0}'.".format(self.myMSVSIDE))
				else:
					print ('VCExpress.exe not found.')

				if self.myMSVCVARS32 and len(self.myMSVCVARS32)>0:
					print ("Found vcvars32.bat in '{0}'.".format(self.myMSVCVARS32))
				else:
					print ('vcvars32.bat not found.')

				if self.myMSVC and len(self.myMSVC)>0:
					print ("Found MSVC in '{0}'.".format(self.myMSVC))
				else:
					print ('MSVC not found.')


		elif self.myEnv['CC'] == 'gcc' :
			# Sets compiler
			self.myCC = 'gcc'
			# Extracts version number
			# Step 1 : Extracts x.y.z
			ccVersion				=	self.myEnv['CCVERSION']
			# Step 2 : Extracts major and minor version
			splittedCCVersion		=	ccVersion.split( '.', 2 )
			if len(splittedCCVersion) !=  3 :
				raise SCons.Errors.UserError( "Unexpected version schema for gcc compiler (expected x.y.z) : %s " % ccVersion )
			# Step 3 : Computes version number
			self.myCCVersionNumber = self.computeVersionNumber( splittedCCVersion[:2] )
			# Constructs myCCVersion ( gccMajor-Minor )
			self.myCCVersion = self.myCC + self.getVersionNumberString2( self.myCCVersionNumber )
		else :
			raise SCons.Errors.UserError( "Unsupported cpp compiler : %s" % self.myEnv['CC'] )

		self.my_Platform_myCCVersion = '_' + self.myPlatform + '_' + self.myCCVersion

		#
		self.initializeGlobalsFromEnv( self.myEnv )

		#
		if initializeOptions:
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

		### configure compiler and linker flags.
		self.configureCxxFlagsAndLinkFlags( self.myEnv )

		# Updates PATH
		toAppend = getPathsForTools()
		#toPrepend = getPathsForSofa(False) + getPathsForRuntime(self)

		print
		appendToPATH( self.myEnv, toAppend, self.myEnv.GetOption('verbosity'))
		#prependToPATH( self.myEnv, toPrepend )
		if self.myEnv.GetOption('verbosity'):
			print

		# Generates help
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

		Help( self.mySBFOptions.GenerateHelpText(self.myEnv) )

		# export SCONS_MSCOMMON_DEBUG=ms.log
		# HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v6.0A\InstallationFolder
		#print self.myEnv.Dump()
		#exit()


	###### Initialize global attributes ######
	def initializeGlobalsFromEnv( self, lenv ) :

		# Updates myNumJobs, myCompanyName, mySvnUrls, mySvnCheckoutExclude and mySvnUpdateExclude
		self.myNumJobs				= lenv['numJobs']

		self.myCompanyName			= lenv['companyName']

		self.mySvnUrls				= lenv['svnUrls']
		self.mySvnCheckoutExclude	= lenv['svnCheckoutExclude']
		self.mySvnUpdateExclude		= lenv['svnUpdateExclude']

		# Updates myInstallPaths, myInstallExtPaths and myInstallDirectory
		self.myInstallPaths = []
		for element in lenv['installPaths'] :
			self.myInstallPaths += [ getNormalizedPathname( element ) ]

		self.myInstallExtPaths = []
		for element in self.myInstallPaths :
			self.myInstallExtPaths	+= [element + 'Ext' + self.my_Platform_myCCVersion]

		if ( len(self.myInstallPaths) >= 1 ):
			self.myInstallDirectory	= self.myInstallPaths[0]
			if not os.path.exists(self.myInstallDirectory):
				print ( 'Creates directory : {0}'.format(self.myInstallDirectory) )
				os.mkdir( self.myInstallDirectory )
		else:
			print 'sbfError: empty installPaths'
			Exit( 1 )

		# Updates myPublishPath
		self.myPublishPath = lenv['publishPath']
		if lenv['publishOn'] and len(self.myPublishPath)==0:
			print ("sbfError: sbf option named 'publishPath' is empty.")
			Exit( 1 )

		# Updates myBuildPath, mySConsignFilePath, myCachePath, myCacheOn, myConfig and myWarningLevel
		self.myBuildPath = getNormalizedPathname( lenv['buildPath'] )

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

		### use myInstallPaths and myInstallExtPaths to update myIncludesInstallPaths, myLibInstallPaths,
		### myIncludesInstallExtPaths, myLibInstallExtPaths, myGlobalCppPath and myGlobalLibPath
		for element in self.myInstallPaths :
			self.myIncludesInstallPaths	+=	[ os.path.join(element, 'include') ]
			self.myLibInstallPaths		+=	[ os.path.join(element, 'bin') ]

		for element in self.myInstallExtPaths :
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


	def initializeProjectFromEnv( self, lenv ):
		"""Initialize project from lenv"""

		self.myVcsUse	= lenv['vcsUse']
		self.myDefines	= lenv['defines']
		self.myType		= lenv['type']
		self.myVersion	= lenv['version']
		self.myPostfix	= lenv['postfix']
		self.myDeps		= lenv['deps']
		self.myUses		= lenv['uses']
		self.myLibs		= lenv['libs']
		self.myStdlibs	= lenv['stdlibs']


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
		lenv.Append( CPPPATH = os.path.join(self.myProjectPathName, 'include') )

		### expands myProjectBuildPathExpanded
		self.myProjectBuildPathExpanded = join( self.myProjectBuildPath, self.myProject, self.myVersion, self.myPlatform, self.myCCVersion, self.myConfig )
		if len(self.myPostfix) > 0:
			self.myProjectBuildPathExpanded += '_' + self.myPostfix


	def configureProject( self, lenv ):

		### configures compiler and linker flags.
		self.configureProjectCxxFlagsAndLinkFlags( lenv )
		### configures CPPDEFINES with myDefines
		lenv.Append( CPPDEFINES = self.myDefines )
		# configures lenv['LIBS'] with lenv['stdlibs']
		lenv.Append( LIBS = lenv['stdlibs'] )
		# configures lenv['LIBS'] with lenv['libs']
		lenv.Append( LIBS = lenv['sbf_libsExpanded'] )
		# Configures lenv[*] with lenv['uses']
		uses( self, lenv, lenv['uses'] )

		# Configures lenv[*] with lenv['test']
		if lenv['test'] != 'none':
			uses( self, lenv, usesConverter(lenv['test']) )



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

			('pakPaths', "Sets the list of paths from which packages can be obtained. No matter what is specified by this options, the first implicit path where packages are searched would be 'installPaths[0]/sbfPak'.", [] ),

			('svnUrls', 'A dictionnary... @todo doc ... The list of subversion repositories used, from first to last, until a successful checkout occurs.', {}),
			('svnDefaultBranch', 'svnMkTag and svnRemoteMkBranch asks user the name of the tag/branch to use. This option sets the default choice suggested to user.', '1.0'),
			('projectExclude', 'The list of projects excludes from any sbf operations. All projects not explicitly excluded will be included. The project from which sbf was initially invoked is never excluded. The unix filename pattern matching is used by the list.', []),
			('weakLocalExtExclude', 'The list of packages (see \'uses\' project option for a complete list of available packages) excludes by the --weak-localext option.'
			' --weak-localext could be used to disables SCons scanners for localExt directories.'
			' All packages not explicitly excluded will be included.', []),
			('svnCheckoutExclude', 'The list of projects excludes from subversion checkout operations. All projects not explicitly excluded will be included. The unix filename pattern matching is used by the list.', []),
			('svnUpdateExclude', 'The list of projects excludes from subversion update operations. All projects not explicitly excluded will be included. The unix filename pattern matching is used by the list.', []),

			EnumVariable(	'clVersion', 'MS Visual C++ compiler (cl.exe) version using the following version schema : x.y or year. Use the special value \'highest\' to select the highest installed version.',
							'highest',
							allowed_values = ( '7.1', '8.0Exp', '8.0', '9.0Exp', '9.0', '10.0Exp', '10.0', 'highest' ),
							map={
									'2003'		: '7.1',
									'2005Exp'	: '8.0Exp',
									'2005'		: '8.0',
									'2008Exp'	: '9.0Exp',
									'2008'		: '9.0',
									'2010Exp'	: '10.0Exp',
									'2010'		: '10.0'
									} ),

			('installPaths', 'The list of search paths to \'/usr/local\' like directories. The first one would be used as a destination path for target named install.', []),

			('postfixTimeFormat', "A string controlling the format of the date/time postfix (used by 'nsis' and 'zip' targets). Default time format is '%Y-%m-%d' producing for example the date 2012-04-12. Adds '%Hh%Mm%Ss' to append for example 10h40m21s. See python documentation on time.strftime() for additionnal informations.", '%Y-%m-%d' ),

			('publishPath', 'The result of a target, typically copied in installPaths[0], could be transfered to another host over a remote shell using rsync. This option sets the destination of publishing (see rsync for destination syntax).', ''),
			BoolVariable('publishOn', 'Sets to True to enabled the publishing. See \'publishPath\' option for additional informations.', False),

			PathVariable(	'buildPath',
							'The build directory in which to build all derived files. It could be an absolute path, or a relative path to the project being build)',
							'build',
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
			BoolVariable(	'generateDebugInfoInRelease', 'The purpose of this option is to be able to fix bug(s) occurring only in release build and/or when no debugger is attached. '
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
	# @todo
	def readProjectOptions( self, file ) :

		myOptions = Variables( file )
		myOptions.AddVariables(
			('description', "Description of the project to be presented to users. This is used on win32 platform to embedded in exe, dll or lib files additional informations.", '' ),
			('productName', 'Name of the product to be presented to users. This information is used by nsis installation program. Default value (i.e. empty string) means that project name is used instead.', ''),

			EnumVariable(	'vcsUse', "'yes' if the project use a versioning control system, 'no' otherwise.", 'yes',
							allowed_values=('yes', 'no'),
							map={}, ignorecase=1 ),

			('defines', 'The list of preprocessor definitions given to the compiler at each invocation (same effect as #define xxx).', ''),
			EnumVariable(	'type', "Specifies the project/target type. 'exec' for executable projects, 'static' for static library projects, 'shared' for dynamic library projects, 'none' for meta or headers only projects.",
							'none',
							allowed_values=('exec', 'static','shared','none'),
							map={}, ignorecase=1 ),

			('version', "Sets the project version. The following version schemas must be used : major-minor-[postfix] or major-minor-maintenance[-postfix]. For example '1-0', '1-0-RC1', '1-0-1' or '0-99-technoPreview'", '0-0'),
			('postfix', 'Adds a postfix to the target name.', ''),
			BoolVariable('generateInfoFile', 'Sets to true enabled the generation of info.sbf file, false to disable it.', False ),

			('deps', 'Specifies list of dependencies to others projects. Absolute path is forbidden.', []),

			(	'uses',
				'Specifies a list of packages to configure for compilation and link stages.\nAvailable packages:%s\nAlias: %s' %
				(convertToString(UseRepository.getAllowedValues()), convertDictToString(UseRepository.getAlias())),
				[],
				usesValidator,
				usesConverter ),

			('libs', 'The list of libraries used during the link stage that have been compiled with SConsBuildFramework (this SCons system).', []),
			('stdlibs', 'The list of standard libraries used during the link stage.', []),
			EnumVariable(	'test', 'Specifies the test framework to configure for compilation and link stages.', 'none',
							allowed_values=('none', 'gtest'), ignorecase=1 ),

			('shareExclude', "The list of Unix shell-style wildcards to exclude files from 'share' directory", []),
			('shareBuild', "Defines the build stage for files from 'share' directory. The following schemas must be used for this option : ( [filters], command ).\n@todo Explains filters and command.", ([],('','',''))),

			('customBuild',	"A dictionnary containing { target : pyScript, ... } to specify a python script for a target. Python script is executed during 'thinking stage' of SConsBuildFramework if its associated target have to be built. Script has access to SCONS_BUILD_FRAMEWORK environment variable and lenv, the SCons environment for the project. Python 'sys.path' is adjusted to allow direct 'import' of python script from the root directory of the project.",
							{}),

			BoolVariable(	'console',
							'True to enable Windows character-mode application and to allow the operating system to provide a console. False to disable the console. This option is specific to MS/Windows executable.',
							True ),

			(	'runParams',
				"The list of parameters given to executable by targets 'run' and 'onlyRun'. To specify multiple parameters at command-line uses a comma-separated list of parameters, which will get translated into a space-separated list for passing to the launching command.",
				[],
				passthruValidator, passthruConverter ),

			EnumVariable(	'deploymentType', "Specifies where the project and its dependencies have to be installed in root of the installation directory and/or in sub-directory 'packages' of the installation directory.",
							'none', allowed_values=('none', 'standalone', 'embedded'), ignorecase=1 ),

			(	'deploymentPrecond', '', ''	),

			(	'nsis', "A dictionnary to customize generated nsis installation program. Key 'autoUninstall' to uninstall automatically previous version (only if needed). Key 'installDirFromRegKey' set to true to tell the installer to check a string in the registry and use it for the install dir if that string is valid, false to do nothing (only for standalone). Key 'ensureNewInstallDir' to ensure that the installation directory is always a newly created directory (by appending a number if needed to the chosen directory name). Key 'uninstallVarDirectory' to allow removing 'var' directory during uninstall stage. Key 'moveLogFileIntoVarDirectory' to move log file into 'var' directory. Key 'copySetupFileIntoVarDirectory' to copy installation program file into 'var' directory. Key 'customPointInstallationValidation' to add nsis code after the copying of all files during installation and before migration of var/packages directories, autoUninstall and registry updating. The variable $installationValidation have to be used to validate (==0) to invalidate (!=0) the installation. Invalidate an installation to abort the installation, nevertheless uninstall.exe is created to be able to clean installed files.",
				{	'autoUninstall'						: True,
					'installDirFromRegKey'				: True,
					'ensureNewInstallDir'				: False,
 					'uninstallVarDirectory'				: False,
					'moveLogFileIntoVarDirectory'		: False,
					'copySetupFileIntoVarDirectory'		: False,
					'customPointInstallationValidation'	: ''
				} )
		)

		return myOptions


	###### Reads a configuration file for a project ######
	###### Updates environment (self.myProjectOptions and lenv are modified).
	# Returns true if config file exists, false otherwise.
	def readProjectOptionsAndUpdateEnv( self, lenv, configDotOptionsFile = 'default.options' ) :
		configDotOptionsPathFile = self.myProjectPathName + os.sep + configDotOptionsFile
		retVal = os.path.isfile(configDotOptionsPathFile)
		if retVal :
			# update lenv with config.options
			self.myProjectOptions = self.readProjectOptions( configDotOptionsPathFile )
			self.myProjectOptions.Update( lenv )
		return retVal



	###### Configures CxxFlags & LinkFlags ######
	def configureCxxFlagsAndLinkFlagsOnWin32( self, lenv ):
		# Assumes cl compiler has been selected
		if self.myCC != 'cl':
			raise SCons.Errors.UserError( "Unexpected compiler %s on Windows platform." % self.myCC )

		# Useful for cygwin 1.7
		# The Microsoft linker requires that the environment variable TMP is set.
		if not os.getenv('TMP'):
			lenv['ENV']['TMP'] = self.myBuildPath
			if self.myEnv.GetOption('verbosity') : print ('TMP sets to {0}'.format(self.myBuildPath))

		# Adds support of Microsoft Manifest Tool for Visual Studio 2005 (cl8) and up
		if self.myCCVersionNumber >= 8.000000 :
			self.myEnv['WINDOWS_INSERT_MANIFEST'] = True

		# @todo CL10, CL9, CL8 classes to configure env and/or retrieves the whole configuration. Idem for gcc...
		if self.myCCVersionNumber >= 10.000000:
			# Configures Microsoft Visual C++ 2010
			# @todo FIXME should be done by SCons...
			visualInclude	= 'C:\\Program Files\\Microsoft Visual Studio 10.0\\VC\\include'
			visualLib		= 'C:\\Program Files\\Microsoft Visual Studio 10.0\\VC\\lib'
			msSDKInclude	= 'C:\\Program Files\\Microsoft SDKs\\Windows\\v7.0A\\Include'
			msSDKLib		= 'C:\\Program Files\\Microsoft SDKs\\Windows\\v7.0A\\Lib'

			#visualInclude	= 'C:\\Program Files (x86)\\Microsoft Visual Studio 10.0\\VC\\include'
			#visualLib		= 'C:\\Program Files (x86)\\Microsoft Visual Studio 10.0\\VC\\lib'
			#msSDKInclude	= 'C:\\Program Files (x86)\\Microsoft SDKs\\Windows\\v7.0A\\Include'
			#msSDKLib		= 'C:\\Program Files (x86)\\Microsoft SDKs\\Windows\\v7.0A\\Lib'

			if self.myIsExpressEdition:
				# at least for rc.exe
				#lenv.AppendENVPath( 'PATH', 'C:\\Program Files\\Microsoft SDKs\\Windows\\v7.0A\\bin' )
				#lenv.AppendENVPath( 'PATH', 'C:\\Program Files (x86)\\Microsoft SDKs\\Windows\\v7.0A\\bin' )

				if lenv.GetOption('weak_localext'):
					lenv.Append( CCFLAGS = ['${INCPREFIX}%s' % visualInclude, '${INCPREFIX}%s' % msSDKInclude] )
				else:
					lenv.Append( CPPPATH = [visualInclude, msSDKInclude] )

				lenv.Append( RCFLAGS = '"${INCPREFIX}%s"' % msSDKInclude )

				lenv.Append( LIBPATH = [visualLib, msSDKLib] )


		elif self.myCCVersionNumber >= 9.000000:
			pass
			# Configures Microsoft Visual C++ 2008
			# @todo FIXME should be done by SCons...
			#visualInclude	= 'C:\\Program Files\\Microsoft Visual Studio 9.0\\VC\\INCLUDE'
			#visualLib		= 'C:\\Program Files\\Microsoft Visual Studio 9.0\\VC\\LIB'
			#msSDKInclude	= 'C:\\Program Files\\Microsoft SDKs\\Windows\\v6.0A\\include'
			#msSDKLib		= 'C:\\Program Files\\Microsoft SDKs\\Windows\\v6.0A\\lib'

			visualInclude	= 'D:\\Program Files (x86)\\Microsoft Visual Studio 9.0\\VC\\include'
			visualLib		= 'D:\\Program Files (x86)\\Microsoft Visual Studio 9.0\\VC\\lib'
			msSDKInclude	= 'D:\\Program Files\\Microsoft SDKs\\Windows\\v6.0A\\Include'
			msSDKLib		= 'D:\\Program Files\\Microsoft SDKs\\Windows\\v6.0A\\Lib'

			if self.myIsExpressEdition:
				# at least for rc.exe
				#lenv.AppendENVPath( 'PATH', 'C:\\Program Files\\Microsoft SDKs\\Windows\\v6.0A\\bin' )
				#lenv.AppendENVPath( 'PATH', 'C:\\Program Files (x86)\\Microsoft SDKs\\Windows\\v6.0A\\bin' )

				if lenv.GetOption('weak_localext'):
					lenv.Append( CCFLAGS = ['${INCPREFIX}%s' % visualInclude, '${INCPREFIX}%s' % msSDKInclude] )
				else:
					lenv.Append( CPPPATH = [visualInclude, msSDKInclude] )

				lenv.Append( RCFLAGS = '"${INCPREFIX}%s"' % msSDKInclude )

				lenv.Append( LIBPATH = [visualLib, msSDKLib] )


		elif self.myCCVersionNumber >= 8.000000:
			pass
			# Configures Microsoft Platform SDK for Windows Server 2003 R2
			# @todo FIXME should be done by SCons...
			#psdkInclude	= 'C:\\Program Files\\Microsoft Platform SDK for Windows Server 2003 R2\\Include'
			#psdkLib		= 'C:\\Program Files\\Microsoft Platform SDK for Windows Server 2003 R2\\Lib'

			#if self.myIsExpressEdition:
			#	if lenv.GetOption('weak_localext'):
			#		lenv.Append( CCFLAGS = '"${INCPREFIX}%s"' % psdkInclude )
			#	else:
			#		lenv.Append( CPPPATH = psdkInclude )

			#	lenv.Append( RCFLAGS = '"${INCPREFIX}%s"' % psdkInclude )

			#	lenv.Append( LIBPATH = psdkLib )


		#
		if self.myCCVersionNumber >= 10.000000 :
			lenv.Append( LINKFLAGS = '/MANIFEST' )
			lenv.Append( CXXFLAGS = ['/GS-', '/EHsc'] )
		elif self.myCCVersionNumber >= 9.000000 :
			lenv.Append( LINKFLAGS = '/MANIFEST' )
			lenv.Append( CXXFLAGS = ['/GS-', '/EHsc'] )
			#lenv.Append( CXXFLAGS = ['/MP'] )
		elif self.myCCVersionNumber >= 8.000000 :
			# /GX is deprecated in Visual C++ 2005
			lenv.Append( CXXFLAGS = ['/GS-', '/EHsc'] ) # @todo FIXME : '/GS-' for SOFA !!!
		elif self.myCCVersionNumber >= 7.000000 :
			lenv.Append( CXXFLAGS = '/GX' )
			if self.myConfig == 'release' :
				lenv.Append( CXXFLAGS = '/Zm600' )

		# /TP : Specify Source File Type (C++) => adds by SCons
		# /GR : Enable Run-Time Type Information
		lenv.AppendUnique( CXXFLAGS = '/GR' )

		# Defines
		lenv.Append( CXXFLAGS = ['/DWIN32', '/D_WINDOWS', '/DNOMINMAX'] )
		# bullet uses _CRT_SECURE_NO_WARNINGS,_CRT_SECURE_NO_DEPRECATE,_SCL_SECURE_NO_WARNINGS
		#lenv.Append( CXXFLAGS = ['/D_CRT_SECURE_NO_WARNINGS', '/D_CRT_SECURE_NO_DEPRECATE', '/D_SCL_SECURE_NO_WARNINGS'] )

		#lenv.Append( CXXFLAGS = ['/D_BIND_TO_CURRENT_VCLIBS_VERSION=1'] )
		#lenv.Append( CXXFLAGS = ['/MP{0}'.format(self.myNumJobs)] )

		if self.myConfig == 'release' :							### @todo use /Zd in release mode to be able to debug a little.
			lenv.Append( CXXFLAGS = ['/DNDEBUG'] )
			lenv.Append( CXXFLAGS = ['/MD', '/O2'] )			# /O2 <=> /Og /Oi /Ot /Oy /Ob2 /Gs /GF /Gy
			#lenv.Append( CXXFLAGS = ['/GL'] )
			if lenv['generateDebugInfoInRelease']:
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
		if self.myWarningLevel == 'normal' :		### @todo it is dependent of the myConfig. Must be changed ? yes, do it...
			lenv.Append( CXXFLAGS = '/W3' )
		else:
			# /Wall : Enables all warnings
			lenv.Append( CXXFLAGS = ['/W4', '/Wall'] )


	# @todo incremental in release, but not for portable app and nsis
	def configureProjectCxxFlagsAndLinkFlagsOnWin32( self, lenv ):
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
		if self.myType == 'exec':
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

		elif self.myType == 'shared':
			lenv.Append( CXXFLAGS = '/D_USRDLL' )



	def configureCxxFlagsAndLinkFlagsOnPosix( self, lenv ):

		lenv['CXX'] = lenv.WhereIs('g++')											### FIXME: remove me
																					### myCxxFlags += ' -pedantic'
		if ( self.myConfig == 'release' ) :
			lenv.Append( CXXFLAGS = ['-DNDEBUG', '-O3'] )
#			self.myCxxFlags	+= ' -DNDEBUG -O3 '										### TODO: more compiler and cpu optimizations
		else:
			lenv.Append( CXXFLAGS = ['-D_DEBUG', '-DDEBUG', '-g', '-O0'] )
#			self.myCxxFlags	+= ' -D_DEBUG -DDEBUG -g -O0 '							### profiling myCxxFlags += ' -pg', mpatrol, leaktracer

		# process myWarningLevel, adds always -Wall option.							TODO: adds more warnings with myWarningLevel = 'high' ?
		lenv.Append( CXXFLAGS = '-Wall' )
		lenv.Append( CXXFLAGS = '-Wno-deprecated' )
		# @todo remove me
		lenv.Append( CXXFLAGS = '-fpermissive' )
#		lenv.Append( CXXFLAGS = '-fvisibility=hidden' )
		lenv.Append( CXXFLAGS = '-fvisibility-inlines-hidden' )
#		lenv.Append( CXXFLAGS = '-fvisibility-ms-compat' )
		lenv.Append( LINKFLAGS = '-Wl,-rpath=%s' % os.path.join( self.myInstallDirectory, 'lib' ) )

#		self.myCxxFlags	+= ' -Wall '


	def configureProjectCxxFlagsAndLinkFlagsOnPosix( self, lenv ):
		pass


	def configureCxxFlagsAndLinkFlags( self, lenv ):
		### TODO: moves defines(-Dxxxx) from platform specific methods into this one.
		### Completes myCxxFlags and myLinkFlags ###
		if self.myPlatform == 'win32':
			self.configureCxxFlagsAndLinkFlagsOnWin32( lenv )
		elif self.myPlatform == 'cygwin' or self.myPlatform == 'posix':
			self.configureCxxFlagsAndLinkFlagsOnPosix( lenv )
		else:
			raise SCons.Errors.UserError("Unknown platform %s." % self.myPlatform)

		if sys.platform == 'darwin':
			lenv.Append( CXXFLAGS = '-D__MACOSX__' )
			#self.myCxxFlags += ' -D__MACOSX__'
		elif ( sys.platform.find( 'linux' ) != -1 ):
			lenv.Append( CXXFLAGS = '-D__linux' )
			#self.myCxxFlags += ' -D__linux'

		lenv.Append( CPPPATH = self.myGlobalCppPath )
		lenv.Append( LIBPATH = self.myGlobalLibPath )


	def configureProjectCxxFlagsAndLinkFlags( self, lenv ):
		if self.myPlatform == 'win32':
			self.configureProjectCxxFlagsAndLinkFlagsOnWin32( lenv )
		elif self.myPlatform in ['cygwin', 'posix']:
			self.configureProjectCxxFlagsAndLinkFlagsOnPosix( lenv )
		else:
			raise SCons.Errors.UserError("Unknown platform %s." % self.myPlatform)

		# Adds to command-line several defines with version number informations.
		lenv.Append( CPPDEFINES = [
						("COMPANY_NAME",	"\\\"%s\\\"" % self.myCompanyName ),
						("MODULE_NAME",		"\\\"%s\\\"" % self.myProject ),
						("MODULE_VERSION",	"\\\"%s\\\"" % self.myVersion ),
						("MODULE_MAJOR_VER",	"%s" % self.myVersionMajor ),
						("MODULE_MINOR_VER",	"%s" % self.myVersionMinor ),
						("MODULE_MAINT_VER",	"%s" % self.myVersionMaintenance ),
						("MODULE_POSTFIX_VER",	"%s" % self.myVersionPostfix ),
						 ] )

		# Completes myCxxFlags with some defines
		if self.myType == 'static':
			lenv.Append( CXXFLAGS = ' -D' + self.myProject.upper() + '_STATIC ' )
		elif self.myType == 'shared':
			lenv.Append( CXXFLAGS = ' -D' + self.myProject.upper() + '_SHARED ' )
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
					if len(projectURL) > 0 :
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
			if lenv['vcsUse'] == 'yes':
				self.vcsUpdate( lenv )
				self.readProjectOptionsAndUpdateEnv( lenv )
			else:
				if lenv.GetOption('verbosity'):
					print ("Skip project {0} in {1}, because 'vcsUse' option sets to no.".format(self.myProject, self.myProjectPath))
		# else nothing to do.


	def doVcsCleanOrAdd( self, lenv ):
		# a vcs cleanup ?
		if self.tryVcsClean:
			if lenv['vcsUse'] == 'yes':
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
				print ( "Ignore project {0} in {1}".format(self.myProject, self.myProjectPath) )
			return


		# Configures a new environment
		self.myCurrentLocalEnv = self.myEnv.Clone()
		lenv = self.myCurrentLocalEnv

		# used by code printing messages during the different build stage.
		lenv['sbf_projectPathName'	] = self.myProjectPathName
		lenv['sbf_projectPath'		] = self.myProjectPath
		lenv['sbf_project'			] = self.myProject


		# VCS checkout or status or relocate or mkTag/Branch or rmTag/Branch
		self.doVcsCheckoutOrOther( lenv )

		# Tests existance of project path name and updates lenv with 'default.options' configuration file
		if os.path.isdir(self.myProjectPathName):
			successful = self.readProjectOptionsAndUpdateEnv( lenv )
			if successful:
				# Adds the new environment
				self.myParsedProjects[self.myProject] = lenv
				self.myParsedProjectsSet.add( self.myProject.lower() )
			else:
				raise SCons.Errors.UserError("Unable to find 'default.options' file for project %s in directory %s." % (self.myProject, self.myProjectPath) )
		else:
			print "sbfWarning: Unable to find project", self.myProject, "in directory", self.myProjectPath
			print "sbfInfo: Skip to the next project..."
			self.myFailedVcsProjects.add( self.myProject )
			return


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
		buildSbfLibrary = False
		libsExpanded = []
		for lib in lenv['libs']:
			libSplitted = splitLibsName( lib )

			buildSbfLibrary = buildSbfLibrary or (libSplitted[0] == 'sbf')

			if len(libSplitted[1])==0:
				# no version information supplied
				libsExpanded.append( libSplitted[0] + self.my_Platform_myCCVersion + self.my_PostfixLinkedToMyConfig )
			else:
				# version information supplied
				libsExpanded.append( libSplitted[0] + '_' + libSplitted[1] + self.my_Platform_myCCVersion + self.my_PostfixLinkedToMyConfig )
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
			if os.path.isabs( dependency ): raise SCons.Errors.UserError("Absolute path is forbidden in 'deps' project option.")

			# dependency is a path relative to the directory containing default.options
			normalizedDependency			= getNormalizedPathname( projectPathName + os.sep + dependency )
			incomingProjectName				= os.path.basename(normalizedDependency)
			lowerCaseIncomingProjectName	= incomingProjectName.lower()
			if lowerCaseIncomingProjectName not in self.myParsedProjectsSet:
				# dependency not already encountered
				#print ('buildProject %s' % normalizedDependency)
				if incomingProjectName not in self.myFailedVcsProjects:
					# Built the dependency and takes care of 'nodeps'.
					if lenv['nodeps'] == False:
						self.buildProject( normalizedDependency, lenv['sbf_parentProjects'], lenv['nodeps'] )
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

		#
		if self.tryVcsOperation or configureOnly:
			if lenv.GetOption('verbosity'): print ( "Parsing project {0}...".format(lenv['sbf_project']) )
			return
		else:
			# Adds the new environment
			self.myBuiltProjects[ lenv['sbf_project'] ] = lenv
			if lenv.GetOption('verbosity'): print ( "Studying project {0}...".format(lenv['sbf_project']) )

		# Dumping construction environment (for debugging) : print lenv.Dump() Exit()

		### Starts building stage
		self.initializeProject( lenv )
		self.configureProject( lenv )



		### BIN BUILD ###

		# lenv modified: CPPPATH, PDB, Precious(), SideEffect(), Alias(), Clean()
		#
		# installInBinTarget
		# lenv['sbf_rc'] =[resource.rc, resource_sbf.rc, project.ico]
		# lenv['sbf_bin_debuginfo']
		# 'myProject_resource_generation' and 'myProject_build' (aliasProjectBuild) targets

		## Processes win32 resource files (resource.rc and resource_sbf.rc)
		objFiles = []
		installInBinTarget = []

		# @todo generalizes a rc system
		Alias( self.myProject + '_resource.rc_generation' )

		rcPath = join(self.myProjectPathName, 'rc')
		if self.myPlatform == 'win32':
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

		# Qt: rcc on rc/resources.qrc
		rcFile = join(rcPath, 'resources.qrc')
		if os.path.isfile( rcFile ):
			# Compiles the resource file
			inputFile = rcFile
			outputFile = join(self.myProjectBuildPathExpanded, 'qrc_resources.cpp')
			objFiles += lenv.Command( outputFile, inputFile,
					Action( [['rcc', '$SOURCE', '-o', '${TARGETS[0]}']] ) )
			lenv['sbf_rc'].append( rcFile )
		#else nothing todo

		## Build source files
		# setup 'pseudo BuildDir' (with OBJPREFIX)
		# @todo use VariantDir()
		filesFromInclude = self.getFiles( 'include', lenv )
		filesFromSrc = self.getFiles( 'src', lenv )

		objProject = join( self.myProjectBuildPathExpanded, self.myProject ) + '_' + self.myVersion + self.my_Platform_myCCVersion + self.my_FullPostfix

		# Qt
		qtUse = UseRepository.getUse( 'qt' )
		if qtUse:
			if qtUse.getName() + qtUse.getVersions()[0] in lenv['uses']: # @todo note very generic 'qt4-8-0' !!!
				# MOC
				moc(lenv, getFilesForMoc(filesFromInclude), objFiles)
			# else nothing to do
		# else nothing to do

		if self.myType in ['exec', 'static']:
			# Compiles source files
			for srcFile in filesFromSrc:
				objFile			=	(os.path.splitext(srcFile)[0]).replace('src', self.myProjectBuildPathExpanded, 1 )
				# Object is a synonym for the StaticObject builder method.
				objFiles		+=	lenv.Object( objFile, join(self.myProjectPathName, srcFile) )
			# Creates executable or static library
			if self.myType == 'exec':
				# executable
				projectTarget = lenv.Program( objProject, objFiles )
			else:
				# static library
				projectTarget = lenv.StaticLibrary( objProject, objFiles )
		elif self.myType == 'shared':
			# Compiles source files
			for srcFile in filesFromSrc:
				objFile			=	(os.path.splitext(srcFile)[0]).replace('src', self.myProjectBuildPathExpanded, 1 )
				objFiles		+=	lenv.SharedObject( objFile, join(self.myProjectPathName, srcFile) )
			# Creates shared library
			projectTarget = lenv.SharedLibrary( objProject, objFiles )

			if self.myPlatform == 'win32':
				# filter *.exp file
				filteredProjectTarget = []				# @todo uses conprehension list
				for elt in projectTarget:
					if os.path.splitext(elt.name)[1] != '.exp':
						filteredProjectTarget.append(elt)
				projectTarget = filteredProjectTarget
			# else no filtering
		else:
			assert( self.myType == 'none' )
			projectTarget = None

		if projectTarget:
			# Installation part
			installInBinTarget += projectTarget

			# projectTarget is not deleted before it is rebuilt.
			lenv.Precious( projectTarget )

# @todo /PDBSTRIPPED:pdb_file_name
			# Generating debug informations
			if self.myPlatform == 'win32':
				if lenv['generateDebugInfoInRelease'] or self.myConfig == 'debug':
					# PDB Generation. Static library don't generate pdb.
					if self.myType in ['exec', 'shared']:
						lenv['PDB'] = objProject + '.pdb'
						lenv.SideEffect( lenv['PDB'], projectTarget )
						# it is not deleted before it is rebuilt.
						lenv.Precious( lenv['PDB'] )
						lenv['sbf_bin_debuginfo'] = lenv['PDB']
					# else nothing to do
				# else nothing to do
			# else nothing to do

		### target 'myProject_build'
		aliasProjectBuild = Alias( self.myProject + '_build', lenv.Command('dummy_build_print_' + self.myProject, 'dummy.in', Action(nopAction, printBuild)) )
		Alias( self.myProject + '_build', self.myProject + '_resource.rc_generation' )
		Alias( self.myProject + '_build', projectTarget )
		Clean( self.myProject + '_build', self.myProjectBuildPathExpanded )



		### SHARE BUILD ###
		# filters, command
		# filesFromShare, filesFromShareToBuild
		# filesFromShareBuilt

		(filters, command) = computeFiltersAndCommand( lenv )
		(filesFromShareToBuild, filesFromShare) = applyFilters( self.getFiles('share', lenv), filters )
		filesFromShareBuilt = buildFilesFromShare( filesFromShareToBuild, lenv, command )



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
		# installTarget

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


		# install libraries and binaries in 'bin' (from installInBinTarget)
		if len(installInBinTarget) > 0:
			for installDir in self.myInstallDirectories:
				installTarget += lenv.Install( join(installDir, 'bin'), installInBinTarget )

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


		# install in 'include'
		# installInIncludeTarget
		installInIncludeTarget = filesFromInclude

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

		lenv['sbf_src']							= filesFromSrc
#		lenv['sbf_lib_object']					= []
#		lenv['sbf_lib_object_for_developer']	= []

		#lenv['sbf_bin_debuginfo'] = lenv['PDB']
		#lenv['sbf_lib_debuginfo'] = lenv['PDB']

		lenv['sbf_files']						= glob.glob( join(self.myProjectPathName, '*.options') )
		lenv['sbf_files'].append( join(self.myProjectPathName, 'sconstruct') )
		#lenv['sbf_info']
		#lenv['sbf_rc']
		# @todo configures sbf_... for msvc/eclipse ?

		for elt in installInBinTarget:
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
		Alias( 'build',		aliasProjectBuild		)
		Alias( 'install',	aliasProjectInstall		)
		Alias( 'deps',		aliasProjectDeps		)
		Alias( 'all',		aliasProject			)
		Alias( 'clean',		aliasProjectClean		)
		Alias( 'mrproper',	[aliasProjectClean, aliasProjectMrproper] )

		# VCS clean and add
		self.doVcsCleanOrAdd( lenv )

		# Targets: onlyRun and run
		executableNode = searchExecutable( lenv, installInBinTarget )
		if executableNode:
			executableFilename	= basename(executableNode.abspath)
			pathForExecutable	= join(self.myInstallDirectory, 'bin')

			cmdParameters = ''
			for param in lenv['runParams']:
				cmdParameters += ' ' + param

			printMsg = '\n' + stringFormatter(lenv, 'Launching {0}'.format(executableFilename))
			if len(cmdParameters) > 0:
				printMsg += stringFormatter(lenv, 'with parameters:{0}'.format(cmdParameters))

			Alias( 'onlyrun', lenv.Command(self.myProject + '_onlyRun.out', 'dummy.in',
								Action(	'cd %s && %s %s' % (pathForExecutable, executableFilename, cmdParameters),
										printMsg ) ) )

			Alias( 'run', lenv.Command(self.myProject + '_run.out', 'install',
								Action(	'cd %s && %s %s' % (pathForExecutable, executableFilename, cmdParameters),
										printMsg ) ) )



	###### Helpers ######

	def getFiles( self, what, lenv ):
		"""what		select what to collect. It could be 'src', 'include', 'share' and 'license'
		"""

		basenameWithDotRe = r"^[a-zA-Z][a-zA-Z0-9_\-]*\."

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
		else:
			raise SCons.Errors.UserError("Internal sbf error in getFiles().")

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

	### Management of version number
	# @todo moves to sbfVersion.py
	def computeVersionNumber( self, versionNumberList ):
		versionNumber	= 0
		coef			= 1.0
		for version in versionNumberList :
			versionNumber += float(version) / coef
			coef = coef * 1000.0
		return versionNumber

	def getVersionNumberTuple( self, versionNumber ) :
		major				= int(versionNumber)
		minorDotMaintenance	= (versionNumber-major)*1000
		minor				= int( round(minorDotMaintenance) )
		maintenance			= int( round((minorDotMaintenance-minor)*1000) )
		return ( major, minor, maintenance )

	def getVersionNumberString1( self, versionNumber ) :
		return str( int(versionNumber) )

	def getVersionNumberString2( self, versionNumber ) :
		tuple = self.getVersionNumberTuple( versionNumber )
		return "%u-%u" % ( tuple[0], tuple[1] )

	def getVersionNumberString3( self, versionNumber ) :
		tuple = self.getVersionNumberTuple( versionNumber )
		return "%u-%u-%u" % ( tuple[0], tuple[1], tuple[2] )



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
		retValUses = set( set(lenv['uses']) )

		# Retrieves all dependencies
		dependencies = self.getAllDependencies(lenv)

		# Adds 'uses' to return value, for each dependency
		for dependency in dependencies:
			dependencyEnv = self.myParsedProjects[ dependency ]
			retValUses = retValUses.union( set(dependencyEnv['uses']) )

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
