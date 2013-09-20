# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, 2010, 2011, 2012, 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
#
# Installation
# -------------
#
# o	Python 2.5 and up ( should work with 2.4.x)
# o	SCons 0.96.95 and up
# o	On MS-Windows platform :	PySVN 1.5.1 for python 2.5 and svn 1.4.3 installation kit (py25-pysvn-svn143-1.5.1-813.exe) or
#								PySVN 1.5.2 for python 2.5 and svn 1.4.5 installation kit (py25-pysvn-svn145-1.5.2-872.exe)
#						PySVN 1.4.2 for python 2.4 and svn 1.3.1 installation kit (py24-pysvn-svn131-1.4.2-640.exe)
#	On Debian\testing: Package python2.4-svn (old one was 1.1.2-3, current one is 1.3.1-1+b1)														??? update and test on linux, MacOSX an unix/posix ???
# o	cygwin on windows platform ?
#
#
#
#
# @todo explains all options
#
# 2. Configuration of a project (default.options file)
#
# - type =	exec to generate an executable (.exe on Windows, nothing on POSIX system),
#		or static to generate a static library (.lib on Windows, .a on POSIX system),
#		or shared to generate a shared library (.so on a POSIX system, .dll on Windows),
#		or none to generate nothing (useful for project containing only include files, or meta-project containing only build dependencies).
#
# @todo explains all options
#
# 3. Remarks
#
# - Executes 'scons -H' to print scons help message about command-line options.
# - Executes 'scons -h' to print sbf help message and sbf configuration values.
#
# - installPaths, config and warningLevel are not used in default.options (only in SConsBuildFramework.options)
# - Spaces are not allowed in a project name.
#
#
#
# SCons targets description
# -----------------------------
#
# list of targets:
#	- specific sbf target :
#		sbfCheck	:	to check sbf and related tools installation.
#					print python version, python version used by scons, scons, CC and sbf version numbers, SCONS_BUILD_FRAMEWORK environment variable, and checks if SCONS_BUILD_FRAMEWORK is well formed.
#					If SCONS_BUILD_FRAMEWORK is not defined, a message to explain how to define it is printed.
#					If SCONS_BUILD_FRAMEWORK is defined, sbf checks if SCONS_BUILD_FRAMEWORK is perfectly defined (i.e. path exists, well written and is the main directory of SConsBuildFramework)
#
#	- svn (subversion) targets :
#		svnCheckout or myProject_svnCheckout :
#				checkout missing project(s) from multiple svn repositories (i.e. when a project specified in dependencies does not exist
#				on the filesystem, sbf try to checkout it from the first repository specified by svnUrls. If checkout fails, the next
#				repository is used. And so on). myProject_svnCheckout target is used to checkout myProject. svnCheckout is used to checkout all projects.
#		svnUpdate or myProject_svnUpdate :
#				update project(s) from multiple svn repositories (sbf try to checkout it from the first repository specified by svnUrls. If checkout fails, the next
#				repository is used. And so on).
#	- doxygen targets :
#		dox_build, dox_install, dox, dox_clean and dox_mrproper.
#		By default, an automatically generated doxygen configuration file is used by these targets (see the file doxyfile in directory SCONS_BUILD_FRAMEWORK)
#		PROJECT_NAME, PROJECT_NUMBER, OUTPUT_DIRECTORY, INPUT, EXAMPLE_PATH and IMAGE_PATH are automatically configured by sbf.
#		sbf sets :
#			- PROJECT_NAME to 'root project name' at 'build date'.
#			- PROJECT_NUMBER to 'version'
#			- OUTPUT_DIRECTORY to 'installPaths[0]/project name/doxygen/doxygen.sbf_build'
#			- INPUT to 'project/include' and 'project/src' and the same recursively for all dependencies.
#			- EXAMPLE_PATH to 'project/doc/example' and the same recursively for all dependencies.
#			- IMAGE_PATH to 'project/doc/image' and the same recursively for all dependencies.
#	- zip related targets :
#		zip				: a shortcut to 'zipRuntime zipDev zipSrc' targets detailed below.
#		zipRuntime		: create a package with binaries, libraries and resource files (the directory 'share').
#		zipDev			: create a package with binaries, libraries and includes files.
#		zipSrc			: create a package with source files, i.e. all files under vcs are considered as source
#	- myproject_build, myproject_install, myproject(idem myproject_install), myproject_clean, myproject_mrproper
#	- and special targets :
#		- build (for all myproject_build)
#		- install (for all myproject_install)
#		- all (for all myproject)
#		- debug (like target all, but config option is forced to debug)
#		- release (like target all but config option is forced to release)
#		- clean (for all myproject_clean)
#		- mrproper (for all myproject_mrproper)
#   - Visual Studio targets :
#       - myproject_vcproj to build a Microsoft Visual Studio project file
#       - vcproj for all myproject_vcproj
#	- default target = all
#
#
#
# Features
# ----------
#
# - project dependencies. 'deps' can be specified with relative or absolute paths. All relative paths are specified from the location of the configuration file 'default.options'.
# - skip any missing projects (i.e. skip a project specified in dependencies but that don't exist on the filesystem).
#
# - build objects outside sources directories.
# - builded files could be shared among all the builds usings the same cache (see cachePath).
#
# - prints sbf version, date and time and at sbf startup.
#
# @todo Completes this list
# examples: scons config=release or scons config=debug to override default values from configuration files



