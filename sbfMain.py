# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, 2010, 2011, 2012, Nicolas Papier.
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

import distutils.archive_util
import os
import string
import sys

# To be able to catch wrong SCons version or missing SCons
try:
	from SCons.Tool.MSCommon.vc import cached_get_installed_vcs
except ImportError as e:
	print ('sbfError: SCons not installed or wrong version.')
	Exit(1)

from SCons.Script.SConscript import SConsEnvironment
from SCons import SCons # for SCons.__version__


from src.sbfCygwin	import *
from src.sbfEnvironment import Environment
from src.sbfFiles	import *
from src.sbfPaths	import Paths
from src.sbfTools	import locateProgram, getPathsForTools, getPathsForRuntime
if sys.platform == 'win32':
	from src.sbfTools import winGetInstallPath
from src.sbfUI		import ask
from src.sbfUses	import uses, getPathsForSofa
from src.sbfUtils	import *
from src.sbfVersion import printSBFVersion
from src.SConsBuildFramework import stringFormatter


###### Archiver action ######
# @todo Uses 7Zip (because make_archive seems to allocate a lot of memory for big files...)
def zipArchiver( target, source, env ) :
	targetName = str(target[0])
	sourceName = str(source[0])
	distutils.archive_util.make_archive( os.path.splitext(targetName)[0], 'zip', sourceName )

def printZipArchiver( target, source, env ) :
	targetName = str(target[0])
	sourceName = str(source[0])
	return ("Generates %s with files from %s" % (targetName, sourceName))



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

	sconsLocation = locateProgram( 'scons' )
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

	# @todo cygwin version

	# SVN
	checkTool( env, 'svn', ['svn', '--version', '--quiet'] )

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

	# @todo gtkmm see sbfUses.py
	# print informations in a pretty table program | version | location
	# @todo others tools (ex : swig, ...)

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


###### Implementation of sbfConfigure and sbfUnconfigure targets #######

def _sbfConfigure( pathsToPrepend, pathsToAppend ):
	if sys.platform == 'win32':
		environment = Environment()
		paths = Paths( environment.get('PATH') )
		paths.prependList( pathsToPrepend, True )
		paths.appendList( pathsToAppend, True )
		print
		environment.set('PATH', paths.getString())
	else:
		print ('Target sbfConfigure* not yet implemented on {0} platform.'.format(env['PLATFORM']))


def _sbfUnconfigure( pathsToRemove ):
	if sys.platform == 'win32':
		environment = Environment()
		paths = Paths( environment.get('PATH') )
		paths.removeList( pathsToRemove )
# @todo asks user
		paths.removeAllNonExisting()
		print
		environment.set('PATH', paths.getString())
	else:
		print ('Target sbfUnconfigure* not yet implemented on {0} platform.'.format(env['PLATFORM']))


def _getSBFRuntimePaths( sbf ):
	prependList = []
	appendList  = []

	# Prepends $SCONS_BUILD_FRAMEWORK in PATH for 'scons' file containing scons.bat $*
	prependList.append( sbf.mySCONS_BUILD_FRAMEWORK )

	# Adds C:\PythonXY (where C:\PythonXY is the path to your python's installation directory) to your PATH environment variable.
	# This is important to be able to run the Python executable from any directory in the command line.
	pythonLocation = locateProgram('python')
	appendList.append( pythonLocation )

	# Adds c:\PythonXY\Scripts (for scons.bat)
	appendList.append( join(pythonLocation, 'Scripts') )

	#
	return (prependList, appendList)


def sbfConfigure( sbf ):
	toPrepend = getPathsForSofa(True) + getPathsForRuntime(sbf)

	sbfRuntimePaths = _getSBFRuntimePaths( sbf )

	_sbfConfigure( toPrepend + sbfRuntimePaths[0], sbfRuntimePaths[1] )


def sbfUnconfigure( sbf ):
	toRemove = getPathsForSofa(True) + getPathsForRuntime(sbf)

	# Don't remove sbfRuntimePaths = _getSBFRuntimePaths()

	_sbfUnconfigure( toRemove )


def sbfConfigureTools( sbf ):
	toAppend = getPathsForTools()
	_sbfConfigure( [], toAppend )


def sbfUnconfigureTools( sbf ):
	toRemove = getPathsForTools()
	_sbfUnconfigure( toRemove )



from src.SConsBuildFramework import SConsBuildFramework, nopAction, printEmptyLine



###### Initial environment ######
EnsurePythonVersion(2, 6)
EnsureSConsVersion(2, 1, 0)

# create objects
sbf = SConsBuildFramework()
SConsEnvironment.sbf = sbf
env = sbf.myEnv # TODO remove me (this line is just for compatibility with the old global env)
buildTargetsSet = sbf.myBuildTargets

