# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, Nicolas Papier.
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
from __future__ import with_statement

#import datetime
#sbfMainBeginTime = datetime.datetime.now()

import distutils.archive_util
#import glob
import os
import string
import sys

from SCons.Script.SConscript import SConsEnvironment
import SCons.Errors

from src.sbfCygwin	import *
from src.sbfFiles	import *
from src.sbfUses	import uses
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



# @todo moves to sbfFiles.py
def computeDepth( path ):
	path = os.path.normpath( path )
	if path == '.':
		return 0

	countNonEmpty = 0
	for elt in path.split( os.sep ):
		if len(elt) > 0:
			countNonEmpty += 1
	return countNonEmpty



###### Action function for sbfCheck target #######
import subprocess

def execute( command ):
	# Executes command
	pipe = subprocess.Popen( command, shell=True, bufsize = 0, stdout=subprocess.PIPE, stderr=subprocess.PIPE )

	# Retrieves stdout or stderr
	lines = pipe.stdout.readlines()
	if len(lines) == 0 :
		lines = pipe.stderr.readlines()

	for line in lines :
		line = line.rstrip('\n')
		if len(line) > 0 :
			return line

def checkTool( env, toolName, toolCmd ):
	whereis = env.WhereIs( toolName )
	if whereis :
		print ( '%s found at %s' % (toolName, whereis) )
		print ( '%s version : ' % toolName ),
		sys.stdout.flush()
		env.Execute( toolCmd )
	else:
		print ( '%s not found' % toolName )
	print

def sbfCheck(target = None, source = None, env = None) :
	print stringFormatter( env, 'Availability and version of tools' )

	checkTool( env, 'python', '@python --version' )

	print 'Version of python used by scons :', sys.version
	print

	whereis_scons = env.WhereIs( 'scons' )
	if whereis_scons :
		print 'scons found at', whereis_scons
		print 'scons version :', SCons.__version__
		sys.stdout.flush()
		#print execute( 'scons --version' )
	else:
		print 'scons not found'
	print

	#@todo pysvn should be optionnal
	import pysvn
	print 'pysvn version: %d.%d.%d-%d' % (pysvn.version[0], pysvn.version[1], pysvn.version[2], pysvn.version[3])
	if len(pysvn.svn_version[3]) == 0 :
		print 'svn version (for pysvn): %d.%d.%d' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2])
	else :
		print 'svn version (for pysvn): %d.%d.%d-%s' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2], pysvn.svn_version[3])
	print

	checkTool( env, 'svn', '@svn --version --quiet' )

	env.Execute( checkCC, nopAction )

	checkTool( env, 'doxygen', '@doxygen --version' )

	whereis_rsync = env.WhereIs( 'rsync' )				# @todo whereis for others tools
	if whereis_rsync :
		print 'rsync found at', whereis_rsync
		print 'rsync version :',
		sys.stdout.flush()
		print execute( 'rsync --version' )
	else:
		print 'rsync not found'
	print

	whereis_ssh = env.WhereIs( 'ssh' )
	if whereis_ssh :
		print 'ssh found at', whereis_ssh
		print 'ssh version   :',
		sys.stdout.flush()
		print execute( 'ssh -v' )
	else:
		print 'ssh not found'
	print

	whereis_TortoiseMerge = env.WhereIs( 'TortoiseMerge' )
	if whereis_TortoiseMerge :
		print 'TortoiseMerge.exe found at', whereis_TortoiseMerge
		sys.stdout.flush()
	else:
		print 'TortoiseMerge.exe not found'
	print

	#@todo nsis

	#@todo others tools (ex : swig, ...)
	#@todo Adds checking for the existance of tools (svn, doxygen...)

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
		print 'cl version :', env['MSVS']['VERSION']
		print 'The available versions of cl installed are', env['MSVS']['VERSIONS']

	checkTool( env, 'gcc', '@gcc -dumpversion' )



from src.SConsBuildFramework import SConsBuildFramework, nopAction, printEmptyLine



###### Initial environment ######
#

# create objects
# HINTS: to propagate the entire external environment to the execution environment for commands : ENV = os.environ

#Export('env') not needed.

EnsurePythonVersion(2, 6)
EnsureSConsVersion(1, 2, 0)

