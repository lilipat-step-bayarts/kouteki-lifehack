#!/usr/bin/env python3
"""
Cloudflare Pages公開用の静的HTMLサイトジェネレーター（忍者AdMax実稼働タグ埋め込み版）
"""

import json
import os
import urllib.parse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_JSON = os.path.join(PROJECT_ROOT, "articles", "articles.json")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")

# ユーザー様から提供された実稼働 忍者AdMax タグ
NINJA_AD_TAG = """
<!-- admax -->
<script src="https://adm.shinobi.jp/s/b133ea03dc5417daa8dc029d6b6b4816"></script>
<!-- admax -->
"""

SITE_URL = "https://hoporin.lilipat-cosme-bayarts.com"

BASE_HTML_HEAD = """
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/jpeg" href="/assets/hoporin_icon.jpg">
  <link rel="alternate" type="application/rss+xml" title="公的ライフハック速報 RSS" href="/rss.xml">
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3133098627249534" crossorigin="anonymous"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Noto Sans JP', sans-serif; }
    .table-container { position: relative; }
  </style>
"""

HEADER_NAV = """
  <header class="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
    <div class="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
      <a href="/" class="flex items-center gap-2.5">
        <img src="/assets/hoporin_icon.jpg" alt="ほぽりん" class="w-9 h-9 rounded-full object-cover shadow-sm border border-slate-200">
        <div class="flex flex-col">
          <span class="font-extrabold text-slate-900 text-base tracking-tight leading-tight">公的ライフハック速報</span>
          <span class="text-[10px] text-slate-500 font-medium">制度とお金の知恵袋 by ほぽりん</span>
        </div>
      </a>
      <nav class="flex items-center gap-3 md:gap-4 text-xs font-semibold text-slate-600">
        <a href="/" class="hover:text-blue-600">最新記事</a>
        <a href="https://ikero.lilipat-cosme-bayarts.com" target="_blank" rel="noopener" class="hidden sm:inline-flex items-center gap-1 text-emerald-700 hover:text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">🦉 姉妹店:コスメ成分ラボ</a>
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
        <a href="/sitemap.xml" class="hover:text-white">サイトマップ</a>
        <a href="https://ikero.lilipat-cosme-bayarts.com" target="_blank" rel="noopener" class="text-emerald-400 hover:text-emerald-300">姉妹サイト：イケロのコスメ成分ラボ</a>
      </div>
      <div class="max-w-lg mx-auto text-slate-500 leading-relaxed text-[11px]">
        当サイトは編集長「ほぽりん」が各省庁・自治体等の公的発表（一次情報）を収集し、生活者視点で分かりやすく図解・要約してお届けする個人メディアです。
      </div>
      <p class="text-slate-600">© 2024-2026 公的ライフハック速報 All Rights Reserved.</p>
    </div>
  </footer>
"""

