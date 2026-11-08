"""使い方のページ（/howto/）を、kouun/docs/howto/ の原稿（Markdown）から作る。

使い方（www/ で実行）:
    python3 tools/gen_howto.py

必要なもの: Python の markdown ライブラリ（pip install markdown）
原稿が変わったら、これを実行して public/howto/ のHTMLと画像を作り直す。

- 目次（public/howto/index.html）と、PAGES の各ページ（public/howto/<名前>.html）を作る
- 原稿がまだないページは「準備中」と出す
- 原稿の中の <!-- --> の注記は、HTMLに出さない
- 原稿が使っている画像だけを public/howto/images/ に写す。画像がまだないときは枠だけを出す
"""
import html
import re
import shutil
from pathlib import Path

import markdown

WWW = Path(__file__).resolve().parent.parent
DOCS_HOWTO = WWW.parent / "docs" / "howto"
OUT = WWW / "public" / "howto"
OUT_IMAGES = OUT / "images"

# 名前（原稿のファイル名と掲載先）、ページの名前、目次に出す番号。並びは目次の順
PAGES = [
    ("setup", "初期設定", "01"),
    ("fields", "圃場の一覧", "02"),
    ("conditions", "足元の状況", "03"),
    ("diary", "栽培日誌", "04"),
    ("notices", "注意情報", "05"),
    ("account", "会員情報", "06"),
    ("scenes", "こんなときは", "?"),
]

# 原稿がまだないページの説明
PENDING_LEAD = {
    "notices": "病害虫に注意したい時期の知らせの見方です。この機能は準備中です。",
}

# スクリーンショットの大きさ（iPhoneの縦の画面）。読み込みの間に、ページの形が崩れないようにするため
SHOT_WIDTH, SHOT_HEIGHT = 1206, 2622

HEAD = """<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <meta name="description" content="{description}">
  <title>{title}｜耕雲</title>
  <link rel="icon" type="image/png" href="/assets/icons/icon_origin.png">
  <link rel="stylesheet" href="/css/style.css">
</head>
<body>
  <p class="notice">耕雲は現在テスト版です。アプリの正式公開に向けて準備しています。</p>
  <header class="site-header">
    <a class="brand" href="/" aria-label="耕雲 トップ">
      <img src="/assets/icons/icon_origin.png" alt="" width="42" height="42">
      <span>耕雲<small>こううん</small></span>
    </a>
    <nav aria-label="メインナビゲーション">
      <a href="/#about">耕雲について</a>
      <a href="/howto/">使い方</a>
      <a href="/news/">お知らせ</a>
    </nav>
  </header>

"""

FOOT = """
  <footer class="site-footer">
    <a class="footer-brand" href="/">耕雲 <span>こううん</span></a>
    <p>天候データで農業を支援する。</p>
    <div class="footer-links">
      <a href="/legal/terms">利用規約</a>
      <a href="/legal/privacy">個人情報の取扱い</a>
      <a href="https://takaosan.app" target="_blank" rel="noopener noreferrer">開発者サイト ↗</a>
    </div>
    <small>© takaosan.app</small>
  </footer>
</body>
</html>
"""


def indent(text, spaces):
    return "\n".join(" " * spaces + line if line else line for line in text.splitlines())


def split_title_lead(md_text):
    """原稿の最初の「# ページの名前」と、その下の一言の説明を取り出し、残りの本文と分ける。"""
    lines = md_text.strip().splitlines()
    title = lines[0].lstrip("# ").strip()
    rest = "\n".join(lines[1:]).strip()
    lead, _, body = rest.partition("\n\n")
    return title, lead.strip(), body


def to_body(md_text, used_images):
    """原稿の本文をHTMLにする。"""
    # 注記は出さない
    md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.S)
    # ほかのページへのリンク（setup.md など）を、掲載先の住所にする
    md_text = re.sub(r"\]\(([a-z_]+)\.md\)", r"](/howto/\1)", md_text)

    body = markdown.markdown(md_text, extensions=["tables"])

    # 見出しに番号の id を付け、ページの中の目次を作る
    sections = []

    def add_id(m):
        sections.append(m.group(1))
        return f'<h2 id="s{len(sections)}">{m.group(1)}</h2>'

    body = re.sub(r"<h2>(.*?)</h2>", add_id, body)

    # スクリーンショットを、枠付きの図にする
    def to_figure(m):
        src, alt = m.group("src"), m.group("alt")
        name = src.split("/")[-1]
        if (DOCS_HOWTO / "images" / name).exists():
            used_images.add(name)
            return (f'<figure class="shot"><img src="/howto/images/{name}" alt="{alt}" '
                    f'width="{SHOT_WIDTH}" height="{SHOT_HEIGHT}" loading="lazy"></figure>')
        return f'<figure class="shot shot-missing" role="img" aria-label="{alt}"><span>画像を準備中です</span></figure>'

    body = re.sub(r'<p><img alt="(?P<alt>[^"]*)" src="(?P<src>[^"]*)" ?/?></p>', to_figure, body)

    body = body.replace("<table>", '<div class="table-wrap">\n<table>')
    body = body.replace("</table>", "</table>\n</div>")
    return body, sections


