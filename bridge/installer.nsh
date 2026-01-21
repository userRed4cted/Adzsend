!include "LogicLib.nsh"

!macro customInit
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{${UNINSTALL_APP_KEY}}" "UninstallString"
  ${If} $0 == ""
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{${UNINSTALL_APP_KEY}}" "UninstallString"
  ${EndIf}

  ${If} $0 != ""
    MessageBox MB_YESNOCANCEL|MB_ICONQUESTION "Adzsend Bridge is already installed.$\r$\n$\r$\n• Yes = Reinstall (update to this version)$\r$\n• No = Uninstall completely$\r$\n• Cancel = Exit setup" IDYES continueInstall IDNO runUninstall
    Abort

    runUninstall:
      ExecWait '"$0" /S'
      Abort

    continueInstall:
  ${EndIf}
!macroend

!macro customUnInstall
  RMDir /r "$INSTDIR"
  RMDir /r "$APPDATA\adzsend-bridge"
  RMDir /r "$APPDATA\Adzsend Bridge"
  RMDir /r "$LOCALAPPDATA\adzsend-bridge"
  RMDir /r "$LOCALAPPDATA\Adzsend Bridge"
  RMDir /r "$LOCALAPPDATA\adzsend-bridge-updater"

  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "AdzsendBridge"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Adzsend Bridge"
  DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "AdzsendBridge"
  DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "Adzsend Bridge"

  Delete "$DESKTOP\Adzsend Bridge.lnk"
  Delete "$COMMONDESKTOP\Adzsend Bridge.lnk"

  RMDir /r "$SMPROGRAMS\Adzsend Bridge"
  RMDir /r "$COMMONPROGRAMS\Adzsend Bridge"

  DeleteRegKey HKCU "Software\adzsend-bridge"
  DeleteRegKey HKCU "Software\Adzsend Bridge"
  DeleteRegKey HKLM "Software\adzsend-bridge"
  DeleteRegKey HKLM "Software\Adzsend Bridge"
!macroend
