# SConsBuildFramework - Copyright (C) 2011, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

def getCMakeCmdConfigure( CC, CCVersionNumber, arch, options, CMakeListsPath = 'CMakeLists.txt' ):
	"""Helper for mkpak."""

	if CC == 'cl':
		cmakeGenerator = {
		8	: 'Visual Studio 8 2005',
		9	: 'Visual Studio 9 2008',
		10	: 'Visual Studio 10',
		11	: 'Visual Studio 11',
		12	: 'Visual Studio 12'
		}
		if CCVersionNumber in cmakeGenerator:
			desiredGenerator = cmakeGenerator[CCVersionNumber]
			if arch == 'x86-64':	desiredGenerator += ' Win64'
			return 'cmake -G "{generator}" {options} {CMakeList}'.format( generator=desiredGenerator, options=options, CMakeList = CMakeListsPath )
		else:
			print ('Given unsupported MSVC version {}. \nVersion 8.0[Exp], 9.0[Exp], 10.0[Exp], 11.0[Exp] or 12.0[Exp] required.'.format(ccVersionNumber))
			exit(1)
	else:
		print ("Given compiler '{}' not yet supported.".format(CC))
		exit(1)


def getCMakeCmdBuildDebug():
	"""Helper for mkpak."""
	cmdDebug = 'cmake --build . --config debug'
	return cmdDebug

def getCMakeCmdBuildRelease():
	"""Helper for mkpak."""
	cmdRelease = 'cmake --build . --config release'
	return cmdRelease
