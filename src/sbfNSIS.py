# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from os.path import join, splitext

from src.sbfArchives	import extractArchive, isExtractionSupported
from src.sbfFiles		import *
from src.sbfRsync		import createRsyncAction
from src.sbfSevenZip	import create7ZipCompressAction
from src.sbfTools		import locateProgram
from src.sbfUses		import UseRepository
from src.sbfUtils		import capitalize
from src.sbfUI			import askQuestion
from src.sbfVersion		import splitUsesName, splitDeploymentPrecond
from src.SConsBuildFramework import stringFormatter, nopAction

# To be able to use this file without SCons
import __builtin__
try:
	from SCons.Script import *
except ImportError as e:
	if not hasattr(__builtin__, 'SConsBuildFrameworkQuietImport'):
		print ('sbfWarning: unable to import SCons.Script')


# @todo debug zipsrc if a used file is no more under vcs.
# @todo Improves redist macros (adding message and with/without confirmation)
# @todo improves output



### Helpers ####

def installAs( lenv, dirDest, dirSource, pruneDirectoriesPatterns = ['.svn'] ):
	"""	@brief Copy the directory tree from dirSource in dirDest using lenv.InstallAs(). pruneDirectoriesPatterns is used to exclude several sources directories.
		@return [ lenv.InstallAs(), ... ]"""
	files = []
	searchFiles( dirSource, files, pruneDirectoriesPatterns )

	installFiles = []
	parentOfDirSource = os.path.dirname(dirSource)
	for file in files:
		installFiles += lenv.InstallAs( file.replace(parentOfDirSource, dirDest, 1), file )
	return installFiles



def printNSISGeneration( target, source, env ):
	return stringFormatter(env, 'Generating {0} nsis setup program'.format(env['sbf_project']))

### project_redist.nsi and project_uninstall_redist.nsi generator ###
def printRedistGeneration( target, source, env ):
	return 'Generating {0} and {1} (redist files)'.format(os.path.basename(str(target[0])), os.path.basename(str(target[1])))

def redistGeneration( target, source, env ):
	"""target must be [${SBFPROJECTNAME}_redist.nsi , ${SBFPROJECTNAME}_uninstall_redist.nsi]"""

	# Retrieves/computes additional information
	targetNameRedist = str(target[0])
	targetNameUninstallRedist = str(target[1])

	sbf = env.sbf

	# compiler : CL90EXP or CL90 for example
	CLXYEXP = sbf.myCCVersion.replace( '-', '', 1 ).upper()

	# dependencies
	uses = sorted(list( sbf.getAllUses(env) ))
	redistFiles = []

# @remark no more used, because redistributables are already unzip in zipPortable
#	for useNameVersion in uses:
#		useName, useVersion = splitUsesName( useNameVersion )
#		use = UseRepository.getUse( useName )
#		if use:
#			redistributables = use.getRedist( useVersion )
#			for redistributable in redistributables:
				# '*.exe' launch executable,	('*.exe', 'question') ask and launch
				# '*.zip' extract in deps,		('*.zip', 'question') ask and extract
#				if isinstance(redistributable, tuple):
#					pass
#				else:
#					redistFiles.append(redistributable)


	# Open output file ${SBFPROJECTNAME}_redist.nsi
	with open( targetNameRedist, 'w' ) as file:
		file.write(
"""!include "redistributable.nsi"
!include "redistributableDatabase.nsi"
\n\n""" )

		# Redistributable for cl compiler
		file.write( "; Redistributable for cl compiler\n" )
		if sbf.myCCVersion >= 9.0:
			file.write( """!insertmacro InstallAndLaunchRedistributableQ "${{{file}}}" "{options}"\n\n\n""".format(file=CLXYEXP, options="/q") )
		else:
			file.write( """!insertmacro InstallAndLaunchRedistributableQ "${{{file}}}" ""\n\n\n""".format(file=CLXYEXP) )

# @remark no more used, because redistributables are already unzip in zipPortable
#		# Redistributable for 'uses'
#		if len(redistFiles)>0:
#			file.write( "; Redistributable for 'uses'\n" )
#			for redistFile in redistFiles:
#				redistFileExtension = splitext(redistFile)[1]
#				if redistFileExtension == '.zip':
#					file.write( """!insertmacro InstallAndUnzipRedistributable "{0}" "$INSTDIR"\n""".format(redistFile.replace('/', '\\') ) )
#				elif redistFileExtension == '.exe' :
#					file.write( """!insertmacro InstallAndLaunchRedistributable "{0}"\n""".format(redistFile.replace('/', '\\') ) )
#				else:
#					raise SCons.Errors.StopError, "Unsupported type of redistributable {0}".format(redistFile)


	# Open output file ${SBFPROJECTNAME}_uninstall_redist.nsi
	with open( targetNameUninstallRedist, 'w' ) as file:
		# Redistributable for cl compiler
		file.write( "; Redistributable for cl compiler\n" )
		file.write( """!insertmacro RmRedistributable "${{{file}}}"\n\n\n""".format(file=CLXYEXP) )



### project_install_files.nsi generator ###
def printGenerateNSISInstallFiles( target, source, env ):
	targetName = str(target[0])
	sourceName = str(source[0])
	return 'Generating {0} (nsis install files) from {1}'.format(os.path.basename(targetName), sourceName)

def generateNSISInstallFiles( target, source, env ):
	# Retrieves informations
	targetName = str( target[0] )
	sourceName = str( source[0] )

	encounteredFiles		= []
	encounteredDirectories	= []
	searchAllFilesAndDirectories( sourceName, encounteredFiles, encounteredDirectories )

	# Creates target file
	with open( targetName, 'w' ) as outputFile:
		# Creates directories
		for directory in encounteredDirectories:
			outputFile.write( 'CreateDirectory \"$OUTDIR\{0}\"\n'.format(convertPathAbsToRel(sourceName, directory)) )
			outputFile.write( 'LogEx::Write \"$OUTDIR\{0}\"\n'.format(convertPathAbsToRel(sourceName, directory)) )

		# Copies files
		for file in encounteredFiles:
			outputFile.write( 'File \"/oname=$OUTDIR\{0}\" \"{1}\"\n'.format(convertPathAbsToRel(sourceName, file), file) )
			outputFile.write( 'LogEx::Write \"/oname=$OUTDIR\{0}\" \"{1}\"\n'.format(convertPathAbsToRel(sourceName, file), file) )


### project_uninstall_files.nsi generator ###
def printGenerateNSISUninstallFiles( target, source, env ):
	targetName = str(target[0])
	sourceName = str(source[0])
	return 'Generating {0} (nsis uninstall files) from {1}'.format(os.path.basename(targetName), sourceName)

