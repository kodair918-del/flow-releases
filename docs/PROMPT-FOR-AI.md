# Flow の景色を AI に作ってもらうためのプロンプト

下の「ここから」〜「ここまで」を、**そのまま AI（ChatGPT・Claude・Gemini など、どれでもよい）に貼り付けて**、最後の「作りたい景色」に希望を書いて送ります。
AI が `pack.json` を返したら、ファイルに保存して `flowpack check` にかけ、エラーが出たらその文字をそのまま AI に貼って直してもらいます（やり方は最後）。

---

## ここから

あなたは「Flow」というアプリの**景色パック**（`pack.json`）を作る係です。ドット絵風の壁紙（desk）と、画面下の帯（task：タスクバー／Dock）の景色を、JSON で書きます。

### ルール（必ず守る）
1. 返事は、**`pack.json` の中身だけを ```json のコードブロック1つ**で書き、そのあとに日本語で2〜3行の説明を付ける。コードブロックの中に説明やコメントを入れない。
2. JSON の決まり: 文字は半角ダブルクォート `"` で囲む。コメントは書けない。**最後の項目のあとにカンマを付けない**。数字は `"` で囲まない。
3. **この仕様に無いキーは書かない**（書くとエラー）。数字は範囲を守る。
4. 迷ったら、短く単純に作る。まず動くものを作り、あとで足す。
5. 先に、作る景色について**質問が必要なら最大3つまで**聞く（desk と task のどちらか、または両方か／雰囲気・時間帯・季節／使いたい色）。答えが返ってきたら作る。

### pack.json の形
```
{ "format": 1, "name": "パックの名前", "author": "",
  "scenes": [ シーン, ... ],
  "pairs": [ { "name": "組み合わせの名前", "desk": "deskのid", "task": "taskのid" } ] }
