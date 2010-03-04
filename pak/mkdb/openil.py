#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for clx.y

# http://openil.sourceforge.net/
descriptor = {
 'urls'			: ['http://downloads.sourceforge.net/openil/DevIL-SDK-x86-1.7.8.zip'],

 'name'			: 'openil',
 'version'		: '1-7-8',

 'license'		: ['COPYING'],
 'include'		: ['include/'],
 'lib'			: ['lib/*.dll', 'lib/*.lib']
}