def generateNSISUninstallFiles( target, source, env ):
	# Retrieves informations
	targetName = str( target[0] )
	sourceName = str( source[0] )

	encounteredFiles		= []
	encounteredDirectories	= []
	searchAllFilesAndDirectories( sourceName, encounteredFiles, encounteredDirectories, walkTopDown = False )

	# Creates target file
	with open( targetName, 'w' ) as outputFile:
		# Removes files
		for file in encounteredFiles:
			outputFile.write( 'Delete /REBOOTOK \"$INSTDIR\{0}\"\n'.format(convertPathAbsToRel(sourceName, file)) )

		# Removes directories
		for directory in encounteredDirectories:
			outputFile.write( 'RmDir /REBOOTOK \"$INSTDIR\{0}\"\n'.format(convertPathAbsToRel(sourceName, directory)) )


### project.nsi generator ###
def printGenerateNSISMainScript( target, source, env ):
	targetName = str(target[0])
	return ( 'Generating {0} (nsis main script)'.format(os.path.basename(targetName)) )


def __computeICON( lenv ):
	iconFile = os.path.join( lenv['sbf_projectPathName'], 'rc', lenv['sbf_project']+'.ico')
	if os.path.exists( iconFile ):
		return 'Icon "{0}"'.format( iconFile )


def generateNSISMainScript( target, source, env ):
	# Retrieves/computes additional information
	targetName = str(target[0])
	sbf = env.sbf

	# Checks unknown option in 'nsis'
	nsisKeys = set(env['nsis'].keys())
	allowedNsisKeys = set(['autoUninstall', 'installDirFromRegKey', 'ensureNewInstallDir', 'uninstallVarDirectory', 'customPointInstallationValidation'])
	unknowOptions = nsisKeys - allowedNsisKeys
	if len(unknowOptions)>0:
		raise SCons.Errors.UserError( "Unknown key(s) ({0}) in 'nsis' option".format(list(unknowOptions)) )

	# Retrieving 'nsis' options
	nsisAutoUninstall = env['nsis'].get('autoUninstall', True)
	nsisInstallDirFromRegKey = env['nsis'].get('installDirFromRegKey', True)
	nsisEnsureNewInstallDir = env['nsis'].get('ensureNewInstallDir', False)
	nsisUninstallVarDirectory = env['nsis'].get('uninstallVarDirectory', False)
	nsisCustomPointInstallationValidation = env['nsis'].get('customPointInstallationValidation', '')

	#
	definesSection = ''
	if env['deploymentType'] == 'standalone':
		definesSection += "!define STANDALONE_DEPLOYMENTTYPE\n"
	elif env['deploymentType'] == 'embedded':
		definesSection += "!define EMBEDDED_DEPLOYMENTTYPE\n"
	elif env['deploymentType'] == 'none':
		definesSection += "!define NONE_DEPLOYMENTTYPE\n"
	else:
		assert( False )

	if nsisAutoUninstall:			definesSection += "!define AUTO_UNINSTALL\n"
	if nsisEnsureNewInstallDir:		definesSection += "!define ENSURE_NEW_INSTALLDIR\n"
	if nsisUninstallVarDirectory:	definesSection += "!define UNINSTALL_VAR_DIRECTORY\n"

	# Open output file
	with open( targetName, 'w' ) as file:
		# Retrieves informations (all executables, ...)
		rootProject = env['sbf_project']

		mainProject = ''	# first project of type 'exec'
		products	= []
		executables	= []
		for (projectName, lenv) in env.sbf.myParsedProjects.iteritems():
			if lenv['type'] == 'exec':
				#print lenv['sbf_project'], os.path.basename(lenv['sbf_bin'][0])
				if len(products) == 0:
					mainProject = lenv['sbf_project']
				products.append( lenv['productName'] + sbf.my_PostfixLinkedToMyConfig )
				executables.append( os.path.basename(lenv['sbf_bin'][0]) )

		# Generates PRODUCTNAME
		PRODUCTNAME = ''
		for (i, product) in enumerate(products):
			PRODUCTNAME += "!define PRODUCTNAME{0}	\"{1}\"\n".format(i, product)
#		PRODUCTNAME += '!define PRODUCTNAME		"${PRODUCTNAME0}"\n'

		# Generates PRODUCTEXE, SHORTCUT, DESKTOPSHORTCUT, QUICKLAUNCHSHORTCUT, UNINSTALL_SHORTCUT, UNINSTALL_DESKTOPSHORTCUT and UNINSTALL_QUICKLAUNCHSHORTCUT
		PRODUCTEXE						= ''
		SHORTCUT						= ''
		DESKTOPSHORTCUT					= ''
		QUICKLAUNCHSHORTCUT				= ''
		UNINSTALL_SHORTCUT				= ''
		UNINSTALL_DESKTOPSHORTCUT		= ''
		UNINSTALL_QUICKLAUNCHSHORTCUT	= ''
