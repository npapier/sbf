#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

version = '3-0-2'
versionDot = version.replace('-', '.')

descriptor = {
 'urls'			: [ '$SRCPAKPATH/swigShp{0}.zip'.format(version) ],

 'name'			: 'swigshp',
 'version'		: version,

 # developer package
 'custom'		: [	(GlobRegEx('Lib/.*', pruneFiles='(?!^.*[.](swg|i)$)', recursive=True), 'bin/Lib/') ]
}
