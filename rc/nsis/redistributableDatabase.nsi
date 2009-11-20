### Redistributable\Codec ###
!define TSCC	"codec_tscc.exe"
;MessageBox MB_YESNO "Install Windows video codec for viewing TechSmith-encoded videos ?" /SD IDYES IDNO endTscc

!define ENSHARPENDECODER	"codec_ensharpendecoder_win.exe"
; MessageBox MB_YESNO "Install Windows video codec for viewing Ensharpen-encoded videos ?" /SD IDYES IDNO endEnsharpendecoder

### Redistributable\VCPP ###
# CLVERSION_DEPENDENCY
!define VCPP2005SP1		"Microsoft Visual C++ 2005 SP1 Redistributable Package (x86)_vcredist_x86.exe"
!define VCPP2008SP1		"Microsoft Visual C++ 2008 SP1 Redistributable Package (x86)_vcredist_x86.exe"

!define CL80			"${VCPP2005SP1}"
!define CL80EXP			"${CL80}"
!define CL90			"${VCPP2008SP1}"
!define CL90EXP			"${CL90}"
; MessageBox MB_YESNO "Install Microsoft Visual C++ 2005 SP1 Redistributable Package (x86) ?" /SD IDYES IDNO endVCPP2005SP1