###### imports ######

#import datetime
#sbfMainBeginTime = datetime.datetime.now()

import __builtin__
import collections, os, string, sys

# To be able to catch wrong SCons version or missing SCons
try:
	from SCons.Tool.MSCommon.vc import cached_get_installed_vcs
except ImportError as e:
	print ('sbfError: SCons not installed or wrong version.')
	Exit(1)

from SCons.Script.SConscript import SConsEnvironment
from SCons import SCons # for SCons.__version__

from src.sbfConfiguration import sbfConfigure, sbfUnconfigure, sbfConfigureTools, sbfUnconfigureTools
from src.sbfFiles	import *
from src.sbfTools	import locateProgram
if sys.platform == 'win32':
	from src.sbfTools import winGetInstallPath
from src.sbfUI		import ask, askQuestion
from src.sbfUses	import uses, UseRepository
from src.sbfUtils	import *
from src.sbfVersion import splitUsesName, printSBFVersion
from src.SConsBuildFramework import stringFormatter
from src.sbfSubversion import anonymizeUrl, unanonymizeUrl, branches2branch, localListSbfTags, printSbfBranch, getLocalTagsContents, locateProject, removeTrunkOrTagsOrBranches, svnIsUpdateAvailable, svnIsVersioned, Subversion, splitSvnUrl, joinSvnUrl

###### Action function for sbfCheck target #######
def checkTool( env, toolName, toolCmdArgs ):
	whereis = locateProgram( toolName )
	if len(whereis)>0:
		print ( '%s found at %s' % (toolName, whereis) )
		print ( '%s version : ' % toolName ),
		sys.stdout.flush()
		print execute( toolCmdArgs, whereis )
		#env.Execute( '@' + toolCmd )
	else:
		print ( '%s not found' % toolName )
	print



def sbfCheck( env ):
	print stringFormatter( env, 'Availability and version of tools' )

	checkTool( env, 'python', ['python', '--version'] )

	sconsLocation = locateProgram( 'scons.bat' )
	if sconsLocation :
		print 'scons found at', sconsLocation
		print 'scons version :', SCons.__version__
		sys.stdout.flush()
	else:
		print 'scons not found'
	print

	print 'Version of python used by scons : {0}\n'.format( sys.version )

	# PYWIN32
	try:
		import distutils.sysconfig
		sitePackages = distutils.sysconfig.get_python_lib(plat_specific=1)
		with open(os.path.join(sitePackages, "pywin32.version.txt")) as file:
			buildNumber = file.read().strip()
			print ('PyWin32 version : {0}\n'.format( buildNumber ))
	except:
		print ('PyWin32 not installed\n')

	# PYSVN
	try:
		import pysvn
		print 'pysvn version: %d.%d.%d-%d' % (pysvn.version[0], pysvn.version[1], pysvn.version[2], pysvn.version[3])
		if len(pysvn.svn_version[3]) == 0 :
			print 'svn version (for pysvn): %d.%d.%d' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2])
		else :
			print 'svn version (for pysvn): %d.%d.%d-%s' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2], pysvn.svn_version[3])
		print
	except ImportError as e:
		print ('pysvn not installed\n')

	# @todo pyreadline
	# @todo pyreadline using pywin32 method 

	# @todo cygwin version

	# SVN
	checkTool( env, 'svn', ['svn', '--version', '--quiet'] )

