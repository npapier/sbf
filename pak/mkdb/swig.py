#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

version = '3-0-2'
versionDot = version.replace('-', '.')

descriptor = {
 'urls'			: [ 'http://sourceforge.net/projects/swig/files/swigwin/swigwin-{version}/swigwin-{version}.zip'.format(version=versionDot) ],
 
 'name'			: 'swig',
 'version'		: version,

 # packages developer and runtime
 'rootDir'		: 'swigwin-{version}'.format(version=versionDot),

 # developer package 
 'license'		: ['LICENSE', 'LICENSE-GPL', 'LICENSE-UNIVERSITIES'],

 'custom'		: [	('swig.exe', 'bin/'),
					(GlobRegEx('Lib/.*', pruneFiles='(?!^.*[.](swg|i)$)', recursive=True), 'bin/Lib/') ]
}
