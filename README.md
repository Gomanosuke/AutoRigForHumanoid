![Maya](https://img.shields.io/static/v1?message=Maya&color=37A5CC&logo=autodeskmaya&logoColor=white&label=)
![Python](https://img.shields.io/static/v1?message=Python&color=3776AB&logo=python&logoColor=white&label=)

# AutoRigForHumanoid

## 📕 概要

Unity HUmanoid規格に準拠して作成された3Dモデルへのリギング、およびリギングされた3Dモデルのアニメーション作業をサポートする。

Debugや一部アクセサリなどの作成にClaudeを利用している。

## 🖥️ 動作環境

- **Windows** Autodesk Maya 2027
- **Windows** Autodesk Maya 2026
- **Windows** Autodesk Maya 2025

## 🔧 インストールと起動方法

1. `Documents\maya\scripts` フォルダーに、`AutoRigForHumanoid` という名前のフォルダーを新規作成。このリポジトリをクローンするか `📦Downlowd Zip` して配置する。
2. Maya のスクリプトエディターの Python タブで以下を実行する。必要であればシェルフに登録する。

### 全機能を使う
全てのツールを含んだメインウィンドウを表示する。
   ```python
   import AutoRigForHumanoid
   AutoRigForHumanoid.show_window()
   ```

### アニメーションサポート機能を使う
アニメーション作業時利用できる ピッカーウィンドウのみを表示する。
   ```python
   from AutoRigForHumanoid import picker
   picker.show_ui()
   ```

## 📖 ドキュメント
[Document](/Document.md)

## 📢 ライセンス

[MIT License](/License.md)