AUTHOR_CARD = """
  <div class="mt-8 p-5 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl flex items-center gap-4">
    <img src="/assets/hoporin_icon.jpg" alt="ほぽりん" class="w-16 h-16 rounded-full object-cover shadow-md border-2 border-white flex-shrink-0">
    <div class="space-y-1">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-xs font-bold text-blue-800">この記事の編集・監修</span>
        <span class="font-extrabold text-sm text-slate-900">ほぽりん</span>
        <span class="text-[10px] px-2 py-0.5 rounded-full bg-blue-200 text-blue-800 font-medium">制度ハック研究家</span>
        <a href="https://x.com/ramune_lilipat" target="_blank" rel="noopener noreferrer" class="ml-auto text-[11px] px-2.5 py-1 rounded-full bg-slate-900 text-white hover:bg-slate-700 font-bold transition">𝕏 @ramune_lilipat をフォロー</a>
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

AMAZON_TAG = "ikerocosme-22"
RAKUTEN_AF_ID = "597f29ed.f305c9f6.597f29ee.8555f86c"

def get_store1_amazon_card(art):
    cat = art.get("category", "")
    title = art.get("title", "")
    if "ふるさと納税" in title or "マイナ" in title or "スマホ" in title or "e-Tax" in title or "確定申告" in title or "税金" in cat or "NISA" in title:
        item_title = "マイナポータル・e-Tax確定申告の必須アイテム＆ふるさと納税返礼品"
        keyword = "マイナンバーカード ICカードリーダー 確定申告 本"
        desc = "スマホやPCでのe-Tax・マイナポータル申請をスムーズにする公的個人認証対応ICカードリーダーや、最新の税金・控除ハック本をAmazon・楽天でチェックできます。"
        high_ticket_badge = "💰 節税・控除枠の無料最大化"
        high_ticket_title = "【楽天ふるさと納税】年収・家族構成を入れるだけ！控除上限額3秒シミュレーター"
        high_ticket_desc = "自己負担2,000円で黒毛和牛・海鮮・日用品がもらえる「ふるさと納税」の自分の上限額を無料で診断。楽天ポイントも同時に貯まってダブルでお得です。"
        high_ticket_target = "https://event.rakuten.co.jp/furusato/guide/totalsimulation/"
        high_ticket_btn = "🎁 楽天ふるさと納税で無料控除シミュレーション＆人気返礼品を見る"
        amazon_sub_keyword = "ふるさと納税 確定申告 節税 本"
    elif "省エネ" in title or "電気" in title or "エアコン" in title or "断熱" in title or "補助金" in cat or "住宅" in title:
        item_title = "電気代・光熱費を即効カットする省エネ・断熱対策グッズ"
        keyword = "省エネ 断熱シート スマートプラグ 節電グッズ"
        desc = "補助金と併用してさらに光熱費を抑える窓用断熱シート、消費電力が見えるスマートプラグ、最新省エネ家電の売れ筋ランキングをチェック！"
        high_ticket_badge = "⚡ 固定費・光熱費の無料診断"
        high_ticket_title = "【固定費削減】省エネ家電・断熱リフォーム＆節電アイテム徹底比較ランキング"
        high_ticket_desc = "国の補助金対象にもなる最新省エネエアコン・給湯器・内窓断熱グッズの価格とポイント還元率を一括比較。毎月の電気・ガス代を根本から引き下げます。"
        high_ticket_target = "https://search.rakuten.co.jp/search/mall/%E7%9C%81%E3%82%A8%E3%83%8D%E5%AE%B6%E9%9B%BB+%E7%AF%80%E9%9B%BB/"
        high_ticket_btn = "⚡ 楽天市場で省エネ・節電ランキング＆還元率をチェックする"
        amazon_sub_keyword = "省エネ家電 節電タップ スマートリモコン"
    elif "教育" in title or "失業" in title or "雇用" in title or "年収" in title or "キャリア" in title:
        item_title = "給付金対象講座にも対応！資格取得・リスキリング実用書ランキング"
        keyword = "資格 勉強 リスキリング 補助金 税金 本"
        desc = "教育訓練給付金（最大70%〜80%還付）の対象となるIT・簿記・FP・医療事務などの人気資格テキストやキャリアアップ実用書。"
        high_ticket_badge = "🎓 給付金対象・キャリア支援"
        high_ticket_title = "【最大70%還付】教育訓練給付金で取れる人気資格・通信講座テキスト特集"
        high_ticket_desc = "ハローワークの給付金制度を使って実質負担を大幅に抑えられる国家資格・ITスキル・FP講座の定番テキスト＆問題集を今すぐチェック！"
        high_ticket_target = "https://search.rakuten.co.jp/search/mall/%E8%B3%87%E6%A0%BC+%E9%80%9A%E4%BF%A1%E8%AC%9B%E5%BA%A7+%E3%83%86%E3%82%AD%E3%82%B9%E3%83%88/"
        high_ticket_btn = "📚 給付金で狙える人気資格テキスト・講座を楽天で見る"
        amazon_sub_keyword = "FP 簿記 ITパスポート 資格 テキスト"
    else:
        item_title = "知らないと損する「お金・補助金・税金」のベストセラー実用書＆家計管理グッズ"
        keyword = "補助金 税金 届出 だけでお金がもらえる本"
        desc = "申請だけで貰える給付金・手当・減税制度を1冊で網羅できる人気の制度ハック本や、領収書・公的書類の整理に便利なドキュメントファイル。"
        high_ticket_badge = "📊 家計防衛・無料診断特集"
        high_ticket_title = "【申請漏れゼロへ】届出だけでもらえるお金・ふるさと納税・節税バイブル特集"
        high_ticket_desc = "年金・医療費・子育て・住宅など、役所や税務署が教えてくれない「申請主義」の給付金を網羅したベストセラーガイドとふるさと納税の特設会場。"
        high_ticket_target = "https://event.rakuten.co.jp/furusato/"
        high_ticket_btn = "🏆 楽天ふるさと納税 特設会場＆控除シミュレーターを見る"
        amazon_sub_keyword = "届出だけでもらえるお金 税金 補助金 本"

    query = urllib.parse.quote(keyword)
    amazon_url = f"https://www.amazon.co.jp/s?k={query}&tag={AMAZON_TAG}"
    rakuten_search_url = f"https://search.rakuten.co.jp/search/mall/{query}/"
    rakuten_pc = urllib.parse.quote(rakuten_search_url, safe="")
    rakuten_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_AF_ID}/?pc={rakuten_pc}&link_type=text"

    ht_pc = urllib.parse.quote(high_ticket_target, safe="")
    ht_rakuten_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_AF_ID}/?pc={ht_pc}&link_type=text"
    ht_amazon_url = f"https://www.amazon.co.jp/s?k={urllib.parse.quote(amazon_sub_keyword)}&tag={AMAZON_TAG}"

    return f"""
    <!-- 特大単価・高成約枠：カテゴリ連動シミュレーション＆特設診断 -->
    <div class="my-6 p-5 bg-gradient-to-br from-indigo-50 via-blue-50 to-emerald-50 border-2 border-indigo-200 rounded-2xl shadow-sm space-y-3">
      <div class="flex items-center justify-between flex-wrap gap-2">
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-indigo-600 text-white">{high_ticket_badge}</span>
        <span class="text-[10px] text-indigo-700 font-bold">PR・公式シミュレーション＆特設ガイド</span>
      </div>
      <h3 class="text-sm md:text-base font-extrabold text-slate-900 leading-snug">{high_ticket_title}</h3>
      <p class="text-xs text-slate-700 leading-relaxed">{high_ticket_desc}</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
        <a href="{ht_rakuten_url}" target="_blank" rel="noopener noreferrer sponsored" class="py-3 px-4 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white text-center rounded-xl font-bold text-xs shadow-md transition-all flex items-center justify-center gap-1.5">
          <span>{high_ticket_btn}</span>
          <span>↗</span>
        </a>
        <a href="{ht_amazon_url}" target="_blank" rel="noopener noreferrer sponsored" class="py-3 px-4 bg-slate-900 hover:bg-slate-800 text-white text-center rounded-xl font-bold text-xs shadow-sm transition-all flex items-center justify-center gap-1.5">
          <span>📘 Amazonでベストセラー解説書・30日間無料読み放題を見る</span>
          <span>↗</span>
        </a>
      </div>
    </div>

    <!-- 物販アフィリエイト枠：記事テーマ別 家計防衛アイテム -->
    <div class="my-6 p-5 bg-gradient-to-r from-amber-50/90 to-orange-50/90 border border-amber-200 rounded-2xl shadow-sm space-y-3">
      <div class="flex items-center justify-between">
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-600 text-white">🐧 ほぽりん厳選・家計防衛アイテム</span>
        <span class="text-[10px] text-amber-700 font-bold">PR・Amazon / 楽天アフィリエイト</span>
      </div>
      <h3 class="text-sm md:text-base font-extrabold text-slate-900">{item_title}</h3>
      <p class="text-xs text-slate-600 leading-relaxed">{desc}</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
        <a href="{amazon_url}" target="_blank" rel="noopener noreferrer sponsored" class="py-2.5 px-4 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white text-center rounded-xl font-bold text-xs shadow-sm transition-all flex items-center justify-center gap-1.5">
          <span>🛒 Amazonで人気の関連アイテムを見る</span>
          <span>↗</span>
        </a>
        <a href="{rakuten_url}" target="_blank" rel="noopener noreferrer sponsored" class="py-2.5 px-4 bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white text-center rounded-xl font-bold text-xs shadow-sm transition-all flex items-center justify-center gap-1.5">
          <span>🛍️ 楽天市場でポイント還元を比較する</span>
          <span>↗</span>
        </a>
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
  <link rel="canonical" href="{SITE_URL}/">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="公的ライフハック速報 by ほぽりん">
  <meta property="og:title" content="公的ライフハック速報 - 制度・給付金・生活マネーまとめ by ほぽりん">
  <meta property="og:description" content="難解な公的制度・補助金・減税手続きを、3秒でわかる結論・チェックリスト・比較表で解説する生活応援メディアです。">
  <meta property="og:url" content="{SITE_URL}/">
  <meta property="og:image" content="{SITE_URL}/assets/hoporin_banner.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@ramune_lilipat">
  <meta name="twitter:title" content="公的ライフハック速報 - 制度・給付金・生活マネーまとめ by ほぽりん">
  <meta name="twitter:description" content="難解な公的制度・補助金・減税手続きを、3秒でわかる結論・チェックリスト・比較表で解説する生活応援メディアです。">
  <meta name="twitter:image" content="{SITE_URL}/assets/hoporin_banner.jpg">
