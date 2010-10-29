# SConsBuildFramework - Copyright (C) 2008, 2010, Nicolas Papier.
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

