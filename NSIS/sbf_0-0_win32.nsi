; SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
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

; @todo svn commit in sbf (run)
; @todo Adds 64 bits detection and switch to 64bits version
; @todo expert mode/basic mode (yes to all)
; @todo Modern UI 
; @todo a version without packages, but with download capabilities
; @todo unboostrap to undo what has been done

; @todo AccessControl.zip plugin installation (for NSIS)
; @toto Redistributable.zip installation (for NSIS)

; @todo others tools ( cygwin/rsync_ssh...)
; @todo silent mode

!define SBFPROJECTNAME		"SConsBuildFramework"
!define SBFPROJECTVERSION	"0-1"
!define PRODUCTNAME			"SConsBuildFramework"

;--------------------------------

!define REDISTDIR	"Redistributable"

!define PYTHON_REG_INSTALLPATH	"SOFTWARE\Python\PythonCore\2.5\InstallPath"

!define PYTHON			"python-2.5.4.msi"
!define PYWIN32			"pywin32-212.win32-py2.5.exe"
!define PYSVN			"py25-pysvn-svn161-1.7.0-1177.exe"
!define SCONS			"scons-1.2.0.win32.exe"
!define PYREADLINE		"pyreadline-1.5-win32-setup.exe"

!define NSIS			"nsis-2.44-setup.exe"


!define DOXYGEN				"doxygen-1.5.8-setup.exe"
!define GRAPHVIZ			"graphviz-2.16.1.exe"


!define SVNCLIENT			"CollabNetSubversion-client-1.6.1-2.win32.exe"
!define TORTOISESVN			"TortoiseSVN-1.6.1.16129-win32-svn-1.6.1.msi"
!define TORTOISESVN64		"TortoiseSVN-1.6.1.16129-x64-svn-1.6.1.msi"


!define GTKMM_DEVEL			"gtkmm-win32-devel-2.16.0-2.exe"


!define PYREADLINE_UNINSTALL_STRING	"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\pyreadline-py2.5"
!define SCONS_UNINSTALL_STRING		"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\scons-py2.5"
!define PYSVN_UNINSTALL_STRING		"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Python 2.5 PySVN_is1"
!define PYWIN32_UNINSTALL_STRING	"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\pywin32-py2.5"

!define DOXYGEN_UNINSTALL_STRING	"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\doxygen_is1"
!define GRAPHVIZ_REG_INSTALLPATH	"SOFTWARE\ATT\Graphviz"

!define SVNCLIENT_UNINSTALL_STRING	"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\CollabNet Subversion Client"


!define GTKMM_DEVEL_UNINSTALL_STRING	"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\gtkmm"


### Redistributable ###
; @todo should go in redistributables.nsi, because more generic
!macro InstallRedistributable file
	CreateDirectory "$INSTDIR\Redistributable"
	File "/oname=$INSTDIR\Redistributable\${file}" "Redistributable\${file}"
!macroend

!macro InstallRedistributableExt directory file
	CreateDirectory "$INSTDIR\${directory}"
	File "/oname=$INSTDIR\${directory}\${file}" "${directory}\${file}"
!macroend


!macro RmRedistributable file
	Delete "$INSTDIR\Redistributable\${file}"
	RmDir "$INSTDIR\Redistributable"
!macroend

!macro RmRedistributableExt directory file
	Delete "$INSTDIR\${directory}\${file}"
	RmDir "$INSTDIR\${directory}"
!macroend


!macro LaunchRedistributable file
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +2
	ExecWait "$INSTDIR\Redistributable\${file}"
!macroend

!macro LaunchRedistributableExt directory file
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +2
	ExecWait "$INSTDIR\${directory}\${file}"
!macroend


!macro MSILaunchRedistributableParams file params
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +2
	ExecWait '"msiexec" ${params} "$INSTDIR\Redistributable\${file}"'
!macroend

!macro MSIUninstallRedistributable file
	MessageBox MB_YESNO "Uninstall ${file} ?" /SD IDYES IDNO +2
	ExecWait '"msiexec" /x "$INSTDIR\Redistributable\${file}"'
!macroend


; @todo Checks if $0  empty
!macro UninstallString name hklmPath
	ReadRegStr $0 HKLM "${hklmPath}" "UninstallString"
	MessageBox MB_YESNO "Uninstall ${name} ?" /SD IDYES IDNO +2
	ExecWait $0
!macroend






!macro InstallAndLaunchRedistributable file
	!insertmacro InstallRedistributable ${file}
	!insertmacro LaunchRedistributable ${file}
!macroend

!macro InstallAndMSILaunchRedistributableParams file params
	!insertmacro InstallRedistributable ${file}
	!insertmacro MSILaunchRedistributableParams ${file} "${params}"
!macroend

;!include "redistributables.nsi"

;
RequestExecutionLevel user /* RequestExecutionLevel REQUIRED! */
!include UAC.nsh
;!include LogicLib.nsh
!include WinMessages.nsh

; @todo see MultiUser.nsh
;Var SBF_DIR

Function .onInit
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

;FIXME 
;PageEx directory
;  DirVar $SBF_DIR
;PageExEnd

Function launchBootstrap
  ReadRegStr $0 HKLM ${PYTHON_REG_INSTALLPATH} ""
  ;MessageBox MB_OK "launchBootstrap:Python is installed at: $0"
  ;ReadEnvStr $1 SCONS_BUILD_FRAMEWORK
  ;MessageBox MB_OK "launchBootstrap:SCONS_BUILD_FRAMEWORK=$1"