</head>
<body class="bg-slate-50 text-slate-800 antialiased min-h-screen flex flex-col justify-between">
  <div>
    {HEADER_NAV}
    
    <main class="max-w-4xl mx-auto px-4 py-6 md:py-8 space-y-6">
      
      <!-- Hero -->
      <section class="bg-gradient-to-r from-blue-700 via-indigo-700 to-blue-800 text-white rounded-3xl p-6 md:p-8 shadow-md">
        <div class="flex items-center gap-2 mb-2 flex-wrap">
          <span class="px-3 py-1 rounded-full text-xs font-semibold bg-white/20 text-white">
            公的情報・補助金速報
          </span>
          <span class="text-xs text-blue-200">編集長：ほぽりん (@ramune_lilipat)</span>
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
            注目の制度・給付金解説（全{len(articles)}記事）
          </h2>
          <span class="text-xs text-slate-400">毎日定時更新中</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          {cards_html}
        </div>
      </section>

      <!-- 姉妹店クロス送客バナー -->
      <section class="p-5 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="space-y-1">
          <span class="text-[11px] font-bold px-2 py-0.5 rounded bg-emerald-600 text-white">姉妹メディアのご案内</span>
          <h3 class="text-sm md:text-base font-bold text-slate-900">🦉 イケロのコスメ成分ラボ・プチプラ速報</h3>
          <p class="text-xs text-slate-600">1万円のデパコスと同じ有効成分が入った1,000円台の神プチプラを科学的根拠で徹底比較！</p>
        </div>
        <a href="https://ikero.lilipat-cosme-bayarts.com" target="_blank" rel="noopener" class="shrink-0 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl shadow-sm transition">
          コスメ成分ラボを見る →
        </a>
      </section>

      {live_ad_box("トップ下部")}

    </main>
  </div>
  {FOOTER}
