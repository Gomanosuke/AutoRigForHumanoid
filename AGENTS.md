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
├─ blendshape_name.json    ブレンドシェイプ名の変換表
├─ unity_fbx_export.py     Unity 向け FBX 書き出し(別プロセスで検証)
└─ unity/Editor/           Unity 側のインポート補助スクリプト
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

---

## Unity FBX export

Maya 2026 の作業中シーンを保護したまま、アニメーション付き FBX を生成します。

AutoRigForHumanoid のメイン画面で、`アクセサリ` タブの `FBX` サブタブにある `Unity FBX 書き出し` 欄の `FBX Exporter For Unity` ボタンを押してください。Python から直接開くこともできます。

```python
from AutoRigForHumanoid import unity_fbx_export
unity_fbx_export.show()
```

1. ジオメトリとスキンの全ジョイントを含む親グループを選択します。
2. `Use selection` で対象を指定し、開始・終了フレームを確認します。
3. 必要なら `Specify rest pose frame` をオンにし、`Rest pose frame` に Unity のデフォルトポーズとするフレームを入れます（範囲外可。optionVar `ARFHUnityFbxRestFrame` / `ARFHUnityFbxRestFrameEnabled` に保存）。
4. `Export and verify on a copy` を押し、新しい FBX ファイル名を指定します。

保存済み原本と未保存変更を含むスナップショットを、OS の一時フォルダ内の固有ジョブフォルダへ保存してサイズを確認します。元のシーン名や編集状態を維持し、別の mayapy プロセスで履歴処理・ベイク・FBX 再読み込み検証を実行します。既存の出力ファイルは上書きしません。

ウィンドウに表示されるジョブフォルダには `report.json`、`worker.log`、復元用シーンが残ります。検証に失敗した場合は最終 FBX を発行せず、同フォルダに原因を記録します。作業終了後、バックアップが不要になってからジョブフォルダを整理してください。

書き出しを開始すると「書き出し状況」画面が開き、複数のジョブの出力ファイル・対象・処理段階・経過時間を個別に表示します。「書き出し状況を表示」ボタンで再表示できます。完了や失敗は一覧に残り、完了ダイアログによる操作の中断はありません。行を選ぶと出力先や失敗理由を確認でき、ジョブフォルダ・ログも開けます。表示は処理段階であり、全体の完了率や残り時間の推定ではありません。閉じてもワーカーは継続し、この Maya セッション内では一覧を再表示できます。

### 処理内容

