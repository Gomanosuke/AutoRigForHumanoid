DisplayShadedAndTextured;
{  string $currentPanel = `getPanel -withFocus`;   string $panelType = `getPanel -to $currentPanel`;  if ($panelType ==  "modelPanel") {    modelEditor -edit -da "smoothShaded" -displayTextures on        -dl "default" $currentPanel;inViewMessage -smg "シェーディング表示(テクスチャ マップを使用)が<hl>オン</hl>になっています。\
ワイヤフレーム モードでオブジェクトを表示するには、<hl>4</hl>を押してください。" -fade -pos topCenter;
  } else if (`isTrue "MayaCreatorExists"` && `scriptedPanel -ex $currentPanel` && `scriptedPanel -q -type $currentPanel` == "dynPaintScriptedPanelType") {     dynPaintEditor -e -dtx 1 -dsa "smoothShaded" -dsl "default" $gDynPaintEditorName;inViewMessage -smg "シェーディング表示(テクスチャ マップを使用)が<hl>オン</hl>になっています。\
ワイヤフレーム モードでオブジェクトを表示するには、<hl>4</hl>を押してください。" -fade -pos topCenter;
  } else if ($panelType ==  "scriptedPanel" ) {
 	 string $scriptedPanelType = `scriptedPanel -query -type $currentPanel`; 
 	 if($scriptedPanelType != "nodeEditorPanel" && $scriptedPanelType != "hyperShadePanel"){ 
 	   string $cmd = "modelEditor -edit -displayAppearance \"smoothShaded\" -displayTextures on -displayLights \"default\" "; 
	   scriptedPanelRunTimeCmd( $cmd, $currentPanel ); 
inViewMessage -smg "シェーディング表示(テクスチャ マップを使用)が<hl>オン</hl>になっています。\
ワイヤフレーム モードでオブジェクトを表示するには、<hl>4</hl>を押してください。" -fade -pos topCenter;
      }
   }};
updateModelPanelBar MainPane|viewPanes|modelPanel4|modelPanel4|modelPanel4;
dR_setModelEditorTypes;
postModelEditorViewMenuCmd_Old MainPane|viewPanes|modelPanel1|modelPanel1|View modelPanel1 modelPanel1 0;
postModelEditorViewMenuCmd_Old MainPane|viewPanes|modelPanel2|modelPanel2|View modelPanel2 modelPanel2 0;
postModelEditorViewMenuCmd_Old MainPane|viewPanes|modelPanel3|modelPanel3|View modelPanel3 modelPanel3 0;
postModelEditorViewMenuCmd_Old MainPane|viewPanes|modelPanel4|modelPanel4|View modelPanel4 modelPanel4 0;
updateLightingMenu MainPane|viewPanes|modelPanel4|modelPanel4|menu25 modelPanel4;
modelEditor -e -dl flat modelPanel4;
// 結果: modelPanel4
updateModelPanelBar MainPane|viewPanes|modelPanel4|modelPanel4|modelPanel4;
dR_setModelEditorTypes;
postModelEditorViewMenuCmd_Old MainPane|viewPanes|modelPanel1|modelPanel1|View modelPanel1 modelPanel1 0;
postModelEditorViewMenuCmd_Old MainPane|viewPanes|modelPanel2|modelPanel2|View modelPanel2 modelPanel2 0;
postModelEditorViewMenuCmd_Old MainPane|viewPanes|modelPanel3|modelPanel3|View modelPanel3 modelPanel3 0;
postModelEditorViewMenuCmd_Old MainPane|viewPanes|modelPanel4|modelPanel4|View modelPanel4 modelPanel4 0;
