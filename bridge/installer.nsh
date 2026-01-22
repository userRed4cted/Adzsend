!include "LogicLib.nsh"
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "nsDialogs.nsh"

; Custom variables
Var CreateDesktopShortcut
Var CreateStartMenuShortcut
Var PinToTaskbar
Var RunAfterInstall
Var OptionsCheckbox1
Var OptionsCheckbox2
Var OptionsCheckbox3
Var OptionsCheckbox4

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

    ; Initialize shortcut variables (defaults)
    StrCpy $CreateDesktopShortcut "1"
    StrCpy $CreateStartMenuShortcut "1"
    StrCpy $PinToTaskbar "0"
    StrCpy $RunAfterInstall "1"

    ; Check if already installed - show uninstall popup
    IfFileExists "$LOCALAPPDATA\Programs\Adzsend Bridge\Adzsend Bridge.exe" 0 check_programfiles_init
        MessageBox MB_YESNO|MB_ICONQUESTION "Adzsend Bridge is already installed.$\r$\n$\r$\nWould you like to uninstall it?" IDYES uninstall_localappdata
        Abort

    check_programfiles_init:
    IfFileExists "$PROGRAMFILES\Adzsend Bridge\Adzsend Bridge.exe" 0 check_programfiles64_init
        MessageBox MB_YESNO|MB_ICONQUESTION "Adzsend Bridge is already installed.$\r$\n$\r$\nWould you like to uninstall it?" IDYES uninstall_programfiles
        Abort

    check_programfiles64_init:
    IfFileExists "$PROGRAMFILES64\Adzsend Bridge\Adzsend Bridge.exe" 0 done_check_init
        MessageBox MB_YESNO|MB_ICONQUESTION "Adzsend Bridge is already installed.$\r$\n$\r$\nWould you like to uninstall it?" IDYES uninstall_programfiles64
        Abort

    uninstall_localappdata:
        IfFileExists "$LOCALAPPDATA\Programs\Adzsend Bridge\Uninstall Adzsend Bridge.exe" 0 abort_after_uninstall
            ExecWait '"$LOCALAPPDATA\Programs\Adzsend Bridge\Uninstall Adzsend Bridge.exe" /S'
            Goto abort_after_uninstall

    uninstall_programfiles:
        IfFileExists "$PROGRAMFILES\Adzsend Bridge\Uninstall Adzsend Bridge.exe" 0 abort_after_uninstall
            ExecWait '"$PROGRAMFILES\Adzsend Bridge\Uninstall Adzsend Bridge.exe" /S'
            Goto abort_after_uninstall

    uninstall_programfiles64:
        IfFileExists "$PROGRAMFILES64\Adzsend Bridge\Uninstall Adzsend Bridge.exe" 0 abort_after_uninstall
            ExecWait '"$PROGRAMFILES64\Adzsend Bridge\Uninstall Adzsend Bridge.exe" /S'

    abort_after_uninstall:
        ; Exit installer after uninstall completes
        Abort

    done_check_init:
!macroend

; ============================================================================
; CUSTOM PAGES - Options page (shown after installation completes)
; ============================================================================

; Page order: Welcome -> License -> Directory -> InstFiles -> [customHeader] -> Finish
; Options page appears after files are installed, user selects options, then clicks Finish

!macro customHeader
    Page custom OptionsPageCreate OptionsPageLeave
!macroend

; ============================================================================
; OPTIONS PAGE
; ============================================================================

Function OptionsPageCreate
    nsDialogs::Create 1018
    Pop $0

    ${If} $0 == error
        Abort
    ${EndIf}

    ; Title
    ${NSD_CreateLabel} 0 0 100% 20u "Installation complete! Choose your options:"
    Pop $0

    ; Run after install checkbox
    ${NSD_CreateCheckbox} 0 30u 100% 12u "Run Adzsend Bridge"
    Pop $OptionsCheckbox4
    ${NSD_SetState} $OptionsCheckbox4 ${BST_CHECKED}

    ; Desktop shortcut checkbox
    ${NSD_CreateCheckbox} 0 48u 100% 12u "Create desktop shortcut"
    Pop $OptionsCheckbox1
    ${NSD_SetState} $OptionsCheckbox1 ${BST_CHECKED}

    ; Start menu shortcut checkbox
    ${NSD_CreateCheckbox} 0 66u 100% 12u "Create Start Menu shortcut"
    Pop $OptionsCheckbox2
    ${NSD_SetState} $OptionsCheckbox2 ${BST_CHECKED}

    ; Pin to taskbar checkbox
    ${NSD_CreateCheckbox} 0 84u 100% 12u "Pin to taskbar"
    Pop $OptionsCheckbox3
    ${NSD_SetState} $OptionsCheckbox3 ${BST_UNCHECKED}

    nsDialogs::Show
FunctionEnd

