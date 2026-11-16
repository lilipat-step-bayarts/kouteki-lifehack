#!/usr/bin/env python3
"""
4号店：バズハック速報 | 知らなきゃ損するSNS神アイテム研究所 by 全知全能の神ゼウス ⚡
Cloudflare Pages公開用の静的HTMLサイトジェネレーター
"""

import json
import os
import urllib.parse
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORE4_DIR = os.path.dirname(SCRIPT_DIR)
ARTICLES_JSON = os.path.join(STORE4_DIR, "articles", "articles.json")
DIST_DIR = os.path.join(STORE4_DIR, "dist")
DIST_ARTICLES_DIR = os.path.join(DIST_DIR, "articles")
DIST_ASSETS_DIR = os.path.join(DIST_DIR, "assets")

SITE_TITLE = "バズハック速報 | 知らなきゃ損するSNS神アイテム研究所 by 神ゼウス ⚡"
SITE_DESCRIPTION = "「知らぬ者は人生を大損しておるぞ！」SNSで10万いいね超えのバズり神アイテム、カルディ・無印・100均・Amazonの品薄名品を全知全能の神ゼウスが忖度なしで緊急審判するトレンド特化メディア。"
SITE_URL = "https://buzzhack-zeus.pages.dev"

# 忍者AdMax 広告コード
NINJA_AD_SCRIPT = """
<!-- 忍者AdMax ビュー報酬ユニット -->
<div class="my-6 p-3 bg-amber-50/50 rounded-2xl border border-amber-200/80 flex flex-col items-center justify-center min-h-[120px] text-center">
  <span class="text-[10px] text-amber-600 font-bold tracking-wider mb-1">⚡ SPONSOR LINK ⚡</span>
  <script src="https://adm.shinobi.jp/s/b133ea03dc5417daa8dc029d6b6b4816"></script>
</div>
"""

AMAZON_TAG = "ikerocosme-22"
RAKUTEN_AF_ID = "597f29ed.f305c9f6.597f29ee.8555f86c"

# ゼウスの執筆・監修者プロフィールカード
ZEUS_AUTHOR_CARD = """
      <!-- ゼウスの神託プロフィールカード -->
      <div class="mt-8 p-5 bg-gradient-to-r from-amber-500/10 via-yellow-400/15 to-amber-500/10 border-2 border-amber-400/80 rounded-3xl space-y-3.5 shadow-md">
        <div class="flex items-start sm:items-center gap-4 flex-col sm:flex-row">
          <img src="/assets/zeus_avatar.jpg" alt="神ゼウス" class="w-16 h-16 rounded-full border-2 border-amber-400 shadow-md object-cover shrink-0">
          <div class="space-y-1 w-full">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-[11px] font-black px-2.5 py-0.5 rounded-full bg-gradient-to-r from-amber-500 to-yellow-500 text-white shadow-xs">審判・最高総責任者</span>
                <span class="font-black text-slate-900 text-base">全知全能の神「ゼウス」⚡</span>
              </div>
              <a href="https://x.com/ramune_lilipat" target="_blank" rel="noopener noreferrer" class="text-[11px] px-3 py-1 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-full transition flex items-center gap-1 shadow-sm">
                <svg class="w-3 h-3 fill-current" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                Xで神速報を受け取る
              </a>
            </div>
            <p class="text-xs font-bold text-amber-900">天上からSNSのトレンドを常時監視 × 損する人間を救う神アイテムハンター</p>
          </div>
        </div>

        <div class="bg-white/95 rounded-2xl p-4 border border-amber-200/90 space-y-2 text-xs">
          <div class="font-black text-slate-800 flex items-center gap-1.5 text-xs text-amber-700">
            <span>⚡</span> ゼウスの絶対審判ルール（編集方針）
          </div>
          <p class="text-[11px] text-slate-600 leading-relaxed font-medium">
            「無駄な出費で消耗する人間どもを救済する！」を唯一の使命とし、企業の提灯記事やステマ広告に一切惑わされず、SNSで10万いいね超えの真の神アイテム・品薄グッズのみを厳選。知らなきゃ損するライフハックだけを天上から授けるメディアである。
          </p>
        </div>
      </div>
"""

