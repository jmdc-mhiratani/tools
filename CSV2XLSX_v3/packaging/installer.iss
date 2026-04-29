
; CSV2XLSX v2.2.0 インストーラースクリプト
[Setup]
AppName=CSV2XLSX
AppVersion=2.2.0
AppPublisher=CSV2XLSX Team
AppPublisherURL=https://github.com/your-username/CSV2XLSX_v2
DefaultDirName={autopf}\CSV2XLSX
DefaultGroupName=CSV2XLSX
OutputBaseFilename=CSV2XLSX_v2.2.0_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "デスクトップにアイコンを作成"; GroupDescription: "追加アイコン:"

[Files]
Source: "dist\CSV2XLSX_v2.2.0.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "dist\CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\sample_data\*"; DestDir: "{app}\sample_data"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\CSV2XLSX"; Filename: "{app}\CSV2XLSX_v2.2.0.exe"
Name: "{group}\{cm:UninstallProgram,CSV2XLSX}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\CSV2XLSX"; Filename: "{app}\CSV2XLSX_v2.2.0.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\CSV2XLSX_v2.2.0.exe"; Description: "CSV2XLSXを起動"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
