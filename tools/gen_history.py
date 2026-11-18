"""アプリの更新履歴のページ（/history/）を、kouun/docs/history/ の原稿（Markdown）から作る。

使い方（www/ で実行）:
    python3 tools/gen_history.py

必要なもの: gen_howto.py と同じ（ページの枠を gen_howto.py から借りる）
更新があったら、HISTORY に1行足して、これを実行する。

- 一覧（public/history/index.html）と、更新の日ごとのページ（public/history/<年月日>.html）を作る
- 日付は、農家さんに新しい版が届いた日（入れ替えの手順書2-10など）。原稿には日付を書かない
"""
import html
import re
from pathlib import Path

import markdown

from gen_howto import FOOT, HEAD, indent

WWW = Path(__file__).resolve().parent.parent
DOCS_HISTORY = WWW.parent / "docs" / "history"
OUT = WWW / "public" / "history"

# 更新の日と原稿（docs/history/<版>+<ビルド番号>.md）。日付の新しいものを上に書く
HISTORY = [
    ("2026-11-18", "1.0.0+3"),
]


def version_label(name):
    """「1.0.0+3」を、アプリの表示と同じ「1.0.0 (3)」にする。"""
    version, _, build = name.partition("+")
    return f"{version} ({build})"


def date_label(date):
    year, month, day = date.split("-")
    return f"{int(year)}年{int(month)}月{int(day)}日"


def page_name(date):
    return date.replace("-", "")


def read_entry(name):
    """原稿から、題名、一言の説明、本文のHTMLを取り出す。"""
    lines = (DOCS_HISTORY / f"{name}.md").read_text(encoding="utf-8").strip().splitlines()
    title = lines[0].lstrip("# ").strip()
    rest = "\n".join(lines[1:]).strip()
    lead, _, body = rest.partition("\n\n")
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    body = markdown.markdown(body, extensions=["tables"])
    body = body.replace("<table>", '<div class="table-wrap">\n<table>')
    body = body.replace("</table>", "</table>\n</div>")
    return title, lead.strip(), body


def page_nav(index):
    """新しい更新・前の更新へのリンク。"""
    parts = []
    if index < len(HISTORY) - 1:
        date, name = HISTORY[index + 1]
        parts.append(f'<a class="prev" href="/history/{page_name(date)}"><small>前の更新</small>{date_label(date)}</a>')
    else:
        parts.append("<span></span>")
    if index > 0:
        date, name = HISTORY[index - 1]
        parts.append(f'<a class="next" href="/history/{page_name(date)}"><small>新しい更新</small>{date_label(date)}</a>')
    return '<nav class="page-nav" aria-label="前後の更新">\n  ' + "\n  ".join(parts) + "\n</nav>"


def build_page(index):
    date, name = HISTORY[index]
    title, lead, body = read_entry(name)
    main = f"""<main class="howto-page">
  <p class="breadcrumb"><a href="/history/">更新履歴</a></p>
  <h1>{title}</h1>
  <p class="history-date"><time datetime="{date}">{date_label(date)}</time>　版 {version_label(name)}</p>
  <p class="lead">{lead}</p>
  <article>
{indent(body, 4)}
  </article>
{indent(page_nav(index), 2)}
</main>
"""
    out = HEAD.format(title=f"{title}｜更新履歴", description=html.escape(lead)) + indent(main, 2) + "\n" + FOOT
    (OUT / f"{page_name(date)}.html").write_text(out, encoding="utf-8")
    return lead


def build_index(leads):
    items = []
    for (date, name), lead in zip(HISTORY, leads):
        items.append(f"""<li>
  <a href="/history/{page_name(date)}">
    <time class="date" datetime="{date}">{date_label(date)}</time>
    <span class="text"><b>版 {version_label(name)}</b><small>{lead}</small></span>
  </a>
</li>""")
    main = f"""<main class="howto-page">
  <p class="eyebrow">HISTORY</p>
  <h1>更新履歴</h1>
  <p class="lead">耕雲のアプリを更新したときに、変わったところをお知らせします。新しいものから順に並んでいます。</p>
  <ul class="howto-list history-list">
{indent(chr(10).join(items), 4)}
  </ul>
  <a class="back-link" href="/">← トップページへ戻る</a>
</main>
"""
    out = HEAD.format(title="更新履歴", description="耕雲のアプリの更新履歴です。") + indent(main, 2) + "\n" + FOOT
    (OUT / "index.html").write_text(out, encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    leads = [build_page(i) for i in range(len(HISTORY))]
    build_index(leads)
    # HISTORY から外した日のページは消す
    keep = {f"{page_name(date)}.html" for date, _ in HISTORY} | {"index.html"}
    for old in OUT.glob("*.html"):
        if old.name not in keep:
            old.unlink()
    for date, name in HISTORY:
        print(f"history/{page_name(date)}.html ← {name}.md")


if __name__ == "__main__":
    main()
