# GitHub Release 作成手順

## 📋 準備完了したファイル

### 🎯 アップロード対象ファイル
| ファイル名 | サイズ | 説明 |
|-----------|--------|------|
| `CSV2XLSX_v2.0_Portable.zip` | 34.4MB | ポータブル版（推奨） |
| `CSV2XLSX_v2.0.exe` | 34.8MB | Windows実行ファイル |

### 📄 リリースドキュメント
- ✅ `github_release_template.md` - リリースノート完成
- ✅ `release_info.json` - リリースメタデータ
- ✅ `CHANGELOG.md` - 変更履歴
- ✅ `USER_GUIDE.md` - ユーザーガイド

## 🚀 GitHub Release 作成手順

### Step 1: GitHubリポジトリにアクセス
1. リポジトリページにアクセス
2. 右側の「Releases」セクションをクリック
3. 「Create a new release」ボタンをクリック

### Step 2: リリース情報を入力

#### タグ情報
- **Tag version**: `v2.0.0`
- **Target**: `main` branch
- **Release title**: `CSV2XLSX v2.0.0 - Enterprise Edition`

#### リリースノート
`github_release_template.md`の内容をコピー＆ペースト

### Step 3: ファイルアップロード

#### アップロード順序（推奨）
1. **メインファイル**: `CSV2XLSX_v2.0_Portable.zip`（ポータブル版）
2. **実行ファイル**: `release/CSV2XLSX_v2.0.exe`（Windows実行ファイル）

#### アップロード方法
1. 「Attach binaries」セクションにファイルをドラッグ＆ドロップ
2. または「choose your files」をクリックしてファイル選択

### Step 4: リリース設定

#### オプション設定
- ✅ **This is a pre-release**: チェックしない（正式リリース）
- ✅ **Set as the latest release**: チェックする
- ✅ **Create a discussion for this release**: チェックする（推奨）

### Step 5: 公開
「Publish release」ボタンをクリック

## 🎯 リリース後の確認事項

### ✅ チェックリスト
- [ ] ダウンロードリンクが正常に動作
- [ ] ファイルサイズが正確に表示
- [ ] リリースノートが適切に表示
- [ ] タグが正しく作成されている

### 📊 期待される結果
- **Tag**: `v2.0.0` が作成される
- **Downloads**: 2つのファイルが利用可能
- **Documentation**: 完全なリリースノートが表示
- **Latest**: このリリースが最新として表示

## 🔗 関連リンク

- **Repository**: [プロジェクトURL]
- **Issues**: [プロジェクトURL]/issues
- **Discussions**: [プロジェクトURL]/discussions
- **Releases**: [プロジェクトURL]/releases

## 💡 補足情報

### ファイル説明
- **ポータブル版**: インストール不要、解凍して即使用可能
- **実行ファイル**: 単体の.exeファイル、ダブルクリックで起動

### サポート情報
- **対応OS**: Windows 10以降
- **メモリ**: 4GB以上推奨
- **機能**: CSV↔Excel変換、バッチ処理、自動エンコーディング検出

---
**📝 作成日**: 2025-09-23
**📍 バージョン**: v2.0.0
**🎯 対象**: Production Release