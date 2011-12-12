; SConsBuildFramework - Copyright (C) 2009, 2011, Nicolas Papier.
; Distributed under the terms of the GNU General Public License (GPL)
; as published by the Free Software Foundation.
; Author Nicolas Papier
;
; This script :
; @todo begin(Updates what the script do)
; - It will install files into a directory that the user selects
; - remember the installation directory (so if you install again, it will
; overwrite the old one automatically).
; - run as admin and installation occurs for all users
; - components chooser
; - has uninstall support
; - install/launch/uninstall Redistributable
; - and (optionally) installs start menu shortcuts (run all exe and uninstall).

; @todo write access on several directories
; @todo section with redistributable

; @todo mui
; @todo quicklaunch and desktop
; @todo repair/modify
; @todo LogSet on
; @todo end(Updates what the script do)

;--------------------------------
; @todo adds notepad++
; @todo silent mode
; @todo Shortcuts for sbfConfigure
; @todo others tools ( cygwin/rsync_ssh...) => installer embedded @todo embedded download
; @todo 32 and 64 bits version (Adds 64 bits detection and switch to 64bits version)
; PEP 370: Per-user site-packages Directory
; @todo installs python module for gtest
; @todo buildbot slave
; @todo adds new page(s) (with treeview) to select tools to install
; @todo expert mode/basic mode (yes to all)
; @todo Modern UI
; @todo a version without packages, but with download capabilities
; @todo unbootstrap to undo what has been done
; @todo portable apps for dt (eclipse, npp)

!define SBFPROJECTNAME		"SConsBuildFramework"
!define SBFPROJECTVERSION	"0-9-5"
!define PRODUCTNAME			${SBFPROJECTNAME}

;--------------------------------

!define REDISTDIR				"Redistributable"

!define PYTHON_REG_INSTALLPATH	"SOFTWARE\Python\PythonCore\2.7\InstallPath"

!define PYTHON							"python-2.7.2.msi"
!define PYWIN32							"pywin32-216.win32-py2.7.exe"
!define PYWIN32_UNINSTALL_STRING		"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\pywin32-py2.7"
!define PYSVN							"py27-pysvn-svn1615-1.7.5-1360.exe"
!define PYSVN_UNINSTALL_STRING			"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Python 2.7 PySVN_is1"
!define SCONS							"scons-2.1.0.win32.exe"
!define SCONS_UNINSTALL_STRING			"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\scons-py2.7"
!define PYREADLINE						"pyreadline-1.7.1.win32.exe"
!define PYREADLINE_UNINSTALL_STRING		"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\pyreadline-py2.7"

!define CYGWIN							"cygwinSetup.exe"

!define SEVENZIP						"7z920.exe"
!define SEVENZIP64						"7z920-x64.msi"
!define SEVENZIP_UNINSTALL_STRING		"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\7-Zip"

!define NSIS						"nsis-2.46-setup.exe"
; http://nsis.sourceforge.net/Nsisunz_plug-in
!define NSIS_PLUGIN_NSISUNZ			"NSIS_nsisunz.zip"
; http://nsis.sourceforge.net/AccessControl_plug-in
!define NSIS_PLUGIN_ACCESSCONTROL	"NSIS_AccessControl.zip"
; http://nsis.sourceforge.net/UAC_plug-in
!define NSIS_PLUGIN_UAC				"NSIS_UAC0-0-11d.zip"

; SConsBuildFramework redistributable
!define SCONS_BUILD_FRAMEWORK_REDIST	"SConsBuildFrameworkRedistributable.zip"

!define DOXYGEN							"doxygen-1.7.6.1-setup.exe"
!define DOXYGEN_UNINSTALL_STRING		"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\doxygen_is1"
!define GRAPHVIZ						"graphviz-2.26.3.msi"

!define SVNCLIENT						"CollabNetSubversion-client-1.6.15-1.win32.exe"
!define SVNCLIENT_UNINSTALL_STRING		"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\CollabNet Subversion Client"
!define TORTOISESVN						"TortoiseSVN-1.6.16.21511-win32-svn-1.6.17.msi"
!define TORTOISESVN64					"TortoiseSVN-1.6.16.21511-x64-svn-1.6.17.msi"


