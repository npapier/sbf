#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2014, Philippe Sengchanpheng, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Philippe Sengchanpheng

# ok for clx.y
version = '0.95'
versionDash = version.replace('.', '-')

descriptor = {
 'urls'			: ['$SRCPAKPATH/stb_image_write_{version}.zip'.format(version=version)],

 'name'			: 'stbImageWrite',
 'version'		: versionDash,

 #'license'		: ['copying.txt'],
 'include'		: [('stb_image_write.h', 'stb/')]
}
