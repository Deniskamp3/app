; Inno Setup Script для СтройУчёт
; Версия 1.0.0

[Setup]
AppName=СтройУчёт
AppVersion=1.0.0
AppPublisher=Маторин И.П.
DefaultDirName={autopf}\StroyUchet
DefaultGroupName=СтройУчёт
OutputBaseFilename=StroyUchet_Setup_v1.0.0
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\StroyUchet.exe
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
WizardStyle=modern

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "dist\StroyUchet.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\СтройУчёт"; Filename: "{app}\StroyUchet.exe"
Name: "{group}\Удалить СтройУчёт"; Filename: "{uninstallexe}"
Name: "{commondesktop}\СтройУчёт"; Filename: "{app}\StroyUchet.exe"

[Run]
Filename: "{app}\StroyUchet.exe"; Description: "Запустить"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
end;
