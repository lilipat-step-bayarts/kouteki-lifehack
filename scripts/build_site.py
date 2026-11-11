#!/usr/bin/env python3
"""
Cloudflare Pages公開用の静的HTMLサイトジェネレーター（忍者AdMax実稼働タグ埋め込み版）
"""

import json
import os

ARTICLES_JSON = "/home/antigravity/proto/articles/articles.json"
DIST_DIR = "/home/antigravity/proto/dist"

# ユーザー様から提供された実稼働 忍者AdMax タグ
NINJA_AD_TAG = """
<!-- admax -->
<script src="https://adm.shinobi.jp/s/b133ea03dc5417daa8dc029d6b6b4816"></script>
<!-- admax -->
"""

BASE_HTML_HEAD = """
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Noto Sans JP', sans-serif; }
    /* テーブル横スクロールのヒント */
    .table-container {
      position: relative;
    }
  </style>
"""

HEADER_NAV = """
  <header class="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
    <div class="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
      <a href="/" class="flex items-center gap-2">
        <span class="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-bold text-base shadow-sm">公</span>
        <div class="flex flex-col">
          <span class="font-extrabold text-slate-900 text-base tracking-tight leading-tight">公的ライフハック速報</span>
          <span class="text-[10px] text-slate-500 font-medium">制度とお金の知恵袋 by ほぽりん</span>
        </div>
      </a>
      <nav class="flex items-center gap-3 md:gap-4 text-xs font-semibold text-slate-600">
        <a href="/" class="hover:text-blue-600">最新記事</a>
        <a href="/about.html" class="hover:text-blue-600">運営者:ほぽりん</a>
        <a href="/privacy.html" class="hover:text-blue-600">プライバシー</a>
      </nav>
    </div>
  </header>
"""

FOOTER = """
  <footer class="bg-slate-900 text-slate-400 py-12 mt-16 text-xs pb-28 md:pb-16">
    <div class="max-w-4xl mx-auto px-4 space-y-6 text-center">
      <div class="flex flex-wrap justify-center gap-6">
        <a href="/" class="hover:text-white">トップページ</a>
        <a href="/about.html" class="hover:text-white">運営者情報・編集方針（ほぽりん）</a>
        <a href="/privacy.html" class="hover:text-white">プライバシーポリシー・免責事項</a>
      </div>
      <div class="max-w-lg mx-auto text-slate-500 leading-relaxed text-[11px]">
        当サイトは編集長「ほぽりん」が各省庁・自治体等の公的発表（一次情報）を収集し、生活者視点で分かりやすく図解・要約してお届けする個人メディアです。
      </div>
      <p class="text-slate-600">© 2024 公的ライフハック速報 All Rights Reserved.</p>
    </div>
  </footer>
"""

AUTHOR_CARD = """
  <div class="mt-8 p-5 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl flex items-center gap-4">
    <div class="w-14 h-14 rounded-full bg-blue-600 text-white flex-shrink-0 flex items-center justify-center font-bold text-xl shadow-md border-2 border-white">
      ほ
    </div>
    <div class="space-y-1">
      <div class="flex items-center gap-2">
        <span class="text-xs font-bold text-blue-800">この記事の編集・監修</span>
        <span class="font-extrabold text-sm text-slate-900">ほぽりん</span>
        <span class="text-[10px] px-2 py-0.5 rounded-full bg-blue-200 text-blue-800 font-medium">制度ハック研究家</span>
      </div>
      <p class="text-xs text-slate-600 leading-relaxed">
        「難解な官公庁の発表を、3秒でわかる結論にする」をモットーに公的情報・補助金・税制改正を毎日チェック＆発信中。損をしない生活防衛術をお届けします。
      </p>
    </div>
  </div>
"""

def live_ad_box(label):
    return f"""
    <div class="my-6 border border-slate-200/80 bg-slate-50/80 rounded-2xl p-3 text-center overflow-hidden">
      <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">スポンサーリンク</div>
      <div class="flex justify-center items-center min-h-[250px]">
        {NINJA_AD_TAG}
      </div>
    </div>
    """

