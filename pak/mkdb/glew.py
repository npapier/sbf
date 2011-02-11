#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for clx.y
import os

sofaUse = UseRepository.getUse('sofa')

print ('INFO: This package exists only as a sofa dependency (this is not a full package).')

descriptor = {
 'urls'			: ['http://sourceforge.net/projects/glew/files/glew/1.5.1/glew-1.5.1-src.zip/download'],

 'name'			: 'glew',
 'version'		: '1-5-1',

 'rootDir'		: 'glew',
 'license'		: ['LICENSE.txt'],

 'custom'		: [ (os.path.join(sofaUse.getBasePath(), 'bin', 'glew32.dll'), 'lib/'),
					(os.path.join(sofaUse.getBasePath(), 'lib', 'win32', 'Common', 'glew32.lib'), 'lib/') ]
}