# @todo check svn patch available (i.e. svn version > 1.7)

	# CC
	checkCC( env = env )

	# doxygen
	checkTool( env, 'doxygen', ['doxygen', '--version'] )

	# graphviz
	checkTool( env, 'graphviz', ['dot', '-V'] )

	# rsync
	checkTool( env, 'rsync', ['rsync', '--version'] )

	# ssh
	checkTool( env, 'ssh', ['ssh', '-v'] )

	# TortoiseMerge
	tortoiseMergeLocation = locateProgram( 'TortoiseMerge' )
	if tortoiseMergeLocation :
		print ('TortoiseMerge.exe found at {0}'.format( tortoiseMergeLocation ))
		sys.stdout.flush()
	else:
		print ('TortoiseMerge.exe not found')
	print

	# 7z
	checkTool( env, '7z', ['7z'] )

	# NSIS
	nsisLocation = locateProgram('nsis')
	if len(nsisLocation)>0:
		major = winGetInstallPath(subkey=r'SOFTWARE\NSIS\VersionMajor')
		minor = winGetInstallPath(subkey=r'SOFTWARE\NSIS\VersionMinor')
		print ('nsis version : {0}.{1}\n'.format( major, minor ))
	else:
		print ('nsis not installed\n')

	# Swig
	swigLocation = locateProgram( 'swig' )
	if len(swigLocation)>0:
		print ( 'swig found at {}'.format(swigLocation) )
		sys.stdout.flush()
		print execute( ['swig', '-version'], swigLocation )
	else:
		print ( 'swig not found' )
	print

	# CMake
	cmakeLocation = locateProgram( 'cmake' )
	if len(cmakeLocation)>0:
		print ( 'cmake found at {}'.format(cmakeLocation) )
		sys.stdout.flush()
		print execute( ['cmake', '--version'], cmakeLocation )
	else:
		print ( 'cmake not found' )
	print

	# @todo gtkmm see sbfUses.py
	# print informations in a pretty table program | version | location
	# @todo others tools

	#
	printSBFVersion()

	sbf_root = os.getenv('SCONS_BUILD_FRAMEWORK')
	if ( sbf_root == None ) :
		print 'sbfError: SCONS_BUILD_FRAMEWORK environment variable is not defined'
		print 'sbfInfo: You must set the SCONS_BUILD_FRAMEWORK environment variable to ', env.GetLaunchDir()
		print 'sbfInfo: This can be done with the following bash command : export SCONS_BUILD_FRAMEWORK=\'', env.GetLaunchDir(), '\''
	else :
		print 'Environment variable SCONS_BUILD_FRAMEWORK=', sbf_root
		sbf_root_normalized	= getNormalizedPathname( sbf_root )
		if ( sbf_root == sbf_root_normalized ) :
			if ( not os.path.exists(sbf_root) ) :
				print 'sbfError: SCONS_BUILD_FRAMEWORK is not an existing path'
			else :
				sbf_root_main = sbf_root_normalized + os.sep + 'sbfMain.py'
				if ( os.path.exists( sbf_root_main ) ) :
					print 'sbfInfo: SCONS_BUILD_FRAMEWORK is perfectly defined'
					print 'sbfInfo: i.e. existing path, well written'
					print 'sbfInfo: and is the main directory of SConsBuildFramework.'
				else :
					print 'sbfInfo: SConsBuildFramework not found at ', sbf_root_normalized
		else :
			print 'sbfInfo: the path defining by SCONS_BUILD_FRAMEWORK is automatically normalized. Try to normalize it yourself.'
			print 'sbfInfo: the normalized SCONS_BUILD_FRAMEWORK=', sbf_root_normalized


def checkCC(target = None, source = None, env = None) :
	print 'Current default compiler :', env['CC']

	if env['CC'] == 'cl' :
		#ccVersionAction		= Action( 'cl /help' )
		print 'cl version :', env['MSVC_VERSION']
		print 'The installed versions of cl are', sorted(cached_get_installed_vcs())

	checkTool( env, 'gcc', ['gcc', '-dumpversion'] )


from src.SConsBuildFramework import SConsBuildFramework, nopAction, printEmptyLine


###### Initial environment ######
EnsurePythonVersion(2, 7)
EnsureSConsVersion(2, 1, 0)

