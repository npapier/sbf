#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for clx.y
descriptor = {
 'urls'			: ['http://sourceforge.net/projects/ogl-math/files/glm-0.9.3.3/glm-0.9.3.3.zip'],

 'name'			: 'glm',
 'version'		: '0-9-3-3',

 'rootDir'		: 'glm-0.9.3.3',
 'license'		: ['copying.txt'],
 'include'		: [('glm/', 'glm/')],
}
