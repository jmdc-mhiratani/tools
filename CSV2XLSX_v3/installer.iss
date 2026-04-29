
; CSV2XLSX v3.1.1 インストーラースクリプト (PySide6版)
[Setup]
AppName=CSV2XLSX
AppVersion=3.1.1
AppPublisher=CSV2XLSX Team
AppPublisherURL=https://github.com/your-username/CSV2XLSX_v2
DefaultDirName={autopf}\CSV2XLSX
DefaultGroupName=CSV2XLSX
OutputBaseFilename=CSV2XLSX_v3.1.1_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "デスクトップにアイコンを作成"; GroupDescription: "追加アイコン:"

[Files]
Source: "dist\CSV2XLSX_v3.1.1\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme; DestName: "README.md"

[Icons]
Name: "{group}\CSV2XLSX"; Filename: "{app}\CSV2XLSX_v3.1.1.exe"
Name: "{group}\{cm:UninstallProgram,CSV2XLSX}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\CSV2XLSX"; Filename: "{app}\CSV2XLSX_v3.1.1.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\CSV2XLSX_v3.1.1.exe"; Description: "CSV2XLSXを起動"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