# create objects
sbf = SConsBuildFramework()
SConsEnvironment.sbf = sbf
env = sbf.myEnv # TODO remove me (this line is just for compatibility with the old global env)
buildTargetsSet = sbf.myBuildTargets

# checks if target is valid
if buildTargetsSet.issubset(sbf.myAllTargets) == False:
	print( 'sbfError: invalid target(s): {0}'.format(string.join(list(buildTargetsSet-sbf.myAllTargets), ', ')) )
	exit(1)

# Prints current 'config' option
print ( "Configuration: {0}\n".format(env['config']) )

# Dumping construction environment (for debugging).
#print env.Dump()


# build project from launch directory (and all dependencies recursively)
env['sbf_launchDir'			]	= getNormalizedPathname( os.getcwd() )
env['sbf_projectPathName'	]	= env['sbf_launchDir']
env['sbf_projectPath'		]	= os.path.dirname(env['sbf_launchDir'])
env['sbf_project'			]	= os.path.basename(env['sbf_launchDir'])
env['sbf_launchProject'		]	= env['sbf_project']


### special targets about svn ###
# svnAdd svnCheckout svnClean svnRelocate svnStatus svnUpdate
if len(buildTargetsSet & sbf.mySvnTargets) > 0:
	Alias( 'svnadd',		Command('dummySvnAdd.main.out1',		'dummy.in', Action( nopAction, nopAction ) ) )
	Alias( 'svncheckout',	Command('dummySvnCheckout.main.out1',	'dummy.in', Action( nopAction, nopAction ) ) )
	Alias( 'svnclean',		Command('dummySvnClean.main.out1',		'dummy.in', Action( nopAction, nopAction ) ) )
	Alias( 'svnrelocate',	Command('dummySvnRelocate.main.out1',	'dummy.in', Action( nopAction, nopAction ) ) )
	Alias( 'svnstatus',		Command('dummySvnStatus.main.out1',		'dummy.in', Action( nopAction, nopAction ) ) )
	Alias( 'svnupdate',		Command('dummySvnUpdate.main.out1',		'dummy.in', Action( nopAction, nopAction ) ) )


