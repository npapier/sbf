# SConsBuildFramework - Copyright (C) 2009, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from sbfUtils import execute

# cygpath utilities (used by rsync)
def callCygpath2Unix( path, cygwinBinPath ):
	cmdParams = ['cygpath', '-u', "'{path}'".format(path=path)]
	output = execute(cmdParams, cygwinBinPath)
	return output.rstrip('\n')


class PosixSource:
	def __init__( self, platform, cygwinBinPath ):
		self.platform = platform
		self.cygwinBinPath = cygwinBinPath

	def __call__( self, target, source, env, for_signature ):
		if self.platform == 'win32' :
			return callCygpath2Unix(str(source[0]), self.cygwinBinPath)
		else:
			return str(source[0])


class PosixTarget:
	def __init__( self, platform, cygwinBinPath ):
		self.platform = platform
		self.cygwinBinPath = cygwinBinPath

	def __call__( self, target, source, env, for_signature ):
		if self.platform == 'win32' :
			return callCygpath2Unix(str(target[0]), self.cygwinBinPath)
		else:
			return str(target[0])
