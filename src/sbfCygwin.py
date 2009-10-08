# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os

# cygpath utilities (used by rsync)
def callCygpath2Unix( path ):
	return os.popen('cygpath -u "' + path + '"' ).readline().rstrip('\n')

class PosixSource:
	def __init__( self, platform ):
		self.platform = platform

	def __call__( self, target, source, env, for_signature ):
		if self.platform == 'win32' :
			return callCygpath2Unix(str(source[0]))
#			return "`cygpath -u '" + str(source[0]) + "'`"
		else:
			return str(source[0])


class PosixTarget:
	def __init__( self, platform ):
		self.platform = platform

	def __call__( self, target, source, env, for_signature ):
		if self.platform == 'win32' :
			return callCygpath2Unix(str(target[0]))
#			return "`cygpath -u '" + str(target[0]) + "'`"
		else:
			return str(target[0])
