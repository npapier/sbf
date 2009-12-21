# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from SCons.Script import *

from src.sbfFiles import convertPathAbsToRel
from src.sbfPackagingSystem import PackagingSystem
from src.sbfUses import UseRepository
from src.SConsBuildFramework import printEmptyLine, stringFormatter



def doTargetInfo( target, source, env ):
	# Retrieves the SConsBuildFramework
	sbf = env.sbf
	pakSystem = PackagingSystem(sbf)

	# Prints startup message
	print stringFormatter( env, 'Informations about {0}'.format(env['sbf_project'] ) )
	print

	# Computes common root of projects
	rootOfProjects = env.sbf.getProjectsRoot( env )

	# Retrieves informations
	dependencies = sbf.getAllDependencies(env)
	uses = sorted(list(sbf.getAllUses(env)))

	# Prints informations about 'uses'
#	if len(uses)>0:
#		print ("external dependencies:".format(env['sbf_project']))
	lenColPackage = 30
	lenColVersion = 15
	lenColRepo = 74
	print ('{0}{1}{2}'.format( 'Package'.ljust(lenColPackage), 'Version'.ljust(lenColVersion), 'Repository'.ljust(lenColRepo) ))
	print ('{0}{1}{2}'.format( '-------'.ljust(lenColPackage), '-------'.ljust(lenColVersion), '----------'.ljust(lenColRepo) ))
	for useNameVersion in uses:
		useName, useVersion = UseRepository.extract( useNameVersion )
		use = UseRepository.getUse( useName )
		packageFile = '{0}{1}{2}.zip'.format(useName, useVersion, sbf.my_Platform_myCCVersion)
# @todo checks if use is supported for my platform, config, cc version...
# pakSystem.test(packagePath)
		packagePath = pakSystem.locatePackage(packageFile)
		if not packagePath:
			packagePath = '-'
#		print packageFile, packagePath
		print ('{0}{1}{2}'.format(useName.ljust(lenColPackage), useVersion.ljust(lenColVersion), packagePath.ljust(lenColRepo) ))
	else:
		print ('\n')

	# Prints informations about projects
	lenColProject = 52
	lenColType = 7
	lenColUses = 60
	print ( '{0}{1}{2}'.format( 'Project path '.ljust(lenColProject), 'Type'.ljust(lenColType), 'uses/stdlibs'.ljust(lenColUses) ) )
	print ( '{0}{1}{2}'.format( '-------------'.ljust(lenColProject), '----'.ljust(lenColType), '------------'.ljust(lenColUses) ) )
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

		print ( '{0}{1}{2}'.format( projectRelPath.ljust(lenColProject), typeOfProject.ljust(lenColType), libs.ljust(lenColUses) ) )
	else:
		print


def configureInfoTarget( env ):
	if 'info' in env.sbf.myBuildTargets:
		rootProjectEnv = env.sbf.getRootProjectEnv()
		Alias( 'info', rootProjectEnv.Command('dummyInfo.out1', 'dummy.in', Action( doTargetInfo, printEmptyLine ) ) )