def build_index(articles):
    cards_html = ""
    for art in articles:
        cards_html += f"""
        <article class="bg-white border border-slate-200 rounded-2xl p-5 md:p-6 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold px-2.5 py-0.5 rounded bg-blue-100 text-blue-800">{art['category']}</span>
              <time class="text-xs text-slate-400">{art['date']}</time>
            </div>
            <h2 class="text-base md:text-lg font-bold text-slate-900 hover:text-blue-600 transition-colors leading-snug">
              <a href="/articles/{art['id']}.html">{art['title']}</a>
            </h2>
            <p class="text-xs text-slate-600 mt-2.5 leading-relaxed line-clamp-3">{art['summary']}</p>
          </div>
          <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
            <span class="text-[11px] text-slate-400 flex items-center gap-1">
              <span>✍ ほぽりん要約</span>
            </span>
            <a href="/articles/{art['id']}.html" class="text-xs font-bold text-blue-600 hover:underline flex items-center gap-1">
              詳しく見る →
            </a>
          </div>
        </article>
        """

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  {BASE_HTML_HEAD}
  <title>公的ライフハック速報 - 制度・給付金・生活マネーまとめ by ほぽりん</title>
  <meta name="description" content="難解な公的制度・補助金・減税手続きを、3秒でわかる結論・チェックリスト・比較表で解説する生活応援メディアです。運営：ほぽりん">
</head>
<body class="bg-slate-50 text-slate-800 antialiased min-h-screen flex flex-col justify-between">
  <div>
    {HEADER_NAV}
    
    <main class="max-w-4xl mx-auto px-4 py-6 md:py-8 space-y-6">
      
      <!-- Hero -->
      <section class="bg-gradient-to-r from-blue-700 via-indigo-700 to-blue-800 text-white rounded-3xl p-6 md:p-8 shadow-md">
        <div class="flex items-center gap-2 mb-2">
          <span class="px-3 py-1 rounded-full text-xs font-semibold bg-white/20 text-white">
            公的情報・補助金速報
          </span>
          <span class="text-xs text-blue-200">編集長：ほぽりん</span>
        </div>
        <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight">「知らないと損する」公的制度を<br class="hidden sm:inline">3秒でわかる結論に。</h1>
        <p class="text-xs md:text-sm text-blue-100 mt-2 max-w-xl leading-relaxed">
          難しいお役所発表を、生活者が今すぐ得する具体的なアクションに要約してお届けします。
        </p>
      </section>

      {live_ad_box("トップ上部")}

      <!-- Article Grid -->
      <section class="space-y-4">
        <div class="flex items-center justify-between border-b border-slate-200 pb-2">
          <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
            注目の制度・給付金解説
          </h2>
          <span class="text-xs text-slate-400">毎日更新中</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          {cards_html}
        </div>
      </section>

      {live_ad_box("トップ下部")}

    </main>
  </div>
  {FOOTER}
</body>
</html>
"""

def build_article_page(art):
    audience_li = "".join([f'<li class="flex items-start gap-2 text-sm text-slate-700"><span class="text-blue-500 font-bold mt-0.5">✅</span><span class="leading-relaxed">{a}</span></li>' for a in art['target_audience']])
    
    table_headers = "".join([f'<th class="px-3 py-2.5 font-bold bg-slate-100 whitespace-nowrap">{h}</th>' for h in art['table_headers']])
    table_rows = ""
    for r in art['table_rows']:
        table_rows += '<tr class="border-b border-slate-100 hover:bg-slate-50/50">' + "".join([f'<td class="px-3 py-2.5 text-slate-700 whitespace-nowrap sm:whitespace-normal">{c}</td>' for c in r]) + '</tr>'

    steps_html = ""
    for s in art['steps']:
        steps_html += f"""
        <div class="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-1.5">
          <div class="font-bold text-xs text-blue-600 flex items-center gap-1.5">
            <span class="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-mono font-bold">{s['step']}</span>
            <span class="text-slate-900 text-sm">{s['title']}</span>
          </div>
          <p class="text-xs md:text-sm text-slate-600 leading-relaxed pl-1">{s['desc']}</p>
        </div>
        """

    faq_html = ""
    for f in art['faq']:
        faq_html += f"""
        <div class="space-y-1 p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div class="font-bold text-xs md:text-sm text-slate-900 flex items-start gap-1.5">
            <span class="text-blue-600 font-bold">Q.</span>
            <span>{f['q']}</span>
          </div>
          <div class="text-xs md:text-sm text-slate-600 pl-4 border-l-2 border-emerald-500 mt-1 leading-relaxed">
            {f['a']}
          </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  {BASE_HTML_HEAD}
  <title>{art['title']} - 公的ライフハック速報 by ほぽりん</title>
  <meta name="description" content="{art['summary']}">