;MessageBox MB_OK "launchBootstrap:OUTDIR=$OUTDIR"
;Push $OUTDIR
;SetOutPath $INSTDIR
  MessageBox MB_YESNO "Launch SConsBuildFramework bootstrap python script ?" /SD IDYES IDNO +2
  ExecWait '"$0python.exe" "$INSTDIR\bootstrap.py"'
;Pop $0
;SetOutPath $0
;MessageBox MB_OK "launchBootstrap:OUTDIR=$OUTDIR"

FunctionEnd


UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------


; Optional section (can be disabled by the user)
Section "Documentation tools"

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Redistributable
!insertmacro InstallAndLaunchRedistributable ${DOXYGEN}
!insertmacro InstallAndLaunchRedistributable ${GRAPHVIZ}

SectionEnd


; Optional section (can be disabled by the user)
Section "Version control system"

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Redistributable
!insertmacro InstallAndLaunchRedistributable ${SVNCLIENT}
!insertmacro InstallAndMSILaunchRedistributableParams ${TORTOISESVN} "/i"
!insertmacro InstallAndMSILaunchRedistributableParams ${TORTOISESVN64} "/i"

; @todo portable apps for dt (eclipse, npp)

SectionEnd


; Optional section (can be disabled by the user)
Section "gtkmm"

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Redistributable
!insertmacro InstallAndLaunchRedistributable ${GTKMM_DEVEL}

SectionEnd



; The stuff to install
; @todo separates prerequisites and core
Section "Sbf prerequisites and core (required)"

  SectionIn RO

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Redistributable
  CreateDirectory $INSTDIR\${REDISTDIR}

  SetDetailsView show

;PYTHON
!insertmacro InstallAndMSILaunchRedistributableParams ${PYTHON} "/i" ; @todo "ALLUSERS=1 ADDLOCAL=DefaultFeature"
;PYWIN32
!insertmacro InstallAndLaunchRedistributable ${PYWIN32}
;PYSVN
!insertmacro InstallAndLaunchRedistributable ${PYSVN}
;SCONS
!insertmacro InstallAndLaunchRedistributable ${SCONS}
;PYREADLINE
!insertmacro InstallAndLaunchRedistributable ${PYREADLINE}

;NSIS
!insertmacro InstallAndLaunchRedistributable ${NSIS}

; bootstrap.py and Environment.py
  File "/oname=$INSTDIR\bootstrap.py" "bootstrap.py"
  File "/oname=$INSTDIR\Environment.py" "Environment.py"
 
  HideWindow
  GetFunctionAddress $0 launchBootstrap
  UAC::ExecCodeSegment $0
  showWindow $HWNDPARENT "${SW_SHOW}"

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

;  CreateShortCut "$SMPROGRAMS\${PRODUCTNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0

;  SetOutPath $INSTDIR

;SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"

  SetShellVarContext all

  ; Remove redistributables
; NSIS
ReadRegStr $0 HKLM "Software\NSIS" ""
MessageBox MB_YESNO "Uninstall NSIS ?" /SD IDYES IDNO +2
ExecWait "$0\uninst-nsis.exe"
!insertmacro RmRedistributable ${NSIS}

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
!insertmacro MSIUninstallRedistributable ${PYTHON}
!insertmacro RmRedistributable ${PYTHON}

; DOXYGEN
!insertmacro UninstallString "doxygen" ${DOXYGEN_UNINSTALL_STRING}
!insertmacro RmRedistributable ${DOXYGEN}
; GRAPHVIZ
ReadRegStr $0 HKLM ${GRAPHVIZ_REG_INSTALLPATH} InstallPath
MessageBox MB_YESNO "Uninstall Graphviz ?" /SD IDYES IDNO +2
ExecWait "$0\Uninstall.exe"
!insertmacro RmRedistributable ${GRAPHVIZ}

; SVNCLIENT
!insertmacro UninstallString "CollabNet subversion (client version)" "${SVNCLIENT_UNINSTALL_STRING}"
!insertmacro RmRedistributable ${SVNCLIENT}
; TORTOISESVN
!insertmacro MSIUninstallRedistributable ${TORTOISESVN}
!insertmacro RmRedistributable ${TORTOISESVN}
; TORTOISESVN64
!insertmacro MSIUninstallRedistributable ${TORTOISESVN64}
!insertmacro RmRedistributable ${TORTOISESVN64}

; GTKMM_DEVEL
!insertmacro UninstallString "gtkmm" ${GTKMM_DEVEL_UNINSTALL_STRING}
!insertmacro RmRedistributable ${GTKMM_DEVEL}

  RmDir $INSTDIR\Redistributable

  ; Remove registry keys
  DeleteRegKey HKLM "SOFTWARE\${PRODUCTNAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCTNAME}"

  ; Remove uninstaller
  Delete $INSTDIR\uninstall.exe

  ; Remove installation directory
  RmDir $INSTDIR

  ; Remove shortcuts, if any
;  Delete "$SMPROGRAMS\${PRODUCTNAME}\tools\*.*"
;  RMDir "$SMPROGRAMS\${PRODUCTNAME}\tools"

;  Delete "$SMPROGRAMS\${PRODUCTNAME}\*.*"
  ; Remove directories used
;  RMDir "$SMPROGRAMS\${PRODUCTNAME}"

SectionEnd
