# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, Nicolas Papier.
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

import distutils.archive_util
#import glob
import os
import string
import sys

from SCons.Script.SConscript import SConsEnvironment
import SCons.Errors

from sbfFiles		import *
from src.sbfUses	import uses
from src.sbfUtils	import *
from src.SConsBuildFramework import stringFormatter









###### Archiver action ######
def zipArchiver( target, source, env ) :
	targetName = str(target[0])
	sourceName = str(source[0])
	distutils.archive_util.make_archive( targetName, 'zip', sourceName )

def printZipArchiver( target, source, env ) :
	targetName = str(target[0])
	sourceName = str(source[0])
	return "=> Create %s with files from %s" % (targetName, sourceName)


###### Action function for sbfCheck target #######
def sbfCheck(target = None, source = None, env = None) :
	print stringFormatter( env, 'Availability and version of tools' )

	print 'python version : ',
	env.Execute( '@python -V' )
	print

	print 'Version of python used by scons :', sys.version
	print

	print 'scons version :'
	env.Execute( '@scons -v' )
	print

	#@todo pysvn should be optionnal
	import pysvn
	print 'pysvn version: %d.%d.%d-%d' % (pysvn.version[0], pysvn.version[1], pysvn.version[2], pysvn.version[3])
	if len(pysvn.svn_version[3]) == 0 :
		print 'svn version (for pysvn): %d.%d.%d\n' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2])
	else :
		print 'svn version (for pysvn): %d.%d.%d-%s\n' % (pysvn.svn_version[0], pysvn.svn_version[1], pysvn.svn_version[2], pysvn.svn_version[3])

	print 'svn version : ',
	env.Execute( '@svn --version --quiet' )
	print

	env.Execute( checkCC, nopAction )
	print

	print 'doxygen version : ',
	env.Execute( '@doxygen --version' )
	print

	#@todo others tools (ex : swig, ...)
	#@todo Adds checking for the existance of tools (svn, doxygen...)

	printSBFVersion()
	print

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
					print 'sbfInfo: SCONS_BUILD_FRAMEWORK is perfectly defined (existing path, well written and is the main directory of SConsBuildFramework)'
				else :
					print 'sbfInfo: SConsBuildFramework not found at ', sbf_root_normalized
		else :
			print 'sbfInfo: the path defining by SCONS_BUILD_FRAMEWORK is automatically normalized. Try to normalize it yourself.'
			print 'sbfInfo: the normalized SCONS_BUILD_FRAMEWORK=', sbf_root_normalized


def checkCC(target = None, source = None, env = None) :
	print 'Current default compiler :', env['CC']

	if ( env['CC'] == 'cl' ) :
		#ccVersionAction		= Action( 'cl /help' )
		print 'cl version :', env['MSVS']['VERSION']
		print 'The available versions of cl installed are ', env['MSVS']['VERSIONS']

	print
	print 'gcc version : ',
	env.Execute( '@gcc -dumpversion' )


def printSBFVersion() :
	print 'SConsBuildFramework version : %s' % getSBFVersion()


def getSBFVersion() :
	# Retrieves and normalizes SCONS_BUILD_FRAMEWORK
	sbfRoot = getNormalizedPathname( os.getenv('SCONS_BUILD_FRAMEWORK') )

	# Reads version number in VERSION file
	versionFile	= os.path.join(sbfRoot, 'VERSION')
	if os.path.lexists( versionFile ) :
		with open( versionFile ) as file :
			return file.readline()
	else :
		return "Missing %s file. So version number is unknown." % versionFile



from src.SConsBuildFramework import SConsBuildFramework, nopAction

###### Initial environment ######
#

# create objects
# HINTS: to propagate the entire external environment to the execution environment for commands : ENV = os.environ

#Export('env') not needed.

EnsurePythonVersion(2, 5)
EnsureSConsVersion(1, 0, 0)

SConsEnvironment.sbf = SConsBuildFramework()
env = SConsEnvironment.sbf.myEnv # TODO remove me (this line is just for compatibility with the old global env)
# Prints current 'config' option
print "\nConfiguration: %s\n" % env['config']

# Dumping construction environment (for debugging).																	# TODO : a method printDebugInfo()
#env.Dump()

# target 'sbfCheck'
Alias('sbfCheck', env.Command('dummyCheckVersion.out1', 'dummy.in', Action( sbfCheck, nopAction ) ) )