# Prints current 'config' option
print ( "Configuration: {0}\n".format(env['config']) )

# Dumping construction environment (for debugging).
#print env.Dump()

# rsync builder
# @todo lazy construction
cygpathLocation = locateProgram( 'cygpath' )
sshLocation = locateProgram( 'ssh' )
if len(sshLocation)>0:
	if env['PLATFORM'] == 'win32':
		sshLocation = callCygpath2Unix(sshLocation, cygpathLocation).lower()
	env['RSYNCRSH'] = '--rsh={0}/ssh'.format(sshLocation)
	#print '--rsh={0}/ssh'.format(sshLocation)
else:
	env['RSYNCRSH'] = ''

env['RSYNCFLAGS']			= "-av --chmod=u=rwX,go=rX" # --progress

def createRsyncAction( env, target, source, alias = None ):
	# Example of generated rsync command :
	# rsync --delete -av --chmod=u=rwX,go=rX --rsh=/usr/bin/ssh /cygdrive/d/tmp/sbf/build/pak/ulisProduct_2-0-beta13_2012-02-01_setup.exe farmer@orange:/srv/files/Dev/buildbot/vista-farm/ulisProduct_2-0-beta13_2012-02-01_setup.exe
	cygpathLocation = locateProgram('cygpath')

	if env['PLATFORM']=='win32':
		fullSource = callCygpath2Unix( source, cygpathLocation )
	else:
		fullSource = source
	#print source

	publishPath = env['publishPath']
	fullTarget = publishPath + '/' + str(target)
	#print fullTarget

	if GetOption('weakPublishing'):
		dynamicFlags = ''
	else:
		dynamicFlags = '--delete'

	cmd = 'rsync {rsyncFlags} {weakPublishingFlags} {rsh} {src} {dst}'.format( rsyncFlags=env['RSYNCFLAGS'], weakPublishingFlags=dynamicFlags, rsh=env['RSYNCRSH'], src=fullSource, dst=fullTarget)
	#print cmd
	rsyncAction = env.Command( 'dummyRsync{0}.out'.format(target), source, cmd )
	if alias:
		env.Alias( alias, rsyncAction )
	return rsyncAction
env.AddMethod( createRsyncAction )


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

# svnMkTag, svnRmTag, svnMkBranch and svnRmBranch
hasBranchOrTagTarget = len(buildTargetsSet & sbf.mySvnBranchOrTagTargets) > 0
if hasBranchOrTagTarget:
	# branch or tag targets ?
	if len( set(['svnmktag', 'svnrmtag']) & buildTargetsSet ) > 0:
		branch = 'tags'
	else:
		branch = 'branches'

	# Lists available tag/branch in repository for the launching project
	entries = sbf.myVcs.listBranch( env['sbf_projectPathName'], branch )
	if len(entries) > 0:
		print ('List of {0} in repository of project {1}:'.format(branch, env['sbf_project']))
		for entry in entries:
			print entry.lstrip('/')
	else:
		print ('No {0} in repository of project {1}'.format(branch, env['sbf_project']))

	answer = ask( '\nGives the name of {0}'.format(branch.rstrip('s')), env['svnDefaultBranch'] )
	env['myBranch'] = answer

	Alias( 'svnmktag',		Command('dummySvnMkTag.main.out1',		'dummy.in', Action( nopAction, nopAction ) ) )
	Alias( 'svnrmtag',		Command('dummySvnRmTag.main.out1',		'dummy.in', Action( nopAction, nopAction ) ) )
	Alias( 'svnmkbranch',	Command('dummySvnMkBranch.main.out1',	'dummy.in', Action( nopAction, nopAction ) ) )
	Alias( 'svnrmbranch',	Command('dummySvnRmBranch.main.out1',	'dummy.in', Action( nopAction, nopAction ) ) )


# Builds sbf library
if env['nodeps'] == False and env['sbf_project'] != 'sbf':
	# Builds sbf project
	sbf.buildProject( sbf.mySbfLibraryRoot, None )

# Builds the root project (i.e. launchDir).
sbf.buildProject( env['sbf_projectPathName'], None, False )


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
from src.sbfInfo import configureInfoTarget
configureInfoTarget( env )


### special target : vcproj ###
from src.sbfVCProj import configureVCProjTarget
configureVCProjTarget( env )


### special doxygen related targets : dox_build dox_install dox dox_clean dox_mrproper ###

