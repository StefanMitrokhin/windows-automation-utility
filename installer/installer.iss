#define MyAppName "DeskKit"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Stefan Mitrokhin"
#define MyAppURL "https://github.com/StefanMitrokhin/windows-automation-utility"
#define MyAppExeName "DeskKit.exe"
#define MyAppId "{{8F3C1A2E-6B47-4D91-9C5E-2A7F0B4D8E16}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\DeskKit
DefaultGroupName=DeskKit
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=DeskKit-Setup-{#MyAppVersion}
SetupIconFile=..\deskkit\assets\icon.ico
UninstallDisplayIcon={app}\DeskKit\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
MinVersion=10.0
VersionInfoVersion=0.1.0.0
VersionInfoCompany=Stefan Mitrokhin
VersionInfoDescription=DeskKit setup
VersionInfoProductName=DeskKit
CloseApplications=yes
UsedUserAreasWarning=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Ярлык на рабочем столе"; GroupDescription: "Ярлыки:"; Flags: checkedonce

[Files]
Source: "..\dist\DeskKit\*"; DestDir: "{app}\DeskKit"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\DeskKit-cli\*"; DestDir: "{app}\DeskKit-cli"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DeskKit"; Filename: "{app}\DeskKit\{#MyAppExeName}"
Name: "{group}\Удалить DeskKit"; Filename: "{uninstallexe}"
Name: "{autodesktop}\DeskKit"; Filename: "{app}\DeskKit\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\DeskKit\{#MyAppExeName}"; Description: "Запустить DeskKit"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C schtasks /Delete /TN ""\DeskKit\Backup"" /F & exit /B 0"; Flags: runhidden
Filename: "{cmd}"; Parameters: "/C schtasks /Delete /TN ""DeskKit Backup"" /F & exit /B 0"; Flags: runhidden