#		if len(executables) > 1:
#			SHORTCUT = '  CreateDirectory \"${STARTMENUROOT}\\tools\"\n'
#			UNINSTALL_SHORTCUT	=	'  Delete \"${STARTMENUROOT}\\tools\\*.*\"\n'
#			UNINSTALL_SHORTCUT	+=	'  RMDir \"${STARTMENUROOT}\\tools\"\n'

		for (i, executable) in enumerate(executables) :
			PRODUCTEXE	+=	'!define PRODUCTEXE{0}	"{1}"\n'.format( i, executable)
			if i > 0:
				SHORTCUT	+=	'  SetOutPath \"$INSTDIR\\bin\"\n'
				SHORTCUT	+=	"  CreateShortCut \"${STARTMENUROOT}\\tools\\${PRODUCTNAME%s}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE%s}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE%s}\" 0\n" % (i, i, i)
			else:
				SHORTCUT						=	'  SetOutPath \"$INSTDIR\\bin\"\n'
				SHORTCUT						+=	'  CreateShortCut \"${STARTMENUROOT}\\${PRODUCTNAME0}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" 0\n'
				DESKTOPSHORTCUT					=	'  SetOutPath \"$INSTDIR\\bin\"\n'
				DESKTOPSHORTCUT					+=	'  CreateShortCut \"$DESKTOP\\${PRODUCTNAME0}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" 0\n'
				QUICKLAUNCHSHORTCUT				=	'  SetOutPath \"$INSTDIR\\bin\"\n'
				QUICKLAUNCHSHORTCUT				+=	'  CreateShortCut \"$QUICKLAUNCH\\${PRODUCTNAME0}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" 0\n'
				UNINSTALL_DESKTOPSHORTCUT		=	'  Delete /REBOOTOK \"$DESKTOP\\${PRODUCTNAME0}.lnk\"\n'
				UNINSTALL_QUICKLAUNCHSHORTCUT	=	'  Delete /REBOOTOK \"$QUICKLAUNCH\\${PRODUCTNAME0}.lnk\"\n'

		PRODUCTEXE += "!define PRODUCTEXE	${PRODUCTEXE0}\n"

		# installationDirectorySection
		if env['deploymentType'] in ['none', 'standalone']:
			### standalone|none project
			installationDirectorySection = """
; standalone or none project
InstallDir "$PROGRAMFILES\${SBFPROJECTVENDOR}\${SBFPRODUCTNAME}${SBFPROJECTCONFIG}\${SBFPROJECTVERSION}"
"""
			if nsisInstallDirFromRegKey:
				installationDirectorySection += """
; Registry key to check for directory (so if you install again, it will overwrite the old one automatically)
InstallDirRegKey HKLM "${REGKEYROOT}" "InstallDir"
"""
		else:
			### embedded project
			assert( env['deploymentType'] == 'embedded' )

			if len(env['deploymentPrecond'])==0:
				print ('sbfError: deploymentPrecond have to be defined for {0} project.'.format(env['sbf_project']))
				Exit(1)

			# Extract deployment preconditions
			(name, operator, version) = splitDeploymentPrecond(env['deploymentPrecond'])

			# Test version
			assert( operator == '>=' )
			testVersionPrecond = """
			; prepare version numbers
			${{VersionConvert}} $1 "" $5
			${{VersionConvert}} ${{DEPLOYMENTPRECOND_STANDALONE_VERSION}} "" $6

			; test version
			${{VersionCompare}} $5 $6 $7

			; >=
			${{If}} $7 == 2
				; test failed (<)
				MessageBox MB_ICONSTOP|MB_OK "Version of $3 currently installed in the system is $1. But it have to be at least ${{DEPLOYMENTPRECOND_STANDALONE_VERSION}}." /SD IDOK
				LogEx::Write "Version of $3 currently installed in the system is $1. But it have to be at least ${{DEPLOYMENTPRECOND_STANDALONE_VERSION}}."
				Abort
			${{EndIf}}

			; test passed
			;LogText "Version of $3 currently installed in the system is $1 (req. at least ${{DEPLOYMENTPRECOND_STANDALONE_VERSION}})."
""".format()

			installationDirectorySection = """
; embedded project

; deploymentPrecond = 'projectName >= 2-0-beta15'
!define DEPLOYMENTPRECOND_STANDALONE_NAME				"{deploymentPrecond_standalone_name}"
!define DEPLOYMENTPRECOND_STANDALONE_COMPAREOPERATOR	"{deploymentPrecond_standalone_compareOperator}"
!define DEPLOYMENTPRECOND_STANDALONE_VERSION			"{deploymentPrecond_standalone_version}"

Function initInstallDir

	!insertmacro GetInfos "${{DEPLOYMENTPRECOND_STANDALONE_NAME}}"
	; Test if standalone is installed
	${{If}} $0 == ''
		; never installed, abort
		MessageBox MB_ICONSTOP|MB_OK "${{DEPLOYMENTPRECOND_STANDALONE_NAME}} have to be installed in the system before installing '${{SBFPRODUCTNAME}}'." /SD IDOK
		LogEx::Write "${{DEPLOYMENTPRECOND_STANDALONE_NAME}} have to be installed in the system before installing '${{SBFPRODUCTNAME}}'."
		Abort
	${{Else}} ;$0 != ''
		${{If}} $4 != 'installed'
			; already installed, but not now => abort
			MessageBox MB_ICONSTOP|MB_OK "$3 have to be installed in the system before installing '${{SBFPRODUCTNAME}}'." /SD IDOK
			LogEx::Write "$3 have to be installed in the system before installing '${{SBFPRODUCTNAME}}'."
			Abort
		${{Else}} ; $0 != '' & $4 != 'installed'
			; test version precondition
			{testVersionPrecond}

			StrCpy $INSTDIR "$0\packages\${{SBFPROJECTNAME}}_${{SBFPROJECTVERSION}}"

			; debug message
			MessageBox MB_ICONINFORMATION|MB_OK "$3 $1 is installed in the system in $0." /SD IDOK
			LogEx::Write "$3 $1 is installed in the system in $0."
		${{EndIf}}
	${{EndIf}}
FunctionEnd
""".format( deploymentPrecond_standalone_name=name, deploymentPrecond_standalone_compareOperator=operator, deploymentPrecond_standalone_version=version, testVersionPrecond = testVersionPrecond )

		# Generates ICON
		# icon from the project launching sbf ?
		ICON = __computeICON( sbf.myParsedProjects[rootProject] )
		# icon from the first project containing an executable ?
		if not ICON and mainProject:
			ICON = __computeICON( sbf.myParsedProjects[mainProject] )

		# no icon ?
		if not ICON:
			ICON = "; no icon"


		str_sbfNSISTemplate = """\
; sbfNSISTemplate.nsi
;
; This script :
; - Uninstall previous version before installing the new one (see nsis['autoUninstall'] option)
; - allow removing 'var' directory during uninstall stage (see nsis['uninstallVarDirectory'] option).
; - It will install files into a "PROGRAMFILES\SBFPROJECTVENDOR\SBFPROJECTNAME SBFPROJECTCONFIG\SBFPROJECTVERSION" or a directory that the user selects for 'standalone' or 'none' project
; - or in a directory found in registry for 'embedded' project
; - checks if deploymentPrecond is true (for embedded project)
; - remember the installation directory (see nsis['installDirFromRegKey'] option). So if you install again, it will overwrite the old one automatically.
; - remember the installed version.
; - creates a 'var' directory with full access for 'Users' and backups 'var' directory if already present.
; - icon of setup program comes from the launching project (if it contains an icon in rc/project.ico), otherwise from the first executable project (if any and if it contains an icon), else no icon at all.
; - ProductName, CompanyName, LegalCopyright, FileDescription, FileVersion and ProductVersion fields in the version tab of the File Properties are filled.
; - install in registry Software/SBFPROJECTVENDOR/SBFPROJECTNAME/InstallDir
; - install in registry Software/SBFPROJECTVENDOR/SBFPROJECTNAME/Version
; - run as admin and installation occurs for all users
; - components chooser
; - has uninstall support (no modify, no repair).
; - install/launch/uninstall Visual C++ redistributable and sbfPak redistributable.
; - installs start menu shortcuts (run all exe and uninstall).
; - (optionally) installs desktop menu shortcut for the main executable.
; @todo Uses UAC to - and (optionally) installs quicklaunch menu shortcuts for the main executable.
; - prevent running multiple instances of the installer
; - silent installation is supported (especially MessageBox())
; - support simultaneous installation/uninstallation of several versions of a project.
; - logging installation into $EXEDIR/$EXEFILE.replace('.exe', '_log.txt')

; @todo mui
; @todo quicklaunch
; @todo repair/modify


;--------------------------------

!include "FileFunc.nsh"		; for GetSize and GetTime
!include "LogicLib.nsh"
!include "StrFunc.nsh"		; for StrTok
!include "WordFunc.nsh"		; for VersionCompare and VersionConvert

# Declare used functions
${{StrRep}}
${{StrTok}}

;SetCompress off
SetCompressor /FINAL /SOLID lzma

XPStyle on

!define SBFPROJECTNAME				"{projectName}"
!define SBFPRODUCTNAME				"{productName}"
!define SBFPROJECTVERSION			"{projectVersion}"
!define SBFPROJECTCONFIG			"{projectConfig}"
!define SBFPROJECTVENDOR			"{projectVendor}"
!define SBFDATE						"{date}"

{definesSection}

; SETUPFILE
!define SETUPFILE "${{SBFPRODUCTNAME}}_${{SBFPROJECTVERSION}}${{SBFPROJECTCONFIG}}_${{SBFDATE}}_setup.exe"

;
!define REGKEYROOT				"Software\${{SBFPROJECTVENDOR}}\${{SBFPROJECTNAME}}"
!define REGKEYROOTVER			"Software\${{SBFPROJECTVENDOR}}\${{SBFPROJECTNAME}}\${{SBFPROJECTVERSION}}"
!define REGKEYUNINSTALLROOT		"Software\Microsoft\Windows\CurrentVersion\Uninstall\${{SBFPROJECTNAME}}"
!define REGKEYUNINSTALLROOTVER	"Software\Microsoft\Windows\CurrentVersion\Uninstall\${{SBFPROJECTNAME}}_${{SBFPROJECTVERSION}}"

!define STARTMENUROOT		"$SMPROGRAMS\${{SBFPROJECTVENDOR}}\${{SBFPRODUCTNAME}}\${{SBFPROJECTVERSION}}"

; PRODUCTNAME section
{productNameSection}

; PRODUCTEXE
{productExe}

; Macros

; --- writeRegInstall deleteRegInstall GetInstallDir GetInstallDirAndVersion GetInfos ---
!macro writeRegInstall path
  ; Write the installation path into the registry
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "InstallDir" "${{path}}"			; don't remove in uninstall stage

  ; Write product name into the registry
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "ProductName" "${{SBFPRODUCTNAME}}"

  ; Write deploymentType into the registry
!ifndef EMBEDDED_DEPLOYMENTTYPE
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "DeploymentType"								"standalone"
!else
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "DeploymentType"								"embedded"
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "DeploymentPrecond_standalone_name"				"${{DEPLOYMENTPRECOND_STANDALONE_NAME}}"
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "DeploymentPrecond_standalone_compareOperator"	"${{DEPLOYMENTPRECOND_STANDALONE_COMPAREOPERATOR}}"
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "DeploymentPrecond_standalone_version"			"${{DEPLOYMENTPRECOND_STANDALONE_VERSION}}"
!endif

  ; Write the installation date and time into the registry
  ${{GetTime}} "" "L" $2 $1 $0 $6 $3 $4 $5
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "InstallDate" "$0-$1-$2"
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "InstallTime" "$3-$4-$5"

  ; Write status into the registry
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "Status" "installed"
!macroend

!macro deleteRegInstall
  ; Write the uninstallation date and time into the registry
  ${{GetTime}} "" "L" $2 $1 $0 $6 $3 $4 $5
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "UninstallDate" "$0-$1-$2"
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "UninstallTime" "$3-$4-$5"

  ; Write status into the registry
  WriteRegStr HKLM "${{REGKEYROOTVER}}" "Status" "uninstalled"
!macroend

!macro GetInstallDir projectName
	; $0 InstallDir
	Push $1
	ReadRegStr $1 HKLM "Software\${{SBFPROJECTVENDOR}}\${{projectName}}"		"Version"
	ReadRegStr $0 HKLM "Software\${{SBFPROJECTVENDOR}}\${{projectName}}\$1"		"InstallDir"
	Pop $1
!macroend

!macro GetInstallDirAndVersion projectName
	; $0 InstallDir, $1 Version
	ReadRegStr $1 HKLM "Software\${{SBFPROJECTVENDOR}}\${{projectName}}"		"Version"
	ReadRegStr $0 HKLM "Software\${{SBFPROJECTVENDOR}}\${{projectName}}\$1"		"InstallDir"
!macroend

!macro GetInfos projectName
	; $0 InstallDir, $1 Version, $2 DeploymentType, $3 ProductName, $4 Status
	!insertmacro GetInstallDirAndVersion "${{projectName}}"
	ReadRegStr $2 HKLM "Software\${{SBFPROJECTVENDOR}}\${{projectName}}\$1"		"DeploymentType"
	ReadRegStr $3 HKLM "Software\${{SBFPROJECTVENDOR}}\${{projectName}}\$1"		"ProductName"
	ReadRegStr $4 HKLM "Software\${{SBFPROJECTVENDOR}}\${{projectName}}\$1"		"Status"
!macroend

!macro GetVersionAndStatus projectName resultVersion resultStatus
	ReadRegStr "${{resultVersion}}"	HKLM "Software\${{SBFPROJECTVENDOR}}\${{projectName}}"						"Version"
	ReadRegStr "${{resultStatus}}"	HKLM "Software\${{SBFPROJECTVENDOR}}\${{projectName}}\${{resultVersion}}"	"Status"
!macroend

; --- ---
!macro writeRegCurrent path version
  ; Write the installation path into the registry
; WriteRegStr HKLM "${{REGKEYROOT}}" "InstallDir" ${{path}}		; todo remove

  ; Write the version into the registry
  WriteRegStr HKLM "${{REGKEYROOT}}" "Version" ${{version}}
!macroend

!macro deleteRegCurrent path version
  ReadRegStr $0 HKLM "${{REGKEYROOT}}" "Version"
  ${{If}} $0 == ${{version}}
;    DeleteRegValue HKLM "${{REGKEYROOT}}" "InstallDir"		; todo remove
    DeleteRegValue HKLM "${{REGKEYROOT}}" "Version"
  ${{Else}}
    ; Uninstall version != current version
    ; do nothing
    Nop
  ${{EndIf}}
!macroend


!macro writeRegUninstall0 regRoot installDir productExe
  WriteRegStr HKLM "${{regRoot}}"	"DisplayIcon"		'"${{installDir}}\\bin\\${{productExe}}"'
  WriteRegStr HKLM "${{regRoot}}"	"UninstallString"	'"${{installDir}}\\uninstall.exe"'

  WriteRegStr HKLM "${{regRoot}}"	"InstallDir"		'${{installDir}}'
  WriteRegStr HKLM "${{regRoot}}"	"ProductExe"		'${{productExe}}'
!macroend

!macro writeRegUninstall regRoot installDir productExe sbfProjectVendor sbfProductName sbfProjectVersion
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "${{regRoot}}"		"DisplayName"		"${{sbfProjectVendor}} - ${{sbfProductName}} ${{sbfProjectVersion}}"
  WriteRegStr HKLM "${{regRoot}}"		"DisplayVersion"	"${{sbfProjectVersion}}"
  WriteRegStr HKLM "${{regRoot}}"		"Publisher"			"${{sbfProjectVendor}}"
  ${{GetSize}} "${{installDir}}" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKLM "${{regRoot}}"		"EstimatedSize"		"$0"

  WriteRegDWORD HKLM "${{regRoot}}"		"NoModify"			1
  WriteRegDWORD HKLM "${{regRoot}}"		"NoRepair"			1

  !insertmacro writeRegUninstall0 "${{regRoot}}" "$INSTDIR" "${{productExe}}"
!macroend

!macro getRegUninstallProductExe regRoot ResultProductExe
  ReadRegStr "${{ResultProductExe}}" HKLM "${{regRoot}}"	"ProductExe"
!macroend

!macro deleteRegUninstall regRoot
  DeleteRegKey HKLM "${{regRoot}}"
!macroend


;--- Functions ---
Function .onInstFailed
  ;
  MessageBox MB_OK "Installation failed." /SD IDOK
  LogEx::Write "Installation failed."

  ; Logging
  LogEx::Close
FunctionEnd


Function .onInstSuccess

  ;
  MessageBox MB_OK "Installation was successful." /SD IDOK
  LogEx::Write "Installation was successful."

;    MessageBox MB_YESNO "Congrats, it worked. View readme?" IDNO NoReadme
;      Exec notepad.exe ; view readme or whatever, if you want.
;    NoReadme:

  ; Logging
  LogEx::Close
FunctionEnd


Function .onRebootFailed
  MessageBox MB_OK|MB_ICONSTOP "Reboot failed. Please reboot manually." /SD IDOK
  LogEx::Write "Reboot failed. Please reboot manually."
FunctionEnd


Var Uninstall_InstallDir
Var Uninstall_ProductName
Var Uninstall_UninstallString

Function Uninstall_ask
 ; Ask if current version of SBFPROJECTNAME has to be removed (if already installed of course)
 ; remarks $0 InstallDir, $3 ProductName and $9 UninstallString of current SBFPROJECTNAME
 ; Variables Uninstall_InstallDir = $0, Uninstall_ProductName = $3 and Uninstall_UninstallString = $9 if uninstallation stage is desired

 !insertmacro GetInfos "${{SBFPROJECTNAME}}"
 ReadRegStr $9 HKLM "${{REGKEYUNINSTALLROOT}}_$1" "UninstallString"

 StrCpy $Uninstall_InstallDir		''
 StrCpy $Uninstall_ProductName		''
 StrCpy $Uninstall_UninstallString	''

 ${{If}} $9 == ''
	; Nothing to uninstall
	;MessageBox MB_ICONINFORMATION|MB_OK "No previous version of ${{SBFPRODUCTNAME}} to remove." /SD IDOK
	LogEx::Write "No previous version of ${{SBFPRODUCTNAME}} to remove."
 ${{Else}}
	MessageBox MB_ICONQUESTION|MB_YESNO "Do you want to remove previous version $1 of $3 ?" /SD IDYES IDYES doUninstall IDNO skipUninstall
	doUninstall:
	StrCpy $Uninstall_InstallDir		$0
	StrCpy $Uninstall_ProductName		$3
	StrCpy $Uninstall_UninstallString	$9
	LogEx::Write "Uninstall previous version $1 of $3 using '$9'"
 ${{Endif}}
 skipUninstall:
FunctionEnd


Function migratePackagesAndVar
	!define migratePackagesAndVar '!insertmacro migratePackagesAndVarCall'

	!macro migratePackagesAndVarCall source destination
	Push ${{destination}}
	Push ${{source}}
	Call migratePackagesAndVar
	!macroend

	; $0 source and $1 destination
	Exch $0
	Exch
	Exch $1
	Exch

	MessageBox MB_OK "Directories 'packages' and 'var' have to be migrated from $0 into $1." /SD IDOK
	LogEx::Write "Directories 'packages' and 'var' have to be migrated from $0 into $1."

	; --- migrate var ---
	${{If}} ${{FileExists}} "$0\\var"
		Rename /REBOOTOK "$0\\var" "$1\\varPrevious"
		LogEx::Write 'Rename "$0\\var" into "$1\\varPrevious.'
	${{Else}}
		LogEx::Write 'No var directory in $0'
	${{Endif}}

	; --- migrate packages ---
	ClearErrors
	FindFirst $8 $9 "$0\\packages\\*.*"
	${{DoUntil}} ${{Errors}}
		${{If}} $9 != "."
		${{AndIf}} $9 != ".."

			;MessageBox MB_OK "Found $9"

			; for myPackageName_2-1 => $6 myPackageName, $7 2-1
			${{StrTok}} $6 "$9" "_" "0" "1"
			${{StrTok}} $7 "$9" "_" "1" "1"

			; $R0 version, $R1 status
			!insertmacro GetVersionAndStatus "$6" $R0 $R1
			;MessageBox MB_OK "$R0 $R1"
			${{If}} $R0 == $7				; package found in registry and in filesystem have the same version
			${{AndIf}} $R1 == "installed"	; and the package in registry is installed
				;MessageBox MB_OK "$6:$7: is an installed package"
				LogEx::Write "$6:$7: is an installed package"
				StrCpy $R2 "Software\Microsoft\Windows\CurrentVersion\Uninstall\$6_$7"
				!insertmacro getRegUninstallProductExe "$R2" $R3
				!insertmacro writeRegUninstall0 "$R2" "$1\\packages\\$6_$7" "$R3"
				; In 'install section' of registry, 'InstallDir' is not modified by migration
				; todo add migrationDate/Time/DirDest in registry
			${{Else}}
				;MessageBox MB_OK "$6:$7: is not an installed package"
				LogEx::Write "$6:$7: is not an installed package"
			${{Endif}}
		${{Endif}}
		FindNext $8 $9
	${{Loop}}
	FindClose $8

	;	move 'packages' directory
	${{If}} ${{FileExists}} "$0\\packages"
		;MessageBox MB_OK "Rename $0\\packages into $1\\packages"
		LogEx::Write "Rename $0\\packages into $1\\packages"
		Rename /REBOOTOK "$0\\packages" "$1\\packages"
	${{Else}}
		;MessageBox MB_OK "No package directory in $0."
		LogEx::Write "No package directory in $0."
	${{Endif}}

	; restore
	Pop $0
	Pop $1
FunctionEnd


Function UninstallFunction
	; Remove program using 'var Uninstall_UninstallString' (if not empty), 'var Uninstall_InstallDir' and 'var Uninstall_ProductName'

	StrCpy $0 $Uninstall_InstallDir
	StrCpy $3 $Uninstall_ProductName
	StrCpy $9 $Uninstall_UninstallString
	${{If}} $9 == ""
		LogEx::Write "Nothing to uninstall"
	${{Else}}
		ClearErrors
		${{If}} ${{Silent}}
			; silent uninstall
			LogEx::Write "Uninstall silently $3"
			ExecWait '$9 /S _?=$0'
		${{Else}}
			; non silent uninstall
			;MessageBox MB_ICONINFORMATION|MB_OK "Uninstall $3" /SD IDOK
			LogEx::Write "Uninstall $3"
			ExecWait '$9 _?=$0'
		${{Endif}}

		; result
		${{If}} ${{Errors}}
			; error(s)
			MessageBox MB_ICONSTOP|MB_OK "Error during removing of $3" /SD IDOK
			LogEx::Write "Error during removing of $3"
			Abort
		${{Else}}
			; no errors, continue
			LogEx::Write "no errors during removing of $3, continue"
			;  Remove uninstaller
			Delete /REBOOTOK "$0\uninstall.exe"
			;  Remove installation directory
			RmDir /REBOOTOK "$0"
		${{Endif}}
	${{Endif}} ; $9 == ''
FunctionEnd


Function writeRegistryInstallAndUninstallFunction
	!define writeRegistryInstallAndUninstall 'Call writeRegistryInstallAndUninstallFunction'

 !insertmacro writeRegInstall $INSTDIR
 !insertmacro writeRegUninstall ${{REGKEYUNINSTALLROOTVER}} "$INSTDIR" "${{PRODUCTEXE}}" "${{SBFPROJECTVENDOR}}" "${{SBFPRODUCTNAME}}" "${{SBFPROJECTVERSION}}"
FunctionEnd


;--------------------------------
; The installation directory
{installationDirectorySection}


; --- onInit ---
Var logex_logname

Function .onInit

 ; Logging
 ${{StrRep}} $logex_logname "$EXEFILE" ".exe" "_log.txt"
 LogEx::Init "$EXEDIR\\$logex_logname"
 LogEx::Write ""


 ; --- Abort installation process if installer is already running ---
 System::Call 'kernel32::CreateMutexA(i 0, i 0, t "${{SETUPFILE}}") i .r1 ?e'
 Pop $R0
 StrCmp $R0 0 notAlreadyRunning
 MessageBox MB_OK|MB_ICONSTOP "The installer is already running." /SD IDOK
 LogEx::Write "The installer is already running."
 Abort
notAlreadyRunning:

 ; --- Initializing installation directory ---
!ifdef EMBEDDED_DEPLOYMENTTYPE
  ; Initialize $INSTDIR
  Call initInstallDir
!else
  ; standalone/none project initializes the installation directory in global section and not here.
!endif


!ifdef ENSURE_NEW_INSTALLDIR
 ; --- installation directory have to be a new directory ---
 ${{If}} ${{FileExists}} "$INSTDIR"
  ; choose a new directory
  StrCpy $0 0
  ${{DoWhile}} ${{FileExists}} "$INSTDIR_$0"
    ;Log "$INSTDIR_$0 exists"
    IntOp $0 $0 + 1
  ${{Loop}}
  StrCpy $INSTDIR "$INSTDIR_$0"
 ${{EndIf}}
 LogEx::Write "Installation directory choosed '$INSTDIR'"
!endif

 MessageBox MB_ICONINFORMATION|MB_OK "Installing ${{SBFPRODUCTNAME}} ${{SBFPROJECTVERSION}} in $INSTDIR." /SD IDOK
 LogEx::Write "Installing ${{SBFPRODUCTNAME}} ${{SBFPROJECTVERSION}} in $INSTDIR."
 

 ; --- Ask uninstall previous version --
 Call Uninstall_ask

FunctionEnd


;--------------------------------

; The name of the installer
Name "${{SBFPRODUCTNAME}}${{SBFPROJECTCONFIG}} v${{SBFPROJECTVERSION}}"

; Version information
VIAddVersionKey "ProductName"		"${{SBFPRODUCTNAME}}"
VIAddVersionKey "InternalName"		"${{SBFPROJECTNAME}}"
!ifndef EMBEDDED_DEPLOYMENTTYPE
VIAddVersionKey "deploymentType"	"standalone"
!else
VIAddVersionKey "deploymentType"	"embedded"
!endif
VIAddVersionKey "CompanyName"		"${{SBFPROJECTVENDOR}}"
VIAddVersionKey "LegalCopyright"	"(C) ${{SBFPROJECTVENDOR}}"
VIAddVersionKey "FileDescription"	"{projectDescription}"
VIAddVersionKey "FileVersion"		"{projectVersion}"
VIAddVersionKey "ProductVersion"	"{projectVersion}"

VIProductVersion "{productVersion}"

; icon of the installer
{icon}

; The file to write
OutFile "${{SETUPFILE}}"


; Request application privileges for Windows Vista
RequestExecutionLevel admin

;--------------------------------

; Pages

Page components

!ifdef EMBEDDED_DEPLOYMENTTYPE | ENSURE_NEW_INSTALLDIR
!else
 Page directory
!endif

Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; The stuff to install

Var installationValidation		; 0 valid, != 0 invalid

Section "${{SBFPRODUCTNAME}} core (required)"
  SectionIn RO

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Backups 'var' directory if already present
  ${{GetTime}} "" "L" $2 $1 $0 $6 $3 $4 $5
  CopyFiles /SILENT "$INSTDIR\\var" "$INSTDIR\\var_backup_$0-$1-$2_$3-$4-$5"
  RmDir /r "$INSTDIR\\var"

  ; Put files there
  LogEx::Write "Install all files of ${{SBFPROJECTNAME}}"
  !include "${{SBFPROJECTNAME}}_install_files.nsi"
 
  ; 'var' directory is created by SBFPROJECTNAME_install_files.nsi

  ; Changes ACL
  ; From MSDN
  ; SID: S-1-5-32-545
  ; Name: Users
  ; Description: A built-in group.
  ; After the initial installation of the operating system, the only member is the Authenticated Users group.
  ; When a computer joins a domain, the Domain Users group is added to the Users group on the computer.

  AccessControl::GrantOnFile "$INSTDIR\\var" "(S-1-5-32-545)" "FullAccess"
;AccessControl::EnableFileInheritance "$INSTDIR\\var"

  ; Redistributable
  LogEx::Write "Install Redistributable files of ${{SBFPROJECTNAME}}"
  !include "${{SBFPROJECTNAME}}_install_redist.nsi"


  ; --- customPointInstallationValidation ---
  ;	by default, installation is validated
  StrCpy $installationValidation 0

  {nsisCustomPointInstallationValidation}

  ; - Post customPointInstallationValidation -
  ${{If}} $installationValidation <> 0
	${{writeRegistryInstallAndUninstall}}
	WriteUninstaller "uninstall.exe"
	; todo status = error
	Abort "Can't validate installation."
  ${{Endif}}


  ; --- Migration var and packages ---
  !ifdef STANDALONE_DEPLOYMENTTYPE
	${{If}} $Uninstall_UninstallString != ''
		${{migratePackagesAndVar}} "$Uninstall_InstallDir" "$INSTDIR"
	${{Endif}}
  !endif


  ; --- Uninstall previous version ---
!ifdef AUTO_UNINSTALL
  Call UninstallFunction
!endif	; AUTO_UNINSTALL


  ; --- Registry ---
  ${{writeRegistryInstallAndUninstall}}

  ; --- uninstall.exe ---
  WriteUninstaller "uninstall.exe"

  ; --- Registry last part (version switch) ---
  !insertmacro writeRegCurrent $INSTDIR "${{SBFPROJECTVERSION}}"

SectionEnd



!ifndef EMBEDDED_DEPLOYMENTTYPE

Section "Start Menu Shortcuts"
  SectionIn RO

  SetShellVarContext all
  CreateDirectory "${{STARTMENUROOT}}"
{startMenuShortcuts}
  CreateShortCut "${{STARTMENUROOT}}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
SectionEnd


; Optional section (can be disabled by the user)
Section "Shortcut on desktop"

  SetShellVarContext all
{desktopShortcuts}

SectionEnd

!endif ; !ifndef EMBEDDED_DEPLOYMENTTYPE


;--------------------------------
; Uninstaller

Section "Uninstall"

  SetShellVarContext all

  SetOutPath $TEMP

  ; Remove files
  !include "${{SBFPROJECTNAME}}_uninstall_files.nsi"

  ; Remove redistributable
  !include "${{SBFPROJECTNAME}}_uninstall_redist.nsi"

  ; Remove 'var' directory ?
  !ifdef UNINSTALL_VAR_DIRECTORY
  ${{If}} ${{FileExists}} "$INSTDIR\\var"
	MessageBox MB_ICONQUESTION|MB_YESNO "Do you want to remove the 'var' directory ?" /SD IDYES IDNO dontRemoveVar
	RMDir /REBOOTOK /r "$INSTDIR\\var"
	LogEx::Write "Remove $INSTDIR\\var directory"
	dontRemoveVar:
  ${{Endif}}
  !endif

  ; Remove 'packages' directory ?
  !ifdef STANDALONE_DEPLOYMENTTYPE
  ${{If}} ${{FileExists}} "$INSTDIR\packages"
	RmDir /REBOOTOK "$INSTDIR\packages"
	LogEx::Write "Remove $INSTDIR\packages"
  ${{EndIf}}
  !endif

  ; Remove registry keys
  !insertmacro deleteRegInstall

  !insertmacro deleteRegUninstall ${{REGKEYUNINSTALLROOTVER}}

  ; Registry last part
  !insertmacro deleteRegCurrent $INSTDIR "${{SBFPROJECTVERSION}}"

  DeleteRegKey /ifempty HKLM "Software\${{SBFPROJECTVENDOR}}"

  ; Remove uninstaller
  Delete /REBOOTOK "$INSTDIR\uninstall.exe"

  ; Remove installation directory
  RmDir /REBOOTOK "$INSTDIR"


  ; ------ Section "Start Menu Shortcuts" ------
  ; Remove shortcuts, if any
{removeStartMenuShortcuts}
  Delete /REBOOTOK "${{STARTMENUROOT}}\*.*"
  ; Remove directories used
  RMDir /REBOOTOK "${{STARTMENUROOT}}"
  ; Remove root directory if empty
  RMDir /REBOOTOK "$SMPROGRAMS\${{SBFPROJECTVENDOR}}"


  ; ------ Section "Shortcut on desktop" ------
  {removeDesktopShortcuts}
 
SectionEnd
""".format(	definesSection = definesSection,
			projectName=env['sbf_project'],
			productName=env['productName'],
			projectNameCapitalized=capitalize(env['sbf_project']),
			projectVersion=env['version'],
			projectConfig=env.sbf.my_PostfixLinkedToMyConfig,
			projectVendor=env.sbf.myCompanyName,
			projectDescription=env['description'],
			date=lenv.sbf.myTimePostFix,
			productNameSection=PRODUCTNAME,
			productExe=PRODUCTEXE,
			productVersion='{0}.{1}.{2}.0'.format( env['sbf_version_major'], env['sbf_version_minor'], env['sbf_version_maintenance'] ),
			installationDirectorySection=installationDirectorySection,
			nsisCustomPointInstallationValidation=nsisCustomPointInstallationValidation,
			icon=ICON,
			startMenuShortcuts=SHORTCUT,
			desktopShortcuts=DESKTOPSHORTCUT,
#			quicklaunchShortcuts=QUICKLAUNCHSHORTCUT,
			removeStartMenuShortcuts=UNINSTALL_SHORTCUT,
			removeDesktopShortcuts=UNINSTALL_DESKTOPSHORTCUT,
#			removeQuicklaunchShortcuts=UNINSTALL_QUICKLAUNCHSHORTCUT
			)

		file.write( str_sbfNSISTemplate )


