# 開発者・AI エージェント向けガイド

このファイルは開発者と AI エージェント向けです。利用者向けの説明は [README.md](README.md) にあり、README からこのファイルへはリンクしていません。

## 前提とルール

- Maya 用 Python パッケージです。`Documents/maya/scripts/AutoRigForHumanoid` に置き、`from AutoRigForHumanoid import show_window` で起動します(`__init__.py`)。Maya 2025 以降(Picker が PySide6 を使用)。
- **このリポジトリは GitHub で公開されています。** 特定のプロジェクト・キャラクター・シーンのファイル名や名前を、コード・ドキュメント・コミットメッセージに含めないでください。作業用の `.ma` / `.mb` / `.fbx` は `.gitignore` で除外済みです。コミットしないでください。
- GUI は `maya.cmds` で組んでいます。GUI の呼び出しが Python レベルで通るかは `mayapy`(standalone)で確認できますが、見た目・タブの切り替え・ボタン操作は対話式の Maya でしか確認できません。

## README.md のルール

README.md は GitHub で第三者の利用者が読む文書です。AI・エージェント向けの情報は書かず、このファイルに書いてください(ユーザー指示、2026-09-24)。

- README に書くのは、利用者が操作・判断するのに必要なことだけです: 機能、動作環境、インストール、UI の操作手順、Unity 側の設定、制限事項。
- README に書かないもの(このファイルへ置く): エージェントへの指示や作業ルール、ファイル構成・関数名・内部データ構造などの実装の詳細、テスト手順、不具合の調査経緯、許容差などの検証の内部値。
- README からこのファイルへリンクしません。
- 文体は「です・ます」の自然な日本語にします。「〜の選択。」のような名詞止めの手順や体言止めの羅列にせず、手順は番号付きで「〜します」と書きます。
- ボタン名・タブ名は `gui.py` の実際のラベルと揃えます。UI を変えたら README の該当箇所も直します。

## ファイル構成

```
AutoRigForHumanoid/
├─ __init__.py             show_window()(gui を再読み込みして表示)
├─ gui.py                  メインウィンドウ(formLayout + タブ + 色分け)
├─ auto_apply.py           関節の自動割り当て(joint_name.json のキーワード照合)
├─ joint_name.json         自動割り当て用の名前キーワード
├─ autorig_preparation.py  ガイド(Orient / Position)作成
├─ autorig_createBase.py   リグ作成の入口(入力検証・Undo チャンク・失敗時 undo)
├─ autorig_createRig.py    体幹・頭・腕・脚・手のリグ構築
├─ autorig_utility.py      IK の曲がる側・ツイスト計算など共通処理
├─ nurvs_shape.json        コントローラー形状のテンプレート
├─ picker.py               Picker(PySide6, MayaQWidgetBaseMixin)
├─ designer_ui.ui          Picker の UI(Qt Designer)
├─ control_shape.py        コントロールシェイプの書き出し/読み込み
├─ rig_import.py           UUID 維持のリグ読み込み
├─ blendshape.py           ブレンドシェイプコントローラー
├─ fbx_shape_rename.py     FBX インポート補助、ブレンドシェイプ名の変換
└─ blendshape_name.json    ブレンドシェイプ名の変換表
```

## 設計上の要点

### メインウィンドウ(`gui.py`)

- ウィンドウ直下は `formLayout`。Picker フレームを上端に、`tabLayout` を残り全域に `attachForm` / `attachControl` で貼る。`columnLayout` だとタブの中身が希望サイズ止まりで、縦が極端に短くなる。
- タブ: `リグ制作` / `アクセサリ`(サブタブ `リグ読み込み`・`FBX`・`シェイプ`)/ `ブレンドシェイプ`。Picker は使用頻度が高いためタブに入れず常設。
- 色は `_COLOR_*` 定数。Maya 既定のグレーから大きく外れない淡い色に留める。
- GUI に説明文の行は置かない方針(利用者の要望)。
- ボタンの `command=` は各機能モジュールの関数を直接呼ぶだけにし、GUI 側にロジックを持たせない。

### リグ作成(`autorig_createBase.py`, `autorig_createRig.py`)

- `<キャラクター名>_Rig` が既にある、または Orient / Position ガイドが 1 セットに定まらない場合は、元のジョイントに触る前にエラーにする。
- 作成全体を `undoInfo` の 1 チャンクにまとめ、例外時は `cmds.undo()` で元のジョイントへの変更ごと戻す。
- `ARFH_information` ノードにコントローラー等の辞書(`obj_dic`)を UUID で記録し、`<characterName>_names` 属性にノード名との対応を持つ。Picker と `rig_import.py` はこれを参照する。`characterName` を書き換えると Picker の対象キャラクターを切り替えられる。
- **IK の曲がる側**: RP ソルバーでは `preferredAngle` を手掛かりにしても曲がる側は安定しない。一直線に近いチェーンでは、`autorig_utility.set_ik_preferred_angle()` が希望する世界方向(脚は +Z、腕は −Z)を、ジョイント自身の `worldMatrix` の逆行列でローカルへ変換し、約 1° の曲げを `jointOrient` へ直接焼き込む。Pole Vector の縮退時のフォールバックも同じ方向を使う。
- `create_controller(rotate_order=...)`: Con の回転順序の初期値(`"xyz"` などの文字列か 0～5)。既定は `"xyz"`。Drv は Con の `rotateOrder` に接続されて追従するので、Con だけに設定する。
- `IKFK` アトリビュート: 腕は `Con_*_Shoulder`(初期値 1 = FK)、脚は `Con_*_LegRoot`(初期値 0 = IK)。

