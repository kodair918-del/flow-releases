# Flow は安全？（入れる前に読んでください）

Flow は、署名のないアプリで、**Windows では Explorer（タスクバー）に小さな部品を読み込ませます**。警戒するのは正しいです。
ここに、**何をするか・何をしないか・どうやって確かめるか**を、隠さずに書きます。

## インストールで起きること

### Windows（`irm … | iex` の1行）

1. `raw.githubusercontent.com` から `latest.json` と `Flow-win.zip`（このリポジトリの `dist` ブランチ）をダウンロードします。
2. **SHA-256 を `latest.json` と照合**し、合わなければ中止します。
3. `%LOCALAPPDATA%\Flow` に展開します（**管理者権限は要りません**）。設定ファイル `xamlh.cfg` は上書きしません。
4. スタートメニューに「Flow」「Flow - on」「Flow - off」「Flow - uninstall」を作り、`HKCU\Software\Microsoft\Windows\CurrentVersion\Run` に `Flow` を1つ書きます（Windows の起動時に開始）。
5. `FlowTray.exe` を起動します。

インストールのスクリプト（`install.ps1`）は、このリポジトリで全文を読めます。**実行前に読んでかまいません。**

### Mac（`curl … | bash` の1行）

`flow-mac-releases` から zip を取り、同じくチェックサムを照合して、`~/Applications/Flow.app` に置き、起動します（管理者権限は要りません）。設定は `~/Library/Application Support/Flow` に書きます。

## 動いているもの（Windows）

| ファイル | 役目 |
|---|---|
| `FlowTray.exe` | 通知領域のアイコンとメニュー。設定、更新、ほかのプログラムの起動 |
| `FlowWall.exe` | 壁紙の裏に絵を描く窓 |
| `watch.exe` ＋ `xamlh.dll` | タスクバーに絵を差し込む。**自分のユーザーの `explorer.exe` に `xamlh.dll` を読み込ませます**（Visual Studio が使う XAML Diagnostics という公開の仕組み）。システムのファイルは書き換えません。ドライバーも入れません |
| `flowpack.exe` | 景色パックの検査・導入の道具（使わなければ動きません） |

すべて `%LOCALAPPDATA%\Flow` の中にあります。ほかの場所へは、設定の保存（同じフォルダー）と、一時ファイル（`%TEMP%`）だけです。

## 通信するもの

- **更新の確認**: 1日1回（メニューで切れます）。`raw.githubusercontent.com` の `flow-releases/dist/latest.json` を読みます。新しい版があれば、同じ場所から zip を取り、SHA-256 を照合してから入れ替えます。
- **ギャラリー**: メニューの「ギャラリーから入れる」を使ったときだけ、`flow-releases/main/gallery/` を読みます。
- **それ以外は、何も送りません。** 利用状況の集計・解析・広告・アカウントは、ありません。

## 自分で確かめる方法

- **チェックサム**: `latest.json` の `sha256` と、ダウンロードした zip の SHA-256（PowerShell: `Get-FileHash Flow-win.zip`）を比べられます。
- **ウイルススキャン**: zip を [VirusTotal](https://www.virustotal.com/) に上げて、結果を見られます。署名がなく「Explorer に差し込む」動きがあるため、**一部のソフトが警告する可能性**があります（誤検出のことが多いですが、気になるなら使わないでください）。
- **何が動いているか**: タスクマネージャーで `FlowTray` `FlowWall` `watch` が見えます。`explorer.exe` のモジュール一覧に `xamlh.dll` が出ます。
- **通信**: ファイアウォールやネットワークの記録で、上の2か所以外に出ていないことを確かめられます。

## やめるとき・困ったとき

- **完全に消す**: スタートメニューの「Flow - uninstall」。ログオンの登録・ショートカット・フォルダーを消し、Explorer を1回再起動して部品を外します。
- **すぐ止める**: 通知領域のアイコンをダブルクリック（または `Ctrl+Alt+F`）、スタートメニューの「Flow - off」。
- **タスクバーがおかしいとき**: 「Flow - off」を押すか、サインアウト→サインイン。それでも直らなければ「Flow - uninstall」。
- 原因を調べる: `%LOCALAPPDATA%\Flow` の `xamlh.log`・`flowtray.log`・`FlowWall.log`。

## 正直に言っておくこと

- **コードに署名がありません**（署名の証明書は有料です）。そのため、Windows や対策ソフトが警告することがあります。
- **ソースコードは、いまは公開していません。** 動作は上の表のとおりですが、ご自身で中身を読んで確かめることはできません。
- 動作を確かめた Windows は限られます（タスクバーの部分は、Windows 11 のこの版で確認済み。ほかの版では、見つからなければ**何も変えずに**壁紙だけが動きます）。
- 個人が作った無料のアプリで、保証はありません（[LICENSE.txt](../LICENSE.txt)）。

不具合や疑問は、[Issues](https://github.com/kodair918-del/flow-releases/issues) に書いてください。