- 頂点削除履歴を含むスキンでは、残った頂点に元のウェイトを戻してから変形を照合します。Maya の通常の履歴削除によるウェイト補間をそのまま採用しません。
- バインドポーズに不足する親グループを追加します。既存のジョイントのバインド行列を初期化しません。
- FBX が直接扱えない接続を持つ TRS と表情ウェイトを指定範囲でベイクします。FBX 側での二重ベイクと入力接続によるリグ全体の出力を避けます。
- ベイクは `bakeResults` を使わず `_bake` で行います。`bakeResults` は長い範囲で線形より大きく遅くなりました（実案件のキャラクター（13 メッシュ・37 ジョイント、同じシーンに他 2 体）で 10,000 フレーム 7 秒、67,685 フレーム 220 秒）。`MAnimControl.setCurrentTime` と `MPlug.asDouble` で毎フレーム値を読み、カーブごとに `MFnAnimCurve.addKeys` を 1 回呼びます。回転は `numpy.unwrap` でチャンネルごとに 360° の飛びを除きます（`minimizeRotation` 相当）。値が一定のチャンネルは 1 キーにします。
- 読み取りの前に、書き出し対象・ベイク対象・メッシュの上流履歴に含まれないトップレベル階層をコピーから削除し（`_prune_unrelated`）、parallel 評価で読みます。同じシーンに複数キャラクターがあると、parallel 評価では全員分が毎フレーム評価されるためです。同じキャラクターでは、削除後の parallel が DG より約 1.7 倍速でした（2,000 フレームで 4.7 秒と 8.3 秒）。削除前の parallel は DG より遅くなりました。
- 5,000 フレーム以上あれば、フレーム範囲を最大 8 つに分け、別の mayapy（`--sample`、`sample_task`）でも同じスナップショットを開いて分担して読みます。数は CPU スレッド数 / 4、および空き物理メモリの 70% ÷（スナップショットのサイズ × 3）で制限します。2 GB のシーンでは 1 プロセスあたり約 4.7 GB 使いました。読み終えた後、本体が 9 フレームと各分割境界を DG モードで読み直し、1e-6 を超える差があれば失敗にします。
- ワーカーは最終レポートを書いた後、Windows では `TerminateProcess` で終了します。`maya.standalone.uninitialize()` も `os._exit` もプラグインのアンロード処理でクラッシュし、Maya のクラッシュハンドラーが TEMP に `source_snapshot[回復-…].ma`（1～3 GB）を書き出していました。ctypes では `GetCurrentProcess` の `restype` を HANDLE にしないと 64 ビットのハンドルが切り詰められ、呼び出しが失敗します。
- 同じキャラクター（67,685 フレーム、60 fps、Ryzen 9 9950X）では、全体が約 330 秒から 128 秒になりました（ベイク 220 秒 → 86 秒、2026-09-29）。report.json の `stage_seconds` に工程ごとの秒数が入ります。
- シアーの接続も毎フレーム評価します。絶対値 0.00001 以下の数値ノイズだけを書き出し用コピーでゼロにし、変形差を照合します。それを超えるシアーは FBX で保持できないため、出力せずエラーにします。
- 定数チャンネルを１キーに縮約します。縮約後にも変形を照合します。
- デフォルトポーズ（`rest_frame`、`_key_rest_pose`）: Unity 2022.3.22f1 は、アニメーション付きノードのデフォルトポーズ（Humanoid Avatar の基準）を、FBX の時刻 0 のアニメーション値から取ります。時刻 0 がテイク範囲外ならテイクの先頭フレームの値です。FBX の静的な `Lcl` 値は使いません。テイク範囲外のキーも無視します（2026-09-27、Unity バッチモードで読み込んだプレハブの Transform を人工 FBX 6 通りで確認）。そのため `rest_frame` 指定時は、クリップを 1 フレーム始まりへずらし（`offset = 1 - start`）、全カーブの 0 フレームに記録したポーズのキーを打ち、テイク（playback range）を 0～終了にします。範囲外のキーは後で削除するので、ポーズは加工前のリグで記録します。キー追加で auto タンジェントが再計算されないよう、両端のキーを fixed にして角度を固定し、端の区間の曲線が変わらないことを確認します。変形照合は offset 分ずらしたフレームで行います。ベイクで Euler 値が ±360° 変わることがあるので、0 フレームのポーズはローカル行列で照合します。再読み込みしたジョイントの 0 フレームの行列も照合します。未指定時はずらさず、従来どおりです。
- 既知の制限: 直接キーを打ったチャンネルが auto/spline タンジェントで範囲外にもキーを持つ場合、範囲外のキー削除でタンジェントが再計算され、クリップ内の曲線が変わります。変形照合で失敗として止まります（`rest_frame` 対応とは別の既存の挙動、2026-09-26 に人工シーンで確認）。
- 別シーンへ FBX を再読み込みし、メッシュの存在・頂点数・表情ターゲット名・サンプルフレームの変形を確認します。
- 再読み込みでメッシュ名に数字が付く場合は、同じ親階層と頂点数で候補を絞り、変形も照合します。対応が一意に決まらない場合は出力しません。

### 精度と対応範囲

履歴処理とベイクの位置許容差は Maya API の座標で 0.001 cm、FBX 往復の許容差は 0.1 cm（1 mm）です。実測値はレポートに記録されます。FBX は元シーンとの完全な数値一致を保証する形式ではありません。確認は通常９フレームのサンプルであり、全フレームの全頂点検証ではありません。

複数スキン、異なるウェイトを持つ重複位置、対応していない履歴、offsetParentMatrix を使う書き出し階層などは、推測で変換せずエラーにします。外部プラグイン・参照・テクスチャはワーカーからも参照できる必要があります。

### Unity

このモデルの骨の動きをそのまま再生する用途では、Rig の `Animation Type` を `Generic`、`Import BlendShapes` を ON にします。Humanoid のリターゲットで元の腰の移動カーブが破棄される警告とは区別してください。別キャラクターへの Humanoid リターゲットは、この設定の検証範囲に含みません。

付属の `unity/Editor/AutoRigFbxImport.cs` を Unity プロジェクトの Editor フォルダへ配置すると、選択中の FBX に `Assets > AutoRig > Use Source Animation (Generic)` から設定を適用できます。変更前の importer 設定は Library 内へ退避します。元の FBX とマテリアルの設定は変更しません。

アニメーション圧縮は精度確認のため OFF です。容量調整が必要なら、実際の再生を比較したうえで Unity 側の圧縮を設定してください。