# build project from launch directory (and all dependencies recursively)
env['sbf_launchDir'			]	= getNormalizedPathname( os.getcwd() )
env['sbf_projectPathName'	]	= env['sbf_launchDir']
env['sbf_projectPath'		]	= os.path.dirname(env['sbf_launchDir'])
env['sbf_project'			]	= os.path.basename(env['sbf_launchDir'])

env.sbf.buildProject( env['sbf_projectPathName'] )


### special targets: svnCheckout svnUpdate ###

Alias( 'svnCheckout', Command('dummySvnCheckout.main.out1', 'dummy.in', Action( nopAction, nopAction ) ) )
Alias( 'svnUpdate', Command('dummySvnUpdate.main.out1', 'dummy.in', Action( nopAction, nopAction ) ) )
#Alias( 'svnCheckout', env.Command('dummySvnCheckout.out1', 'dummy.in', Action( nopAction, nopAction ) ) )
#Alias( 'svnUpdate', env.Command('dummySvnUpdate.out1', 'dummy.in', Action( nopAction, nopAction ) ) )


### special target : vcproj ###
from src.SConsBuildFramework import printGenerate

# @todo Creates a new python file for vcproj stuffs and embedded file sbfTemplateMakefile.vcproj
# @todo Generates section "Header Files", "Share Files" and "Source Files" only if not empty.
# @todo Generates sln
# @todo Configures localExt include path.
# @todo Generates vcproj but with c++ project and not makefile project.
# @todo Generates eclipse cdt project.