# svnMkTag and svnRemoteMkBranch
hasBranchOrTagTarget = len(buildTargetsSet & sbf.mySvnBranchOrTagTargets) > 0
if hasBranchOrTagTarget:
	# branch or tag targets ?
	if len( set(['svnmktag']) & buildTargetsSet ) > 0:
		env['myBranchesOrTags'] = 'tags'
	else:
		env['myBranchesOrTags'] = 'branches'
	env['myBranchOrTag'] = branches2branch(env['myBranchesOrTags'])

	# svnMkTag
	if 'svnmktag' in buildTargetsSet:
		printSeparator('Creating a tag')
		print('Tag is created locally and used revision from working copy. But any local modifications are ignored.\n')

		# Lists available tags for the launching project
		tags = localListSbfTags( env['sbf_projectPathName'] )
		printSbfBranch( env['sbf_project'], env['myBranchesOrTags'], tags, True )

		#
		env['myBranch'] = ask( "\nGives the name of the {0}".format(env['myBranchOrTag'] ), env['svnDefaultBranch'] )

		# Adds informations about SConsBuildFramework project used into self.myBranchSvnUrls
		(url, revision ) = sbf.myVcs.getUrlAndRevision(sbf.mySCONS_BUILD_FRAMEWORK)
		url = anonymizeUrl(url)
		sbf.myBranchSvnUrls[ 'SConsBuildFramework' ] = '{0}@{1}'.format(url, revision)
	# svnRemoteMkBranch
	elif 'svnremotemkbranch' in buildTargetsSet:
		printSeparator('Creating a branch from a tag')
		print('Local tag file is used to created a branch directly on the repository.\n')

		# Lists available tags for the launching project
		branchChoicesList = localListSbfTags( env['sbf_projectPathName'] )
		printSbfBranch( env['sbf_project'], 'tags', branchChoicesList, True )
		if len(branchChoicesList)==0:	exit(1)

		# Chooses one tag
		desiredTag = askQuestion( "Choose one tag among the following ", branchChoicesList )
		env['myBranch'] = desiredTag
		print

		# Retrieves informations about the desired tag
		tagContents = getLocalTagsContents( env['sbf_projectPathName'], desiredTag )
		tagSbfConfigFileDict = {}
		exec( tagContents, globals(), tagSbfConfigFileDict )

		# for each project
		tagSvnUrls = tagSbfConfigFileDict.get( 'svnUrls', {} )
		vcs = Subversion( svnUrls=tagSvnUrls )
		for project in tagSvnUrls.keys():
			(projectTagSvnUrl, projectTagSvnRevision) = splitSvnUrl( tagSvnUrls[project] )
			projectBaseSvnUrl = removeTrunkOrTagsOrBranches(projectTagSvnUrl)
			projectBranchSvnUrl = '{0}/branches/{1}'.format( projectBaseSvnUrl, desiredTag )

			print stringFormatter( env, 'project {0}'.format(project) )

			# Checks if branch already created in repository ?
			if svnIsVersioned(projectBranchSvnUrl):
				# branch already created
				print ("branch '{0}' already in repository of project {1}\n".format(desiredTag, project) )
				# Updated myBranchSvnUrls for project
				sbf.myBranchSvnUrls[ project ] = projectBranchSvnUrl
				continue
			else:
				answer = askQuestion(	"Do you want to create a vcs branch named '{0}' for {1}".format(desiredTag, project),
										['(n)o', '(y)es'] )
				if answer == 'yes':
					# Created the branch
					logMessage = "Created branch '{0}' for {1}".format( desiredTag, project )
					vcs.copy( project, unanonymizeUrl(projectTagSvnUrl), projectTagSvnRevision, unanonymizeUrl(projectBranchSvnUrl), logMessage )
					# Updated myBranchSvnUrls for project
					sbf.myBranchSvnUrls[ project ] = projectBranchSvnUrl
				else:
					# Updated myBranchSvnUrls for project
					sbf.myBranchSvnUrls[ project ] =  joinSvnUrl( projectTagSvnUrl, projectTagSvnRevision )
			print
	else:
		assert( False )
	Alias( 'svnmktag',			Command('dummySvnMkTag.main.out1',		'dummy.in', Action( nopAction, nopAction ) ) )
	Alias( 'svnremotemkbranch',	Command('dummySvnRemoteMkBranch.main.out1',	'dummy.in', Action( nopAction, nopAction ) ) )


# Initializes 'uses' repository
if UseRepository.isInitialized() == False :
	UseRepository.initialize( sbf )


# target sbfCheck sbfPak sbfConfigure sbfUnconfigure sbfConfigureTools and sbfUnconfigureTools
hasSbfTargets = len( buildTargetsSet & sbf.mySbfTargets ) > 0
if hasSbfTargets:
	# target sbfcheck
	if 'sbfcheck' in buildTargetsSet:
		sbfCheck( env )
	# target 'sbfPak'
	elif 'sbfpak' in buildTargetsSet:
		import src.sbfPackagingSystem
		src.sbfPackagingSystem.runSbfPakCmd(sbf)
	# all sbf*configure* targets
	elif 'sbfconfigure' in buildTargetsSet:
		sbfConfigure( sbf )
	elif 'sbfunconfigure' in buildTargetsSet:
		sbfUnconfigure( sbf )
	elif 'sbfconfiguretools' in buildTargetsSet:
		sbfConfigureTools( sbf )
	elif 'sbfunconfiguretools' in buildTargetsSet:
		sbfUnconfigureTools( sbf )
	else:
		raise SCons.Errors.UserError("Internal sbf error.")
	Exit(0)


# Builds the root project (i.e. launchDir).
sbf.buildProject( env['sbf_projectPathName'], None, False )
Clean( 'mrproper', join(sbf.myInstallDirectory, 'include') )
env = sbf.getRootProjectEnv()

