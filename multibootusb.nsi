;--------------------------------
;NSIS script for creating multibootusb setup file

Name "multibootusb 8.2.0"
OutFile "multibootusb-8.2.0-setup.exe"

SetCompressor lzma

;--------------------------------
;!Include Modern UI
!include "MUI2.nsh"
;--------------------------------


;--------------------------------
;	Pages
  !insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  !insertmacro MUI_LANGUAGE "English"

;--------------------------------


InstallDir "$PROGRAMFILES\multibootusb"
InstallDirRegKey HKEY_LOCAL_MACHINE "SOFTWARE\multibootusb" ""

DirText $(s_InstallHere)

Icon data\tools\multibootusb.ico

Section "Dummy Section" SecDummy

	; Install files.
	SetOverwrite on

	SetOutPath "$INSTDIR"
	File /r "dist\multibootusb\*"
	
	SetOutPath "$INSTDIR\data"
	File /r "data\*"
	
	; Create shortcut.
	SetOutPath -
	CreateDirectory "$SMPROGRAMS\multibootusb"
	CreateShortCut "$SMPROGRAMS\multibootusb\multibootusb.lnk" "$INSTDIR\multibootusb.exe"
	CreateShortCut "$SMPROGRAMS\multibootusb\Uninstall multibootusb.lnk" "$INSTDIR\uninst.exe" "" "$INSTDIR\uninst.exe" 0

	; Optionally start program.
	MessageBox MB_YESNO|MB_ICONQUESTION "Do you want to run multibootusb now?" IDNO SkipRunProgram
	Exec "$INSTDIR\multibootusb.exe"
SkipRunProgram:

	; Create uninstaller.
	WriteRegStr HKEY_LOCAL_MACHINE "SOFTWARE\multibootusb" "" "$INSTDIR"
	WriteRegStr HKEY_LOCAL_MACHINE "Software\Microsoft\Windows\CurrentVersion\Uninstall\multibootusb" "DisplayName" "multibootusb (remove only)"
	WriteRegStr HKEY_LOCAL_MACHINE "Software\Microsoft\Windows\CurrentVersion\Uninstall\multibootusb" "UninstallString" '"$INSTDIR\uninst.exe"'
	WriteUninstaller "$INSTDIR\uninst.exe"

SectionEnd

UninstallText $(s_UnInstall)

Section Uninstall

	; Delete shortcuts.
	Delete "$SMPROGRAMS\multibootusb\multibootusb.lnk"
	Delete "$SMPROGRAMS\multibootusb\Uninstall multibootusb.lnk"
	RMDir "$SMPROGRAMS\multibootusb"
	Delete "$DESKTOP\multibootusb.lnk"

	; Delete registry keys.
	Delete "$INSTDIR\uninst.exe"
	DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\multibootusb"
	DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\multibootusb"

	; Remove the installation directories.
	RMDir /R "$INSTDIR"

SectionEnd
