#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

version = '2-0-12'
#version = '3-0-2'
versionDot = version.replace('-', '.')

descriptor = {
 'urls'			: [ 'http://orange/files/Dev/localExt/PUBLIC/src/swigShp{0}.zip'.format(version) ],

 'name'			: 'swigShp',
 'version'		: version,

 # developer package
 'custom'		: [	(GlobRegEx('Lib/.*', pruneFiles='(?!^.*[.](swg|i)$)', recursive=True), 'bin/Lib/') ]
}
