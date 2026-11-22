"""Gallery submissions: read a pack from a GitHub issue, check it, and (when approved) add it to the gallery.

    python .github/scripts/pack_issue.py check    -> checks the submission; writes work/report.md (+ pictures) for the comment
    python .github/scripts/pack_issue.py add      -> adds the (already approved) submission to gallery/ and index.json

The issue text is UNTRUSTED data. It is only ever read from the event file (never put into a shell command), the pack is
only parsed by flowpack (no code runs), and every name that becomes a file name is checked against a strict pattern.
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = os.getcwd()
WORK = os.path.join(ROOT, 'work')
GALLERY = os.path.join(ROOT, 'gallery')
FEED = 'https://raw.githubusercontent.com/kodair918-del/flow-releases/dist/'
ID_RULE = re.compile(r'^[a-z0-9][a-z0-9-]{1,39}$')
MAX_PACK = 64 * 1024


def event_issue():
    with open(os.environ['GITHUB_EVENT_PATH'], encoding='utf-8') as f:
        return json.load(f)['issue']


def sections(body):
    """An issue form is posted as '### Label' sections."""
    out, name, lines = {}, None, []
    for line in (body or '').replace('\r\n', '\n').split('\n'):
        if line.startswith('### '):
            if name is not None:
                out[name] = '\n'.join(lines).strip()
            name, lines = line[4:].strip(), []
        else:
            lines.append(line)
    if name is not None:
        out[name] = '\n'.join(lines).strip()
    return out


def field(secs, *keys):
    for k, v in secs.items():
        if any(key in k for key in keys):
            return v
    return ''


def unfence(text):
    m = re.match(r'^```[a-zA-Z]*\n(.*?)\n?```\s*$', text.strip(), re.S)
    return m.group(1) if m else text


def read_submission():
    """Returns (fields, problems)."""
    issue = event_issue()
    secs = sections(issue.get('body'))
    pid = field(secs, 'ID').strip()
    author = field(secs, '作者').strip()
    desc = field(secs, '紹介').strip()
    pack = unfence(field(secs, 'pack.json'))
    agree = field(secs, '同意')
    problems = []
    if not ID_RULE.match(pid):
        problems.append('「ギャラリーでの名前（ID）」は、半角の小文字・数字・ハイフンだけで 2〜40 文字にしてください（例: `rainy-seaside`）。')
    if not author or len(author) > 40 or '\n' in author:
        problems.append('「作者名」を 40 文字以内で1行に書いてください。')
    if not desc or len(desc) > 80 or '\n' in desc:
        problems.append('「ひとことの紹介」を 80 文字以内で1行に書いてください。')
    if '[x]' not in agree.lower():
        problems.append('同意のチェックが必要です。')
    data = pack.encode('utf-8').replace(b'\r\n', b'\n')
    if not data.strip():
        problems.append('`pack.json` の中身が空です。')
    if len(data) > MAX_PACK:
        problems.append('`pack.json` が大きすぎます（64KB まで）。')
    # a gallery id that is already taken (the submitter can pick another)
    index = load_index()
    if any(p['id'] == pid for p in index['packs']):
        problems.append('ID `%s` はもうギャラリーにあります。別の ID にしてください。' % pid)
    return {'id': pid, 'author': author, 'description': desc, 'data': data, 'issue': issue}, problems


def load_index():
    path = os.path.join(GALLERY, 'index.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return {'format': 1, 'packs': []}


def ensure_tool():
    """flowpack.exe from the public release (the same checker people run themselves)."""
    tool = os.path.join(ROOT, 'flowpack-tool', 'flowpack.exe')
    if os.path.exists(tool):
        return tool
    os.makedirs(os.path.dirname(tool), exist_ok=True)
    info = json.loads(urllib.request.urlopen(FEED + 'latest.json', timeout=60).read().decode('utf-8'))
    blob = urllib.request.urlopen(info['url'], timeout=120).read()
    if hashlib.sha256(blob).hexdigest() != info['sha256']:
        raise SystemExit('the release does not match its checksum')
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        with open(tool, 'wb') as f:
            f.write(z.read('flowpack.exe'))
    return tool


def run_tool(tool, *args):
    r = subprocess.run([tool] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
    return r.returncode, r.stdout


def prepare(sub):
    folder = os.path.join(WORK, sub['id'] or 'pack')
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(folder)
    with open(os.path.join(folder, 'pack.json'), 'wb') as f:
        f.write(sub['data'])
    return folder


def preview_png(tool, folder, out_png):
    """A 640x360 picture of the first pair (or the first scene)."""
    from PIL import Image
    pics = os.path.join(WORK, 'pics')
    code, _ = run_tool(tool, 'preview', folder, pics)
    names = sorted(os.listdir(pics)) if os.path.isdir(pics) else []
    pick = next((n for n in names if n.startswith('pair-')), None) or next((n for n in names if n.startswith('scene-')), None)
    if code != 0 or not pick:
        return False
    Image.open(os.path.join(pics, pick)).convert('RGB').resize((640, 360), Image.LANCZOS).save(out_png, optimize=True)
    return True


def write_report(text):
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, 'report.md'), 'w', encoding='utf-8') as f:
        f.write(text)


def set_output(name, value):
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out, 'a', encoding='utf-8') as f:
            f.write('%s=%s\n' % (name, value))


def do_check():
    sub, problems = read_submission()
    lines = []
    if problems:
        lines.append('## 投稿を確認できませんでした\n')
        lines += ['- ' + p for p in problems]
        lines.append('\nIssue を編集して直すと、自動でもう一度確認します。')
        write_report('\n'.join(lines))
        set_output('result', 'needs-fix')
        return 0
    folder = prepare(sub)
    tool = ensure_tool()
    code, report = run_tool(tool, 'check', folder)
    if code != 0:
        lines.append('## `flowpack check` が失敗しました\n')
        lines.append('```\n' + report.strip() + '\n```')
        lines.append('\nメッセージの場所（`scenes[0].layers[1].count` など）を直して、Issue を編集してください。自動でもう一度確認します。')
        lines.append('作り方は [ガイド](https://github.com/kodair918-del/flow-releases/blob/main/docs/SCENE-PACK-GUIDE.md) にあります。')
        write_report('\n'.join(lines))
        set_output('result', 'needs-fix')
        return 0
    pic = os.path.join(WORK, 'preview.png')
    got_pic = preview_png(tool, folder, pic)
    lines.append('## 検査を通りました\n')
    lines.append('```\n' + report.strip() + '\n```')
    lines.append('\n見た目は、この確認の実行結果（Artifacts の `preview`）で見られます。' if got_pic else '\n（絵は作れませんでした）')
    lines.append('\nオーナーが見た目を確認して、問題なければギャラリーに載せます。')
    write_report('\n'.join(lines))
    set_output('result', 'valid')
    return 0


def do_add():
    sub, problems = read_submission()
    if problems:
        write_report('## ギャラリーに載せられませんでした\n\n' + '\n'.join('- ' + p for p in problems))
        set_output('result', 'failed')
        return 1
    folder = prepare(sub)
    tool = ensure_tool()
    code, report = run_tool(tool, 'check', folder)
    if code != 0:
        write_report('## ギャラリーに載せられませんでした\n\n```\n' + report.strip() + '\n```')
        set_output('result', 'failed')
        return 1
    os.makedirs(GALLERY, exist_ok=True)
    pid = sub['id']
    with open(os.path.join(GALLERY, pid + '.json'), 'wb') as f:
        f.write(sub['data'])                                   # LF, byte for byte what the SHA-256 is of
    if not preview_png(tool, folder, os.path.join(GALLERY, pid + '.png')):
        write_report('## 絵を作れませんでした')
        set_output('result', 'failed')
        return 1
    doc = json.loads(sub['data'].decode('utf-8-sig'))
    index = load_index()
    index['packs'].append({
        'id': pid,
        'name': doc.get('name', pid),
        'author': sub['author'],
        'description': sub['description'],
        'file': pid + '.json',
        'sha256': hashlib.sha256(sub['data']).hexdigest(),
        'size': len(sub['data']),
    })
    with open(os.path.join(GALLERY, 'index.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        f.write('\n')
    write_report('## ギャラリーに載せました\n\n「%s」（`%s`）を追加しました。Flow のメニュー「追加パック → ギャラリーから入れる」に、まもなく並びます。ありがとうございます！' % (doc.get('name', pid), pid))
    set_output('result', 'added')
    return 0


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    sys.exit(do_check() if mode == 'check' else do_add() if mode == 'add' else 2)