!define GTKMM_DEVEL						"gtkmm-win32-devel-2.22.0-2.exe"
!define GTKMM_DEVEL_UNINSTALL_STRING	"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\gtkmm"


!define VCSETUP_2008					"vcsetup_2008ExpressEdWebInstall.exe"
!define VCSETUP_2010					"vcsetup_2010ExpressEdWebInstall.exe"


### Functions ###
Function launchBootstrap
  ReadRegStr $0 HKLM ${PYTHON_REG_INSTALLPATH} ""
  ;MessageBox MB_OK "launchBootstrap:Python is installed at: $0"
  ;ReadEnvStr $1 SCONS_BUILD_FRAMEWORK
  ;MessageBox MB_OK "launchBootstrap:SCONS_BUILD_FRAMEWORK=$1"
  ExecWait '"$0python.exe" "$INSTDIR\initScripts\bootstrap.py"'
FunctionEnd

Function getUser_SCONS_BUILD_FRAMEWORK
  ;ReadEnvStr $0 SCONS_BUILD_FRAMEWORK
  ;MessageBox MB_OK "getUser_SCONS_BUILD_FRAMEWORK=$0"
  ReadRegStr $0 HKCU "Environment" "SCONS_BUILD_FRAMEWORK"
  ;MessageBox MB_OK "getUser_SCONS_BUILD_FRAMEWORK=$0"
  FileOpen $1 $EXEDIR\SCONS_BUILD_FRAMEWORK.txt w
  FileWrite $1 $0
  FileClose $1
FunctionEnd



### Redistributable ###

!include redistributable.nsi

!macro InstallAndUnzipRedistributableOfNSISPlugins file
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +9
	IfFileExists "$INSTDIR\Redistributable\*.*" +2
	CreateDirectory "$INSTDIR\Redistributable"
	File "/oname=$INSTDIR\Redistributable\${file}" "Redistributable\${file}"
	ReadRegStr $0 HKLM "Software\NSIS" ""
	nsisunz::UnzipToLog "$INSTDIR\Redistributable\${file}" $0
	; Always check result on stack
	Pop $0
	StrCmp $0 "success" +2
	DetailPrint "$0" ;print error message to log
!macroend


;
SetCompressor lzma

;
RequestExecutionLevel user /* RequestExecutionLevel REQUIRED! */
!include UAC.nsh
;!include LogicLib.nsh
!include WinMessages.nsh
;!include "FileFunc.nsh"		; for GetParent

; @todo see MultiUser.nsh
; Contains SCONS_BUILD_FRAMEWORK environment variable (not initialized at the beginning)
Var SBF_DIR

Function .onInit
	InitPluginsDir
;	UAC::IsAdmin
;	${If} $0 < 1
;		MessageBox MB_OK "onInit:isAdmin then : NO"
;		ReadEnvStr $0 SCONS_BUILD_FRAMEWORK
;		MessageBox MB_OK "onInit:SCONS_BUILD_FRAMEWORK=$0"
;		FileOpen $1 $EXEDIR\SCONS_BUILD_FRAMEWORK.txt w
;		FileWrite $1 $0
;		FileClose $1
;	${Else}
;		MessageBox MB_OK "onInit:isAdmin else : YES"
;		FileOpen $0 $EXEDIR\SCONS_BUILD_FRAMEWORK.txt r
;		FileRead $0 $1
;		FileClose $0
;		StrCpy $SBF_DIR $1
;		MessageBox MB_OK "onInit:SCONS_BUILD_FRAMEWORK=$1"
;		MessageBox MB_OK "onInit:SCONS_BUILD_FRAMEWORK=$SBF_DIR"
;	${EndIf}
;	MessageBox MB_OK "onInit:next"

	${UAC.I.Elevate.AdminOnly}

FunctionEnd

;--------------------------------

; The name of the installer
Name "${PRODUCTNAME}"