SConsEnvironment.sbf = SConsBuildFramework()
env = SConsEnvironment.sbf.myEnv # TODO remove me (this line is just for compatibility with the old global env)
# Prints current 'config' option
print "\nConfiguration: %s\n" % env['config']

# Dumping construction environment (for debugging).
#print env.Dump()

# rsync builder
env['POSIX_SOURCE'] = PosixSource( env['PLATFORM'] )
env['POSIX_TARGET'] = PosixTarget( env['PLATFORM'] )

whereis_ssh = env.WhereIs( 'ssh' )
if whereis_ssh :
	if env['PLATFORM'] == 'win32' :
		whereis_ssh = callCygpath2Unix(whereis_ssh).lower()
	env['RSYNCRSH'] = '--rsh=%s' % whereis_ssh
else:
	env['RSYNCRSH'] = ''

env['RSYNCFLAGS']			= "--delete -av --chmod=u=rwX,go=rX" # --progress
env['BUILDERS']['Rsync']	= Builder( action = "rsync $RSYNCFLAGS $RSYNCRSH $POSIX_SOURCE $publishPath/${TARGET}" ) # adds @ and printMsg
def createRsyncAction( env, target, source, alias = None ):
	rsyncAction = env.Rsync( Value(target), source )
	env.AlwaysBuild( rsyncAction )
	if alias is not None :
		env.Alias( alias, rsyncAction )
	return rsyncAction
env.AddMethod( createRsyncAction )

# target 'sbfCheck'
Alias('sbfCheck', env.Command('dummyCheckVersion.out2', 'dummy.in', Action( sbfCheck, printEmptyLine ) ) )

# target 'sbfPak'
import src.sbfPackagingSystem

def sbfPakAction(target = None, source = None, env = None):
	src.sbfPackagingSystem.runSbfPakCmd(SConsEnvironment.sbf)
	return 0

sbfPakTargets = ['sbfPak', 'sbfpak']
Alias(sbfPakTargets, Command('dummySbfPak.out', 'dummy.in', Action( sbfPakAction, nopAction ) ) )

# build project from launch directory (and all dependencies recursively)
env['sbf_launchDir'			]	= getNormalizedPathname( os.getcwd() )
env['sbf_projectPathName'	]	= env['sbf_launchDir']
env['sbf_projectPath'		]	= os.path.dirname(env['sbf_launchDir'])
env['sbf_project'			]	= os.path.basename(env['sbf_launchDir'])


# Builds sbf library
buildStage = True
for target in sbfPakTargets:
	if target in BUILD_TARGETS:
		buildStage = False
		break

if buildStage:
	if env['nodeps'] == False and env['sbf_project'] != 'sbf':
		# Builds sbf project
		env.sbf.buildProject( env.sbf.mySbfLibraryRoot )

	# Builds the root project (i.e. launchDir).
	env.sbf.buildProject( env['sbf_projectPathName'] )


### special targets: svnAdd svnCheckout svnCleanup svnStatus svnUpdate ###
Alias( 'svnAdd',		Command('dummySvnAdd.main.out1',		'dummy.in', Action( nopAction, nopAction ) ) )
Alias( 'svnCheckout',	Command('dummySvnCheckout.main.out1',	'dummy.in', Action( nopAction, nopAction ) ) )
Alias( 'svnClean',		Command('dummySvnClean.main.out1',		'dummy.in', Action( nopAction, nopAction ) ) )
Alias( 'svnStatus',		Command('dummySvnStatus.main.out1',		'dummy.in', Action( nopAction, nopAction ) ) )
Alias( 'svnUpdate',		Command('dummySvnUpdate.main.out1',		'dummy.in', Action( nopAction, nopAction ) ) )


### special targets: onlyRun (or onlyrun) and run ###
Alias( 'onlyRun' )
Alias( 'onlyrun', 'onlyRun' )

Alias( 'run' )


### special target : vcproj ###

from src.SConsBuildFramework import printGenerate

# @todo Creates a new python file for vcproj stuffs and embedded file sbfTemplateMakefile.vcproj
# @todo Configures localExt include path.

# @todo Generates section "Header Files", "Share Files" and "Source Files" only if not empty.
# @todo Generates vcproj but with c++ project and not makefile project.
# @todo Generates eclipse cdt project.

