#define MyAppName "Elektronik Okul V2.0"
#define MyAppVersion "1.1"
#define MyAppPublisher "Elektronik Okul"
#define MyAppExeName "Elektronik Okul V2.0.exe"

[Setup]
AppId={{A7E7A1C2-8A1B-4B5D-9E3E-OTOYOKLAMA2026}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Elektronik Okul V2.0
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=Elektronik_Okul_V2.0_Setup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

; Kullanıcı verileri {userappdata}\YoklamaOtomasyonuVerileri altında tutulur.
; Kaldırma işlemi bu klasörü silmez.
