!include "LogicLib.nsh"

!macro customInit
  ; Check if already installed
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{${UNINSTALL_APP_KEY}}" "UninstallString"

  ${If} $0 != ""
    ; Already installed - silently uninstall old version first
    ExecWait '"$0" /S'
  ${EndIf}
!macroend

!macro customUnInstall
  ; Remove installation directory
  RMDir /r "$INSTDIR"

  ; Remove app data
  RMDir /r "$APPDATA\adzsend-bridge"
  RMDir /r "$APPDATA\Adzsend Bridge"
  RMDir /r "$LOCALAPPDATA\adzsend-bridge"
  RMDir /r "$LOCALAPPDATA\Adzsend Bridge"
  RMDir /r "$LOCALAPPDATA\adzsend-bridge-updater"

  ; Remove auto-start registry entries
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "AdzsendBridge"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Adzsend Bridge"

  ; Remove shortcuts
  Delete "$DESKTOP\Adzsend Bridge.lnk"
  RMDir /r "$SMPROGRAMS\Adzsend Bridge"

  ; Remove app registry keys
  DeleteRegKey HKCU "Software\adzsend-bridge"
  DeleteRegKey HKCU "Software\Adzsend Bridge"
!macroend