def get_god_item_card(art):
    query = urllib.parse.quote(art.get("search_keyword", art.get("product_name", "")))
    amazon_url = f"https://www.amazon.co.jp/s?k={query}&tag={AMAZON_TAG}"
    rakuten_search_url = f"https://search.rakuten.co.jp/search/mall/{query}/"
    rakuten_pc = urllib.parse.quote(rakuten_search_url, safe="")
    rakuten_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_AF_ID}/?pc={rakuten_pc}&link_type=text"

    return f"""
    <!-- ⚡ ゼウス公認・神アイテム衝動買いカード ⚡ -->
    <div class="my-6 p-5 bg-gradient-to-br from-amber-50 via-yellow-50/60 to-amber-100/50 rounded-3xl border-2 border-amber-300 shadow-md space-y-3">
      <div class="flex items-center justify-between flex-wrap gap-2">
        <span class="px-3 py-1 rounded-full text-xs font-black bg-gradient-to-r from-amber-500 to-yellow-500 text-white shadow-sm flex items-center gap-1">
          <span>⚡</span> ゼウス公認・神アイテム
        </span>
        <span class="text-xs font-black text-amber-900 bg-amber-100 px-2.5 py-0.5 rounded-full border border-amber-300">
          {art.get('god_level', '神コスパ度: ★★★★★')}
        </span>
      </div>

      <div>
        <h4 class="text-base md:text-lg font-black text-slate-900 leading-snug">{art.get('product_name', '')}</h4>
        <div class="text-xs font-bold text-amber-700 font-mono mt-0.5">参考相場: {art.get('price', '売り切れ注意')}</div>
      </div>

      <div class="p-3 bg-white/90 rounded-2xl border border-amber-200 text-xs text-slate-700 leading-relaxed font-medium">
        <span class="font-bold text-amber-900">👑 ゼウスの神託：</span>{art.get('merit', '')}
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
        <a href="{amazon_url}" target="_blank" rel="noopener noreferrer sponsored" class="py-3 px-4 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white text-center rounded-2xl font-black text-xs shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2">
          <span>⚡ Amazonで在庫・価格を即確認</span>
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
        </a>
        <a href="{rakuten_url}" target="_blank" rel="noopener noreferrer sponsored" class="py-3 px-4 bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white text-center rounded-2xl font-black text-xs shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2">
          <span>🎁 楽天市場で最安値を今すぐ比較</span>
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
        </a>
      </div>
    </div>
    """

def get_header(current_page="home"):
    return f"""
  <header class="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-amber-200 shadow-sm">
    <div class="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
      <a href="/" class="flex items-center gap-2.5 group">
        <img src="/assets/zeus_avatar.jpg" alt="神ゼウス" class="w-10 h-10 rounded-full border-2 border-amber-400 shadow-sm object-cover group-hover:scale-105 transition-transform">
        <div>
          <span class="text-[10px] font-black text-amber-600 tracking-wider block">知らなきゃ大損！SNS神アイテム</span>
          <span class="text-base font-black text-slate-900 tracking-tight flex items-center gap-1">
            バズハック速報 <span class="text-amber-500 text-xs">⚡</span>
          </span>
        </div>
      </a>
      <nav class="flex items-center gap-4 text-xs font-bold text-slate-700">
        <a href="/" class="hover:text-amber-600 transition {'text-amber-600' if current_page == 'home' else ''}">新着神アイテム</a>
        <a href="/about" class="hover:text-amber-600 transition {'text-amber-600' if current_page == 'about' else ''}">ゼウスとは？</a>
        <a href="/privacy" class="hover:text-amber-600 transition {'text-amber-600' if current_page == 'privacy' else ''}">免責・広告方針</a>
      </nav>
    </div>
  </header>
"""

