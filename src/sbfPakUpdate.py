# SConsBuildFramework - Copyright (C) 2012, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from SCons.Script import *

from src.sbfPackagingSystem import PackagingSystem
from src.sbfUses import UseRepository, generateAllUseNames
from src.sbfVersion import splitUsesName
from src.SConsBuildFramework import printEmptyLine



def doTargetPakUpdate( target, source, env ):
	def pakUpdate( pakSystem, useName, useVersion, use, hasPackage, packageFilename ):
		if pakSystem.isInstalled(useName):
			# installed
			oPakInfo = {}
			pakSystem.loadPackageInfo( useName, oPakInfo )
			if hasPackage:
				if useVersion == oPakInfo['version']:
					print ( '{0} {1} is installed.'.format(useName.ljust(32), useVersion.ljust(8)) )
				else:
					print ( '{0} {1} is installed, but {2} is needed.'.format(oPakInfo['name'], oPakInfo['version'], useVersion) )
					print ( 'Upgrading or downgrading...' )
					pakSystem.remove( oPakInfo['name'] )
					retVal = pakSystem.install( packageFilename )
					if not retVal:	Exit(1)
					print ('\n'* 3)
			else:
				print ( '{0} {1} is installed, but it is no more needed.'.format(oPakInfo['name'], oPakInfo['version']) )
				print ( 'Removing...' )
				pakSystem.remove( oPakInfo['name'] )
				print ('\n'* 3)
		else:
			# not installed
			if hasPackage:
				print ( '{0} {1} is NOT installed.'.format(useName.ljust(16), useVersion))
				retVal = pakSystem.install( packageFilename )
				if not retVal:	Exit(1)
				print ('\n'* 3)
			#else nothing to do



	# Retrieves/computes additional informations
	sbf = env.sbf
	pakSystem = PackagingSystem(sbf, verbose=False)

	# Retrieves informations
	uses = sorted(list(sbf.getAllUses(env)))

	for useNameVersion in uses:
		useName, useVersion = splitUsesName( useNameVersion )

		use = UseRepository.getUse( useName )

		# Updating packages (development and runtime packages)
		for useName in generateAllUseNames(useName):
			packageFilename = '{0}{1}{2}.zip'.format(useName, useVersion, sbf.my_Platform_myArch_myCCVersion)
			pakUpdate( pakSystem, useName, useVersion, use, use.hasPackage(useName, useVersion), packageFilename )


def configurePakUpdateTarget( env ):
	rootProjectEnv = env.sbf.getRootProjectEnv()
	# Target 'pakUpdate'
	if 'pakupdate' in env.sbf.myBuildTargets:
		Alias( 'pakupdate', rootProjectEnv.Command( 'dummyPakUpdate.out1', 'dummy.in', rootProjectEnv.Action( doTargetPakUpdate, printEmptyLine ) ) )
