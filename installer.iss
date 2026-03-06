; ============================================================
;  FrameExporter — Inno Setup Installer Script
;  Author  : Hemy Gulati
;  GitHub  : https://github.com/HemyGulati/FrameExporter
;  Version : 1.0.0
;
;  BEFORE compiling: run build_windows.bat first so that
;  dist\FrameExporter.exe and assets\tesseract-ocr-w64-setup.exe exist.
;
;  Compile: open this file in Inno Setup 6 → Ctrl+F9
;  Output:  installer_output\FrameExporter_Setup.exe
; ============================================================

#define MyAppName      "FrameExporter"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "Hemy Gulati"
#define MyAppURL       "https://github.com/HemyGulati/FrameExporter"
#define MyAppExeName   "FrameExporter.exe"

[Setup]
AppId={{A3F7C8D2-1B4E-4F9A-8C6D-5E2B7A903F41}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Install location
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; Allow user to choose between admin (all users) and per-user install
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Uninstall entry — shows correctly in Windows Settings → Apps & Features
; and legacy Control Panel → Programs and Features
UninstallDisplayName={#MyAppName} {#MyAppVersion}
UninstallDisplayIcon={app}\assets\icon.ico
CreateUninstallRegKey=yes

AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer_output
OutputBaseFilename=FrameExporter_Setup
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}";               DestDir: "{app}";        Flags: ignoreversion
Source: "assets\icon.ico";                    DestDir: "{app}\assets"; Flags: ignoreversion
Source: "LICENSE.txt";                        DestDir: "{app}";        Flags: ignoreversion
; Tesseract installer is embedded into FrameExporter_Setup.exe at compile time.
Source: "assets\tesseract-ocr-w64-setup.exe"; DestDir: "{tmp}";        Flags: ignoreversion deleteafterinstall

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
; Desktop shortcut (optional, off by default)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
; Silently install Tesseract OCR — only if not already present on this machine
Filename: "{tmp}\tesseract-ocr-w64-setup.exe"; Parameters: "/S"; StatusMsg: "Installing OCR engine — please wait..."; Flags: waituntilterminated runhidden; Check: ShouldInstallTesseract

; Offer to launch the app immediately after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove everything left in the install folder on uninstall
Type: filesandordirs; Name: "{app}"

[Code]

// ── TesseractMissing ─────────────────────────────────────────────────────────
// Returns True when Tesseract is NOT already installed on this machine.
// Checks both 64-bit and 32-bit (WOW) registry hives.
function TesseractMissing: Boolean;
begin
  Result :=
    not RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Tesseract-OCR') and
    not RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\WOW6432Node\Tesseract-OCR') and
    not RegKeyExists(HKEY_CURRENT_USER,  'SOFTWARE\Tesseract-OCR');
end;

// ── TesseractInstallerPresent ─────────────────────────────────────────────────
// Returns True when the bundled Tesseract setup file has been extracted to {tmp}.
function TesseractInstallerPresent: Boolean;
begin
  Result := FileExists(ExpandConstant('{tmp}\tesseract-ocr-w64-setup.exe'));
end;

// ── ShouldInstallTesseract ────────────────────────────────────────────────────
// Single wrapper function used as Check: in [Run].
// Inno Setup Check: only accepts one function name — no inline boolean expressions.
function ShouldInstallTesseract: Boolean;
begin
  Result := TesseractMissing and TesseractInstallerPresent;
end;

// ── AddToUserPath ─────────────────────────────────────────────────────────────
// Appends a directory to the current user PATH if not already present.
procedure AddToUserPath(NewDir: String);
var
  OldPath: String;
  NewPath: String;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OldPath) then
    OldPath := '';
  if Pos(LowerCase(NewDir), LowerCase(OldPath)) = 0 then
  begin
    if OldPath = '' then
      NewPath := NewDir
    else if OldPath[Length(OldPath)] = ';' then
      NewPath := OldPath + NewDir
    else
      NewPath := OldPath + ';' + NewDir;
    RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', NewPath);
    Log('Added to user PATH: ' + NewDir);
  end;
end;

// ── CurStepChanged ────────────────────────────────────────────────────────────
// After all files are installed, add Tesseract to the user PATH so that
// pytesseract can locate tesseract.exe without any manual configuration.
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not TesseractMissing then
      AddToUserPath('C:\Program Files\Tesseract-OCR');
  end;
end;

// ── InitializeWizard ──────────────────────────────────────────────────────────
// Customise the welcome screen shown to the user before installation begins.
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption :=
    'This will install FrameExporter {#MyAppVersion} on your computer.'
    + #13#10#13#10
    + 'What you can do with FrameExporter:'
    + #13#10
    + '  • Extract frames from any video at custom intervals'
    + #13#10
    + '  • Export a CSV with frame names, numbers and timestamps'
    + #13#10
    + '  • Automatically detect numbers inside frames (OCR)'
    + #13#10#13#10
    + 'Everything is included. The OCR engine (Tesseract) will be'
    + #13#10
    + 'installed silently — no extra steps needed.'
    + #13#10#13#10
    + 'Click Next to continue.';
end;