def get_footer():
    return f"""
  <footer class="bg-slate-950 text-slate-400 py-12 mt-16 border-t-2 border-amber-500/40">
    <div class="max-w-4xl mx-auto px-4 text-center space-y-4">
      <div class="flex items-center justify-center gap-2">
        <img src="/assets/zeus_avatar.jpg" alt="神ゼウス" class="w-8 h-8 rounded-full border border-amber-400 object-cover">
        <span class="font-black text-white text-sm">バズハック速報 by 全知全能の神ゼウス ⚡</span>
      </div>
      <p class="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
        「知らぬ者は人生を大損しておるぞ！」SNSで10万いいね超えの神アイテム・バズり名品をゼウスが忖度なしで緊急審判するトレンド特化メディア。
      </p>
      <div class="text-[11px] text-slate-500 space-x-3 pt-2">
        <a href="/" class="hover:text-slate-200">トップ</a>
        <span>•</span>
        <a href="/about" class="hover:text-slate-200">サイト理念・ゼウスの神託</a>
        <span>•</span>
        <a href="/privacy" class="hover:text-slate-200">プライバシーポリシー・広告開示</a>
        <span>•</span>
        <a href="https://hoporin.lilipat-cosme-bayarts.com" target="_blank" rel="noopener" class="text-blue-400 hover:underline">1号店：公的ライフハック</a>
        <span>•</span>
        <a href="https://ikero.lilipat-cosme-bayarts.com" target="_blank" rel="noopener" class="text-emerald-400 hover:underline">2号店：イケロのコスメ成分ラボ</a>
      </div>
      <div class="text-[11px] text-slate-600 font-mono">
        © 2026 BuzzHack Zeus. All Rights Reserved.
      </div>
    </div>
  </footer>
"""

def markdown_to_html(md_text):
    lines = md_text.strip().split("\\n")
    html_parts = []
    in_table = False
    table_rows = []

    for line in lines:
        if line.startswith("# "):
            continue
        elif line.startswith("## "):
            heading = line[3:].strip()
            html_parts.append(f'<h2 class="text-lg md:text-xl font-black text-slate-900 mt-8 mb-3 pb-2 border-b-2 border-amber-400 flex items-center gap-2"><span class="text-amber-500">⚡</span>{heading}</h2>')
        elif line.startswith("### "):
            heading = line[4:].strip()
            html_parts.append(f'<h3 class="text-base md:text-lg font-bold text-slate-800 mt-6 mb-2 flex items-center gap-1.5"><span class="text-amber-500 font-black">▶</span>{heading}</h3>')
        elif line.startswith("|") and line.endswith("|"):
            if not in_table:
                in_table = True
                table_rows = [line]
            else:
                table_rows.append(line)
        else:
            if in_table:
                html_parts.append(render_table(table_rows))
                in_table = False
                table_rows = []
            if line.strip() == "---":
                html_parts.append('<hr class="my-6 border-amber-200">')
            elif line.strip():
                formatted_p = line
                # bold
                import re
                formatted_p = re.sub(r'\\*\\*(.*?)\\*\\*', r'<strong class="font-bold text-slate-900 bg-amber-100/70 px-1 py-0.5 rounded">\\1</strong>', formatted_p)
                html_parts.append(f'<p class="text-sm md:text-base leading-relaxed text-slate-700 my-3 font-normal">{formatted_p}</p>')

    if in_table:
        html_parts.append(render_table(table_rows))

    return "\\n".join(html_parts)

def render_table(rows):
    if len(rows) < 2:
        return ""
    header_cols = [c.strip() for c in rows[0].strip("|").split("|")]
    data_rows = rows[2:] if len(rows) > 2 and "---" in rows[1] else rows[1:]

    html = '<div class="overflow-x-auto my-4 rounded-2xl border border-amber-200 shadow-sm"><table class="w-full text-xs md:text-sm text-left">'
    html += '<thead class="bg-amber-100/80 text-amber-950 font-black"><tr>'
    for col in header_cols:
        html += f'<th class="px-4 py-2.5">{col}</th>'
    html += '</tr></thead><tbody>'
    for r in data_rows:
        cols = [c.strip() for c in r.strip("|").split("|")]
        html += '<tr class="border-t border-amber-100 hover:bg-amber-50/50 transition">'
        for c in cols:
            html += f'<td class="px-4 py-2 text-slate-700 font-medium">{c}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html

