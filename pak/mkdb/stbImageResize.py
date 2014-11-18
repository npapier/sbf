#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2014, Philippe Sengchanpheng, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Philippe Sengchanpheng

# ok for clx.y
version = '0.90'
versionDash = version.replace('.', '-')

descriptor = {
 'urls'			: ['$SRCPAKPATH/stb_image_resize_{version}.zip'.format(version=version)],

 'name'			: 'stbImageResize',
 'version'		: versionDash,

 #'license'		: ['copying.txt'],
 'include'		: [('stb_image_resize.h', 'stb/')]
}
