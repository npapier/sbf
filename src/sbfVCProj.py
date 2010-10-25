# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from __future__ import with_statement

from SCons.Script import *

from SConsBuildFramework import nopAction, printGenerate, stringFormatter
from src.sbfFiles import computeDepth, convertPathAbsToRel, getNormalizedPathname

import os
import re

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
							defines += define[0] + "=" + str(define[1]).replace('\"', '&quot;') + ';'
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



def configureVCProjTarget( env ):
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