def build_article_page(art, all_articles):
    slug = art['slug']
    article_url = f"{SITE_URL}/articles/{slug}"
    encoded_title = urllib.parse.quote(f"【知らなきゃ大損】{art['title']} #バズハック #神アイテム #ゼウス")
    encoded_share_url = urllib.parse.quote(article_url)

    related = [a for a in all_articles if a['id'] != art['id']][:4]
    related_html = ""
    for r_art in related:
        related_html += f"""
        <a href="/articles/{r_art['slug']}" class="block p-4 bg-white hover:bg-amber-50/60 border border-amber-200 hover:border-amber-400 rounded-2xl transition group shadow-2xs">
          <div class="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span class="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-bold">{r_art['category']}</span>
            <span>{r_art['date']}</span>
          </div>
          <div class="text-xs md:text-sm font-bold text-slate-900 group-hover:text-amber-700 leading-snug">{r_art['title']}</div>
        </a>
        """

    content_html = markdown_to_html(art['content'])
    god_card_html = get_god_item_card(art)

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": art['title'],
        "description": art['summary'],
        "image": [f"{SITE_URL}/assets/zeus_banner.jpg"],
        "datePublished": art['date'],
        "dateModified": art['date'],
        "author": [{"@type": "Person", "name": "神ゼウス (バズハック速報)", "url": f"{SITE_URL}/about"}]
    }, ensure_ascii=False)

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{art['title']} | バズハック速報</title>
  <meta name="description" content="{art['summary']}">
  <link rel="canonical" href="{article_url}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="バズハック速報 by 神ゼウス">
  <meta property="og:title" content="{art['title']}">
  <meta property="og:description" content="{art['summary']}">
  <meta property="og:url" content="{article_url}">
  <meta property="og:image" content="{SITE_URL}/assets/zeus_banner.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@ramune_lilipat">
  <meta name="twitter:title" content="{art['title']}">
  <meta name="twitter:description" content="{art['summary']}">
  <meta name="twitter:image" content="{SITE_URL}/assets/zeus_banner.jpg">
  <script type="application/ld+json">{json_ld}</script>
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3133098627249534" crossorigin="anonymous"></script>
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-amber-50/20 text-slate-800 antialiased font-sans min-h-screen flex flex-col justify-between">
  <div>
    {get_header("article")}

    <main class="max-w-3xl mx-auto px-4 py-6 md:py-8">
      <article class="bg-white rounded-3xl p-5 md:p-8 border border-amber-200/90 shadow-sm space-y-6">
        
        <!-- パンくず -->
        <nav class="text-xs text-slate-400 flex items-center gap-1.5">
          <a href="/" class="hover:underline">ホーム</a>
          <span>›</span>
          <span class="text-amber-700 font-bold">{art['category']}</span>
        </nav>

        <!-- タイトルエリア -->
        <header class="space-y-3">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300">{art['category']}</span>
            <time class="text-xs text-slate-400">{art['date']} 更新</time>
            <span class="text-xs text-amber-600 font-bold">⚡ 審判: 神ゼウス</span>
          </div>
          <h1 class="text-xl md:text-2xl font-black text-slate-900 leading-snug">
            {art['title']}
          </h1>
        </header>

        <!-- ゼウスの警告リード文 -->
        <div class="p-4 bg-gradient-to-r from-amber-100/90 via-yellow-100/70 to-amber-100/90 border-l-4 border-amber-500 rounded-r-2xl text-xs md:text-sm text-amber-950 font-bold leading-relaxed shadow-2xs">
          ⚡ 【ゼウスの緊急神託】{art['summary']}
        </div>

        {NINJA_AD_SCRIPT}

        <!-- 本文 -->
        <div class="article-content pt-2">
          {content_html}
        </div>

        <!-- 神アイテムカード -->
        {god_card_html}

        {ZEUS_AUTHOR_CARD}

        {NINJA_AD_SCRIPT}

        <!-- シェア & フォロー -->
        <div class="pt-6 border-t border-amber-100 flex flex-col sm:flex-row items-center justify-between gap-4">
          <a href="/" class="text-xs font-bold text-amber-700 hover:text-amber-800 flex items-center gap-1">
            ← 神アイテム一覧に戻る
          </a>
          <div class="flex items-center gap-2">
            <a href="https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_share_url}" target="_blank" rel="noopener noreferrer" class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm transition">
              <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
              Xでシェアして保存
            </a>
          </div>
        </div>

        <!-- 関連神アイテム -->
        <section class="pt-6 border-t border-amber-100 space-y-3">
          <h3 class="text-sm md:text-base font-black text-slate-900 flex items-center gap-1.5">
            <span>⚡</span> あわせて読みたい！知らなきゃ損する神アイテム
          </h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {related_html}
          </div>
        </section>

        <!-- 姉妹メディア送客 -->
        <div class="p-4 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-3">
          <div class="text-xs space-y-1">
            <span class="px-2 py-0.5 rounded bg-emerald-600 text-white font-bold text-[10px]">姉妹メディア</span>
            <div class="font-bold text-slate-900 text-sm">🦊 イケロのコスメ成分ラボ（最上位資格者監修）</div>
            <div class="text-slate-600">デパコス級なのに1,000円台！成分で選ぶ本当に効くプチプラコスメ速報！</div>
          </div>
          <a href="https://ikero.lilipat-cosme-bayarts.com" target="_blank" rel="noopener" class="shrink-0 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition">
            コスメ比較を見る →
          </a>
        </div>

      </article>
    </main>
  </div>

  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_ARTICLES_DIR, f"{slug}.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(page_html)