def __printGenerateNSISSetupProgram( target, source, env ):
	targetName = str(target[0])
	return ( '\nBuilding {0} setup program'.format(env['sbf_project']) )



### special zip related targets : zipRuntime, zipDeps, portable, zipPortable, zipDev, zipSrc and zip ###
# @todo zip*_[build,install,clean,mrproper]
# @todo zip doxygen

### ZIP/NSIS ###
def getTmpNSISPath( lenv ):
	sbf = lenv.sbf
	return join( sbf.myBuildPath, 'nsis' )

def __getProjectSubdir( lenv ):
	sbf = lenv.sbf
	return lenv['sbf_project'] + '_' + lenv['version'] + sbf.my_Platform_myCCVersion + sbf.my_FullPostfix

def getTmpNSISPortablePath( lenv ):
	return join( getTmpNSISPath(lenv), __getProjectSubdir(lenv) + '_portable_' + lenv.sbf.myTimePostFix )

def getTmpNSISDbgPath( lenv ):
	return join( getTmpNSISPath(lenv), __getProjectSubdir(lenv) + '_dbg_' + lenv.sbf.myTimePostFix )

def getTmpNSISSetupPath( lenv ):
	return join( getTmpNSISPath(lenv), __getProjectSubdir(lenv) + '_setup_' + lenv.sbf.myTimePostFix )

