!include "LogicLib.nsh"

; Close the app before install/uninstall
!macro customInit
  ; Kill running instance before install
  nsExec::ExecToStack 'taskkill /F /IM "Adzsend Bridge.exe"'
  Sleep 500
!macroend

!macro customUnInstall
  ; Kill running instance before uninstall
  nsExec::ExecToStack 'taskkill /F /IM "Adzsend Bridge.exe"'
  Sleep 500

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