def printDoxygenBuild( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Build documentation with doxygen" )

def printDoxygenInstall( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Install doxygen documentation" )



# Creates a custom doxyfile
def doxyfileAction( target, source, env ) :

	# Compute inputList, examplePath and imagePath parmeters of doxyfile
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

	shutil.copyfile(sourceName, targetName)			# or env.Execute( Copy(targetName, sourceName) )

	file = open( targetName, 'a' )

	file.write( '\n### Added by SConsBuildFramework\n' )
	file.write( 'PROJECT_NAME		= "%s"\n'					% sbf.myProject )
	file.write( 'PROJECT_NUMBER		= "%s generated at %s"\n'	% (sbf.myVersion, sbf.myDateTime) )
	file.write( 'OUTPUT_DIRECTORY	= "%s"\n'					% (targetName + '_build') )
	file.write( 'INPUT				= %s\n'						% inputList )
	#FIXME: FILE_PATTERNS, EXCLUDE, EXCLUDE_PATTERNS
	file.write( 'EXAMPLE_PATH		= %s\n'				% examplePath )
	file.write( 'IMAGE_PATH			= %s\n'				% imagePath )

	file.close()


# Synchronizes files from source to target.
# target should be yourDestinationPath/dummy.out
# Recursively copy the entire directory tree rooted at source to the destination directory (named by os.path.dirname(target)).
# Remark : the destination directory would be removed before the copying occurs (even if not empty, so be carefull).
def syncAction( target, source, env ) :

	import shutil

	sourcePath		= str(source[0])
	destinationPath	= os.path.dirname(str(target[0]))

	print 'Copy %s at %s' % (sourcePath, destinationPath)

	if ( os.path.ismount(destinationPath) ) :
		print 'sbfError: Try to use %s as an installation/desinstallation directory. Stop action to prevent any unwanted file destruction'
		return None

	shutil.rmtree( destinationPath, True )

	if ( os.path.isdir( os.path.dirname(destinationPath) ) == False ):
		os.makedirs( os.path.dirname(destinationPath) )
	shutil.copytree( sourcePath, destinationPath )


# @todo improves output message
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
	commandCompileDoxygen = env.Command( 'dox_build.out2', 'dummy.in', 'doxygen ' + doxOutputCustomDoxyfile )
	env.Alias( 'dox_build', commandCompileDoxygen )
	env.AlwaysBuild( [commandGenerateDoxyfile, commandCompileDoxygen] )

	# target dox_install
	dox_install_cmd = env.Command( os.path.join(doxInstallPath,'dummy.out'), Dir(os.path.join(doxBuildPath, 'html')), Action(syncAction, printDoxygenInstall) )
	env.Alias( 'dox_install', [	'dox_build', dox_install_cmd ] )
	env.AlwaysBuild( dox_install_cmd )
	env.Depends( dox_install_cmd, 'dox_build' )

	if env['publishOn'] :
		# @todo print message
		rsyncAction = env.createRsyncAction( 'doc_%s_%s' % (sbf.myProject, sbf.myVersion), Dir(os.path.join(doxBuildPath, 'html')) )

		env.Alias( 'dox_install', rsyncAction )
		env.Depends( rsyncAction, 'dox_build' )

	# target dox
	env.Alias( 'dox', 'dox_install' )

	# target dox_clean
	env.Alias( 'dox_clean', 'dox' )
	env.Clean( 'dox_clean', doxOutputPath )

	# target dox_mrproper
	env.Alias( 'dox_mrproper', 'dox_clean' )
	env.Clean( 'dox_mrproper', doxInstallPath )

### special zip related targets : zipRuntime, zipDeps, zipPortable, zipDev, zipSrc and zip ###
from src.sbfNSIS import configureZipAndNSISTargets
configureZipAndNSISTargets( env )

# Tests if SConsBuildFramework is up-to-date
# @todo Updates SConsBuildFramework
if 'svnupdate' in buildTargetsSet:
	from src.sbfSubversion import SvnUpdateAvailable
	print stringFormatter( env, "Tests if project {project} in {projectPath} is up-to-date".format( project=os.path.basename(sbf.mySCONS_BUILD_FRAMEWORK), projectPath=os.path.dirname(sbf.mySCONS_BUILD_FRAMEWORK)) )
	updateAvailable = SvnUpdateAvailable()( sbf.mySCONS_BUILD_FRAMEWORK )
	if updateAvailable:
		print ('AN UPDATE IS AVAILABLE FOR SCONSBUILDFRAMEWORK')
	else:
		print ('SConsBuildFramework is up-to-date')
	print
	#print stringFormatter( env, "vcs %s project %s in %s" % ('update', os.path.basename(sbf.mySCONS_BUILD_FRAMEWORK), os.path.dirname(sbf.mySCONS_BUILD_FRAMEWORK)) )
	#sbf.myVcs.update( sbf.mySCONS_BUILD_FRAMEWORK, os.path.basename(sbf.mySCONS_BUILD_FRAMEWORK) )

#print (datetime.datetime.now() - sbfMainBeginTime).microseconds/1000