; The file to write
OutFile "${SBFPROJECTNAME}_${SBFPROJECTVERSION}_setup.exe"

; The default installation directory
InstallDir $PROGRAMFILES\${PRODUCTNAME}

; Registry key to check for directory (so if you install again, it will
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\${PRODUCTNAME}" "Install_Dir"

; Request application privileges for Windows Vista
; RequestExecutionLevel admin

;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------


; Optional section (can be disabled by the user)
;Section "Buildbot (slave only)"

;  SetShellVarContext all

  ; Set output path to the installation directory.
;  SetOutPath $INSTDIR
  ;SetDetailsView show

  ; Redistributable
; @todo Twisted_NoDocs-8.2.0.win32-py2.5.exe, PIL and buildbot-0.7.10p1.zip (p3 ?)

;SectionEnd


; Optional section (can be disabled by the user)
Section "Visual C++ 2008 Express Edition (web install)"

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  SetDetailsView show

  ; Redistributable
!insertmacro InstallAndLaunchRedistributable ${VCSETUP_2008} ""

SectionEnd


Section "Visual C++ 2010 Express Edition (web install)"

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  SetDetailsView show

  ; Redistributable
!insertmacro InstallAndLaunchRedistributable ${VCSETUP_2010} ""

SectionEnd


; Optional section (can be disabled by the user)
Section "Documentation tools"

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  SetDetailsView show

  ; Redistributable
!insertmacro InstallAndLaunchRedistributable ${DOXYGEN} ""
!insertmacro InstallAndMSILaunchRedistributable ${GRAPHVIZ} "/i"

SectionEnd


; Optional section (can be disabled by the user)
Section "Version control system"

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  SetDetailsView show

  ; Redistributable
!insertmacro InstallAndLaunchRedistributable ${SVNCLIENT} ""
!insertmacro InstallAndMSILaunchRedistributable ${TORTOISESVN} "/i"
!insertmacro InstallAndMSILaunchRedistributable ${TORTOISESVN64} "/i"

SectionEnd


; Optional section (can be disabled by the user)
Section "gtkmm SDK"

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  SetDetailsView show

  ; Redistributable
!insertmacro InstallAndLaunchRedistributable ${GTKMM_DEVEL} ""

SectionEnd



; The stuff to install
; @todo separates prerequisites and core
Section "Sbf prerequisites and core (required)"

  SectionIn RO

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  SetDetailsView show

  ; Redistributable

;PYTHON
!insertmacro InstallAndMSILaunchRedistributable ${PYTHON} "/i" ; @todo "ALLUSERS=1 ADDLOCAL=DefaultFeature"
;PYWIN32
!insertmacro InstallAndLaunchRedistributable ${PYWIN32} ""
;PYSVN
!insertmacro InstallAndLaunchRedistributable ${PYSVN} ""
;SCONS
!insertmacro InstallAndLaunchRedistributable ${SCONS} ""
;PYREADLINE
!insertmacro InstallAndLaunchRedistributable ${PYREADLINE} ""

;CYGWIN
; @todo http://cygwin.com/faq/faq.setup.html#faq.setup.cli
MessageBox MB_YESNO "Do you want to launch cygwin setup ?$\nRecommanded installation for SConsBuildFramework :$\ndefault selection + openssh + rsync" IDYES +1 IDNO cygwin_end
!insertmacro InstallAndLaunchRedistributableQ ${CYGWIN} ""
cygwin_end:

;SEVENZIP
!insertmacro InstallAndLaunchRedistributable ${SEVENZIP} ""
;SEVENZIP64
!insertmacro InstallAndMSILaunchRedistributable ${SEVENZIP64} "/i"

;NSIS
!insertmacro InstallAndLaunchRedistributable ${NSIS} ""

;NSIS plugins
!insertmacro InstallAndUnzipRedistributableOfNSISPlugins ${NSIS_PLUGIN_NSISUNZ}
!insertmacro InstallAndUnzipRedistributableOfNSISPlugins ${NSIS_PLUGIN_ACCESSCONTROL}
!insertmacro InstallAndUnzipRedistributableOfNSISPlugins ${NSIS_PLUGIN_UAC}

;bootstrap.py
  MessageBox MB_YESNO "Launch SConsBuildFramework bootstrap python script ?" /SD IDYES IDNO +7
  CreateDirectory "$INSTDIR\initScripts"
  AccessControl::GrantOnFile "$INSTDIR\initScripts" "(S-1-5-32-545)" "FullAccess"
  File "/oname=$INSTDIR\initScripts\bootstrap.py" "bootstrap.py"
  File "/oname=$INSTDIR\initScripts\sbfEnvironment.py" "..\src\sbfEnvironment.py"
  File "/oname=$INSTDIR\initScripts\sbfPaths.py" "..\src\sbfPaths.py"
  HideWindow
  GetFunctionAddress $0 launchBootstrap
  UAC::ExecCodeSegment $0
  showWindow $HWNDPARENT "${SW_SHOW}"

; Installs SConsBuildFrameworkRedistributable.zip
  ; Initializes SBF_DIR (i.e. SCONS_BUILD_FRAMEWORK environment variable for the current user)
  HideWindow
  GetFunctionAddress $0 getUser_SCONS_BUILD_FRAMEWORK
  UAC::ExecCodeSegment $0
  FileOpen $0 $EXEDIR\SCONS_BUILD_FRAMEWORK.txt r
  FileRead $0 $1
  FileClose $0
  ; MessageBox MB_OK "from $EXEDIR\SCONS_BUILD_FRAMEWORK.txt:SCONS_BUILD_FRAMEWORK=$1"
  StrCpy $SBF_DIR $1
  Delete "$EXEDIR\SCONS_BUILD_FRAMEWORK.txt"
  showWindow $HWNDPARENT "${SW_SHOW}"

  ; Installs SCONS_BUILD_FRAMEWORK_REDIST
  ; Gets parent directory of SCONS_BUILD_FRAMEWORK => ${GetParent} "$SBF_DIR" $0
  !insertmacro InstallAndUnzipRedistributable ${SCONS_BUILD_FRAMEWORK_REDIST} "$SBF_DIR"

  ; Start Menu Shortcuts
  ReadRegStr $0 HKLM ${PYTHON_REG_INSTALLPATH} ""
  ;MessageBox MB_OK "Python is installed at: $0"

  CreateDirectory "$SMPROGRAMS\${PRODUCTNAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCTNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  SetOutPath "$INSTDIR\initScripts"
  CreateShortCut "$SMPROGRAMS\${PRODUCTNAME}\Launch bootstrap.lnk" "$0python.exe" '"$INSTDIR\initScripts\bootstrap.py"' "$0python.exe" 0
  ; @todo CreateShortCut "$SMPROGRAMS\${PRODUCTNAME}\Launch sbfConfigure" "$0python.exe" "%SCONS_BUILD_FRAMEWORK%/$INSTDIR\bootstrap.py" "$0python.exe" 0

  ; Write the installation path into the registry
  WriteRegStr HKLM "SOFTWARE\${PRODUCTNAME}" "Install_Dir" "$INSTDIR"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCTNAME}" "DisplayName" "${PRODUCTNAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCTNAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCTNAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCTNAME}" "NoRepair" 1
  WriteUninstaller "uninstall.exe"