Function OptionsPageLeave
    ; Get checkbox states
    ${NSD_GetState} $OptionsCheckbox1 $CreateDesktopShortcut
    ${NSD_GetState} $OptionsCheckbox2 $CreateStartMenuShortcut
    ${NSD_GetState} $OptionsCheckbox3 $PinToTaskbar
    ${NSD_GetState} $OptionsCheckbox4 $RunAfterInstall

    ; Convert BST_CHECKED (1) to "1", BST_UNCHECKED (0) to "0"
    ${If} $CreateDesktopShortcut == ${BST_CHECKED}
        StrCpy $CreateDesktopShortcut "1"
    ${Else}
        StrCpy $CreateDesktopShortcut "0"
    ${EndIf}

    ${If} $CreateStartMenuShortcut == ${BST_CHECKED}
        StrCpy $CreateStartMenuShortcut "1"
    ${Else}
        StrCpy $CreateStartMenuShortcut "0"
    ${EndIf}

    ${If} $PinToTaskbar == ${BST_CHECKED}
        StrCpy $PinToTaskbar "1"
    ${Else}
        StrCpy $PinToTaskbar "0"
    ${EndIf}

    ${If} $RunAfterInstall == ${BST_CHECKED}
        StrCpy $RunAfterInstall "1"
    ${Else}
        StrCpy $RunAfterInstall "0"
    ${EndIf}

    ; Create shortcuts now (after user selects options)
    ${If} $CreateDesktopShortcut == "1"
        CreateShortcut "$DESKTOP\Adzsend Bridge.lnk" "$INSTDIR\Adzsend Bridge.exe" "" "$INSTDIR\Adzsend Bridge.exe" 0
    ${EndIf}

    ${If} $CreateStartMenuShortcut == "1"
        CreateDirectory "$SMPROGRAMS\Adzsend Bridge"
        CreateShortcut "$SMPROGRAMS\Adzsend Bridge\Adzsend Bridge.lnk" "$INSTDIR\Adzsend Bridge.exe" "" "$INSTDIR\Adzsend Bridge.exe" 0
        CreateShortcut "$SMPROGRAMS\Adzsend Bridge\Uninstall Adzsend Bridge.lnk" "$INSTDIR\Uninstall Adzsend Bridge.exe"
    ${EndIf}

    ${If} $PinToTaskbar == "1"
        nsExec::ExecToStack 'powershell -ExecutionPolicy Bypass -Command "(New-Object -ComObject Shell.Application).Namespace(\"$INSTDIR\").ParseName(\"Adzsend Bridge.exe\").InvokeVerb(\"taskbarpin\")"'
    ${EndIf}

    ; Launch app if checkbox is checked
    ${If} $RunAfterInstall == "1"
        Exec '"$INSTDIR\Adzsend Bridge.exe"'
    ${EndIf}
FunctionEnd

; ============================================================================
; CUSTOM INSTALL - Shortcuts and launch handled in OptionsPageLeave
; ============================================================================

!macro customInstall
    ; Shortcuts and app launch are handled in OptionsPageLeave (after user selects options)
    ; This macro runs during InstFiles, before the options page is shown
!macroend

; ============================================================================
; CUSTOM UNINSTALL - Comprehensive cleanup
; ============================================================================

!macro customUnInstall
    ; Kill running instance before uninstall
    nsExec::ExecToStack 'taskkill /F /IM "Adzsend Bridge.exe"'
    Sleep 1000

    ; Unpin from taskbar BEFORE removing files (best effort)
    nsExec::ExecToStack 'powershell -ExecutionPolicy Bypass -Command "try { (New-Object -ComObject Shell.Application).Namespace(\"$INSTDIR\").ParseName(\"Adzsend Bridge.exe\").InvokeVerb(\"taskbarunpin\") } catch {}"'

    ; Remove installation directory
    RMDir /r "$INSTDIR"

    ; Remove Electron/Chromium app data (includes all cache subdirectories)
    RMDir /r "$APPDATA\adzsend-bridge"
    RMDir /r "$APPDATA\Adzsend Bridge"
    RMDir /r "$LOCALAPPDATA\adzsend-bridge"
    RMDir /r "$LOCALAPPDATA\Adzsend Bridge"
    RMDir /r "$LOCALAPPDATA\adzsend-bridge-updater"

    ; Remove from all possible install locations
    RMDir /r "$LOCALAPPDATA\Programs\Adzsend Bridge"
    RMDir /r "$PROGRAMFILES\Adzsend Bridge"
    RMDir /r "$PROGRAMFILES64\Adzsend Bridge"

    ; Remove auto-start registry entries (current user - no admin required)
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "AdzsendBridge"
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Adzsend Bridge"
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "adzsend-bridge"

    ; Remove shortcuts (current user - no admin required)
    Delete "$DESKTOP\Adzsend Bridge.lnk"
    RMDir /r "$SMPROGRAMS\Adzsend Bridge"

    ; Remove app registry keys (current user - no admin required)
    DeleteRegKey HKCU "Software\adzsend-bridge"
    DeleteRegKey HKCU "Software\Adzsend Bridge"
    DeleteRegKey HKCU "Software\AdzsendBridge"

    ; Remove uninstall registry entry (current user - no admin required)
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\adzsend-bridge"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Adzsend Bridge"

    ; Clean up temp files using PowerShell (NSIS RMDir doesn't support wildcards)
    nsExec::ExecToStack 'powershell -ExecutionPolicy Bypass -Command "Remove-Item -Path \"$TEMP\adzsend-bridge*\" -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path \"$TEMP\Adzsend Bridge*\" -Recurse -Force -ErrorAction SilentlyContinue"'
!macroend