# Creates (if needed) the file named branchName.tags|branches
if len(sbf.myBranchSvnUrls)>0:
	# Checks target
	target = join( env['sbf_projectPathName'], 'branching', '{0}.{1}'.format(env['myBranch'], env['myBranchesOrTags']) )

	# Filling source

	#	Adds creation time
	source = ['# Created on {0}\n'.format(sbf.myDateTimeForUI)]

	#	Adds log message
	emptyLogMessage = 'no log message'
	logMessage = ask( "\nGives the log message to add in the {0}.{1} file.".format( env['myBranch'], env['myBranchesOrTags'] ), emptyLogMessage )

	if len(logMessage)>0 and (logMessage is not emptyLogMessage):
		source.append( '# log message: {0}\n'.format(logMessage) )

	#	Constructs the 'svnUrls'
	source.extend( getDictPythonCode( sbf.myBranchSvnUrls, 'svnUrls', orderedDict=True ) )

	#	clVersion
	source.append( "\nclVersion	= '{0}'\n".format(env['clVersion']) )

	#	'uses' alias
	allUses = sbf.getAllUses( env )
	usesAlias = collections.OrderedDict()
	for useNameVersion in sorted(allUses):
		# Extracts name and version of incoming external dependency
		useName, useVersion = splitUsesName( useNameVersion )
		if len(useVersion)>0:
			usesAlias[useName] = useVersion

	source.append( getDictPythonCode(usesAlias, 'usesAlias', orderedDict=True, addImport=False) )

	#
	textFile = env.Textfile( target = target, source = source )
	Alias( 'svnmktag', textFile )
	Alias( 'svnremotemkbranch', textFile )

#
if env.GetOption('verbosity'):
	if len(sbf.myInstallDirectories)>1:
		print 'Installation directories', sbf.myInstallDirectories
	elif len(sbf.myInstallDirectories)==1:
		print 'Installation directory', sbf.myInstallDirectories
	#else nothing to do


### special targets: onlyRun and run ###
Alias( 'onlyrun' )
Alias( 'run' )


### target configure ###
# @todo


### target sbfConfigure ###
# @todo


### target pakUpdate ###
from src.sbfPakUpdate import configurePakUpdateTarget
configurePakUpdateTarget( env )

### target info ###
#from src.sbfInfo import configureInfoTarget
#configureInfoTarget( env )


### special target : vcproj ###
from src.sbfVCProj import configureVCProjTarget
configureVCProjTarget( env )


### target dox ###
from src.sbfDoxygen import configureDoxTarget
configureDoxTarget( env )


# SConsBuildFramework auto-update
def runSbfAutoUpdater():
	# Create directory 'sbfAutoUpdater'
	sandboxPath = join(sbf.mySCONS_BUILD_FRAMEWORK, 'sbfAutoUpdater')
	if not exists(sandboxPath):	os.makedirs(sandboxPath)

	# Copy files in directory 'sbfAutoUpdater'
	for file in ['sbfFiles.py', 'sbfIVersionControlSystem.py', 'sbfSubversion.py']:
		shutil.copy( join(sbf.mySCONS_BUILD_FRAMEWORK, 'src', file), sandboxPath )

	# Create autoUpdater.py
	autoUpdater = join(sandboxPath, 'autoUpdater.py')
	with open( autoUpdater, 'w' ) as f:
		autoUpdaterCode = """import os
from collections import OrderedDict
from sbfSubversion import Subversion

SCONS_BUILD_FRAMEWORK = os.getenv('SCONS_BUILD_FRAMEWORK')
svnUrls = {svnUrls}

vcs = Subversion( svnUrls=svnUrls )

vcs.update( SCONS_BUILD_FRAMEWORK, "SConsBuildFramework" )
"""
		f.write( autoUpdaterCode.format( svnUrls=str(sbf.mySvnUrls) ) )

	# Replace current process with autoUpdater.py
	if sbf.myPlatform == 'win32':
		autoUpdater = autoUpdater.replace('\\', '\\\\')
		print 'Asynchronous update of SConsBuildFramework'
	os.execlp( 'python', 'python', '"{0}"'.format(autoUpdater) )

# Test if SConsBuildFramework needs to update itself. Takes care of 'svnUrls' values.
if 'svnupdate' in buildTargetsSet:
	# test if update has to be done
	print stringFormatter( env, 'vcs update project {0} in {1}'.format(basename(sbf.mySCONS_BUILD_FRAMEWORK), sbf.mySCONS_BUILD_FRAMEWORK) )

	(svnUrl, desiredRevision) = sbf.myVcs.locateProject('SConsBuildFramework')

	isAnUpdateAvailable = svnIsUpdateAvailable( sbf.mySCONS_BUILD_FRAMEWORK, desiredRevision, True, env.GetOption('verbosity'), True )
	if isAnUpdateAvailable:
		runSbfAutoUpdater()
	print

#print (datetime.datetime.now() - sbfMainBeginTime).microseconds/1000
