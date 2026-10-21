"""利用規約と個人情報の取扱いのHTMLを、kouun/docs/legal/ の原稿（Markdown）から作る。

使い方（www/ で実行）:
    python3 tools/gen_legal.py

必要なもの: Python の markdown ライブラリ（pip install markdown）
原稿が変わったら、これを実行して public/legal/ のHTMLを作り直す。
"""
from pathlib import Path

import markdown

WWW = Path(__file__).resolve().parent.parent
DOCS_LEGAL = WWW.parent / "docs" / "legal"

# 原稿のファイル名、出力先、ページのタイトル
PAGES = [
    ("terms.md", "terms.html", "利用規約"),
    ("privacy.md", "privacy.html", "個人情報の取扱い"),
]

TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>{title}｜耕雲（kouun）</title>
  <link rel="stylesheet" href="/css/style.css">
</head>
<body>
  <p class="notice">テスト版です。</p>
  <main>
    <p class="formal">正式な内容は、アプリの中で表示されるものです。ご利用の際は、アプリの中で内容をご確認のうえ、同意していただきます。</p>
    <article>
{body}
    </article>
    <p><a href="/">トップへ戻る</a></p>
  </main>
  <footer>© takaosan.app</footer>
</body>
</html>
"""


def to_body(md_text):
    """Markdownを本文のHTMLにする。表はスマホで横にスクロールできるよう囲む。"""
    body = markdown.markdown(md_text, extensions=["tables"])
    body = body.replace("<table>", '<div class="table-wrap">\n<table>')
    body = body.replace("</table>", "</table>\n</div>")
    return "\n".join("      " + line if line else line for line in body.splitlines())


def main():
    for src, dst, title in PAGES:
        md_text = (DOCS_LEGAL / src).read_text(encoding="utf-8")
        html = TEMPLATE.format(title=title, body=to_body(md_text))
        out = WWW / "public" / "legal" / dst
        out.write_text(html, encoding="utf-8")
        print(f"{src} -> {out.relative_to(WWW)}")


if __name__ == "__main__":
    main()