def printVisualStudioProjectStage( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Visual Studio Project generation stage" ) + '\n'

def printVisualStudioProjectBuild( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Build %s Visual Studio Project" % localenv['sbf_project'] )
#	return "---- Build %s Visual Studio Project ----\n---- from %s ----" % (localenv['sbf_project'], localenv['sbf_projectPath'])



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
	Version="8,00"
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
		file.write( fileStr % (workingDirectory, remoteMachine, workingDirectory, remoteMachine ) )


def vcprojAction( target, source, env ) :

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
	else :
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

	# Creates new output file (vcproj)
	targetFile = open( targetName, 'w')

	# Opens template input file
	with open( sourceName ) as sourceFile :
		# Computes regular expressions
		customizePoint		= r"^#sbf"
		reCustomizePoint	= re.compile( customizePoint )
		re_sbfProjectName		= re.compile( customizePoint + r"(.*)(sbfProjectName)(.*)$" )
		re_sbfProjectPathName	= re.compile( customizePoint + r"(.*)(sbfProjectPathName)(.*)$" )
		re_sbfOutputDebug		= re.compile( customizePoint + r"(.*)(sbfOutputDebug)(.*)$" )
		re_sbfOutputRelease		= re.compile( customizePoint + r"(.*)(sbfOutputRelease)(.*)$" )
		re_sbfDefines			= re.compile( customizePoint + r"(.*)(sbfDefines)(.*)$" )
		re_sbfInclude			= re.compile( customizePoint + r"(.*)(sbfInclude)(.*)$" )
		re_sbfShare				= re.compile( customizePoint + r"(.*)(sbfShare)(.*)$" )
		re_sbfSrc				= re.compile( customizePoint + r"(.*)(sbfSrc)(.*)$" )
		re_sbfFiles				= re.compile( customizePoint + r"(.*)(sbfFiles)(.*)$" )

		for line in sourceFile :
			# Tests if the incoming line has a customization point, i.e. '#sbf' at the beginning.
			if reCustomizePoint.search( line ) is None :
				# Writes the line without any modifications
				targetFile.write( line )
			else :
				# The line must be customized

				# sbfProjectName customization point
				res = re_sbfProjectName.match(line)
				if res != None :
					newLine = res.expand(r"\1%s\3\n" % env['sbf_project'] )
					targetFile.write( newLine )
					continue

				# sbfProjectPathName customization point
				res = re_sbfProjectPathName.match(line)
				if res != None :
					newLine = res.expand( r"\1%s\3\n" % env['sbf_projectPathName'].replace('\\', '\\\\') )
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
							defines += define + ';'
						else :
							defines += define[0] + "=" + define[1].replace('\"', '&quot;') + ';'
					newLine = res.expand( r"\1%s\3\n" % defines )
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

	#
	env.Alias( 'vcproj_build_print', env.Command('vcproj_build_print.out1', 'dummy.in', Action( nopAction, printVisualStudioProjectStage ) ) )

	# target vcproj_build
	env.Alias( 'vcproj_build', 'vcproj_build_print' )

	for projectName in env.sbf.myParsedProjects :
		lenv			= env.sbf.myParsedProjects[projectName]
		projectPathName	= lenv['sbf_projectPathName']
		project			= lenv['sbf_project']
		output1			= getNormalizedPathname( projectPathName + os.sep + project + '.vcproj' )
		output2			= output1 + vcprojDebugFilePostFix
		env.Alias( 'vcproj_build', lenv.Command('vcproj_build_%s.out' % project, 'dummy.in', Action( nopAction, printVisualStudioProjectBuild ) ) )
		# Creates the project file (.vcproj)
		env.Alias( 'vcproj_build', lenv.Command( output1, 'dummy.in', Action( vcprojAction, printGenerate) ) )
		# Creates project file (.vcproj) containing informations about the debug session.
		env.Alias( 'vcproj_build', lenv.Command( output2, 'dummy.in', Action( vcprojDebugFileAction, printGenerate) ) )
		env.AlwaysBuild( [ output1, output2 ] )

	env.Alias( 'vcproj', 'vcproj_build' )
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


if (	('dox_build' in env.sbf.myBuildTargets) or
		('dox_install' in env.sbf.myBuildTargets) or
		('dox' in env.sbf.myBuildTargets) or
		('dox_clean' in env.sbf.myBuildTargets) or
		('dox_mrproper' in env.sbf.myBuildTargets)	):

	if (	('dox_clean' in env.sbf.myBuildTargets) or
			('dox_mrproper' in env.sbf.myBuildTargets)	):
		env.SetOption('clean', 1)

	env.Alias( 'dox_build_print', env.Command('dox_build_print.out1', 'dummy.in', Action( nopAction, printDoxygenBuild ) ) )

	#@todo use other doxyfile(s). see doxInputDoxyfile
	doxInputDoxyfile		= os.path.join(env.sbf.mySCONS_BUILD_FRAMEWORK, 'doxyfile')
	doxOutputPath			= os.path.join(env.sbf.myBuildPath, env.sbf.myProject, 'doxygen', env.sbf.myVersion )
	doxOutputCustomDoxyfile	= os.path.join(doxOutputPath, 'doxyfile.sbf')

	doxBuildPath			= os.path.join(doxOutputPath, 'doxyfile.sbf_build')
	doxInstallPath			= os.path.join(env.sbf.myInstallDirectory, 'doc', env.sbf.myProject, env.sbf.myVersion)

	# target dox_build
	env.Alias( 'dox_build', 'dox_build_print' )
	env.Alias( 'dox_build', env.Command( doxOutputCustomDoxyfile, doxInputDoxyfile, Action(doxyfileAction, nopAction) )	)
	env.AlwaysBuild( doxOutputCustomDoxyfile )
	env.Alias( 'dox_build', env.Command( 'dox_build.out2', 'dummy.in', 'doxygen ' + doxOutputCustomDoxyfile )	)

	# target dox_install
	env.Alias( 'dox_install_print', env.Command('dox_install_print.out1', 'dummy.in', Action( nopAction, printDoxygenInstall ) ) )
	env.Alias( 'dox_install', 'dox_build' )
	env.Alias( 'dox_install', 'dox_install_print' )
	env.Alias( 'dox_install', env.Command( os.path.join(doxInstallPath,'dummy.out'), doxBuildPath, Action(syncAction, nopAction) )	)

	# target dox
	env.Alias( 'dox', 'dox_install' )

	# target dox_clean
	env.Alias( 'dox_clean', 'dox' )
	env.Clean( 'dox_clean', doxOutputPath )

	# target dox_mrproper
	env.Alias( 'dox_mrproper', 'dox_clean' )
	env.Clean( 'dox_mrproper', doxInstallPath )


### special zip related targets : zipRuntime, zipDeps, zipPortable, zipDev, zipSrc and zip ###
# @todo zip*_[build,install,clean,mrproper]
# @todo zip doxygen

from src.sbfSubversion import svnGetAllVersionedFiles
from src.sbfUses import UseRepository


def printZip( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create zip archives" )

def printZipRuntime( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create runtime package" )

def printZipDeps( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create deps package" )

def printZipPortable( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create portable package" )

def printZipDev( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create dev package" )

def printZipSrc( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create src package" )



if (	('zipRuntime'		in env.sbf.myBuildTargets) or
		('zipDeps'			in env.sbf.myBuildTargets) or
		('zipPortable'		in env.sbf.myBuildTargets) or
		('zipDev'			in env.sbf.myBuildTargets) or
		('zipSrc'			in env.sbf.myBuildTargets) or
		('zip'				in env.sbf.myBuildTargets)	) :
																							# FIXME: lazzy scons env construction => TODO: generalize (but must be optional)
	# Create a builder to zip files
	import SCons																			# from SCons.Script.SConscript import SConsEnvironment
	zipBuilder = env.Builder(	action=Action(zipArchiver,printZipArchiver),
								source_factory=SCons.Node.FS.default_fs.Entry,
								target_factory=SCons.Node.FS.default_fs.Entry,
								multi=0 )
	env['BUILDERS']['zipArchiver'] = zipBuilder

	sbf = env.sbf
	rootProjectEnv = sbf.myParsedProjects[env['sbf_project']]

	# compute zipPath (where files are copying before creating the zip file)
	# zipPathBase = /mnt/data/sbf/build/pak/vgsdk_0-4
	zipPathBase	=	os.path.join( sbf.myBuildPath, 'pak', env['sbf_project'] + '_' + rootProjectEnv['version'] )

	# zipPath = zipPathBase + "_win32_cl7-1_D"
	zipPath		=	zipPathBase + sbf.my_Platform_myCCVersion + sbf.my_FullPostfix

	#_dev_2005_08_09
	runtimeZipPath	= zipPath		+ '_runtime_'	+ sbf.myDate
	depsZipPath		= zipPath		+ '_deps_'		+ sbf.myDate
	portableZipPath	= zipPath		+ '_portable_'	+ sbf.myDate
	devZipPath		= zipPath		+ '_dev_'		+ sbf.myDate
	srcZipPath		= zipPathBase	+ '_src_'		+ sbf.myDate

	#
	Alias( 'zip_print', env.Command('zip_print.out1', 'dummy.in', Action( nopAction, printZip ) ) )
	AlwaysBuild( 'zip_print' )

	Alias( 'zipRuntime_print',	env.Command('zipRuntime_print.out1','dummy.in',	Action( nopAction, printZipRuntime ) ) )
	Alias( 'zipDeps_print',		env.Command('zipDeps_print.out1','dummy.in',	Action( nopAction, printZipDeps ) ) )
	Alias( 'zipPortable_print',	env.Command('zipPortable_print.out1','dummy.in',Action( nopAction, printZipPortable ) ) )
	Alias( 'zipDev_print',		env.Command('zipDev_print.out1',	'dummy.in',	Action( nopAction, printZipDev ) ) )
	Alias( 'zipSrc_print',		env.Command('zipSrc_print.out1',	'dummy.in',	Action( nopAction, printZipSrc ) ) )

	Alias( 'zipRuntime',	['build', 'zip_print', 'zipRuntime_print'] )
	Alias( 'zipDeps',		['build', 'zip_print', 'zipDeps_print'] )
	Alias( 'zipPortable',	['build', 'zip_print', 'zipPortable_print'] )
	Alias( 'zipDev',		['build', 'zip_print', 'zipDev_print'] )
	Alias( 'zipSrc',		['build', 'zip_print', 'zipSrc_print'] )

	# Computes common root of all projects
	projectPathNameList = []
	for projectName in sbf.myParsedProjects :
		lenv = sbf.myParsedProjects[projectName]
		projectPathNameList.append( lenv['sbf_projectPathName'] )

	rootOfProjects = getNormalizedPathname( os.path.commonprefix( projectPathNameList ) )
#print "rootOfProjects=", rootOfProjects
	# Collects files to create the zip
	runtimeZipFiles 	= []
	depsZipFiles		= []
	portableZipFiles	= []
	devZipFiles			= []
	srcZipFiles			= []

	usesSet				= set()

	for projectName in sbf.myParsedProjects :
		lenv			= sbf.myParsedProjects[projectName]
		projectPathName	= lenv['sbf_projectPathName']
		project			= lenv['sbf_project']

		# Adds files to runtime and portable zip
		runtimeZipFiles		+= Install(	os.path.join(runtimeZipPath, 'bin'),	lenv['sbf_bin'] )
		runtimeZipFiles		+= Install(	os.path.join(runtimeZipPath, 'bin'),	lenv['sbf_lib_object'] )
		portableZipFiles	+= Install(	os.path.join(portableZipPath, 'bin'),	lenv['sbf_bin'] )
		portableZipFiles	+= Install(	os.path.join(portableZipPath, 'bin'),	lenv['sbf_lib_object'] )

		if len(lenv['sbf_share']) > 0:
			runtimeDestPath		= os.path.join(runtimeZipPath, 'share', project, lenv['version'])
			portableDestPath	= os.path.join(portableZipPath, 'share', project, lenv['version'])
			for file in lenv['sbf_share'] :
				runtimeZipFiles += InstallAs(	file.replace('share', runtimeDestPath, 1),
												os.path.join(projectPathName, file) )
				portableZipFiles+= InstallAs(	file.replace('share', portableDestPath, 1),
												os.path.join(projectPathName, file) )

		# Adds files to deps zip
#		print ("Dependencies (only 'uses' option) for %s :" % project), lenv['uses']

		for element in lenv['uses']:
#			if element not in usesSet:
#				print ("Found a new dependency : %s" % element)
			usesSet.add( element )

		# Adds files to dev zip
		devZipFiles += Install(		os.path.join(devZipPath, 'bin'),			lenv['sbf_bin'] )

		for file in lenv['sbf_include'] :
			devZipFiles += InstallAs(	os.path.join(devZipPath, file),		os.path.join(projectPathName, file) )

		devZipFiles += Install( os.path.join(devZipPath, 'lib'), lenv['sbf_lib_object'] )
		devZipFiles += Install( os.path.join(devZipPath, 'lib'), lenv['sbf_lib_object_for_developer'] )

		# Adds files to src zip
		if lenv['vcsUse'] == 'yes' :
			allFiles = svnGetAllVersionedFiles( projectPathName )

			projectRelPath = convertPathAbsToRel( rootOfProjects, projectPathName )

			for absFile in allFiles :
				relFile = convertPathAbsToRel( projectPathName, absFile )
				srcZipFiles += lenv.InstallAs( os.path.join(srcZipPath, projectRelPath, relFile), absFile )
		# else nothing to do

	# Processes external dependencies
	listOfExternalDependencies = sorted(list(usesSet))
#print ("List of external dependencies for %s :" % env['sbf_project'])

	# For each external dependency, do
	for useNameVersion in listOfExternalDependencies:
		# Extracts name and version of incoming external dependency
		useName, useVersion = UseRepository.extract( useNameVersion )
#print ("%s = %s, %s" %(useNameVersion, useName, useVersion))

		# Retrieves use object for incoming dependency
		use = UseRepository.getUse( useName )
		if use != None :
			# Retrieves LIBS of incoming dependency
			libs = use.getLIBS( useVersion )
			if libs != None and len(libs) == 2:
				extension = env['SHLIBSUFFIX']

				# Computes the search path list where libraries could be located
				searchPathList = [os.path.join( sbf.myInstallExtPaths[0], 'lib' )]		# @todo support of len(myInstallExtPaths) > 1
				print "searchPathList", searchPathList
				libpath = use.getLIBPATH( useVersion )
				if (libpath != None) and (len(libpath) > 0 ) :
					searchPathList += libpath
				print "searchPathList", searchPathList

				# For each library, do
				for file in libs[1]:
					fileExtension = file + extension
					for path in searchPathList :
						sourceFile = os.path.join(path, fileExtension)
						print "sourceFile=", sourceFile
						if os.path.isfile( sourceFile ):
	#print ( "Found file : %s" % sourceFile )
							depsZipFiles		+= Install( os.path.join(depsZipPath, 'bin'), sourceFile )
							portableZipFiles	+= Install( os.path.join(portableZipPath, 'bin'), sourceFile )
							break
					else:
						raise SCons.Errors.UserError( "File %s not found." % sourceFile )
			else:
				raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (useNameVersion, sbf.myPlatform) )

	runtimeZipFiles		+= env.zipArchiver( runtimeZipPath + '_pak',	runtimeZipPath )
	depsZipFiles		+= env.zipArchiver( depsZipPath + '_pak',		depsZipPath )
	portableZipFiles	+= env.zipArchiver( portableZipPath + '_pak',	portableZipPath )
	devZipFiles			+= env.zipArchiver( devZipPath + '_pak',		devZipPath )
	srcZipFiles			+= env.zipArchiver(	srcZipPath + '_pak',		srcZipPath )

	Alias( 'zipRuntime',	runtimeZipFiles )
	Alias( 'zipDeps',		depsZipFiles )
	Alias( 'zipPortable',	portableZipFiles )
	Alias( 'zipDev',		devZipFiles )
	Alias( 'zipSrc',		srcZipFiles )

	Alias( 'zip', ['zipRuntime', 'zipDeps', 'zipPortable', 'zipDev', 'zipSrc'] )

#@todo function
#import shutil
#if ( os.path.ismount(srcZipPath) ) :
#	print 'sbfError: Try to use %s as an installation/desinstallation directory. Stop action to prevent any unwanted file destruction'
#else:
#	shutil.rmtree( srcZipPath, True )
#endtodo
