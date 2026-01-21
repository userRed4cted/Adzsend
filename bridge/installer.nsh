; Custom NSIS installer script for Adzsend Bridge

!macro customInstall
  ; Check if already installed
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${UNINSTALL_APP_KEY}" "UninstallString"
  StrCmp $0 "" done

  ; Show message box asking what to do
  MessageBox MB_YESNOCANCEL|MB_ICONQUESTION "Adzsend Bridge is already installed.$\n$\nWould you like to:$\n$\n  Yes = Reinstall (update)$\n  No = Uninstall$\n  Cancel = Exit" IDYES reinstall IDNO uninstall

  ; Cancel - exit installer
  Quit

  uninstall:
    ; Run uninstaller
    ExecWait '"$0" /S'
    Quit

  reinstall:
    ; Continue with installation (will overwrite)

  done:
!macroend

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
