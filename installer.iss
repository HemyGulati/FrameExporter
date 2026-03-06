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
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer_output
OutputBaseFilename=FrameExporter_Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
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
Name: "{group}\{#MyAppName}";                        Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}";  Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";                  Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
; ShouldInstallTesseract is a single function that combines both checks.
; Check: only accepts one function name — boolean expressions are not allowed.
Filename: "{tmp}\tesseract-ocr-w64-setup.exe"; Parameters: "/S"; StatusMsg: "Installing OCR engine — please wait..."; Flags: waituntilterminated runhidden; Check: ShouldInstallTesseract

Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]

// Returns True when Tesseract is NOT already on this machine.
function TesseractMissing: Boolean;
begin
  Result :=
    not RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Tesseract-OCR') and
    not RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\WOW6432Node\Tesseract-OCR') and
    not RegKeyExists(HKEY_CURRENT_USER,  'SOFTWARE\Tesseract-OCR');
end;

// Returns True when the bundled Tesseract installer file is present.
function TesseractInstallerPresent: Boolean;
begin
  Result := FileExists(ExpandConstant('{tmp}\tesseract-ocr-w64-setup.exe'));
end;

// Single wrapper used as Check: in [Run] — Inno Setup only accepts one function name.
function ShouldInstallTesseract: Boolean;
begin
  Result := TesseractMissing and TesseractInstallerPresent;
end;

// Adds a path to the current user's PATH env var if not already present.
procedure AddToUserPath(NewDir: String);
var
  OldPath: String;
  NewPath: String;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OldPath) then
    OldPath := '';
  if Pos(LowerCase(NewDir), LowerCase(OldPath)) = 0 then
  begin
    if (OldPath = '') then
      NewPath := NewDir
    else if OldPath[Length(OldPath)] = ';' then
      NewPath := OldPath + NewDir
    else
      NewPath := OldPath + ';' + NewDir;
    RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', NewPath);
    Log('Added to PATH: ' + NewDir);
  end;
end;

// After install: add Tesseract to PATH so pytesseract can find it.
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not TesseractMissing then
      AddToUserPath('C:\Program Files\Tesseract-OCR');
  end;
end;

// Customise the welcome screen text.
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