### ユーティリティノードの命名

DAG 以外のノード(multMatrix・floatMath など)は `cmds.createNode` を直接呼ばず、`autorig_utility.util_node(ノードタイプ, 持ち主, 用途)` で作ります。名前は `<持ち主>_<用途>_<ノードタイプ>` になります(例: `Grp_L_LegIkHandle_smoothT_floatMath`、`Drv_C_Hips_translateAdvance_blendColors`)。

- 持ち主: そのノードが最終的に動かす DAG ノード。1 つのジョイントだけを動かすならそのジョイント、複数で共有するなら読み取り元。フルパスを渡してよく、短い名前の `:` は `_` に置き換わる。持ち主のグループがまだ無い時点で作る場合は、そのグループの名前を文字列で渡す(`f"Grp_{clr}_ArmPV"`)。
- 用途: 出力が何を表すかを camelCase の 1 語で書く(`offset`、`rotParentA`、`stretchRatio` など)。計算手順ではなく意味で付ける。
- ノードタイプ: 略さずにそのまま付ける(`_dm` ではなく `_decomposeMatrix`)。
- 同じ名前が既にあると、用途の後ろに 2 から番号が付く(2 体目のキャラクターなど)。同じ持ち主・同じ用途を 2 回作らないよう、用途の語を分ける。
- `connectAttr` で Maya が自動挿入する unitConversion は、`create_rig` の最後に `rename_unit_conversions()` が `<接続先>_<接続先アトリビュート>_unitConversion` へ改名する。接続先が DAG 以外なら、その名前から末尾のノードタイプを除いた部分を持ち主にする。
- IK ソルバー(`ikRPsolver` など)は Maya が管理する共有ノードなので改名しない。

### 手作業リギング用のシェイプ作成(`autorig_utility.create_shape`)

- `アクセサリ` → `シェイプ` サブタブから呼ぶ。中身は `create_nurvs()`(リグ作成と同じ `nurvs_shape.json`)に色付けと配置を足しただけ。
- 選択した transform(ジョイント含む)ごとに 1 つ作り、`matchTransform` で位置と回転を合わせる。フリーズしないので、そのまま Grp を挟んでオフセットに使える。形状・サイズ・法線軸は `create_nurvs` 内の `makeIdentity` で CV に焼き込む。
- 法線軸: json の形状は XZ 平面(法線 +Y)。X は Z 軸 -90°、Z は X 軸 +90° 回転で作る。
- `Grp`/`Drv` は作らず、`ARFH_information` にも登録しない(Picker の対象外)。
- 置き換え(`replace_shape`): 選択のうち nurbsCurve シェイプを持つ transform だけが対象。一時ナーブスを作り、元のシェイプを全部削除してから新しいシェイプを `parent -r -s` で移し、最初の元シェイプ名へ改名する。色は transform の `overrideColorRGB` に設定する。
- `create_shape` / `replace_shape` はどちらも `undoInfo` の 1 チャンクにまとめ、Ctrl+Z 1 回で戻る(mayapy で確認)。

### Picker(`picker.py`)

- コントローラーは `ARFH_information` の辞書から UUID で引く。指のジョイントが無いリグではキーが無いため、`cmds.error` でなく `cmds.warning` でスキップする。
- Mirror Pose は、右側 Grp に仕込まれた軸反転を前提に、左右のローカル行列を入れ替える。中央は自身のローカル行列を、親を固定したまま反転する。

### 別ファイルのリグ読み込み(`rig_import.py`)

- Maya の `cmds.file(..., i=True)` は UUID を維持しない。`ARFH_information` に記録した UUID とノードのフルパス名の対応から、インポート直後に `MFnDependencyNode.setUuid()` で復元する。
- 既存の `ARFH_information` がある場合、Maya は読み込み側を「<ファイル名>_ARFH_information」のようにリネームして取り込む(連番ではない)。復元後にその内容を既存側へ統合し、重複ノードを削除する。
- ノード名の記録が無い古い形式のリグは復元対象外。
- `reference_rig()`(**Reference Rig**): リファレンスはファイル側の UUID を保持するので復元しない。ネームスペースはファイル名(衝突時は Maya が連番を付けるので `cmds.file(q=True, namespace=True)` で実際の値を取る)。Picker はシーン直下の `ARFH_information` しか読まないため、`<ns>:ARFH_information` のキャラクター記録(`{tuple_key: UUID}`)をシーン直下へコピーする(無ければ作成し、そのときだけ `characterName` を設定。同名キーは上書き)。`_names` はコピーしない。
- 同じファイルを2回リファレンスすると全コピーが同じ UUID になり、`setUuid()` で変えても開き直すとファイル側の値に戻る(mayapy で確認)。2回読まない前提とし、Picker は変更していない(ユーザー指示、2026-10-18)。

### コントロールシェイプ(`control_shape.py`)

- 履歴の無い静的な nurbsCurve の CV ローカル座標を json に保存する。CV 数が違う場合は書き戻さずスキップする。
- 対象は選択(またはその子孫)の `Con_*`。選択に `Con_*` が無い場合は警告して、シーン内の全 `Con_*` へフォールバックする。

## テスト

`mayapy` で `gui.create_window()` を呼ぶと、GUI フラグ名の誤りなど Python レベルのエラーは検出できます。