def build_home_page(articles):
    cards_html = []
    for art in articles:
        cards_html.append(f"""
        <a href="/articles/{art['slug']}" class="block bg-white rounded-3xl p-5 border border-amber-200 hover:border-amber-400 hover:shadow-md transition group flex flex-col justify-between">
          <div class="space-y-2">
            <div class="flex items-center justify-between text-xs text-slate-400">
              <span class="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 font-bold text-[11px] border border-amber-300">{art['category']}</span>
              <span>{art['date']}</span>
            </div>
            <h3 class="text-base font-black text-slate-900 group-hover:text-amber-600 transition leading-snug">
              {art['title']}
            </h3>
            <p class="text-xs text-slate-600 line-clamp-2 leading-relaxed font-medium">
              {art['summary']}
            </p>
          </div>
          <div class="mt-4 pt-3 border-t border-amber-100 flex items-center justify-between text-[11px] text-amber-700 font-black">
            <span>⚡ 神の審判を読む →</span>
            <span class="text-slate-400 font-normal">{art.get('reading_time', 3)}分で読める</span>
          </div>
        </a>
        """)

    home_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{SITE_TITLE}</title>
  <meta name="description" content="{SITE_DESCRIPTION}">
  <link rel="canonical" href="{SITE_URL}/">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="バズハック速報 by 神ゼウス">
  <meta property="og:title" content="{SITE_TITLE}">
  <meta property="og:description" content="{SITE_DESCRIPTION}">
  <meta property="og:url" content="{SITE_URL}/">
  <meta property="og:image" content="{SITE_URL}/assets/zeus_banner.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{SITE_TITLE}">
  <meta name="twitter:description" content="{SITE_DESCRIPTION}">
  <meta name="twitter:image" content="{SITE_URL}/assets/zeus_banner.jpg">
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3133098627249534" crossorigin="anonymous"></script>
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-amber-50/20 text-slate-800 antialiased font-sans min-h-screen flex flex-col justify-between">
  <div>
    {get_header("home")}

    <!-- ヒーローセクション -->
    <section class="relative bg-gradient-to-b from-amber-100/70 via-yellow-50/40 to-transparent py-10 border-b border-amber-200">
      <div class="max-w-4xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-6">
        <div class="space-y-3 max-w-xl text-center md:text-left">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500 text-white text-xs font-black shadow-sm">
            <span>⚡</span> 全知全能の神ゼウス降臨・忖度なし神アイテム審判
          </div>
          <h1 class="text-2xl md:text-3xl font-black text-slate-900 leading-tight">
            知らなきゃ人生大損！<br>
            <span class="text-amber-600">SNSで10万いいね超えの「神アイテム」速報。</span>
          </h1>
          <p class="text-xs md:text-sm text-slate-700 leading-relaxed font-medium">
            「人間どもよ、まだ無駄な出費で消耗しておるのか！？」カルディ・無印・100均・Amazonでバズりまくっている品薄神グッズを、全知全能の神ゼウスが天上から厳選審判！
          </p>
          <div class="flex flex-wrap gap-1.5 justify-center md:justify-start pt-1 text-[11px] font-bold text-slate-700">
            <span class="px-2.5 py-1 rounded-full bg-white border border-amber-300 shadow-2xs">⚡ 売り切れ必至の神グルメ</span>
            <span class="px-2.5 py-1 rounded-full bg-white border border-amber-300 shadow-2xs">⚡ 100均ジェネリック日用品</span>
            <span class="px-2.5 py-1 rounded-full bg-white border border-amber-300 shadow-2xs">⚡ QOL爆上げAmazonガジェット</span>
          </div>
        </div>
        <div class="shrink-0 relative">
          <img src="/assets/zeus_avatar.jpg" alt="神ゼウス" class="w-32 h-32 md:w-40 md:h-40 rounded-3xl border-4 border-amber-400 shadow-xl object-cover">
          <span class="absolute -bottom-2 -right-2 px-3 py-1 bg-gradient-to-r from-amber-500 to-yellow-500 text-white rounded-full text-xs font-black shadow">
            神ゼウス ⚡
          </span>
        </div>
      </div>
    </section>

    <!-- メインコンテンツ -->
    <main class="max-w-4xl mx-auto px-4 py-8 space-y-6">
      {NINJA_AD_SCRIPT}

      <div class="flex items-center justify-between">
        <h2 class="text-lg font-black text-slate-900 flex items-center gap-2">
          <span>⚡</span> 最新のバズり神アイテム・緊急審判一覧
        </h2>
        <span class="text-xs text-slate-500 font-bold">{len(articles)}件の神託</span>
      </div>

      <!-- 記事グリッド -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {''.join(cards_html)}
      </div>

      {NINJA_AD_SCRIPT}
    </main>
  </div>

  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_DIR, "index.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(home_html)
    print("Built Store 4 index: dist/index.html")

