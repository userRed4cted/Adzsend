!include "LogicLib.nsh"
!include "MUI2.nsh"
!include "FileFunc.nsh"

; ============================================================================
; INSTALLER CONFIGURATION
; ============================================================================

; Abort warning
!define MUI_ABORTWARNING
!define MUI_ABORTWARNING_TEXT "Are you sure you want to cancel Adzsend Bridge installation?"

; ============================================================================
; CUSTOM WELCOME PAGE
; ============================================================================

!define MUI_WELCOMEPAGE_TITLE "Welcome to Adzsend Bridge Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of Adzsend Bridge.$\r$\n$\r$\nAdzsend Bridge allows you to send Discord messages directly from your desktop.$\r$\n$\r$\nClick Next to continue."

; ============================================================================
; MACROS FOR ELECTRON-BUILDER
; ============================================================================

!macro customInit
    ; Kill running instance before install
    nsExec::ExecToStack 'taskkill /F /IM "Adzsend Bridge.exe"'
    Sleep 500

    ; Check if already installed - show uninstall popup
    IfFileExists "$LOCALAPPDATA\Programs\Adzsend Bridge\Adzsend Bridge.exe" 0 check_programfiles_init
        MessageBox MB_YESNO|MB_ICONQUESTION "Adzsend Bridge is already installed.$\r$\n$\r$\nWould you like to uninstall it?" IDYES cleanup_localappdata
        Abort

    check_programfiles_init:
    IfFileExists "$PROGRAMFILES\Adzsend Bridge\Adzsend Bridge.exe" 0 check_programfiles64_init
        MessageBox MB_YESNO|MB_ICONQUESTION "Adzsend Bridge is already installed.$\r$\n$\r$\nWould you like to uninstall it?" IDYES cleanup_programfiles
        Abort

    check_programfiles64_init:
    IfFileExists "$PROGRAMFILES64\Adzsend Bridge\Adzsend Bridge.exe" 0 done_check_init
        MessageBox MB_YESNO|MB_ICONQUESTION "Adzsend Bridge is already installed.$\r$\n$\r$\nWould you like to uninstall it?" IDYES cleanup_programfiles64
        Abort

    cleanup_localappdata:
        ; Try uninstaller first, then force cleanup
        IfFileExists "$LOCALAPPDATA\Programs\Adzsend Bridge\Uninstall Adzsend Bridge.exe" 0 force_cleanup_localappdata
            ExecWait '"$LOCALAPPDATA\Programs\Adzsend Bridge\Uninstall Adzsend Bridge.exe" /S'
            Goto done_check_init
        force_cleanup_localappdata:
            RMDir /r "$LOCALAPPDATA\Programs\Adzsend Bridge"
            Goto done_check_init

    cleanup_programfiles:
        IfFileExists "$PROGRAMFILES\Adzsend Bridge\Uninstall Adzsend Bridge.exe" 0 force_cleanup_programfiles
            ExecWait '"$PROGRAMFILES\Adzsend Bridge\Uninstall Adzsend Bridge.exe" /S'
            Goto done_check_init
        force_cleanup_programfiles:
            RMDir /r "$PROGRAMFILES\Adzsend Bridge"
            Goto done_check_init

    cleanup_programfiles64:
        IfFileExists "$PROGRAMFILES64\Adzsend Bridge\Uninstall Adzsend Bridge.exe" 0 force_cleanup_programfiles64
            ExecWait '"$PROGRAMFILES64\Adzsend Bridge\Uninstall Adzsend Bridge.exe" /S'
            Goto done_check_init
        force_cleanup_programfiles64:
            RMDir /r "$PROGRAMFILES64\Adzsend Bridge"

    done_check_init:
!macroend

; ============================================================================
; CUSTOM INSTALL - Create desktop shortcut and launch app
; ============================================================================

!macro customInstall
    ; Always create desktop shortcut (like Discord)
    CreateShortcut "$DESKTOP\Adzsend Bridge.lnk" "$INSTDIR\Adzsend Bridge.exe" "" "$INSTDIR\Adzsend Bridge.exe" 0

    ; App launch handled by electron-builder's runAfterFinish (when user clicks Finish)
!macroend

; ============================================================================
; CUSTOM UNINSTALL - Comprehensive cleanup
; ============================================================================

!macro customUnInstall
    ; Kill running instance before uninstall
    nsExec::ExecToStack 'taskkill /F /IM "Adzsend Bridge.exe"'
    Sleep 1000

    ; Remove installation directory
    RMDir /r "$INSTDIR"

    ; Remove Electron/Chromium app data (includes all cache subdirectories)
    RMDir /r "$APPDATA\adzsend-bridge"
    RMDir /r "$APPDATA\Adzsend Bridge"
    RMDir /r "$LOCALAPPDATA\adzsend-bridge"
    RMDir /r "$LOCALAPPDATA\Adzsend Bridge"
    RMDir /r "$LOCALAPPDATA\adzsend-bridge-updater"

    ; Remove electron-store config files
    Delete "$APPDATA\adzsend-bridge\adzsend-bridge-config.json"
    Delete "$APPDATA\Adzsend Bridge\adzsend-bridge-config.json"

    ; Remove from all possible install locations
    RMDir /r "$LOCALAPPDATA\Programs\Adzsend Bridge"
    RMDir /r "$PROGRAMFILES\Adzsend Bridge"
    RMDir /r "$PROGRAMFILES64\Adzsend Bridge"

    ; Remove auto-start registry entries (current user - no admin required)
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "AdzsendBridge"
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Adzsend Bridge"
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "adzsend-bridge"

    ; Remove desktop shortcut
    Delete "$DESKTOP\Adzsend Bridge.lnk"

    ; Remove Start Menu shortcuts
    RMDir /r "$SMPROGRAMS\Adzsend Bridge"
    Delete "$SMPROGRAMS\Adzsend Bridge.lnk"

    ; Remove app registry keys (current user - no admin required)
    DeleteRegKey HKCU "Software\adzsend-bridge"
    DeleteRegKey HKCU "Software\Adzsend Bridge"
    DeleteRegKey HKCU "Software\AdzsendBridge"

    ; Remove uninstall registry entry (current user - no admin required)
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\adzsend-bridge"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Adzsend Bridge"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{adzsend-bridge}"

    ; Clean up temp files using PowerShell (NSIS RMDir doesn't support wildcards)
    nsExec::ExecToStack 'powershell -ExecutionPolicy Bypass -Command "Remove-Item -Path \"$TEMP\adzsend-bridge*\" -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path \"$TEMP\Adzsend Bridge*\" -Recurse -Force -ErrorAction SilentlyContinue"'

    ; Show success message
    MessageBox MB_OK|MB_ICONINFORMATION "Adzsend Bridge has been successfully uninstalled."
!macroend
