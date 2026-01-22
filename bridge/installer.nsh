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

    ; Check if already installed and prompt user
    IfFileExists "$LOCALAPPDATA\Programs\Adzsend Bridge\Adzsend Bridge.exe" 0 check_programfiles
        MessageBox MB_YESNOCANCEL|MB_ICONQUESTION "Adzsend Bridge is already installed.$\r$\n$\r$\nWould you like to:$\r$\n$\r$\nYes - Uninstall the existing version first$\r$\nNo - Update/Reinstall over existing installation$\r$\nCancel - Cancel installation" IDYES uninstall_localappdata IDNO continue_install
        Abort

    check_programfiles:
    IfFileExists "$PROGRAMFILES\Adzsend Bridge\Adzsend Bridge.exe" 0 check_programfiles64
        MessageBox MB_YESNOCANCEL|MB_ICONQUESTION "Adzsend Bridge is already installed.$\r$\n$\r$\nWould you like to:$\r$\n$\r$\nYes - Uninstall the existing version first$\r$\nNo - Update/Reinstall over existing installation$\r$\nCancel - Cancel installation" IDYES uninstall_programfiles IDNO continue_install
        Abort

    check_programfiles64:
    IfFileExists "$PROGRAMFILES64\Adzsend Bridge\Adzsend Bridge.exe" 0 continue_install
        MessageBox MB_YESNOCANCEL|MB_ICONQUESTION "Adzsend Bridge is already installed.$\r$\n$\r$\nWould you like to:$\r$\n$\r$\nYes - Uninstall the existing version first$\r$\nNo - Update/Reinstall over existing installation$\r$\nCancel - Cancel installation" IDYES uninstall_programfiles64 IDNO continue_install
        Abort

    uninstall_localappdata:
        IfFileExists "$LOCALAPPDATA\Programs\Adzsend Bridge\Uninstall Adzsend Bridge.exe" 0 continue_install
            ExecWait '"$LOCALAPPDATA\Programs\Adzsend Bridge\Uninstall Adzsend Bridge.exe" /S'
            Goto continue_install

    uninstall_programfiles:
        IfFileExists "$PROGRAMFILES\Adzsend Bridge\Uninstall Adzsend Bridge.exe" 0 continue_install
            ExecWait '"$PROGRAMFILES\Adzsend Bridge\Uninstall Adzsend Bridge.exe" /S'
            Goto continue_install

    uninstall_programfiles64:
        IfFileExists "$PROGRAMFILES64\Adzsend Bridge\Uninstall Adzsend Bridge.exe" 0 continue_install
            ExecWait '"$PROGRAMFILES64\Adzsend Bridge\Uninstall Adzsend Bridge.exe" /S'

    continue_install:
    ; Initialize shortcut variables (defaults)
    StrCpy $CreateDesktopShortcut "1"
    StrCpy $CreateStartMenuShortcut "1"
    StrCpy $PinToTaskbar "0"
!macroend

; ============================================================================
; CUSTOM OPTIONS PAGE - Inserted via customHeader
; ============================================================================

!macro customHeader
    ; Insert custom page into the installer flow
    Page custom OptionsPageCreate OptionsPageLeave
!macroend

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
; CUSTOM UNINSTALL
; ============================================================================

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

    ; Unpin from taskbar (best effort)
    nsExec::ExecToStack 'powershell -ExecutionPolicy Bypass -Command "try { (New-Object -ComObject Shell.Application).Namespace(\"$INSTDIR\").ParseName(\"Adzsend Bridge.exe\").InvokeVerb(\"taskbarunpin\") } catch {}"'

    ; Remove app registry keys
    DeleteRegKey HKCU "Software\adzsend-bridge"
    DeleteRegKey HKCU "Software\Adzsend Bridge"
!macroend