def initializeNSISInstallDirectories( sbf, lenv ):
	sbf.myNSISInstallDirectories = []

	if len( set(['portable', 'zipportable', 'nsis']) & sbf.myBuildTargets )>0:			# @todo set()
		# portable, zipportable
		portablePath = getTmpNSISPortablePath(lenv)
		varPortablePath = join( portablePath, 'var' )
		# To ensure that only latest files would be package in zip* and nsis targets, removes directories
		if not GetOption('weakPublishing'):
			Execute([Delete(varPortablePath), Delete(portablePath), Mkdir(portablePath), Mkdir(varPortablePath)])

			nsisSetupPath = getTmpNSISSetupPath(lenv)
			Execute([Delete(nsisSetupPath), Mkdir(nsisSetupPath)])
		else:
			print ('Weak publishing option is enabled. So intermediate files are not cleaned.\nTips: Do the first publishing of the day without --weak-publishing.\n')
		sbf.myNSISInstallDirectories.append( portablePath )
	#else nothing to do

	# for debugging
	#print 'myNSISInstallDirectories:', sbf.myNSISInstallDirectories


def getAllDebugFiles( env ):
	"""@return the list of all pdb files (on windows platform) for the project described by 'env' and all its dependencies.
	Append files returned by IUse::getDbg() for all 'uses' of the project described by 'env' and all its dependencies."""
	sbf = env.sbf
	debugFiles = []

	# Collect debug files from sbf projects
	for project in sbf.getAllDependencies( env ):
		lenv = sbf.getEnv(project)
		if 'PDB' in lenv: debugFiles.append( lenv['PDB'] )

	# Collect debug files from 'uses'
	for useNameVersion in sbf.getAllUses( env ):
		# Extracts name and version of incoming external dependency
		useName, useVersion = splitUsesName( useNameVersion )

		# Retrieves use object for incoming dependency
		use = UseRepository.getUse( useName )
		if use:
			#print useName, use.getDbg(useVersion)
			debugFiles.extend( use.getDbg(useVersion) )

	return debugFiles


