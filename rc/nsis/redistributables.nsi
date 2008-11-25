### Redistributable\VCPP ###
!define VCPP2005SP1DIR	"Redistributable\Microsoft Visual C++ 2005 SP1 Redistributable Package (x86)"
!define VCPP2005SP1		"vcredist_x86.exe"

!macro InstallRedistributableVCPP2005SP1
	CreateDirectory "$INSTDIR\${VCPP2005SP1DIR}"
	File "/oname=$INSTDIR\${VCPP2005SP1DIR}\${VCPP2005SP1}" "${VCPP2005SP1DIR}\${VCPP2005SP1}"
!macroend

!macro RmRedistributableVCPP2005SP1
	Delete "$INSTDIR\${VCPP2005SP1DIR}\${VCPP2005SP1}"
	RmDir "$INSTDIR\${VCPP2005SP1DIR}"
!macroend

!macro LaunchRedistributableVCPP2005SP1
	MessageBox MB_YESNO "Install Microsoft Visual C++ 2005 SP1 Redistributable Package (x86) ?" /SD IDYES IDNO endVCPP2005SP1
	ExecWait "$INSTDIR\${VCPP2005SP1DIR}\${VCPP2005SP1}"
endVCPP2005SP1:
!macroend

### Redistributable\Codec ###
!define TSCCDIR	"Redistributable\Codec"
!define TSCC	"tscc.exe"

!macro InstallRedistributableTscc
	CreateDirectory "$INSTDIR\${TSCCDIR}"
	File "/oname=$INSTDIR\${TSCCDIR}\${TSCC}" "${TSCCDIR}\${TSCC}"
!macroend

!macro RmRedistributableTscc
	Delete "$INSTDIR\${TSCCDIR}\${TSCC}"
	RmDir "$INSTDIR\${TSCCDIR}"
!macroend

!macro LaunchRedistributableTscc
	MessageBox MB_YESNO "Install Windows video codec for viewing TechSmith-encoded videos ?" /SD IDYES IDNO endTscc
	ExecWait "$INSTDIR\${TSCCDIR}\${TSCC}"
endTscc:
!macroend



!define ENSHARPENDECODERDIR	"Redistributable\Codec"
!define ENSHARPENDECODER	"ensharpendecoder_win.exe"

!macro InstallRedistributableEnsharpendecoder
	CreateDirectory "$INSTDIR\${ENSHARPENDECODERDIR}"
	File "/oname=$INSTDIR\${ENSHARPENDECODERDIR}\${ENSHARPENDECODER}" "${ENSHARPENDECODERDIR}\${ENSHARPENDECODER}"
!macroend

!macro RmRedistributableEnsharpendecoder
	Delete "$INSTDIR\${ENSHARPENDECODERDIR}\${ENSHARPENDECODER}"
	RmDir "$INSTDIR\${ENSHARPENDECODERDIR}"
!macroend

!macro LaunchRedistributableEnsharpendecoder
	MessageBox MB_YESNO "Install Windows video codec for viewing Ensharpen-encoded videos ?" /SD IDYES IDNO endEnsharpendecoder
	ExecWait "$INSTDIR\${ENSHARPENDECODERDIR}\${ENSHARPENDECODER}"
endEnsharpendecoder:
!macroend