</body>
</html>
"""

def build_article_page(art, all_articles=None):
    import urllib.parse
    all_articles = all_articles or []
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
    faq_entities = []
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
        faq_entities.append({
            "@type": "Question",
            "name": f['q'],
            "acceptedAnswer": {"@type": "Answer", "text": f['a']}
        })

    # 関連人気記事（自記事以外から最大4件）
    related = [a for a in all_articles if a['id'] != art['id']][:4]
    related_html = ""
    for r_art in related:
        related_html += f"""
        <a href="/articles/{r_art['id']}.html" class="block p-4 bg-slate-50 hover:bg-blue-50/60 border border-slate-200 hover:border-blue-300 rounded-2xl transition group">
          <div class="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span class="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-bold">{r_art['category']}</span>
            <span>{r_art['date']}</span>
          </div>
          <div class="text-xs md:text-sm font-bold text-slate-900 group-hover:text-blue-600 leading-snug">{r_art['title']}</div>
        </a>
        """
    next_art = related[0] if related else art
    article_url = f"{SITE_URL}/articles/{art['id']}.html"
    encoded_title = urllib.parse.quote(f"【保存版】{art['title']} #公的ライフハック #給付金 #ほぽりん")
    encoded_url = urllib.parse.quote(article_url)

    json_ld = json.dumps([
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": art['title'],
            "description": art['summary'],
            "image": [f"{SITE_URL}/assets/hoporin_banner.jpg"],
            "datePublished": art['date'],
            "dateModified": art['date'],
            "author": [{"@type": "Person", "name": "ほぽりん", "url": f"{SITE_URL}/about.html"}]
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_entities
        }
    ], ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  {BASE_HTML_HEAD}
  <title>{art['title']} - 公的ライフハック速報 by ほぽりん</title>
  <meta name="description" content="{art['summary']}">
  <link rel="canonical" href="{article_url}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="公的ライフハック速報 by ほぽりん">
  <meta property="og:title" content="{art['title']}">
  <meta property="og:description" content="{art['summary']}">
  <meta property="og:url" content="{article_url}">
  <meta property="og:image" content="{SITE_URL}/assets/hoporin_banner.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@ramune_lilipat">
  <meta name="twitter:title" content="{art['title']}">
  <meta name="twitter:description" content="{art['summary']}">
  <meta name="twitter:image" content="{SITE_URL}/assets/hoporin_banner.jpg">
  <script type="application/ld+json">{json_ld}</script>
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

        <!-- ほぽりんの生活者リアルアドバイス -->
        <div class="p-5 bg-amber-50/80 border-2 border-amber-200/90 rounded-2xl space-y-2 shadow-sm">
          <div class="flex items-center gap-2">
            <span class="w-7 h-7 rounded-full bg-amber-500 text-white flex items-center justify-center font-bold text-xs shadow">ほ</span>
            <span class="font-extrabold text-sm text-amber-900">ほぽりんの生活者リアルアドバイス（編集後記）</span>
          </div>
          <p class="text-xs md:text-sm text-amber-950/90 leading-relaxed pl-1 font-medium">
            {art.get('hoporin_tip', '申請窓口は混雑することが多いので、オンライン手続きが可能なものはスマホから済ませるのが一番おすすめです！')}
          </p>
        </div>

        <!-- Amazonアソシエイト連動（ikerocosme-22）：記事テーマ別 節税・家計防衛おすすめアイテム枠 -->
        {get_store1_amazon_card(art)}

        <!-- SNSシェア＆フォロー促しボタン -->
        <div class="flex flex-wrap items-center justify-between gap-3 p-4 bg-slate-900 text-white rounded-2xl">
          <div class="text-xs">
            <div class="font-bold">📢 家族や友人にもこの制度をシェアしませんか？</div>
            <div class="text-slate-300 text-[11px]">申請漏れを防ぐため、Xでのブックマーク・共有がおすすめです🐧</div>
          </div>
          <div class="flex items-center gap-2">
            <a href="https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_url}" target="_blank" rel="noopener noreferrer" class="px-3.5 py-2 bg-blue-500 hover:bg-blue-400 text-white rounded-xl text-xs font-bold transition">
              𝕏 ポストして保存
            </a>
            <a href="https://x.com/ramune_lilipat" target="_blank" rel="noopener noreferrer" class="px-3.5 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-bold transition">
              フォローする
            </a>
          </div>
        </div>

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

        <!-- 🔥 サイト内回遊（PV倍増用・関連記事レコメンド） -->
        <section class="pt-4 border-t border-slate-200 space-y-3">
          <h3 class="text-sm md:text-base font-extrabold text-slate-900 flex items-center gap-1.5">
            <span>🔥</span> あわせて読みたい！今もっとも多く読まれている制度ハック
          </h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {related_html}
          </div>
        </section>

        <!-- 🦉 姉妹サイト相互送客カード -->
        <div class="p-4 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-3">
          <div class="text-xs space-y-1">
            <span class="px-2 py-0.5 rounded bg-emerald-600 text-white font-bold text-[10px]">姉妹メディア人気記事</span>
            <div class="font-bold text-slate-900 text-sm">🦉 デパコス級なのに1,000円台！イケロのコスメ成分ラボ</div>
            <div class="text-slate-600">レチノール・ナイアシンアミド・セラミドなど科学的根拠で日用品・美容費を賢く節約！</div>
          </div>
          <a href="https://ikero.lilipat-cosme-bayarts.com" target="_blank" rel="noopener" class="shrink-0 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition">
            成分比較を見る →
          </a>
        </div>

      </div>

    </main>
  </div>
  <!-- スマホ下部固定「次の注目記事」回遊バー -->
  <div class="fixed bottom-0 inset-x-0 z-40 bg-white/95 backdrop-blur border-t border-slate-200 px-4 py-2.5 shadow-lg flex items-center justify-between gap-2 md:hidden">
    <div class="truncate text-xs">
      <span class="text-[10px] font-bold text-blue-600 block">NEXT › 次に読まれている記事</span>
      <a href="/articles/{next_art['id']}.html" class="font-bold text-slate-900 truncate block">{next_art['title']}</a>
    </div>
    <a href="/articles/{next_art['id']}.html" class="shrink-0 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-bold">読む →</a>
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
            当サイトでは、第三者配信の広告サービス（Google AdSense、忍者AdMax、各種アフィリエイトプログラム等）を利用しています。広告配信事業者は、利用者の興味に応じた広告を表示するためにCookie（クッキー）を使用することがあります。
          </p>
          <p>
            Amazonのアソシエイトとして、公的ライフハック速報は適格販売により収入を得ています。また、楽天アフィリエイト等のアフィリエイトプログラムに参加しています。
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

def build_seo_files(articles):
    # sitemap.xml
    urls = [f"  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>"]
    for art in articles:
        urls.append(f"  <url><loc>{SITE_URL}/articles/{art['id']}.html</loc><lastmod>{art['date']}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>")
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    with open(os.path.join(DIST_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    # robots.txt
    robots_txt = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    with open(os.path.join(DIST_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots_txt)

    # rss.xml
    items = []
    for art in articles[:15]:
        items.append(f"    <item><title>{art['title']}</title><link>{SITE_URL}/articles/{art['id']}.html</link><description>{art['summary']}</description><pubDate>{art['date']}</pubDate></item>")
    rss_xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>公的ライフハック速報 by ほぽりん</title><link>{SITE_URL}/</link><description>知らないと損する公的制度・給付金・減税まとめ</description>\n' + "\n".join(items) + "\n</channel></rss>\n"
    with open(os.path.join(DIST_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

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
            f.write(build_article_page(art, articles))

    # 3. about & privacy & SEO files (sitemap.xml, robots.txt, rss.xml)
    about_html, privacy_html = build_static_pages()
    with open(os.path.join(DIST_DIR, "about.html"), "w", encoding="utf-8") as f:
        f.write(about_html)
    with open(os.path.join(DIST_DIR, "privacy.html"), "w", encoding="utf-8") as f:
        f.write(privacy_html)
    build_seo_files(articles)

    print("Site generated with real Ninja AdMax tags, OGP cards, and SEO sitemaps at:", DIST_DIR)

    import sys
    build_only = "--build-only" in sys.argv

    # 2号店（コスメ成分ラボ・イケロ）の記事生成＆サイトビルド
    try:
        import subprocess
        store2_dir = os.path.join(PROJECT_ROOT, "store2")
        store2_gen = os.path.join(store2_dir, "scripts", "generate_articles.py")
        store2_build = os.path.join(store2_dir, "scripts", "build_site.py")
        if os.path.exists(store2_gen):
            print("Running Store 2 (Ikero Cosme Lab) article generator...")
            subprocess.run(["python3", store2_gen], check=False)
        if os.path.exists(store2_build):
            print("Triggering Store 2 (Ikero Cosme Lab) site build...")
            subprocess.run(["python3", store2_build], check=False)
    except Exception as e:
        print("Note: Store 2 build skipped or failed:", e)

    if build_only:
        return

    # サイトビルド完了時に自動でXへ新着記事を速報ツイート (1号店: @ramune_lilipat)
    try:
        distribute_script = os.path.join(SCRIPT_DIR, "distribute_tweet.py")
        if os.path.exists(distribute_script):
            import subprocess
            print("Triggering automated X tweet distribution for Store 1 (@ramune_lilipat)...")
            subprocess.run(["python3", distribute_script], check=False)
    except Exception as e:
        print("Note: Store 1 automated tweet skipped or failed:", e)

    # 2号店のデプロイ＆自動ツイート (2号店: @ikero_lab)
    try:
        import subprocess
        store2_dir = os.path.join(PROJECT_ROOT, "store2")
        store2_tweet = os.path.join(store2_dir, "scripts", "distribute_tweet.py")
        if os.environ.get("CLOUDFLARE_API_TOKEN"):
            print("Deploying Store 2 to Cloudflare Pages (cosme-lab-ikero)...")
            subprocess.run([
                "npx", "wrangler", "pages", "deploy",
                os.path.join(store2_dir, "dist"),
                "--project-name=cosme-lab-ikero",
                "--commit-dirty=true"
            ], check=False)

        if os.path.exists(store2_tweet):
            print("Triggering Store 2 automated X tweet distribution (@ikero_lab)...")
            subprocess.run(["python3", store2_tweet], check=False)
    except Exception as e:
        print("Note: Store 2 automated pipeline skipped or failed:", e)

if __name__ == "__main__":
    main()