</head>
<body class="bg-slate-50 text-slate-800 antialiased min-h-screen flex flex-col justify-between">
  <div>
    {HEADER_NAV}

    <main class="max-w-3xl mx-auto px-4 py-6 md:py-8">
      
      <div class="bg-white border border-slate-200 rounded-3xl p-5 md:p-8 shadow-sm space-y-6">
        
        <!-- Breadcrumbs -->
        <nav class="text-xs text-slate-400 flex items-center gap-1.5">
          <a href="/" class="hover:underline">ホーム</a>
          <span>›</span>
          <span>{art['category']}</span>
        </nav>

        <div>
          <div class="flex items-center gap-2 mb-2 flex-wrap">
            <span class="text-xs font-bold px-2.5 py-0.5 rounded bg-blue-100 text-blue-800">{art['category']}</span>
            <time class="text-xs text-slate-400">{art['date']} 更新</time>
            <span class="text-xs text-slate-400">・ 編集: ほぽりん</span>
          </div>
          <h1 class="text-xl md:text-2xl font-bold text-slate-900 leading-snug">
            {art['title']}
          </h1>
        </div>

        <!-- 3-sec summary -->
        <div class="bg-blue-50 border-l-4 border-blue-600 p-4 md:p-5 rounded-r-2xl">
          <div class="text-xs font-bold text-blue-800 mb-1 flex items-center gap-1">
            <span>⏱️</span> 【3秒でわかる結論】
          </div>
          <p class="text-sm md:text-base text-slate-700 leading-relaxed font-medium">
            {art['summary']}
          </p>
        </div>

        {live_ad_box("記事上部・ファーストビュー直下")}

        <!-- Section 1 -->
        <section class="space-y-3">
          <h2 class="text-base md:text-lg font-bold text-slate-900 flex items-center gap-2 border-b border-slate-200 pb-2">
            <span class="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs">1</span>
            あなたは対象？対象者チェックリスト
          </h2>
          <ul class="space-y-2.5 pl-1">
            {audience_li}
          </ul>
          <div class="mt-4 p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs md:text-sm">
            <span class="text-emerald-800 font-semibold">💡 いくら得する？（目安受給・減税額）</span>
            <span class="font-bold text-emerald-700 text-sm md:text-base">{art['benefit_amount']}</span>
          </div>
        </section>

        <!-- Section 2 -->
        <section class="space-y-3">
          <div class="flex items-center justify-between border-b border-slate-200 pb-2">
            <h2 class="text-base md:text-lg font-bold text-slate-900 flex items-center gap-2">
              <span class="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs">2</span>
              【一覧表】条件と具体的な控除・補助内容
            </h2>
          </div>
          <div class="text-[11px] text-slate-400 block sm:hidden">← 指で左右にスクロールできます →</div>
          <div class="overflow-x-auto rounded-2xl border border-slate-200">
            <table class="w-full text-xs md:text-sm text-left">
              <thead><tr>{table_headers}</tr></thead>
              <tbody>{table_rows}</tbody>
            </table>
          </div>
        </section>

        {live_ad_box("記事中間・高クリック率枠")}

        <!-- Section 3 -->
        <section class="space-y-3">
          <h2 class="text-base md:text-lg font-bold text-slate-900 flex items-center gap-2 border-b border-slate-200 pb-2">
            <span class="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs">3</span>
            損しないための手続き 3ステップ
          </h2>
          <div class="space-y-3">
            {steps_html}
          </div>
        </section>

        <!-- Section 4 -->
        <section class="space-y-3">
          <h2 class="text-base md:text-lg font-bold text-slate-900 flex items-center gap-2 border-b border-slate-200 pb-2">
            <span class="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs">4</span>
            よくある疑問・Q&A
          </h2>
          <div class="space-y-3">
            {faq_html}
          </div>
        </section>

        <!-- Official source -->
        <div class="p-4 bg-slate-50 border border-slate-200 rounded-2xl text-xs space-y-1">
          <div class="font-bold text-slate-800">🏛️ 一次情報・公式発表引用元</div>
          <p class="text-slate-500">本記事は正確な制度理解のため、以下の公的機関の発表情報を基に要約・作成しています。</p>
          <a href="{art['source_url']}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline flex items-center gap-1 font-medium mt-1">
            <span>{art['source_name']}</span> ↗
          </a>
        </div>

        <!-- 著者プロフィールカード（E-E-A-T対策） -->
        {AUTHOR_CARD}

        {live_ad_box("記事末尾・読了後レコメンド枠")}

      </div>

    </main>
  </div>
  {FOOTER}
