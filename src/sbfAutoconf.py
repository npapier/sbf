# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

def getAutoconfBuildingCommands( configureOptions = None ):
	"""	@brief Returns ['./configure' + configureOptions, 'make', 'make install']

		@param configureOptions		option(s) to append to './configure ' command, or None to call ./configure
	"""
	if configureOptions:
		return ['./configure {}'.format(configureOptions), 'make', 'make install']
	else:
		return ['./configure', 'make', 'make install']