#@todo Moves to a more private location
VisualStudioDict = {	'slnHeader'				: '',
						'vcprojHeader'			: '',


						'slnHeader9'			:
"""Microsoft Visual Studio Solution File, Format Version 10.00
# Visual C++ Express 2008
""",
						'vcprojHeader9'			: '9,00',


						'slnHeader8'			:
"""Microsoft Visual Studio Solution File, Format Version 9.00
# Visual C++ Express 2005
""",
						'vcprojHeader8'			: '8,00',

}

def printVisualStudioSolutionBuild( target, source, localenv ):
	return '\n' + stringFormatter( localenv, "Build %s Visual Studio Solution" % localenv['sbf_project'] )

def printVisualStudioProjectBuild( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Build %s Visual Studio Project" % localenv['sbf_project'] )



def vcprojWrite( targetFile, indent, output ) :
	targetFile.write( output.replace("INDENT", '\t' * indent) )

def vcprojWriteFile( targetFile, indent, file ) :
	output = "INDENT<File RelativePath=\"%s\"></File>\n" % file
	vcprojWrite( targetFile, indent, output )

def vcprojWriteTree( targetFile, files ):
	# Checks if files list is empty
	if len(files) == 0 :
		return

	#
	filterStack		= [ files[0].split(os.sep)[0] ]
	currentLength	= 2
	currentFile		= []

	for file in files :
		splitedFile	= file.split( os.sep )
		newLength	= len(splitedFile)

		# Checks common paths
		minLength = min(currentLength, newLength)
		for commonLength in range( minLength-1 ) :
			if filterStack[commonLength] != splitedFile[commonLength] :
				# Paths are differents
				# Decreases depth
				count = currentLength - commonLength
				for i in range(count-1) :
					vcprojWrite( targetFile, len(filterStack)+2, "INDENT</Filter>\n" )
					filterStack.pop()
					currentLength = currentLength - 1
				break
			#else nothing to do

		if newLength > currentLength :
			# Increases depth
			for depth in splitedFile[currentLength-1:newLength-1] :
				filterStack.append( depth )
				vcprojWrite( targetFile, len(filterStack)+2, """INDENT<Filter Name="%s" Filter="">\n""" % depth )
		elif newLength < currentLength :
			# Decreases depth
			count = currentLength - newLength
			for i in range(count) :
				vcprojWrite( targetFile, len(filterStack)+2, "INDENT</Filter>\n" )
				filterStack.pop()

		# newLength == currentLength
		vcprojWriteFile( targetFile, len(filterStack)+2, file )

		currentLength	= newLength
		currentFile		= splitedFile

	# Adds closing markup
	for i in range(currentLength-2) :
		vcprojWrite( targetFile, len(filterStack)+2, "INDENT</Filter>\n" )
		filterStack.pop()


# Creates project file (.vcproj) containing informations about the debug session.
def vcprojDebugFileAction( target, source, env ) :

	# Retrieves/computes additional informations
	targetName = str(target[0])

	workingDirectory = os.path.join( env.sbf.myInstallDirectory, 'bin' )

	# Retrieves informations
	import platform
	remoteMachine	= platform.node()

	# Opens output file
	with open( targetName, 'w' ) as file :
		fileStr = """<?xml version="1.0" encoding="Windows-1252"?>
<VisualStudioUserFile
	ProjectType="Visual C++"
	Version="%s"
	ShowAllFiles="false"
	>
	<Configurations>
		<Configuration
			Name="Debug|Win32"
			>
			<DebugSettings
				Command="$(TargetPath)"
				WorkingDirectory="%s"
				CommandArguments=""
				Attach="false"
				DebuggerType="3"
				Remote="1"
				RemoteMachine="%s"
				RemoteCommand=""
				HttpUrl=""
				PDBPath=""
				SQLDebugging=""
				Environment=""
				EnvironmentMerge="true"
				DebuggerFlavor=""
				MPIRunCommand=""
				MPIRunArguments=""
				MPIRunWorkingDirectory=""
				ApplicationCommand=""
				ApplicationArguments=""
				ShimCommand=""
				MPIAcceptMode=""
				MPIAcceptFilter=""
			/>
		</Configuration>
		<Configuration
			Name="Release|Win32"
			>
			<DebugSettings
				Command="$(TargetPath)"
				WorkingDirectory="%s"
				CommandArguments=""
				Attach="false"
				DebuggerType="3"
				Remote="1"
				RemoteMachine="%s"
				RemoteCommand=""
				HttpUrl=""
				PDBPath=""
				SQLDebugging=""
				Environment=""
				EnvironmentMerge="true"
				DebuggerFlavor=""
				MPIRunCommand=""
				MPIRunArguments=""
				MPIRunWorkingDirectory=""
				ApplicationCommand=""
				ApplicationArguments=""
				ShimCommand=""
				MPIAcceptMode=""
				MPIAcceptFilter=""
			/>
		</Configuration>
	</Configurations>
</VisualStudioUserFile>"""
		file.write( fileStr % (VisualStudioDict['vcprojHeader'], workingDirectory, remoteMachine, workingDirectory, remoteMachine ) )


def vcprojAction( target, source, env ):

	# Retrieves template location
	templatePath = os.path.join( env.sbf.mySCONS_BUILD_FRAMEWORK, 'sbfTemplateMakefile.vcproj' )

	# Retrieves/computes additionnal informations
	targetName = str(target[0])
	sourceName = templatePath #str(source[0])

	myInstallDirectory = env.sbf.myInstallDirectory

	MSVSProjectBuildTarget			= ''
	MSVSProjectBuildTargetDirectory	= ''

	if len(env['sbf_bin']) > 0 :
		MSVSProjectBuildTarget = os.path.basename( env['sbf_bin'][0] )
		MSVSProjectBuildTargetDirectory = 'bin'
	elif len(env['sbf_lib_object']) > 0 :
		MSVSProjectBuildTarget = os.path.basename( env['sbf_lib_object'][0] )
		MSVSProjectBuildTargetDirectory = 'lib'
	else:
		# Nothing to debug (project of type 'none')
		return

	debugIndex = MSVSProjectBuildTarget.rfind( '_D.' )
	if debugIndex == -1 :
		# It's not a debug target
		MSVSProjectBuildTargetRelease	= MSVSProjectBuildTarget
		(filename, extension) = os.path.splitext(MSVSProjectBuildTarget)
		MSVSProjectBuildTargetDebug		= filename + '_D' + extension
	else :
		# It's a debug target
		MSVSProjectBuildTargetRelease	= MSVSProjectBuildTarget.replace('_D.', '.', 1)
		MSVSProjectBuildTargetDebug		= MSVSProjectBuildTarget

	# Generates project GUID
	# {7CB2C740-32F7-4EE3-BE34-B98DFD1CE0C1}
	# @todo moves import elsewhere
	import uuid
	env['sbf_projectGUID'] = '{%s}' % str(uuid.uuid4()).upper()
#	env['sbf_projectGUID'] = str(pythoncom.CreateGuid())

	# Creates new output file (vcproj)
	targetFile = open( targetName, 'w')

	# Opens template input file
	with open( sourceName ) as sourceFile :
		# Computes regular expressions
		customizePoint		= r"^#sbf"
		reCustomizePoint	= re.compile( customizePoint )
		re_sbfFileVersion			= re.compile( customizePoint + r"(.*)(sbfFileVersion)(.*)$" )
		re_sbfProjectName			= re.compile( customizePoint + r"(.*)(sbfProjectName)(.*)$" )
		re_sbfProjectGUID			= re.compile( customizePoint + r"(.*)(sbfProjectGUID)(.*)$" )
		re_sbfOutputDebug			= re.compile( customizePoint + r"(.*)(sbfOutputDebug)(.*)$" )
		re_sbfOutputRelease			= re.compile( customizePoint + r"(.*)(sbfOutputRelease)(.*)$" )
		re_sbfDefines				= re.compile( customizePoint + r"(.*)(sbfDefines)(.*)$" )
		re_sbfIncludeSearchPath		= re.compile( customizePoint + r"(.*)(sbfIncludeSearchPath)(.*)$" )
		re_sbfInclude				= re.compile( customizePoint + r"(.*)(sbfInclude)(.*)$" )
		re_sbfShare					= re.compile( customizePoint + r"(.*)(sbfShare)(.*)$" )
		re_sbfSrc					= re.compile( customizePoint + r"(.*)(sbfSrc)(.*)$" )
		re_sbfFiles					= re.compile( customizePoint + r"(.*)(sbfFiles)(.*)$" )

		for line in sourceFile :
			# Tests if the incoming line has a customization point, i.e. '#sbf' at the beginning.
			if reCustomizePoint.search( line ) is None :
				# Writes the line without any modifications
				targetFile.write( line )
			else :
				# The line must be customized

				# sbfFileVersion customization point
				res = re_sbfFileVersion.match(line)
				if res != None :
					newLine = res.group(1) + VisualStudioDict['vcprojHeader'] + res.group(3) + '\n'
					targetFile.write( newLine )
					continue

				# sbfProjectName customization point
				res = re_sbfProjectName.match(line)
				if res != None :
					newLine = res.expand(r"\1%s\3\n" % env['sbf_project'] )
					targetFile.write( newLine )
					continue

				# sbfProjectGUID customization point
				res = re_sbfProjectGUID.match(line)
				if res != None :
					newLine = res.expand( r"\1%s\3\n" % env['sbf_projectGUID'] )
					targetFile.write( newLine )
					continue

				# sbfOutputDebug customization point
				res = re_sbfOutputDebug.match(line)
				if res != None :
					outputDebug = os.path.join(	myInstallDirectory,
												MSVSProjectBuildTargetDirectory,
												MSVSProjectBuildTargetDebug )
					newLine = res.expand( r"\1%s\3\n" % outputDebug.replace('\\', '\\\\') )
					targetFile.write( newLine )
					continue

				# sbfOutputRelease customization point
				res = re_sbfOutputRelease.match(line)
				if res != None :
					outputRelease = os.path.join(	myInstallDirectory,
													MSVSProjectBuildTargetDirectory,
													MSVSProjectBuildTargetRelease )
					newLine = res.expand( r"\1%s\3\n" % outputRelease.replace('\\', '\\\\') )
					targetFile.write( newLine )
					continue

				# sbfDefines customization point
				res = re_sbfDefines.match(line)
				if res != None :
					# @todo OPTME computes defines only once
					defines = ''
					for define in env['CPPDEFINES'] :
						if isinstance( define, str ) :
							defines += define.replace('\"', '&quot;') + ';'
						else :
							defines += define[0] + "=" + define[1].replace('\"', '&quot;') + ';'
					newLine = res.expand( r"\1%s\3\n" % defines )
					targetFile.write( newLine )
					continue

				# sbfIncludeSearchPath customization point
				res = re_sbfIncludeSearchPath.match(line)
				if res != None :
					# Adds 'include' directory of all dependencies
# @todo Adds localext/include ?
# @todo a function (see same code in slnAction())
					projectsRoot = env.sbf.getProjectsRoot(env)
					depthFromProjectsRoot = computeDepth( convertPathAbsToRel(projectsRoot, env['sbf_projectPathName']) )
					relPathToProjectsRoot = "..\\" * depthFromProjectsRoot

					allDependencies = env.sbf.getAllDependencies( env )

					includeSearchPath = 'include;'
					for dependency in allDependencies:
						dependencyEnv = env.sbf.myParsedProjects[ dependency ]
						pathToInclude = getNormalizedPathname( os.path.join( dependencyEnv['sbf_projectPathName'], 'include' ) )
						if not os.path.exists(pathToInclude):
							# Skip project without 'include' sub-directory
							continue

						newPath = relPathToProjectsRoot + convertPathAbsToRel(projectsRoot, pathToInclude)
						includeSearchPath += newPath + ';'

					newLine = res.group(1) + includeSearchPath + res.group(3) + '\n'
					targetFile.write( newLine )
					continue

				# sbfInclude customization point
				res = re_sbfInclude.match(line)
				if res != None :
					vcprojWriteTree( targetFile, env['sbf_include'] )
					continue

				# re_sbfShare customization point
				res = re_sbfShare.match(line)
				if res != None :
					vcprojWriteTree( targetFile, env['sbf_share'] )
					continue

				# sbfSrc customization point
				res = re_sbfSrc.match(line)
				if res != None :
					vcprojWriteTree( targetFile, env['sbf_src'] )
					continue

				# sbfFiles customization point
				res = re_sbfFiles.match(line)
				if res != None :
					for file in env['sbf_files'] :
						targetFile.write( "\t\t<File RelativePath=\"%s\"></File>\n" % file );
					continue

				raise SCons.Errors.StopError, "Unexpected customization point in vcproj generation. The error occurs on the following line :\n%s" % line

		targetFile.close()



# Creates Visual Studio Solution file (.sln).
def slnAction( target, source, env ):
	# Retrieves/computes additional informations
	targetName = str(target[0])

	myProjectPathName	= env['sbf_projectPathName']
	myProject			= env['sbf_project']

	# Opens output file
	with open( targetName, 'w' ) as file :
		fileStr = VisualStudioDict['slnHeader'] + """%s
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|Win32 = Debug|Win32
		Release|Win32 = Release|Win32
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
	EndGlobalSection
	GlobalSection(SolutionProperties) = preSolution
		HideSolutionNode = FALSE
	EndGlobalSection
EndGlobal
"""
		# Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "vgsdkTestGtk", "vgsdkTestGtk.vcproj", "{D09E3669-F458-4EDB-90F9-F8E1BD99428C}"
		projectStr = """Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "%s", "%s", "%s"
EndProject
"""

		# Adds all dependencies
		projectsRoot = env.sbf.getProjectsRoot(env)
		depthFromProjectsRoot = computeDepth( convertPathAbsToRel(projectsRoot, myProjectPathName) )
		relPathToProjectsRoot = "..\\" * depthFromProjectsRoot

		allDependencies = env.sbf.getAllDependencies( env )

		ProjectEndProjectSection = ''
		for dependency in allDependencies + [myProject]:
			dependencyEnv = env.sbf.myParsedProjects[ dependency ]
# @todo vgBase (no GUID) should not by skipped and sbf (not in deps) ?
			if 'sbf_projectGUID' not in dependencyEnv:
				#print ('Skip %s' % dependencyEnv['sbf_project'] )
				continue

			pathToVcprojFile = getNormalizedPathname( os.path.join( dependencyEnv['sbf_projectPathName'], dependencyEnv['sbf_project'] + '.vcproj' ) )

			ProjectEndProjectSection += projectStr % (
												dependencyEnv['sbf_project'],
												relPathToProjectsRoot + convertPathAbsToRel(projectsRoot, pathToVcprojFile),
												dependencyEnv['sbf_projectGUID'] )

		file.write( fileStr % ProjectEndProjectSection )



if	'vcproj_build' in env.sbf.myBuildTargets or \
	'vcproj' in env.sbf.myBuildTargets or \
	'vcproj_clean' in env.sbf.myBuildTargets or \
	'vcproj_mrproper' in env.sbf.myBuildTargets :

	if	'vcproj_clean' in env.sbf.myBuildTargets or \
		'vcproj_mrproper' in env.sbf.myBuildTargets :
		env.SetOption('clean', 1)

	# Retrieves informations
	import getpass
	import platform
	user			= getpass.getuser()
	remoteMachine	= platform.node()

	vcprojDebugFilePostFix = "." + remoteMachine + "." + user + ".user"

	# Configures VisualStudioDict
	if env.sbf.myCC == 'cl':
		if env.sbf.myCCVersionNumber >= 9.000000 :
			VisualStudioDict['slnHeader']			= VisualStudioDict['slnHeader9']
			VisualStudioDict['vcprojHeader']		= VisualStudioDict['vcprojHeader9']
		elif env.sbf.myCCVersionNumber >= 8.000000 :
			VisualStudioDict['slnHeader']			= VisualStudioDict['slnHeader8']
			VisualStudioDict['vcprojHeader']		= VisualStudioDict['vcprojHeader8']
		else:
			raise SCons.Errors.UserError( "Unsupported cl compiler version: %i" % env.sbf.myCCVersionNumber )
	else:
		# Uses cl8-0 by default
		VisualStudioDict['slnHeader']			= VisualStudioDict['slnHeader8']
		VisualStudioDict['vcprojHeader']		= VisualStudioDict['vcprojHeader8']

	# target vcproj_build
	for projectName in env.sbf.myBuiltProjects:
		lenv			= env.sbf.myBuiltProjects[projectName]
		projectPathName	= lenv['sbf_projectPathName']
		project			= lenv['sbf_project']

		output1			= getNormalizedPathname( projectPathName + os.sep + project + '.vcproj' )
		output2			= output1 + vcprojDebugFilePostFix
		slnOutput		= getNormalizedPathname( projectPathName + os.sep + project + '.sln' )

		#
		env.Alias( 'vcproj_build', lenv.Command('vcproj_build_%s.out' % project, 'dummy.in', Action( nopAction, printVisualStudioProjectBuild ) ) )

		# Creates the project file (.vcproj)
		env.Alias( 'vcproj_build', lenv.Command( output1, 'dummy.in', Action( vcprojAction, printGenerate) ) )

		# Creates project file (.vcproj) containing informations about the debug session.
		env.Alias( 'vcproj_build', lenv.Command( output2, 'dummy.in', Action( vcprojDebugFileAction, printGenerate) ) )

		env.AlwaysBuild( [ output1, output2 ] )

		# Creates the solution file (.sln)
		env.Alias( 'sln_build', lenv.Command('sln_build_%s.out' % project, 'dummy.in', Action( nopAction, printVisualStudioSolutionBuild ) ) )
		env.Alias( 'sln_build', lenv.Command( slnOutput, 'dummy.in', Action( slnAction, printGenerate) ) )
		env.AlwaysBuild( slnOutput )

	env.Alias( 'vcproj', ['vcproj_build', 'sln_build'] )
# @todo Removes .ncb and .suo
	env.Alias( 'vcproj_clean', 'vcproj' )
	env.Alias( 'vcproj_mrproper', 'vcproj_clean' )



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
	for projectName in env.sbf.myParsedProjects :

		localenv = env.sbf.myParsedProjects[projectName]
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
	file.write( 'PROJECT_NAME		= "%s"\n'					% env.sbf.myProject )
	file.write( 'PROJECT_NUMBER		= "%s generated at %s"\n'	% (env.sbf.myVersion, env.sbf.myDateTime) )
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
if (	('dox_build' in env.sbf.myBuildTargets) or
		('dox_install' in env.sbf.myBuildTargets) or
		('dox' in env.sbf.myBuildTargets) or
		('dox_clean' in env.sbf.myBuildTargets) or
		('dox_mrproper' in env.sbf.myBuildTargets)	):

	if (	('dox_clean' in env.sbf.myBuildTargets) or
			('dox_mrproper' in env.sbf.myBuildTargets)	):
		env.SetOption('clean', 1)

	#@todo use other doxyfile(s). see doxInputDoxyfile
	doxInputDoxyfile		= os.path.join(env.sbf.mySCONS_BUILD_FRAMEWORK, 'doxyfile')
	doxOutputPath			= os.path.join(env.sbf.myBuildPath, 'doxygen', env.sbf.myProject, env.sbf.myVersion )
	doxOutputCustomDoxyfile	= os.path.join(doxOutputPath, 'doxyfile.sbf')

	doxBuildPath			= os.path.join(doxOutputPath, 'doxyfile.sbf_build')
	doxInstallPath			= os.path.join(env.sbf.myInstallDirectory, 'doc', env.sbf.myProject, env.sbf.myVersion)

	# target dox_build
	commandGenerateDoxyfile = env.Command( doxOutputCustomDoxyfile, doxInputDoxyfile, Action(doxyfileAction, printDoxygenBuild) )
	env.Alias( 'dox_build', commandGenerateDoxyfile	)
	commandCompileDoxygen = env.Command( 'dox_build.out2', 'dummy.in', 'doxygen ' + doxOutputCustomDoxyfile )
	env.Alias( 'dox_build', commandCompileDoxygen )
	env.AlwaysBuild( [commandGenerateDoxyfile, commandCompileDoxygen] )

	# target dox_install
	dox_install_cmd = env.Command( os.path.join(doxInstallPath,'dummy.out'), os.path.join(doxBuildPath, 'html'), Action(syncAction, printDoxygenInstall) )
	env.Alias( 'dox_install', [	'dox_build', dox_install_cmd ] )
	env.AlwaysBuild( dox_install_cmd )
	env.Depends( dox_install_cmd, 'dox_build' )

	if env['publishOn'] :
		# @todo print message
		rsyncAction = env.createRsyncAction( 'doc_%s_%s' % (env.sbf.myProject, env.sbf.myVersion), Dir(os.path.join(doxBuildPath, 'html')) )

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

#print (datetime.datetime.now() - sbfMainBeginTime).microseconds/1000
