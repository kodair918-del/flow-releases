# Flow for Windows

Flow は、タスクバーと壁紙に景色（星・雪・雨・蛍・桜・雲・オーロラ・流星群・霧・灯籠、川・砂・海・山・街・草原・雪原・森）を描くアプリです。
Mac 版は [flow-mac-releases](https://github.com/kodair918-del/flow-mac-releases) にあります。

## インストール（PowerShell に貼って実行）

```powershell
irm https://raw.githubusercontent.com/kodair918-del/flow-releases/main/install.ps1 | iex
```

ダウンロード、チェックサムの確認、`%LOCALAPPDATA%\Flow` への配置、スタートメニューへの登録、起動まで自動です。

## 対応

- 壁紙: Windows 10 (1809) 以降の 64 ビット
- タスクバーの景色: Taskbar.View.dll の版が合う Windows 11 だけ（版ごとにタスクバー内部の位置が違うため）。
  合わない版では壁紙だけ動かし、タスクバーには触りません。対応する版は、更新で増えることがあります。

## アップデート

1日に1回、新しい版を探して自動で入れ替えます（通知領域のメニューで切れます）。

## アンインストール

スタートメニューの「Flow - uninstall」。

## 注意

タスクバーの景色は Explorer に部品を差し込む仕組みで、部品に署名はありません。ウイルス対策ソフトが警告することがあります。

このリポジトリには、インストール用スクリプトと、できあがったアプリ（`dist` ブランチ）だけを置いています。
