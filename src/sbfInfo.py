# SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import getpass
import platform

from SCons.Script import *

from src.sbfFiles import convertPathAbsToRel
from src.sbfPackagingSystem import PackagingSystem
from src.sbfUses import UseRepository
from src.SConsBuildFramework import printEmptyLine, printGenerate, stringFormatter



# Creates info.sbf file containing informations about the current project and its dependencies.
def doTargetInfoFile( target, source, env ):
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
		file.write('{0}{1}{2}\n'.format( 'Package'.ljust(lenColPackage), 'Version'.ljust(lenColVersion), 'Repository'.ljust(lenColRepo) ))
		file.write('{0}{1}{2}\n'.format( '-------'.ljust(lenColPackage), '-------'.ljust(lenColVersion), '----------'.ljust(lenColRepo) ))
		for useNameVersion in uses:
			useName, useVersion = UseRepository.extract( useNameVersion )
			use = UseRepository.getUse( useName )
			packageFile = '{0}{1}{2}.zip'.format(useName, useVersion, sbf.my_Platform_myCCVersion)
	# @todo checks if use is supported for my platform, config, cc version...
	# pakSystem.test(packagePath)
			packagePath = pakSystem.locatePackage(packageFile)
			if not packagePath:
				packagePath = '-'
			file.write('{0}{1}{2}\n'.format(useName.ljust(lenColPackage), useVersion.ljust(lenColVersion), packagePath.ljust(lenColRepo) ))
		else:
			file.write('\n'*3)

		# Prints informations about projects
		lenColProject = env['outputLineLength'] * 45 / 100
		lenColType = env['outputLineLength'] * 5 / 100
		lenColUses = env['outputLineLength'] * 50 / 100
		file.write( '{0}{1}{2}\n'.format( 'Project path '.ljust(lenColProject), 'Type'.ljust(lenColType), 'uses/stdlibs'.ljust(lenColUses) ) )
		file.write( '{0}{1}{2}\n'.format( '-------------'.ljust(lenColProject), '----'.ljust(lenColType), '------------'.ljust(lenColUses) ) )
		for project in [env['sbf_project']] + dependencies:
			projectEnv = sbf.getEnv(project)

			typeOfProject = projectEnv['type']
			if typeOfProject == 'none':
				typeOfProject = 'meta'

			projectPathName = projectEnv['sbf_projectPathName']
			projectRelPath = convertPathAbsToRel( rootOfProjects, projectPathName )

			if len(projectRelPath)==0:
				projectRelPath = projectEnv['sbf_project']

			libs = ''
			for useNameVersion in projectEnv['uses']:
				useName, useVersion = UseRepository.extract( useNameVersion )
				if useVersion:
					libs += ' {0}({1})'.format( useName, useVersion )
				else:
					libs += ' {0}'.format( useName )
			for lib in projectEnv['stdlibs']:
				libs += ' {0} '.format( lib )

			file.write( '{0}{1}{2}\n'.format( projectRelPath.ljust(lenColProject), typeOfProject.ljust(lenColType), libs.ljust(lenColUses) ) )
		else:
			file.write('\n')



def doTargetInfo( target, source, env ):
	# Retrieves additional informations
	sourceName = str(source[0])

	# Prints source
	with open(sourceName) as file:
		for line in file:
			print line,



def configureInfoTarget( env ):
	# Target 'infofile'
	sbf = env.sbf
	rootProjectEnv = sbf.getRootProjectEnv()
	# info.sbf is generated at the root of the project (PS: not in share directory, because it would be always rebuilt to be copy an updated version in local/share).
	infoFile = os.path.join( rootProjectEnv['sbf_projectPathName'], 'info.sbf' )
	rootProjectEnv['sbf_info'] = [infoFile] # @todo adds now and only if generated, but i don't have the information (see HOWTO for generated files).
	rootProjectEnv.Alias( 'infofile', rootProjectEnv.Command( infoFile, 'dummy.in', rootProjectEnv.Action( doTargetInfoFile, printGenerate ) ) )
	rootProjectEnv.Alias( 'infofile', rootProjectEnv.Install( sbf.getShareInstallDirectory(), infoFile ) )
	rootProjectEnv.AlwaysBuild( infoFile )
	Clean( ['clean', 'mrproper'], infoFile )

	# Target 'info'
	if 'info' in env.sbf.myBuildTargets:
		Alias( 'info', rootProjectEnv.Command( 'dummyInfo.out1', os.path.join(sbf.getShareInstallDirectory(), 'info.sbf'), rootProjectEnv.Action( doTargetInfo, printEmptyLine ) ) )
