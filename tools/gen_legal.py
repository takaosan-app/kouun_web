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

  <main>
    <p class="formal">正式な内容は、アプリの中で表示されるものです。ご利用の際は、アプリの中で内容をご確認のうえ、同意していただきます。</p>
    <article>
{body}
    </article>
    <a class="back-link" href="/">← トップページへ戻る</a>
  </main>

  <footer class="site-footer">
    <a class="footer-brand" href="/">耕雲 <span>こううん</span></a>
    <p>天気とともに、畑を育てる。</p>
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
