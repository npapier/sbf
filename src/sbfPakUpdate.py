# SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from SCons.Script import *

from src.sbfPackagingSystem import PackagingSystem
from src.sbfUses import UseRepository
from src.sbfVersion import splitUsesName
from src.SConsBuildFramework import printEmptyLine



def doTargetPakUpdate( target, source, env ):
	# Retrieves/computes additional informations
	sbf = env.sbf
	pakSystem = PackagingSystem(sbf, verbose=False)

	# Retrieves informations
	uses = sorted(list(sbf.getAllUses(env)))

	for useNameVersion in uses:
		useName, useVersion = splitUsesName( useNameVersion )
		packageFilename = '{0}{1}{2}.zip'.format(useName, useVersion, sbf.my_Platform_myCCVersion)
		# Test if package useName is installed
		if pakSystem.isInstalled(useName):
			# installed
			oPakInfo = {}
			pakSystem.loadPackageInfo( useName, oPakInfo )
			if useVersion == oPakInfo['version']:
				print ( '{0} version {1} is installed.'.format(useName.ljust(13), useVersion.ljust(8)) )
			else:
				print ( '{0} version {1} is installed, but version {2} is needed.'.format(oPakInfo['name'], oPakInfo['version'], useVersion) )
				print ( 'Upgrading...' )
				pakSystem.remove( oPakInfo['name'] )
				pakSystem.install( packageFilename )
				print ('\n'* 3)
		else:
			# not installed
			# Test if package 'packageFilename' is available
			if pakSystem.isAvailable( packageFilename ):
				print ( '{0} version {1} is NOT installed.'.format(useName.ljust(13), useVersion))
				pakSystem.install( packageFilename )
				print ('\n'* 3)
			else:
				use = UseRepository.getUse( useName )
				if use.hasAPackage():
					print ( '{0} version {1} is NOT installed and its package is NOT available !!!'.format(useName, useVersion))
					Exit(1)
				#else nothing to do



def configurePakUpdateTarget( env ):
	rootProjectEnv = env.sbf.getRootProjectEnv()
	# Target 'pakUpdate'
	if 'pakupdate' in env.sbf.myBuildTargets:
		Alias( 'pakupdate', rootProjectEnv.Command( 'dummyPakUpdate.out1', 'dummy.in', rootProjectEnv.Action( doTargetPakUpdate, printEmptyLine ) ) )