def build_about_page():
    about_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ゼウスについて・サイト理念 | バズハック速報</title>
  <meta name="description" content="全知全能の神ゼウスが率いる「バズハック速報」の運営方針と理念。無駄な出費で消耗する現代人を救済するため、SNSの10万いいね超え神アイテムを忖度なしで審判。">
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3133098627249534" crossorigin="anonymous"></script>
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-amber-50/20 text-slate-800 antialiased font-sans min-h-screen flex flex-col justify-between">
  <div>
    {get_header("about")}

    <main class="max-w-3xl mx-auto px-4 py-8">
      <div class="bg-white rounded-3xl p-6 md:p-10 border border-amber-200 shadow-sm space-y-8">
        
        <div class="text-center space-y-3 pb-6 border-b border-amber-100">
          <img src="/assets/zeus_avatar.jpg" alt="神ゼウス" class="w-28 h-28 rounded-full border-4 border-amber-400 mx-auto shadow-md object-cover">
          <h1 class="text-2xl font-black text-slate-900">全知全能の神「ゼウス」⚡</h1>
          <p class="text-xs md:text-sm text-amber-700 font-bold">バズハック速報 最高審判官 / SNS神アイテム研究所 所長</p>
        </div>

        <section class="space-y-3">
          <div class="flex items-center gap-2 border-b-2 border-amber-400 pb-2">
            <span class="text-lg">⚡</span>
            <h2 class="text-lg font-black text-slate-900">「バズハック速報」創設の神託</h2>
          </div>
          <div class="text-xs md:text-sm text-slate-700 leading-relaxed space-y-3 font-medium">
            <p>
              人間どもよ、よく聞くがよい！<br>
              世の中には、知っているだけで生活の面倒がゼロになり、毎月数千円〜数万円が浮く<strong>「本物の神アイテム」</strong>が存在する。
            </p>
            <p>
              しかし、多くの人間はその存在を知らぬまま、無駄に高額なブランド品を買い、非効率な毎日にストレスを溜め込んでおる。<br>
              実に嘆かわしい！知恵なき浪費は人生の最大の損失である！
            </p>
            <p>
              当ラボの使命はただ一つ。天上からSNSのビッグデータを常時監視し、<strong>「10万いいね超えの真の神アイテム」「知らなきゃ大損する神コスパ名品」</strong>だけを容赦なく審判し、愚かな人間たちに授けることである。
            </p>
          </div>
        </section>

        <section class="space-y-3">
          <div class="flex items-center gap-2 border-b-2 border-amber-400 pb-2">
            <span class="text-lg">👑</span>
            <h2 class="text-lg font-black text-slate-900">ゼウスの3大鉄則</h2>
          </div>
          <div class="bg-amber-50 rounded-2xl p-4 space-y-2 text-xs md:text-sm text-slate-800 font-medium">
            <div><strong>① ステマ・提灯記事の完全排除</strong>：神は企業からの金銭で評価を曲げぬ。真に生活を変える名品のみを認定する。</div>
            <div class="pt-1"><strong>② 「知らなきゃ損」の徹底追究</strong>：単なる新商品紹介ではなく、「これを使わないといくら損するか」を具体的に突きつける。</div>
            <div class="pt-1"><strong>③ 売り切れ前の最速共有</strong>：SNSでバズった瞬間に入手困難になる神アイテムを、在庫があるうちに読者へ授ける。</div>
          </div>
        </section>

      </div>
    </main>
  </div>

  {get_footer()}
