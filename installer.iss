#define MyAppName "Elektronik Okul"
#define MyAppVersion "2.3"
#define MyAppPublisher "Elektronik Okul"
#define MyAppExeName "Elektronik Okul.exe"

[Setup]
AppId={{A7E7A1C2-8A1B-4B5D-9E3E-OTOYOKLAMA2026}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Elektronik Okul
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=Elektronik_Okul_V2.3_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\Elektronik Okul\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Elektronik Okul\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

; Kullanıcı verileri {userappdata}\YoklamaOtomasyonuVerileri altında tutulur.
; Kaldırma işlemi bu klasörü silmez.
