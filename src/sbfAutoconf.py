# SConsBuildFramework - Copyright (C) 2014, 2015, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

def getAutoconfBuildingCommands( CC, configureOptions = '' ):
	"""	@brief Returns ['./configure' + configureOptions, 'make', 'make install']

		@param configureOptions		option(s) to append to './configure ' command, or None to call ./configure
		@remarks if CC is emcc then emconfigure is prepend to configure command and emmake is prepend to make command
	"""
	if CC == 'emcc':
		return ['emconfigure ./configure {}'.format(configureOptions), 'emmake make', 'emmake make install']
	else:
		return ['./configure {}'.format(configureOptions), 'make', 'make install']