SectionEnd


; @todo Adds menu shortcuts for launching sub-installer and sbf uninstall.

; Optional section (can be disabled by the user)
;Section "Start Menu Shortcuts"

;  CreateDirectory "$SMPROGRAMS\${PRODUCTNAME}"

;  SetOutPath $INSTDIR\bin

;  CreateDirectory "$SMPROGRAMS\${PRODUCTNAME}\tools"
;  CreateShortCut "$SMPROGRAMS\${PRODUCTNAME}\${PRODUCTNAME0}.lnk" "$INSTDIR\bin\${PRODUCTEXE0}" "" "$INSTDIR\bin\${PRODUCTEXE0}" 0
;  CreateShortCut "$SMPROGRAMS\${PRODUCTNAME}\tools\${PRODUCTNAME1}.lnk" "$INSTDIR\bin\${PRODUCTEXE1}" "" "$INSTDIR\bin\${PRODUCTEXE1}" 0

;  

;  SetOutPath $INSTDIR

;SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"

  SetShellVarContext all

  ; @todo Remove redistributables (SCONS_BUILD_FRAMEWORK_REDIST and NSIS_PLUGIN_*)
  ; @todo SBF_DIR !insertmacro RmRedistributable ${SCONS_BUILD_FRAMEWORK_REDIST}

