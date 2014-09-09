# SConsBuildFramework - Copyright (C) 2008, 2010, 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# This file is an helper to give access from a project options file to :
# - 'platform' variable containing the current platform (win32, posix and darwin).
# - 'myCurrentLocalEnv' variable containing the scons environment for this project.
# - 'sbf' variable containing the instance of SConsBuildFramework class.
# - 'userDict' option defined in SConsBuildFramework.options 
from SCons.Script.SConscript import SConsEnvironment

platform	= SConsEnvironment.sbf.myPlatform

SConsEnvironment.sbf.myCurrentLocalEnv.Append( LINKFLAGS = ['/SUBSYSTEM:WINDOWS'] )

sbf = SConsEnvironment.sbf

userDict = SConsEnvironment.sbf.myEnv['userDict']

# customBuild example
customTarget = """from sofa import parser, main
(options, args ) = parser.parse_args( ['{target}', lenv['config']] )
exitCode = main( options, args, lenv )
"""

customBuild = {	'svncheckout'	: customTarget.format(target='checkout'),
				'svnupdate'		: customTarget.format(target='update'),
				'pakupdate'		: customTarget.format(target='init'),
				'mrproper'		: customTarget.format(target='mrproper'),
				'clean'			: customTarget.format(target='clean'),
				'portable'		: customTarget.format(target='build'),
				'all'			: customTarget.format(target='build') }

# UseRepository access
from src.sbfUses import UseRepository
sofaUse = UseRepository.getUse('sofa')

# SCons InstallAs 
installTarget += SCons.Script.InstallAs( os.path.join(self.myLocalBin, os.path.basename(lib)), lib)

# SCons Alias
SCons.Script.Alias( 'Sofa_install', installTarget )
