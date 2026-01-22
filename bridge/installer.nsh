!include "LogicLib.nsh"
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "nsDialogs.nsh"

; Custom variables
Var CreateDesktopShortcut
Var CreateStartMenuShortcut
Var PinToTaskbar
Var OptionsCheckbox1
Var OptionsCheckbox2
Var OptionsCheckbox3

; Variables for existing install dialog
Var ExistingInstallPath
Var ExistingInstallAction
Var ReinstallRadio
Var UninstallRadio

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

    ; Initialize variables
    StrCpy $ExistingInstallPath ""
    StrCpy $ExistingInstallAction "reinstall"
    StrCpy $CreateDesktopShortcut "1"
    StrCpy $CreateStartMenuShortcut "1"
    StrCpy $PinToTaskbar "0"

    ; Check if already installed - store path for later
    IfFileExists "$LOCALAPPDATA\Programs\Adzsend Bridge\Adzsend Bridge.exe" 0 check_programfiles_init
        StrCpy $ExistingInstallPath "$LOCALAPPDATA\Programs\Adzsend Bridge"
        Goto done_check_init

    check_programfiles_init:
    IfFileExists "$PROGRAMFILES\Adzsend Bridge\Adzsend Bridge.exe" 0 check_programfiles64_init
        StrCpy $ExistingInstallPath "$PROGRAMFILES\Adzsend Bridge"
        Goto done_check_init

    check_programfiles64_init:
    IfFileExists "$PROGRAMFILES64\Adzsend Bridge\Adzsend Bridge.exe" 0 done_check_init
        StrCpy $ExistingInstallPath "$PROGRAMFILES64\Adzsend Bridge"

    done_check_init:
!macroend

; ============================================================================
; CUSTOM PAGES - Using customWelcome to insert before directory page
; ============================================================================

; customWelcome inserts pages right after Welcome/License, before Directory
!macro customWelcome
    ; Insert existing install page (shown only if already installed)
    Page custom ExistingInstallPageCreate ExistingInstallPageLeave
!macroend

; customHeader inserts pages after Directory, before InstFiles
!macro customHeader
    ; Insert options page into the installer flow
    Page custom OptionsPageCreate OptionsPageLeave
!macroend

; ============================================================================
; EXISTING INSTALLATION PAGE
; ============================================================================

Function ExistingInstallPageCreate
    ; Skip this page if no existing installation
    StrCmp $ExistingInstallPath "" skip_existing_page

    nsDialogs::Create 1018
    Pop $0

    ${If} $0 == error
        Abort
    ${EndIf}

    ; Title
    ${NSD_CreateLabel} 0 0 100% 24u "Adzsend Bridge is already installed"
    Pop $0
    CreateFont $1 "Segoe UI" 12 700
    SendMessage $0 ${WM_SETFONT} $1 0

    ; Description
    ${NSD_CreateLabel} 0 30u 100% 24u "Choose how you want to proceed with the installation:"
    Pop $0

    ; Reinstall radio button (default selected)
    ${NSD_CreateRadioButton} 0 60u 100% 12u "Reinstall (install over existing)"
    Pop $ReinstallRadio
    ${NSD_SetState} $ReinstallRadio ${BST_CHECKED}

    ; Uninstall radio button
    ${NSD_CreateRadioButton} 0 78u 100% 12u "Uninstall first (clean install)"
    Pop $UninstallRadio

    ; Info text
    ${NSD_CreateLabel} 0 105u 100% 36u "Note: Reinstalling will keep your settings. Uninstalling first will remove all data and provide a fresh installation."
    Pop $0

    nsDialogs::Show
    Return

    skip_existing_page:
        Abort ; Skip this page
FunctionEnd

Function ExistingInstallPageLeave
    ; Check which option was selected
    ${NSD_GetState} $UninstallRadio $0

    ${If} $0 == ${BST_CHECKED}
        ; User chose to uninstall first
        StrCpy $ExistingInstallAction "uninstall"
        ; Run the uninstaller silently
        IfFileExists "$ExistingInstallPath\Uninstall Adzsend Bridge.exe" 0 done_uninstall
            ExecWait '"$ExistingInstallPath\Uninstall Adzsend Bridge.exe" /S'
        done_uninstall:
    ${Else}
        ; User chose to reinstall
        StrCpy $ExistingInstallAction "reinstall"
    ${EndIf}
FunctionEnd

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
    ${NSD_CreateLabel} 0 0 100% 20u "Choose installation options:"
    Pop $0

    ; Desktop shortcut checkbox
    ${NSD_CreateCheckbox} 0 30u 100% 12u "Create desktop shortcut"
    Pop $OptionsCheckbox1
    ${NSD_SetState} $OptionsCheckbox1 ${BST_CHECKED}

    ; Start menu shortcut checkbox
    ${NSD_CreateCheckbox} 0 48u 100% 12u "Create Start Menu shortcut"
    Pop $OptionsCheckbox2
    ${NSD_SetState} $OptionsCheckbox2 ${BST_CHECKED}

    ; Pin to taskbar checkbox
    ${NSD_CreateCheckbox} 0 66u 100% 12u "Pin to taskbar"
    Pop $OptionsCheckbox3
    ${NSD_SetState} $OptionsCheckbox3 ${BST_UNCHECKED}

    nsDialogs::Show
FunctionEnd

Function OptionsPageLeave
    ; Get checkbox states
    ${NSD_GetState} $OptionsCheckbox1 $CreateDesktopShortcut
    ${NSD_GetState} $OptionsCheckbox2 $CreateStartMenuShortcut
    ${NSD_GetState} $OptionsCheckbox3 $PinToTaskbar

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
FunctionEnd

; ============================================================================
; CUSTOM INSTALL - Create shortcuts based on user selection
; ============================================================================

!macro customInstall
    ; Create shortcuts based on user selection
    ${If} $CreateDesktopShortcut == "1"
        CreateShortcut "$DESKTOP\Adzsend Bridge.lnk" "$INSTDIR\Adzsend Bridge.exe" "" "$INSTDIR\Adzsend Bridge.exe" 0
    ${EndIf}

    ${If} $CreateStartMenuShortcut == "1"
        CreateDirectory "$SMPROGRAMS\Adzsend Bridge"
        CreateShortcut "$SMPROGRAMS\Adzsend Bridge\Adzsend Bridge.lnk" "$INSTDIR\Adzsend Bridge.exe" "" "$INSTDIR\Adzsend Bridge.exe" 0
        CreateShortcut "$SMPROGRAMS\Adzsend Bridge\Uninstall Adzsend Bridge.lnk" "$INSTDIR\Uninstall Adzsend Bridge.exe"
    ${EndIf}

    ${If} $PinToTaskbar == "1"
        ; Pin to taskbar using PowerShell (Windows 10/11)
        nsExec::ExecToStack 'powershell -ExecutionPolicy Bypass -Command "(New-Object -ComObject Shell.Application).Namespace(\"$INSTDIR\").ParseName(\"Adzsend Bridge.exe\").InvokeVerb(\"taskbarpin\")"'
    ${EndIf}
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