def __warnAboutProjectExclude( env ):
	# Checks project exclusion to warn user
	if env['exclude'] and len(env['projectExclude'])>0:
		answer = askQuestion(	"WARNING: The following projects are excluded from the build : {0}\nWould you continue the process".format(env['projectExclude']),
								['(y)es', '(n)o'], env['queryUser'] )
		if answer == 'no':
			raise SCons.Errors.UserError( "Build interrupted by user." )
		#else continue the build


# @todo zip targets => package targets
def configureZipAndNSISTargets( lenv ):
	sbf = lenv.sbf

# @todo others targets (deps and runtime at least)
	#zipAndNSISTargets = set( ['zipruntime', 'zipdeps', 'portable', 'zipportable', 'zipdev', 'zipsrc', 'zip', 'nsis'] )
	zipAndNSISTargets = set( ['portable', 'zipportable', 'dbg', 'zipdbg', 'nsis'] )

# @todo clean targets, test clean targets
	cleanAndMrproperTargets = set( ['zip_clean', 'zip_mrproper', 'nsis_clean', 'nsis_mrproper'] )
	allTargets = zipAndNSISTargets | cleanAndMrproperTargets

	# Have to enable clean/mrproper
	if	len(cleanAndMrproperTargets & sbf.myBuildTargets) > 0:
		lenv.SetOption('clean', 1)

	if len(allTargets & sbf.myBuildTargets) > 0:
		__warnAboutProjectExclude(lenv)

		# lazzy scons lenv construction => @todo generalize (but must be optional)

		# 'portable' target
		portablePath = getTmpNSISPortablePath(lenv)
		portableZipPath = portablePath + '.7z'

		Alias( 'portable', ['infofile', 'install', 'deps'] )
		if ('portable' in sbf.myBuildTargets) and lenv['publishOn']:	createRsyncAction( lenv, '', portablePath, 'portable' )

		# 'zipportable' target
		if 'zipportable' in sbf.myBuildTargets:
			Execute( Delete(portableZipPath) )
			Alias( 'zipportable', ['infofile', 'install', 'deps'] )
			create7ZipCompressAction( lenv, portableZipPath, portablePath, 'zipportable' )
			if lenv['publishOn']:	createRsyncAction( lenv, '', portableZipPath, 'zipportable' )

		# 'dbg' target
		dbgPath = getTmpNSISDbgPath(lenv)
		zipDbgPath = dbgPath + '.7z'

		hasDbg = 'dbg' in sbf.myBuildTargets
		hasZipDbg = 'zipdbg' in sbf.myBuildTargets
		if hasDbg or hasZipDbg:
			if hasDbg:	Execute( Delete(dbgPath) )

			# Collect debug files from sbf projects and from 'uses'
			installTarget = []
			for file in getAllDebugFiles(lenv):
				installTarget += lenv.Install( join(dbgPath,'bin'), file )
			Alias( 'dbg', ['install', installTarget] )
			if hasDbg and lenv['publishOn']:	createRsyncAction( lenv, '', dbgPath, 'dbg' )

		# 'zipDbg' target
		if hasZipDbg:
			Execute( Delete(zipDbgPath) )
			Alias( 'zipdbg', 'dbg' )
			create7ZipCompressAction( lenv, zipDbgPath, dbgPath, 'zipdbg' )
			if lenv['publishOn']:	createRsyncAction( lenv, '', zipDbgPath, 'zipdbg' )

		# 'nsis' target
		if 'nsis' in sbf.myBuildTargets:
			tmpNSISSetupPath = getTmpNSISSetupPath(lenv)

			Alias( 'nsis', ['infofile', 'install', 'deps'] )

			# Copies redistributable related files (redistributable.nsi and redistributableDatabase.nsi)
			sbfNSISPath = join(sbf.mySCONS_BUILD_FRAMEWORK, 'NSIS' )
			installRedistributableFiles = lenv.Install( tmpNSISSetupPath, join(sbfNSISPath, 'redistributable.nsi') )

			sbfRcNsisPath = join(sbf.mySCONS_BUILD_FRAMEWORK, 'rc', 'nsis' )
			installRedistributableFiles += lenv.Install( tmpNSISSetupPath, join(sbfRcNsisPath, 'redistributableDatabase.nsi') )

			# Copies $SCONS_BUILD_FRAMEWORK/rc/nsis/Redistributable/*
			installRedistributableFiles += installAs( lenv, tmpNSISSetupPath, join(sbfRcNsisPath, 'Redistributable') )
			Alias( 'nsis', lenv.Command( 'dummy_nsis_print' + lenv['sbf_project'], 'dummy.in', Action(nopAction, printNSISGeneration) ) )
			Alias( 'nsis', installRedistributableFiles )

			# Generates several nsis files
			# project_install_redist.nsi and project_uninstall_redist.nsi
			nsisRedistFiles		= [ join( tmpNSISSetupPath, lenv['sbf_project'] + '_install_redist.nsi' ), join( tmpNSISSetupPath, lenv['sbf_project'] + '_uninstall_redist.nsi' ) ]
			Alias( 'nsis', lenv.Command( nsisRedistFiles, 'dummy.in', lenv.Action(redistGeneration, printRedistGeneration) ) )

			# project_install_files.nsi
			nsisInstallFiles	= join( tmpNSISSetupPath, lenv['sbf_project'] + '_install_files.nsi' )
			Alias( 'nsis', lenv.Command( nsisInstallFiles, portablePath, lenv.Action(generateNSISInstallFiles, printGenerateNSISInstallFiles) ) )

			# project_uninstall_files.nsi
			nsisUninstallFile	= join( tmpNSISSetupPath, lenv['sbf_project'] + '_uninstall_files.nsi' )
			Alias( 'nsis', lenv.Command( nsisUninstallFile, portablePath, lenv.Action(generateNSISUninstallFiles, printGenerateNSISUninstallFiles) ) )

			# Main nsis file
			nsisTargetFile = join(tmpNSISSetupPath, lenv['sbf_project']+'.nsi')
			sourceFiles = [nsisRedistFiles, nsisInstallFiles, nsisUninstallFile]

			Alias( 'nsis', lenv.Command( nsisTargetFile, sourceFiles, lenv.Action(generateNSISMainScript, printGenerateNSISMainScript) ) )

			# Build nsis project
			nsisLocation = locateProgram( 'nsis' )

			nsisSetupFile = '{project}_{version}{config}_{date}_setup.exe'.format(project=lenv['productName'], version=lenv['version'], config=sbf.my_PostfixLinkedToMyConfig, date=lenv.sbf.myTimePostFix)

			nsisBuildAction = lenv.Command(	join(tmpNSISSetupPath, nsisSetupFile), nsisTargetFile,
											"\"{0}\" $SOURCES".format(join(nsisLocation, 'makensis')) )
			Alias( 'nsis', lenv.Command('nsis_build.out', 'dummy.in', Action(nopAction, __printGenerateNSISSetupProgram) ) )
			Alias( 'nsis', nsisBuildAction )
			if lenv['publishOn']: createRsyncAction( lenv, '', join(tmpNSISSetupPath, nsisSetupFile), 'nsis' )



