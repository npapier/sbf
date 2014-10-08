#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for clx.y

import os

sofaUse = UseRepository.gethUse('sofa')

print ('INFO: This package exists only as a sofa dependency (this is not a full package).')

descriptor = {
 'urls'			: ['http://www.opengl.org/resources/libraries/glut/glut37.zip'],

 'name'			: 'glut',
 'version'		: '3-7',

 'rootDir'		: 'glut-3.7',

 # developer package
 'license'		: ['NOTICE'],
 'custom'		: [ (os.path.join(sofaUse.getBasePath(), 'lib', 'win32', 'glut32.lib'), 'lib/') ],

 # runtime package
 'runtimeCustom': [ (os.path.join(sofaUse.getBasePath(), 'lib', 'win32', 'glut32.dll'), 'bin/') ]
}