; @todo unbootstrap

; @todo NSIS plugins

; NSIS
ReadRegStr $0 HKLM "Software\NSIS" ""
MessageBox MB_YESNO "Uninstall NSIS ?" /SD IDYES IDNO +2
ExecWait "$0\uninst-nsis.exe"
!insertmacro RmRedistributable ${NSIS}

;SEVENZIP
!insertmacro UninstallString "7-Zip" ${SEVENZIP_UNINSTALL_STRING}
!insertmacro RmRedistributable ${SEVENZIP}
;SEVENZIP64
!insertmacro MSIUninstallRedistributable ${SEVENZIP64} ""
!insertmacro RmRedistributable ${SEVENZIP64}


;CYGWIN
MessageBox MB_ICONINFORMATION "cygwin must be uninstalled manually."

; PYREADLINE
!insertmacro UninstallString "pyreadline" ${PYREADLINE_UNINSTALL_STRING}
!insertmacro RmRedistributable ${PYREADLINE}
; SCONS
!insertmacro UninstallString "scons" ${SCONS_UNINSTALL_STRING}
!insertmacro RmRedistributable ${SCONS}
; PYSVN
!insertmacro UninstallString "pysvn" "${PYSVN_UNINSTALL_STRING}"
!insertmacro RmRedistributable ${PYSVN}
; PYWIN32
!insertmacro UninstallString "pywin32" ${PYWIN32_UNINSTALL_STRING}
!insertmacro RmRedistributable ${PYWIN32}
; PYTHON
!insertmacro MSIUninstallRedistributable ${PYTHON} ""
!insertmacro RmRedistributable ${PYTHON}

; DOXYGEN
!insertmacro UninstallString "doxygen" ${DOXYGEN_UNINSTALL_STRING}
!insertmacro RmRedistributable ${DOXYGEN}
; GRAPHVIZ
!insertmacro MSIUninstallRedistributable ${GRAPHVIZ} ""
!insertmacro RmRedistributable ${GRAPHVIZ}

; SVNCLIENT
!insertmacro UninstallString "CollabNet subversion (client version)" "${SVNCLIENT_UNINSTALL_STRING}"
!insertmacro RmRedistributable ${SVNCLIENT}
; TORTOISESVN
!insertmacro MSIUninstallRedistributable ${TORTOISESVN} ""
!insertmacro RmRedistributable ${TORTOISESVN}
; TORTOISESVN64
!insertmacro MSIUninstallRedistributable ${TORTOISESVN64} ""
!insertmacro RmRedistributable ${TORTOISESVN64}

; GTKMM_DEVEL
!insertmacro UninstallString "gtkmm" ${GTKMM_DEVEL_UNINSTALL_STRING}
!insertmacro RmRedistributable ${GTKMM_DEVEL}

  RmDir $INSTDIR\Redistributable

 ; bootstrap.py
  Delete $INSTDIR\bootstrap.py
  Delete $INSTDIR\sbfEnvironment.py
  Delete $INSTDIR\sbfPaths.py

  RmDir "$INSTDIR\initScripts"

  ; Remove registry keys
  DeleteRegKey HKLM "SOFTWARE\${PRODUCTNAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCTNAME}"

  ; Remove uninstaller
  Delete $INSTDIR\uninstall.exe

  ; Remove installation directory
  RmDir $INSTDIR

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\${PRODUCTNAME}\*.*"
  ; Remove directories used
  RMDir "$SMPROGRAMS\${PRODUCTNAME}"

SectionEnd
