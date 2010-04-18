# SConsBuildFramework - Copyright (C) 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

global isSubversionAvailable

try:
	from sbfSubversion import Subversion
	isSubversionAvailable = True
except ImportError:
	print ('sbfWarning: sbf subversion support is not available.')
	isSubversionAvailable = False

