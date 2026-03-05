; ============================================================
;  FrameExporter  —  Inno Setup Installer Script
;  Bundles and silently installs Tesseract OCR automatically.
;  Compile with Inno Setup Compiler → FrameExporter_Setup.exe
;
;  Download Inno Setup: https://jrsoftware.org/isinfo.php
;
;  BEFORE compiling: run build_windows.bat first so that
;  dist\FrameExporter.exe and assets\tesseract-ocr-w64-setup.exe exist.
; ============================================================

#define MyAppName      "FrameExporter"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "FrameExporter"
#define MyAppURL       ""
#define MyAppExeName   "FrameExporter.exe"

; Path to the Tesseract installer — downloaded automatically by build_windows.bat
#define TesseractInstaller "assets\tesseract-ocr-w64-setup.exe"

[Setup]
AppId={{A3F7C8D2-1B4E-4F9A-8C6D-5E2B7A903F41}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer_output
OutputBaseFilename=FrameExporter_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=assets\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; ── Main application ──────────────────────────────────────────────────────────
Source: "dist\{#MyAppExeName}";  DestDir: "{app}";        Flags: ignoreversion
Source: "dist\assets\*";         DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LICENSE.txt";           DestDir: "{app}";        Flags: ignoreversion

; ── Tesseract OCR installer (bundled, deleted from temp after install) ─────────
Source: "{#TesseractInstaller}"; DestDir: "{tmp}";        Flags: deleteafterinstall

[Icons]
Name: "{group}\{#MyAppName}";                       Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";                 Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; ── Step 1: Silently install Tesseract OCR ────────────────────────────────────
;   /S          = silent mode (no UI shown to the user)
;   /D=path     = install directory (must be last argument, no quotes)
Filename: "{tmp}\tesseract-ocr-w64-setup.exe"; \
    Parameters: "/S /D={pf}\Tesseract-OCR"; \
    StatusMsg: "Installing OCR engine (this may take a moment)..."; \
    Flags: waitprotterminate runhidden; \
    Check: TesseractNotInstalled

; ── Step 2: Launch app after install (optional) ───────────────────────────────
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent

[Registry]
; ── Add Tesseract install dir to PATH so pytesseract can find tesseract.exe ───
;    Written only when Tesseract was not already installed.
;    Admin install  → system-wide PATH (HKLM)
;    User install   → per-user PATH (HKCU)
Root: HKLM; \
    Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
    ValueType: expandsz; ValueName: "Path"; \
    ValueData: "{olddata};{pf}\Tesseract-OCR"; \
    Check: TesseractNotInstalled and IsAdminInstallMode; \
    Flags: preservestringtype uninsneveruninstall

Root: HKCU; \
    Subkey: "Environment"; \
    ValueType: expandsz; ValueName: "Path"; \
    ValueData: "{olddata};{pf}\Tesseract-OCR"; \
    Check: TesseractNotInstalled and not IsAdminInstallMode; \
    Flags: preservestringtype uninsneveruninstall

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// ─────────────────────────────────────────────────────────────────────────────
//  Returns True when Tesseract is NOT already installed.
//  Checks both 32-bit and 64-bit registry hives.
// ─────────────────────────────────────────────────────────────────────────────
function TesseractNotInstalled: Boolean;
begin
  Result :=
    not RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Tesseract-OCR') and
    not RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\WOW6432Node\Tesseract-OCR');
  if not Result then
    Log('Tesseract already installed — skipping OCR installation.')
  else
    Log('Tesseract not found — will install silently.');
end;

// ─────────────────────────────────────────────────────────────────────────────
//  Custom welcome message
// ─────────────────────────────────────────────────────────────────────────────
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption :=
    'This will install FrameExporter {#MyAppVersion} on your computer.'
    + #13#10 + #13#10
    + 'What you can do with FrameExporter:'                       + #13#10
    + '  • Extract frames from videos at custom intervals'        + #13#10
    + '  • Export a CSV with frame names, numbers & timestamps'   + #13#10
    + '  • Automatically detect numbers inside frames'            + #13#10
    + #13#10
    + 'Everything is included — the OCR engine (Tesseract) will'  + #13#10
    + 'be installed automatically in the background.'             + #13#10
    + 'No extra downloads or steps required.'                     + #13#10
    + #13#10
    + 'Click Next to continue.';
end;
