# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import getpass
import platform

# To be able to use this file without SCons
try:
	from SCons.Script import *
except ImportError as e:
	print ('sbfWarning: unable to import SCons.Script')

from src.sbfFiles import convertPathAbsToRel
from src.sbfPackagingSystem import PackagingSystem
from src.sbfUtils import stringFormatter
from src.sbfUses import UseRepository
from src.sbfVersion import splitUsesName
from src.SConsBuildFramework import printEmptyLine, stringFormatter


def __printGeneratingInfofile( target, source, lenv ) :
	return stringFormatter(lenv, 'Generating {0} for {1}'.format( str(os.path.basename(target[0].abspath)), lenv['sbf_projectPathName'] ))

def __doTargetInfoFile( target, source, env ):
	"""Creates info.sbf file containing informations about the current project and its dependencies."""
	# Retrieves/computes additional informations
	sbf = env.sbf
	pakSystem = PackagingSystem(sbf)
	targetName = str(target[0])

	# Opens output file
	with open( targetName, 'w' ) as file :
		# Prints startup message
		startupMessage = 'Informations about {0}'.format(env['sbf_project'] )
		file.write( startupMessage + '\n' )
		file.write( '-' * len(startupMessage) + '\n\n' )
		file.write( '{0} version {1}\n'.format( env['sbf_project'], env['version'].replace('-','.') ) )
		file.write( 'built {0} on computer {1} by user {2}\n'.format( sbf.myDateTimeForUI, platform.node(), getpass.getuser() ) )
		file.write( 'svn revision: {0}'.format( sbf.myVcs.getRevision(env['sbf_projectPathName']) ) )
		file.write( '\n'*3 )
# @todo others svn info ?

		# Computes common root of projects
		rootOfProjects = sbf.getProjectsRoot( env )

		# Retrieves informations
		dependencies = sbf.getAllDependencies(env)
		uses = sorted(list(sbf.getAllUses(env)))

		# Prints informations about 'uses'
		lenColPackage = env['outputLineLength'] * 25 / 100
		lenColVersion = env['outputLineLength'] * 15 / 100
		lenColRepo = env['outputLineLength'] * 60 / 100
		file.write('{0}{1}\n'.format( 'Package'.ljust(lenColPackage), 'Version'.ljust(lenColVersion) ))
		file.write('{0}{1}\n'.format( '-------'.ljust(lenColPackage), '-------'.ljust(lenColVersion) ))
		for useNameVersion in uses:
			useName, useVersion = splitUsesName( useNameVersion )
			# Test if package useName is installed
			if pakSystem.isInstalled(useName):
				# installed
				oPakInfo = {}
				pakSystem.loadPackageInfo( useName, oPakInfo )
				if useVersion == oPakInfo['version']:
					pass
				else:
					print ( '{0} {1} is NOT installed !!!'.format(useName, useVersion) )
					Exit(1)
			else:
				# not installed
				use = UseRepository.getUse( useName )
				if use:
					if use.getPackageType() in ['Normal', 'Full']:
						print ( '{0} {1} is NOT installed !!!'.format(useName, useVersion) )
						Exit(1)
					else:
						assert( use.getPackageType() in ['None', 'NoneAndNormal'] )
						# nothing to do
				#else nothing to do
			file.write( '{0}{1}\n'.format(useName.ljust(lenColPackage), useVersion.ljust(lenColVersion)) )
		else:
			file.write('\n'*3)

		# Prints informations about projects
		outputLineLength = env['outputLineLength']
		lenColProject = outputLineLength * 45 / 100
		lenColType = max( outputLineLength * 5 / 100, 6 )
		lenColUses = outputLineLength * 50 / 100
		file.write( '{0}{1}{2}\n'.format( 'Project path '.ljust(lenColProject), 'Type'.ljust(lenColType), 'uses/stdlibs'.ljust(lenColUses) ) )
		file.write( '{0}{1}{2}\n'.format( '-------------'.ljust(lenColProject), '----'.ljust(lenColType), '------------'.ljust(lenColUses) ) )

		for project in [env['sbf_project']] + dependencies:
			projectEnv = sbf.getEnv(project)

			typeOfProject = projectEnv['type']
			if typeOfProject == 'none':	typeOfProject = 'meta'

			projectPathName = projectEnv['sbf_projectPathName']

			projectRelPath = convertPathAbsToRel( rootOfProjects, projectPathName )
			if len(projectRelPath)==0:	projectRelPath = projectEnv['sbf_project']

			# Adds vcs branch and revision informations to project path (path/branch@revision)
			if projectEnv['vcsUse'] == 'yes':
				url = sbf.myVcs.getSplitUrl( projectPathName )
				projectRelPath += '{0}@{1}'.format( url[2], url[3])
			else:
				projectRelPath += '@{0}'.format( str(sbf.myVcs.getRevision(projectPathName)) )
			projectRelPath = projectRelPath.replace('\\', '/')

			libs = ''
			for useNameVersion in projectEnv['uses']:
				useName, useVersion = splitUsesName( useNameVersion )
				if useVersion:
					libs += ' {0}({1})'.format( useName, useVersion )
				else:
					libs += ' {0}'.format( useName )
			for lib in projectEnv['stdlibs']:
				libs += ' {0} '.format( lib )

			file.write( '{0}{1}{2}\n'.format( projectRelPath.ljust(lenColProject), typeOfProject.ljust(lenColType), libs.ljust(lenColUses) ) )
		else:
			file.write('\n')



def __doTargetInfo( target, source, env ):
	# Retrieves additional informations
	sourceName = str(source[0])

	# Prints source
	with open(sourceName) as file:
		for line in file:
			print line,



def configureInfofileTarget( lenv, forced = False ):
	"""Alias 'infofile' and lenv['sbf_info']"""

	# Target 'infofile'
	sbf = lenv.sbf
	if forced or lenv['generateInfoFile']:
		# Must generate info.sbf file for this project (forced or option 'generateInfoFile').
		projectPathName	= lenv['sbf_projectPathName']
		project			= lenv['sbf_project']
		# info.sbf is generated at the root of the project build directory
		infoFile = os.path.join( sbf.myProjectBuildPathExpanded, 'info.sbf' )
		Alias( 'infofile', lenv.Command( infoFile, 'dummy.in', lenv.Action( __doTargetInfoFile, __printGeneratingInfofile ) ) )
		lenv.AlwaysBuild( infoFile )
		lenv['sbf_info'] = [infoFile]

def configureInfoTarget( lenv ):
	# Target 'info'
	if 'info' in lenv.sbf.myBuildTargets:
		Alias( 'info', lenv.Command( 'dummyInfo.out', lenv['sbf_info'], lenv.Action( __doTargetInfo, printEmptyLine ) ) )