</body>
</html>"""
    with open(os.path.join(DIST_DIR, "about.html"), "w", encoding="utf-8") as f:
        f.write(about_html)
    print("Built Store 4 about: dist/about")

def build_privacy_page():
    privacy_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>プライバシーポリシー・広告開示 | バズハック速報</title>
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3133098627249534" crossorigin="anonymous"></script>
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-amber-50/20 text-slate-800 antialiased font-sans min-h-screen flex flex-col justify-between">
  <div>
    {get_header("privacy")}

    <main class="max-w-3xl mx-auto px-4 py-8">
      <div class="bg-white rounded-3xl p-6 md:p-10 border border-amber-200 shadow-sm space-y-6">
        <h1 class="text-xl font-black text-slate-900 border-b-2 border-amber-400 pb-2">プライバシーポリシー・広告開示</h1>
        
        <div class="text-xs md:text-sm text-slate-600 leading-relaxed space-y-4">
          <h2 class="font-bold text-slate-800">1. 広告の配信について</h2>
          <p>当サイトでは、第三者配信の広告サービス（Google AdSense、忍者AdMax、Amazonアソシエイト、楽天アフィリエイト等）を利用しています。広告配信事業者は、利用者の興味に応じた広告を表示するためにCookie（クッキー）を使用することがあります。</p>

          <h2 class="font-bold text-slate-800">2. Amazonアソシエイトに関する開示</h2>
          <p>「バズハック速報」は、Amazon.co.jpを宣伝しリンクすることによってサイトが紹介料を獲得できる手段を提供することを目的に設定されたアフィリエイトプログラムである、Amazonアソシエイト・プログラムの参加者です。</p>

          <h2 class="font-bold text-slate-800">3. 免責事項</h2>
          <p>当サイトに掲載された情報については、万全の確認を行っておりますが、その正確性や安全性を保証するものではありません。各商品の最新価格や在庫状況は各販売店の公式サイトにてご確認ください。</p>
        </div>
      </div>
    </main>
  </div>

  {get_footer()}
</body>
</html>"""
    with open(os.path.join(DIST_DIR, "privacy.html"), "w", encoding="utf-8") as f:
        f.write(privacy_html)
    print("Built Store 4 privacy: dist/privacy")

def main():
    print("Building Store 4: バズハック速報 by 神ゼウス ⚡...")
    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(DIST_ARTICLES_DIR, exist_ok=True)
    os.makedirs(DIST_ASSETS_DIR, exist_ok=True)

    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    for art in articles:
        build_article_page(art, articles)
        print(f"Built Store 4 article: {art['slug']}")

    build_home_page(articles)
    build_about_page()
    build_privacy_page()
    print("✨ Successfully built Store 4 (BuzzHack Zeus) static site!")

if __name__ == "__main__":
    main()
