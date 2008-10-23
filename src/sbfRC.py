# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from __future__ import with_statement

import datetime
import os

### Generation of resource file (win32 only)
# @todo Completes VERSIONINFO
def resourceFileGeneration( target, source, env ) :

	# Retrieves/computes additional information
	targetName = str(target[0])

	# Open output file
	with open( targetName, 'w' ) as file :
		# VERSIONINFO
		fileTypeDict =	{
							'exec'		: 'VFT_APP',
							'static'	: 'VFT_STATIC_LIB',
							'shared'	: 'VFT_DLL'
						}

		if fileTypeDict.has_key(env['type']) :
			fileTypeStr = fileTypeDict[env['type']]
		else :
			fileTypeStr = "VFT_UNKNOWN"

		strVersionInfo = """#include <windows.h>

VS_VERSION_INFO VERSIONINFO
FILEVERSION %s, %s, %s, 0
PRODUCTVERSION %s, %s, %s, 0
#ifdef DEBUG
FILEFLAGSMASK VS_FF_DEBUG | VS_FF_PRERELEASE
#else
FILEFLAGSMASK 0
#endif
FILEOS VOS_NT_WINDOWS32
FILETYPE %s
FILESUBTYPE VFT2_UNKNOWN
""" %	(
			env['sbf_version_major'], env['sbf_version_minor'], env['sbf_version_maintenance'],
			env['sbf_version_major'], env['sbf_version_minor'], env['sbf_version_maintenance'],
			fileTypeStr
		)

		file.write( strVersionInfo )
		file.write("""
BEGIN
	BLOCK "StringFileInfo"
	BEGIN
		BLOCK "040904b0"
		BEGIN
//			VALUE "Comments", "\\0"
""" )
		file.write( """			VALUE "CompanyName", "%s\\0"\n""" % env['companyName'] )
		file.write( """			VALUE "FileDescription", "%s\\0"\n""" % env['description'] )

		file.write( """			VALUE "FileVersion", "%s\\0"\n""" % env['version'] )

		file.write( """			VALUE "InternalName", "%s\\0"\n""" % env['sbf_project'] )
		file.write( """			VALUE "LegalCopyright", "Copyright (C) %s, %s, All rights reserved\\0"\n"""
					% ( datetime.date.today().year, env['companyName'] ) )

		file.write( """			VALUE "OriginalFilename", "%s\\0"\n""" % env['sbf_project'] )
#//			VALUE "PrivateBuild", "%s\\0"
		file.write( """			VALUE "ProductName", "%s\\0"\n""" % env['sbf_project'] )
		file.write( """			VALUE "ProductVersion", "%s\\0"\n""" % env['version'] )

		strVersionInfo = """		END
	END
	BLOCK "VarFileInfo"
	BEGIN
		VALUE "Translation", 0x409, 1252
	END
END

"""
		file.write( strVersionInfo )

		# MYPROJECT_ICON ICON DISCARDABLE "myProject.ico"
		strIcon			= """%s_ICON ICON DISCARDABLE "%s" """

		iconFile		= env['sbf_project'] + '.ico'
		iconAbsPathFile	= os.path.join(env['sbf_projectPathName'], 'rc', iconFile )

		if os.path.isfile( iconAbsPathFile ) :
			file.write( strIcon % (	env['sbf_project'].upper(), iconFile ) )