```
シーン = `{ "id": "半角小文字と数字と-（2〜32字・先頭は小文字）", "kind": "desk" か "task", "title": "メニューに出る名前", "layers": [ レイヤー, ... ] }`
- `desk` = 壁紙（画面いっぱいの空）。最初のレイヤーを、全面の gradient（from 0・to 1・alpha 1）にする。地面は描かない。
- `task` = 画面下の細い帯（地面・街・山・波）。上は透明のまま。全面の gradient は使わない。
- レイヤーは最大16枚。**先に書いたものが奥、後が手前。**
- `id` は組み込みの名前（stars snow rain fireflies sakura clouds aurora meteors fog lanterns river sand sea mountains city grass snowfield forest）とかぶらない。
- 組み合わせの `desk` は desk のid（自分のものか上の空の名前）、`task` は task のid（自分のものか上の地面の名前）。

### 色
`"#rrggbb"`（例 `"#ff8800"`）か、パレットに従う色 `"@dark"` `"@mid"` `"@light"` `"@spark"`。

### 単位
横は px、縦は 0〜1 の割合（0＝上、1＝下）。ドットは 2px 角。速さは px/秒。角度 0＝右・90＝下・180＝左・270＝上。

### レイヤー6種（どれにも `"alpha"` 0〜1 が書ける。gradient 以外は `"seed"` 0〜100000 も可）
1. **gradient** … `top` `bottom`（色・必須）、`from`（0〜1）、`to`（0〜1、fromより大きく）
2. **particles**（星・雪・雨など）… `count` 0.01〜60（横1000px×縦100pxあたりの数）、`size` 1〜6、`shape` dot|square|plus|streak、`color`（色か色のリスト・必須）、`speed` [最小,最大]（0〜600）、`angle` 0〜360、`sway` 0〜80、`swayRate` 0.05〜10、`twinkle` 0〜1、`twinkleRate` 0.05〜10、`y` [上,下]（0〜1）、`length` 2〜200（streakの尾）
3. **wave**（水面）… `y` 0〜1、`amp` 0〜0.5、`wavelength` 20〜4000、`speed` −400〜400、`color`（必須）、`foam`（色・省略可）
4. **silhouette**（地面・山・木・ビル）… `base` 0〜1、`profile` 1〜6個の `{ "amp": 0〜0.6, "wavelength": 20〜6000, "phase": −100〜100 }`（amp と wavelength 必須）、`style` smooth|spikes|blocks、`color`（必須）、`lit`（色）、`spacing` 6〜400、`height` [最小,最大]（0.01〜0.9）、`width` [最小,最大]（2〜300）、`window`（色）、`windowDensity` 0〜1、`scroll` −200〜200
5. **orb**（太陽・月などの光）… `x` 0〜1、`y` −0.5〜1.5、`radius` 4〜600、`color`（必須）、`pulse` 0〜1、`rate` 0.05〜10、`drift` −200〜200
6. **sprites**（ドット絵の鳥・雲・舟）… `rows`（文字の並び1〜24行・各32字まで。`.`は透明）、`palette`（rowsに出る文字ごとの色・全部書く）、`count` 0.01〜40（横1000pxあたり）、`speed` [最小,最大]（−300〜300）、`y` [上,下]、`scale` 1〜4、`bob` 0〜60

### 作り方のコツ
- 色は1シーン4〜6色に絞る。奥は明るく・遅く、手前は暗く・速く。動きはゆっくり。
- desk は gradient → orb（太陽・月）→ particles（星・雪）→ sprites（雲・鳥）の順が基本。
- task は silhouette を奥→手前の順に2〜3枚。水なら wave を2〜3枚。

### 完成例（これをお手本にする）
```json
{
  "format": 1,
  "name": "夜の街",
  "author": "",
  "scenes": [
    {
      "id": "moon-night",
      "kind": "desk",
      "title": "月夜",
      "layers": [
        { "type": "gradient", "top": "#04060f", "bottom": "#1a2550" },
        { "type": "particles", "count": 4, "size": 1, "shape": "dot", "color": ["#ffffff", "#bfd8ff", "#ffe9a8"],
          "speed": [1, 3], "angle": 0, "twinkle": 0.8, "twinkleRate": 1.5, "y": [0, 0.8] },
        { "type": "orb", "x": 0.72, "y": 0.22, "radius": 70, "color": "#fff4c8", "alpha": 0.9, "pulse": 0.1, "rate": 0.08 }
      ]
    },
    {
      "id": "town-lights",
      "kind": "task",
      "title": "夜の街あかり",
      "layers": [
        { "type": "silhouette", "style": "blocks", "base": 0.85, "color": "#10162e", "spacing": 34, "height": [0.25, 0.6],
          "width": [14, 26], "window": "#ffd070", "windowDensity": 0.35, "seed": 5,
          "profile": [ { "amp": 0.02, "wavelength": 900, "phase": 0 } ] },
        { "type": "silhouette", "style": "blocks", "base": 0.97, "color": "#070a18", "spacing": 40, "height": [0.3, 0.8],
          "width": [18, 34], "window": "#ffb050", "windowDensity": 0.2, "seed": 11, "profile": [ { "amp": 0.01, "wavelength": 500 } ] }
      ]
    }
  ],
  "pairs": [ { "name": "月夜の街あかり", "desk": "moon-night", "task": "town-lights" } ]
}
```

### 作りたい景色
（ここに希望を書く。例: 「夕立のあとの海辺。空は紫がかった灰色で、手前に波打ち際」「桜並木の通り（task）と、春の朝の空（desk）」）

## ここまで

---

## AI とのやりとりの進め方

1. 上の「ここから〜ここまで」を貼り、「作りたい景色」を書いて送る。
2. AI が返した ```json の中身を、`pack.json` という名前で保存する（フォルダーを作って、その中に）。
3. 検査する。
   - Windows: `flowpack check "フォルダーの場所"`
   - Mac: `/Applications/Flow.app/Contents/MacOS/Flow --check-pack "フォルダーの場所"`（`~/Applications` に入れた場合はその場所）
4. 最後の行が `RESULT: OK` ならよい。`RESULT: FAILED` なら、出た文字を**そのまま全部** AI に貼って、「この検査結果のエラーを直した pack.json 全体を返して」と頼む。OK になるまで繰り返す。
5. 絵を見る: `flowpack preview "フォルダー" "絵を出す場所"`（Mac は `--preview-pack`）。出た PNG を見て、「空をもっと暗く」「波をゆっくり」のように感想を伝えて直してもらう。
6. 気に入ったら `flowpack install "フォルダー"`（または `packs` フォルダーに置く）。Flow のメニューの「組み合わせ」「空だけ」「地面だけ」に出る。

画像を見られる AI なら、手順 5 の PNG を貼ると、見た目も直してくれます。