</body>
</html>
"""

def build_static_pages():
    about_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  {BASE_HTML_HEAD}
  <title>運営者情報・編集方針 - 公的ライフハック速報 (ほぽりん)</title>
</head>
<body class="bg-slate-50 text-slate-800 antialiased min-h-screen flex flex-col justify-between">
  <div>
    {HEADER_NAV}
    <main class="max-w-3xl mx-auto px-4 py-8">
      <div class="bg-white border border-slate-200 rounded-3xl p-6 md:p-8 shadow-sm space-y-6">
        <h1 class="text-xl font-bold text-slate-900 border-b border-slate-200 pb-3">運営者情報・編集方針</h1>
        
        <div class="flex items-center gap-4 p-4 bg-blue-50 rounded-2xl">
          <div class="w-16 h-16 rounded-full bg-blue-600 text-white flex-shrink-0 flex items-center justify-center font-bold text-2xl shadow">
            ほ
          </div>
          <div>
            <div class="text-base font-bold text-slate-900">ほぽりん（編集長・運営者）</div>
            <div class="text-xs text-slate-600 mt-1">
              生活情報ハック・公的給付金・税制リサーチャー。
            </div>
          </div>
        </div>

        <div class="space-y-4 text-xs md:text-sm text-slate-700 leading-relaxed">
          <h2 class="text-sm md:text-base font-bold text-slate-900">サイトの目的と理念</h2>
          <p>
            「公的ライフハック速報」は、省庁や各自治体などが発表する難解な公的制度・補助金・減税・給付金等の公式情報を、生活者が直感的に理解し活用できるよう分かりやすく整理・要約して発信する情報メディアです。
          </p>

          <h2 class="text-sm md:text-base font-bold text-slate-900">情報の正確性と一次情報（一次ソース）へのこだわり</h2>
          <p>
            記事の作成にあたっては、官公庁のプレスリリース、公式Webサイト、各自治体の手引きなどの「一次情報」を必ず精査・引用しています。制度の最新情報や個別具体的な申請方法については、必ず記事末尾に記載の公式リンク先をご確認ください。
          </p>

          <h2 class="text-sm md:text-base font-bold text-slate-900">お問い合わせ</h2>
          <p>
            掲載内容に関するお問い合わせや修正のご要望は、サイト管理者（ほぽりん）宛てにご連絡ください。
          </p>
        </div>
      </div>
    </main>
  </div>
  {FOOTER}
</body>
</html>"""

    privacy_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  {BASE_HTML_HEAD}
  <title>プライバシーポリシー・広告について - 公的ライフハック速報</title>
</head>
<body class="bg-slate-50 text-slate-800 antialiased min-h-screen flex flex-col justify-between">
  <div>
    {HEADER_NAV}
    <main class="max-w-3xl mx-auto px-4 py-8">
      <div class="bg-white border border-slate-200 rounded-3xl p-6 md:p-8 shadow-sm space-y-6">
        <h1 class="text-xl font-bold text-slate-900 border-b border-slate-200 pb-3">プライバシーポリシー・広告配信について</h1>
        <div class="space-y-4 text-xs md:text-sm text-slate-700 leading-relaxed">
          <h2 class="text-sm md:text-base font-bold text-slate-900">広告の配信について</h2>
          <p>
            当サイトでは、第三者配信の広告サービス（忍者AdMax、各種アフィリエイトプログラム等）を利用しています。広告配信事業者は、利用者の興味に応じた広告を表示するためにCookie（クッキー）を使用することがあります。
          </p>
          <h2 class="text-sm md:text-base font-bold text-slate-900">免責事項</h2>
          <p>
            当サイトに掲載されている情報については、可能な限り正確を期しておりますが、内容の正確性や安全性を完全に保証するものではありません。当サイトの情報を利用したことにより生じた損害等について、運営者（ほぽりん）は一切の責任を負いかねます。
          </p>
        </div>
      </div>
    </main>
  </div>
  {FOOTER}
</body>
</html>"""

    return about_html, privacy_html

def main():
    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(os.path.join(DIST_DIR, "articles"), exist_ok=True)

    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # 1. index.html
    with open(os.path.join(DIST_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index(articles))

    # 2. article pages
    for art in articles:
        p = os.path.join(DIST_DIR, "articles", f"{art['id']}.html")
        with open(p, "w", encoding="utf-8") as f:
            f.write(build_article_page(art))

    # 3. about & privacy
    about_html, privacy_html = build_static_pages()
    with open(os.path.join(DIST_DIR, "about.html"), "w", encoding="utf-8") as f:
        f.write(about_html)
    with open(os.path.join(DIST_DIR, "privacy.html"), "w", encoding="utf-8") as f:
        f.write(privacy_html)

    print("Site generated with real Ninja AdMax tags at:", DIST_DIR)

if __name__ == "__main__":
    main()