def page_nav(index):
    """前後のページへのリンク。"""
    parts = []
    if index > 0:
        name, title, _ = PAGES[index - 1]
        parts.append(f'<a class="prev" href="/howto/{name}"><small>前へ</small>{title}</a>')
    else:
        parts.append("<span></span>")
    if index < len(PAGES) - 1:
        name, title, _ = PAGES[index + 1]
        parts.append(f'<a class="next" href="/howto/{name}"><small>次へ</small>{title}</a>')
    return '<nav class="page-nav" aria-label="前後のページ">\n  ' + "\n  ".join(parts) + "\n</nav>"


def build_page(index, used_images):
    name, title, _ = PAGES[index]
    src = DOCS_HOWTO / f"{name}.md"
    if src.exists():
        title, lead, md_body = split_title_lead(src.read_text(encoding="utf-8"))
        body, sections = to_body(md_body, used_images)
        pending = False
    else:
        lead = PENDING_LEAD.get(name, "このページは準備中です。")
        body, sections = '<p class="pending">このページは準備中です。できあがりしだい、ここでご案内します。</p>', []
        pending = True

    toc = ""
    if len(sections) > 1:
        items = "\n".join(f'  <li><a href="#s{i}">{s}</a></li>' for i, s in enumerate(sections, 1))
        toc = f'<nav class="on-this-page" aria-label="このページの内容">\n<p>このページの内容</p>\n<ol>\n{items}\n</ol>\n</nav>\n'

    main = f"""<main class="howto-page">
  <p class="breadcrumb"><a href="/howto/">使い方</a></p>
  <h1>{title}</h1>
  <p class="lead">{lead}</p>
{indent(toc, 2)}
  <article>
{indent(body, 4)}
  </article>
{indent(page_nav(index), 2)}
</main>
"""
    out = HEAD.format(title=f"{title}｜使い方", description=html.escape(lead)) + indent(main, 2) + "\n" + FOOT
    (OUT / f"{name}.html").write_text(out, encoding="utf-8")
    return title, lead, pending


def build_index(entries):
    items = []
    for (name, _, number), (title, lead, pending) in zip(PAGES, entries):
        badge = '<em class="badge">準備中</em>' if pending else ""
        items.append(f"""<li>
  <a href="/howto/{name}">
    <span class="number">{number}</span>
    <span class="text"><b>{title}{badge}</b><small>{lead}</small></span>
  </a>
</li>""")
    main = f"""<main class="howto-page">
  <p class="eyebrow">GUIDE</p>
  <h1>使い方</h1>
  <p class="lead">耕雲のアプリの使い方をご案内します。はじめての方は「初期設定」からお読みください。</p>
  <ul class="howto-list">
{indent(chr(10).join(items), 4)}
  </ul>
  <a class="back-link" href="/">← トップページへ戻る</a>
</main>
"""
    out = HEAD.format(title="使い方", description="耕雲のアプリの使い方をご案内します。") + indent(main, 2) + "\n" + FOOT
    (OUT / "index.html").write_text(out, encoding="utf-8")


def copy_images(used_images):
    """原稿が使っている画像だけを写し、使わなくなった画像は消す。"""
    OUT_IMAGES.mkdir(parents=True, exist_ok=True)
    for name in sorted(used_images):
        shutil.copy2(DOCS_HOWTO / "images" / name, OUT_IMAGES / name)
    for old in OUT_IMAGES.glob("*"):
        if old.name not in used_images:
            old.unlink()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    used_images = set()
    entries = [build_page(i, used_images) for i in range(len(PAGES))]
    build_index(entries)
    copy_images(used_images)
    for (name, _, _), (_, _, pending) in zip(PAGES, entries):
        print(f"howto/{name}.html" + ("（準備中）" if pending else ""))
    print(f"画像 {len(used_images)} 枚")


if __name__ == "__main__":
    main()
