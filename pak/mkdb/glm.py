#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for clx.y
version = '0.9.3.4'
versionDash = version.replace('.', '-')

descriptor = {
 'urls'			: ['http://sourceforge.net/projects/ogl-math/files/glm-{version}/glm-{version}.zip'.format(version=version)],

 'name'			: 'glm',
 'version'		: versionDash,

 'rootDir'		: 'glm-{version}'.format(version=version),
 'license'		: ['copying.txt'],
 'include'		: [('glm/', 'glm/')]
}
