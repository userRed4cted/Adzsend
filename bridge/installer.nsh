; Custom NSIS installer script for Adzsend Bridge

!include "LogicLib.nsh"

Var UninstallPath

; Check for existing installation BEFORE installer wizard appears
!macro customInit
  ; Check if already installed
  ReadRegStr $UninstallPath HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{${UNINSTALL_APP_KEY}}" "UninstallString"

  ${If} $UninstallPath != ""
    ; Already installed - show prompt
    MessageBox MB_YESNOCANCEL|MB_ICONQUESTION "Adzsend Bridge is already installed.$\r$\n$\r$\n• Yes = Reinstall (update to this version)$\r$\n• No = Uninstall completely$\r$\n• Cancel = Exit setup" IDYES continueInstall IDNO runUninstall

    ; Cancel - exit
    Abort

    runUninstall:
      ; Run the uninstaller silently
      ExecWait '"$UninstallPath" /S'
      Abort

    continueInstall:
      ; Continue with reinstall
  ${EndIf}
!macroend

; Thorough cleanup on uninstall
!macro customUnInstall
  ; Clean up installation directory
  RMDir /r "$INSTDIR"

  ; Remove app data (config, secret key, etc.)
  RMDir /r "$APPDATA\adzsend-bridge"

  ; Remove startup entry if exists
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "AdzsendBridge"

  ; Remove desktop shortcut
  Delete "$DESKTOP\Adzsend Bridge.lnk"

  ; Remove start menu shortcuts
  RMDir /r "$SMPROGRAMS\Adzsend Bridge"
!macroend
