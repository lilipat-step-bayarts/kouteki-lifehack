#!/usr/bin/env python3
"""
オニゴンの夜更かしラボ (3号店) 静的Webサイトビルダースクリプト
・18歳以上年齢確認モーダル（DMM / FANZAアフィリエイト審査必須要件）完備
・新人紹介＆サムネイル図鑑ページ (/newcomers.html) 搭載
  - 審査通過前：著作権100%クリアな「オニゴン特製ビジュアルサムネイル＆ステータス図解カード」を表示
  - 審査通過後：newcomers.json に package_image_url / DMM API を設定するだけで公式パッケージサムネイル画像に自動切替
・忍者AdMax（ビュー報酬）＋ DMM / FANZA アフィリエイト導線の二刀流構造
"""

import os
import json
import re
import urllib.parse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
ARTICLES_JSON = os.path.join(ARTICLES_DIR, "articles.json")
NEWCOMERS_JSON = os.path.join(ARTICLES_DIR, "newcomers.json")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
DIST_ARTICLES_DIR = os.path.join(DIST_DIR, "articles")
DIST_ASSETS_DIR = os.path.join(DIST_DIR, "assets")

SITE_TITLE = "オニゴンの夜更かしラボ | 深夜のFANZAセール・大型新人・同人ASMR厳選速報"
SITE_DESCRIPTION = "深夜の案内人『オニゴン』が、FANZAの500円セール・大型新人デビュー作・KU100収録の同人ASMR・DMMプレミアムのコスパを徹底解剖する深夜エンタメ特化型レビューメディア。"
SITE_URL = "https://onigon-night-lab.pages.dev"

DMM_AFFILIATE_ID = os.environ.get("DMM_AFFILIATE_ID", "").strip()

NINJA_AD_SCRIPT = """
<!-- 忍者AdMax ビュー報酬ユニット -->
<div class="my-6 p-3 bg-slate-900/90 rounded-2xl border border-purple-500/30 flex flex-col items-center justify-center min-h-[120px] text-center shadow-inner">
  <span class="text-[10px] text-purple-300/70 font-medium mb-1 tracking-wider uppercase">Sponsored Link</span>
  <script src="https://adm.shinobi.jp/s/b133ea03dc5417daa8dc029d6b6b4816"></script>
</div>
"""

AGE_GATE_MODAL = """
<!-- 18歳以上年齢確認モーダル (DMM/FANZA審査対応) -->
<div id="onigon-age-gate" class="fixed inset-0 z-[100] hidden items-center justify-center bg-slate-950/95 backdrop-blur-md p-4">
  <div class="max-w-md w-full bg-slate-900 border-2 border-purple-500/60 rounded-3xl p-6 md:p-8 text-center shadow-2xl shadow-purple-950/80 space-y-5">
    <div class="relative mx-auto w-20 h-20">
      <img src="/assets/onigon_avatar.jpg" alt="オニゴン" class="w-20 h-20 rounded-full object-cover border-2 border-fuchsia-400 shadow-lg">
      <span class="absolute -bottom-1 -right-1 px-2 py-0.5 rounded-full text-[10px] font-black bg-rose-600 text-white border border-white">18+</span>
    </div>
    <div class="space-y-2">
      <span class="px-3 py-1 rounded-full text-xs font-bold bg-purple-950 text-purple-300 border border-purple-700/60">
        年齢確認 / Age Verification
      </span>
      <h2 class="text-xl font-black text-white leading-snug">
        ここから先は成人向け（18歳以上対象）のレビュー情報を含みます
      </h2>
      <p class="text-xs text-slate-300 leading-relaxed">
        当サイト「オニゴンの夜更かしラボ」は、成人向けエンタメ作品（FANZA / DMM / 同人ASMR等）のセール情報・レビューを掲載しています。18歳未満の方の閲覧は固くお断りいたします。
      </p>
    </div>
    <div class="space-y-2.5 pt-2">
      <button onclick="confirmAgeGate()" class="w-full py-3 px-5 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 text-white font-black text-sm shadow-lg shadow-fuchsia-600/30 transition cursor-pointer">
        はい、私は18歳以上です（ENTER）
      </button>
      <a href="https://www.google.co.jp/" rel="nofollow" class="block w-full py-2.5 px-5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 font-bold text-xs transition">
        いいえ、18歳未満です（EXIT）
      </a>
    </div>
  </div>
</div>
<script>
  (function() {
    try {
      if (localStorage.getItem('onigon_age_verified_v1') !== 'true') {
        var modal = document.getElementById('onigon-age-gate');
        if (modal) {
          modal.classList.remove('hidden');
          modal.classList.add('flex');
        }
      }
    } catch (e) {}
  })();
  function confirmAgeGate() {
    try {
      localStorage.setItem('onigon_age_verified_v1', 'true');
    } catch (e) {}
    var modal = document.getElementById('onigon-age-gate');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  }
</script>
"""


def build_fanza_link(raw_url):
    """DMM_AFFILIATE_ID が設定されていれば公式アフィリエイトリンクに変換、未設定なら公式ページへ直リンク"""
    if DMM_AFFILIATE_ID:
        encoded = urllib.parse.quote(raw_url, safe="")
        return f"https://al.dmm.co.jp/?lurl={encoded}&af_id={DMM_AFFILIATE_ID}&ch=link_tool&ch_id=link"
    return raw_url


def get_header(current_page="home"):
    return f"""
  <header class="sticky top-0 z-50 bg-slate-950/90 backdrop-blur-md border-b border-purple-500/30 shadow-lg">
    <div class="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
      <a href="/" class="flex items-center gap-2.5 group">
        <img src="/assets/onigon_avatar.jpg" alt="オニゴン" class="w-10 h-10 rounded-full border-2 border-fuchsia-400 shadow-md object-cover group-hover:scale-105 transition-transform">
        <div>
          <div class="flex items-center gap-1.5">
            <span class="text-[10px] font-bold text-fuchsia-400 tracking-wider">MIDNIGHT CURATION LAB</span>
            <span class="text-[9px] px-1.5 py-0.2 rounded bg-rose-600/90 text-white font-black">R18</span>
          </div>
          <span class="text-base font-black text-white tracking-tight block">オニゴンの夜更かしラボ</span>
        </div>
      </a>
      <nav class="flex items-center gap-3 md:gap-5 text-xs font-bold text-slate-300">
        <a href="/" class="hover:text-fuchsia-400 transition {'text-fuchsia-400' if current_page == 'home' else ''}">新着速報</a>
        <a href="/newcomers.html" class="px-2.5 py-1 rounded-full border {'bg-fuchsia-600 text-white border-fuchsia-400' if current_page == 'newcomers' else 'bg-purple-950/80 text-fuchsia-300 border-fuchsia-500/40 hover:bg-purple-900'} transition flex items-center gap-1">
          <span>🌟</span><span>新人図鑑・サムネ</span>
        </a>
        <a href="/about.html" class="hidden sm:inline hover:text-fuchsia-400 transition {'text-fuchsia-400' if current_page == 'about' else ''}">オニゴンとは？</a>
        <a href="/privacy.html" class="hidden sm:inline hover:text-fuchsia-400 transition {'text-fuchsia-400' if current_page == 'privacy' else ''}">免責・規約</a>
      </nav>
    </div>
  </header>
"""


def get_footer():
    return """
  <footer class="bg-slate-950 text-slate-400 py-12 mt-16 border-t border-purple-900/50">
    <div class="max-w-5xl mx-auto px-4 text-center space-y-4">
      <div class="flex items-center justify-center gap-2.5">
        <img src="/assets/onigon_avatar.jpg" alt="オニゴン" class="w-8 h-8 rounded-full border border-fuchsia-400 object-cover">
        <span class="font-bold text-white text-sm">オニゴンの夜更かしラボ（Onigon Night Lab）</span>
      </div>
      <p class="text-xs text-slate-400 max-w-lg mx-auto leading-relaxed">
        当サイトは18歳以上を対象とした深夜エンタメ・FANZAセール・大型新人レビュー・同人ASMR音声のキュレーションメディアです。著作権および各配信プラットフォームの規約を遵守して運営しています。
      </p>
      <div class="text-[11px] text-slate-400 flex flex-wrap justify-center gap-4 pt-2">
        <a href="/" class="hover:text-fuchsia-400">トップページ</a>
        <span>•</span>
        <a href="/newcomers.html" class="hover:text-fuchsia-400 font-bold text-fuchsia-300">🌟 新人女優・注目ルーキー図鑑</a>
        <span>•</span>
        <a href="/about.html" class="hover:text-fuchsia-400">運営者情報（オニゴン）</a>
        <span>•</span>
        <a href="/privacy.html" class="hover:text-fuchsia-400">プライバシーポリシー・広告開示</a>
        <span>•</span>
        <a href="/sitemap.xml" class="hover:text-fuchsia-400">サイトマップ</a>
      </div>
      <div class="text-[11px] text-slate-600 font-mono">
        © 2026 Onigon Night Lab. All Rights Reserved. (18+ Adult Only)
      </div>
    </div>
  </footer>
"""


def render_newcomer_card(item):
    """
    新人紹介サムネイルカードを描画
    ・package_image_url が設定されている場合（DMM審査通過後）：公式パッケージサムネイル画像を表示
    ・package_image_url が空の場合（DMM審査中・審査前）：著作権クリアなオリジナル・シルエット＆スペックサムネイルを描画
    """
    pkg_url = item.get("package_image_url", "").strip()
    stage_name = item.get("stage_name", "注目ルーキー")
    catchcopy = item.get("catchcopy", "")
    debut_month = item.get("debut_month", "2026年最新")
    label_genre = item.get("label_genre", "専属レーベル")
    rank = item.get("rank", "S+")
    rating = item.get("rating", 4.9)
    gradient = item.get("theme_gradient", "from-fuchsia-600 via-purple-700 to-indigo-900")
    badge_text = item.get("badge_text", "注目ルーキー")
    tags = item.get("tags", [])
    stats = item.get("stats", {"visual": 96, "style": 95, "immersive": 95})
    comment = item.get("onigon_comment", "")
    search_kw = urllib.parse.quote(item.get("search_keyword", stage_name))

    if item.get("affiliate_url"):
        target_url = item["affiliate_url"]
    elif item.get("fanza_category") == "doujin":
        raw_url = f"https://www.dmm.co.jp/dc/doujin/-/list/narrow/=/word={search_kw}/"
        target_url = build_fanza_link(raw_url)
    else:
        raw_url = f"https://www.dmm.co.jp/digital/videoa/-/list/search/=/?searchstr={search_kw}"
        target_url = build_fanza_link(raw_url)

    # サムネイルヘッダー部分（公式画像 or 審査クリア用オリジナルアートサムネイル）
    if pkg_url:
        thumb_html = f"""
        <div class="relative h-56 w-full overflow-hidden bg-slate-950">
          <img src="{pkg_url}" alt="{stage_name}" loading="lazy" class="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-500">
          <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/30 to-transparent"></div>
          <div class="absolute top-3 left-3 flex items-center gap-1.5">
            <span class="px-2.5 py-1 rounded-full text-[11px] font-black bg-fuchsia-600 text-white shadow-lg">{badge_text}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-black bg-amber-400 text-slate-950">RANK {rank}</span>
          </div>
          <div class="absolute bottom-3 left-3 right-3 flex items-end justify-between">
            <div>
              <span class="text-[11px] text-fuchsia-300 font-bold block">{debut_month} / {label_genre}</span>
              <h3 class="text-lg font-black text-white drop-shadow">{stage_name}</h3>
            </div>
            <span class="px-2 py-1 rounded-lg bg-slate-900/90 border border-amber-400/50 text-amber-300 text-xs font-mono font-bold">★ {rating}</span>
          </div>
        </div>
        """
    else:
        # 審査前でも華やかで著作権100%クリアなビジュアルサムネイルカード
        thumb_html = f"""
        <div class="relative h-52 w-full overflow-hidden bg-gradient-to-br {gradient} p-4 flex flex-col justify-between">
          <!-- 背景装飾シルエット＆ネオンエフェクト -->
          <div class="absolute -right-6 -bottom-6 w-40 h-40 rounded-full bg-white/10 blur-2xl pointer-events-none"></div>
          <svg class="absolute right-3 bottom-0 w-32 h-44 text-white/15 pointer-events-none" viewBox="0 0 200 260" fill="currentColor">
            <circle cx="100" cy="70" r="42"/>
            <path d="M30 250 C30 165, 170 165, 170 250 Z"/>
          </svg>
          <div class="relative z-10 flex items-center justify-between">
            <div class="flex items-center gap-1.5">
              <span class="px-2.5 py-1 rounded-full text-[11px] font-black bg-white/20 backdrop-blur-md text-white border border-white/30 shadow">{badge_text}</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-black bg-amber-400 text-slate-950 shadow">RANK {rank}</span>
            </div>
            <span class="px-2 py-0.5 rounded-md bg-slate-950/60 backdrop-blur text-[10px] text-fuchsia-200 border border-fuchsia-400/30 font-mono">
              📸 公式サムネ枠（審査通過後に自動解禁）
            </span>
          </div>
          <div class="relative z-10 space-y-1">
            <div class="text-[11px] font-bold text-fuchsia-200 flex items-center gap-1.5">
              <span>🗓️ {debut_month}</span>
              <span>•</span>
              <span>{label_genre}</span>
            </div>
            <h3 class="text-lg md:text-xl font-black text-white leading-tight drop-shadow">{stage_name}</h3>
            <div class="flex items-center gap-2 pt-0.5">
              <span class="text-xs font-mono font-bold text-amber-300">★ {rating} / 5.0</span>
              <span class="text-[11px] text-white/80">｜ オニゴン期待度 99%</span>
            </div>
          </div>
        </div>
        """

    tags_html = " ".join([
        f'<span class="text-[11px] px-2 py-0.5 rounded-md bg-purple-950/90 text-purple-200 border border-purple-700/50 font-medium">#{t}</span>'
        for t in tags
    ])

    return f"""
    <div class="group bg-slate-900/95 rounded-3xl border border-purple-500/30 hover:border-fuchsia-400/70 overflow-hidden shadow-xl transition-all flex flex-col justify-between">
      <div>
        {thumb_html}
        <div class="p-5 space-y-4">
          <p class="text-xs md:text-sm font-bold text-fuchsia-200 leading-snug">
            「{catchcopy}」
          </p>
          <div class="flex flex-wrap gap-1.5">
            {tags_html}
          </div>
          <!-- ステータスバー -->
          <div class="bg-slate-950/80 rounded-2xl p-3.5 border border-slate-800 space-y-2 text-[11px]">
            <div class="flex items-center justify-between">
              <span class="text-slate-400 font-medium">✨ ビジュアル・透明感</span>
              <div class="w-36 bg-slate-800 h-2 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-fuchsia-500 to-pink-400 h-full rounded-full" style="width: {stats.get('visual', 95)}%"></div>
              </div>
              <span class="font-mono font-bold text-fuchsia-300">{stats.get('visual', 95)}pt</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400 font-medium">💎 スタイル・表現力</span>
              <div class="w-36 bg-slate-800 h-2 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-purple-500 to-indigo-400 h-full rounded-full" style="width: {stats.get('style', 95)}%"></div>
              </div>
              <span class="font-mono font-bold text-purple-300">{stats.get('style', 95)}pt</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400 font-medium">🎧 没入感・リピート度</span>
              <div class="w-36 bg-slate-800 h-2 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-amber-500 to-rose-400 h-full rounded-full" style="width: {stats.get('immersive', 95)}%"></div>
              </div>
              <span class="font-mono font-bold text-amber-300">{stats.get('immersive', 95)}pt</span>
            </div>
          </div>
          <!-- オニゴン寸評 -->
          <div class="flex items-start gap-2.5 text-xs text-slate-300 bg-purple-950/30 p-3 rounded-xl border border-purple-800/40">
            <img src="/assets/onigon_avatar.jpg" alt="オニゴン" class="w-8 h-8 rounded-full object-cover border border-fuchsia-400 shrink-0 mt-0.5">
            <p class="leading-relaxed">{comment}</p>
          </div>
        </div>
      </div>
      <div class="px-5 pb-5 pt-1">
        <a href="{target_url}" target="_blank" rel="noopener noreferrer sponsored" class="w-full py-3 px-4 bg-gradient-to-r from-fuchsia-600 via-purple-600 to-pink-600 hover:from-fuchsia-500 hover:to-pink-500 text-white text-center rounded-xl font-black text-xs shadow-lg shadow-fuchsia-950/60 transition flex items-center justify-center gap-2">
          <span>🎬 FANZA公式で高画質サンプル＆詳細を見る</span>
          <span>↗</span>
        </a>
      </div>
    </div>
    """


def get_fanza_cta_card(slug, title):
    if "asmr" in slug or "doujin" in slug or "binaural" in slug:
        raw_url = "https://www.dmm.co.jp/dc/doujin/"
        btn_label = "🎧 FANZA同人で人気ASMR・コミックの無料試聴＆セールを見る"
        badge = "同人・ASMR公式ピックアップ"
        desc = "KU100バイノーラル録音ボイスの無料体験版（10〜30分）や、初回購入クーポン・10円〜半額セール対象作品を公式ページで今すぐチェックできます。"
    elif "newcomer" in slug:
        raw_url = "https://www.dmm.co.jp/digital/videoa/-/list/=/article=keyword/id=6565/"
        btn_label = "🌟 FANZAで最新の新人デビュー作品＆高画質サンプル動画を見る"
        badge = "大型新人デビュー特集"
        desc = "今月デビューの大型専属ルーキーの無料サンプル動画（4K/HD）や初回限定特典付きラインナップを公式ページで確認できます。"
    elif "tv" in slug or "premium" in slug:
        raw_url = "https://premium.dmm.com/"
        btn_label = "💎 月額550円のDMMプレミアム（FANZA TV見放題）公式詳細を見る"
        badge = "コスパ最強サブスク"
        desc = "月額550円（税込）で対象2,000作品以上が見放題！単品1本分以下の価格で楽しめる公式キャンペーンページはこちら。"
    else:
        raw_url = "https://www.dmm.co.jp/digital/videoa/"
        btn_label = "🔥 FANZA動画の最新500円セール＆最大70%OFF対象作を見る"
        badge = "オニゴン厳選・公式セール導線"
        desc = "期間限定の500円均一セールや週末割引クーポン対象の名作ラインナップを公式ページでチェック！"

    fanza_url = build_fanza_link(raw_url)

    return f"""
    <div class="my-8 p-5 md:p-6 bg-gradient-to-br from-purple-950/90 via-slate-900 to-fuchsia-950/80 rounded-3xl border border-fuchsia-500/50 shadow-xl space-y-4">
      <div class="flex items-center justify-between flex-wrap gap-2">
        <span class="px-3 py-1 rounded-full text-xs font-black bg-fuchsia-600 text-white">👿 {badge}</span>
        <span class="text-xs font-mono text-fuchsia-300">公式配信・高画質サンプル対応</span>
      </div>
      <h4 class="text-base md:text-lg font-black text-white leading-snug">{title}</h4>
      <p class="text-xs text-slate-300 leading-relaxed">{desc}</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
        <a href="{fanza_url}" target="_blank" rel="noopener noreferrer sponsored" class="py-3 px-4 bg-gradient-to-r from-rose-600 to-fuchsia-600 hover:from-rose-500 hover:to-fuchsia-500 text-white text-center rounded-xl font-black text-xs shadow-lg transition flex items-center justify-center gap-1.5">
          <span>{btn_label}</span>
          <span>↗</span>
        </a>
        <a href="/newcomers.html" class="py-3 px-4 bg-slate-800 hover:bg-slate-700 border border-purple-500/40 text-fuchsia-300 text-center rounded-xl font-bold text-xs transition flex items-center justify-center gap-1.5">
          <span>🌟 当サイトの新人女優・ルーキー図鑑を見る</span>
          <span>→</span>
        </a>
      </div>
    </div>
    """


def render_table(rows):
    if len(rows) < 2:
        return ""
    header_cols = [c.strip() for c in rows[0].split("|")[1:-1]]
    data_rows = rows[2:]

    th_html = "".join([
        f'<th class="py-3 px-3.5 text-left font-bold text-fuchsia-200 border-b border-purple-700/60">{col}</th>'
        for col in header_cols
    ])
    tr_html = []
    for r in data_rows:
        cols = [c.strip() for c in r.split("|")[1:-1]]
        td_items = []
        for col in cols:
            formatted_col = re.sub(r'\*\*(.+?)\*\*', r'<strong class="text-fuchsia-300 font-bold">\1</strong>', col)
            td_items.append(f'<td class="py-2.5 px-3.5 text-slate-300 border-b border-slate-800 text-xs md:text-sm">{formatted_col}</td>')
        tr_html.append(f'<tr class="hover:bg-purple-950/30 transition">{"".join(td_items)}</tr>')

    return f"""
    <div class="my-6 overflow-x-auto rounded-2xl border border-purple-700/50 shadow-lg">
      <table class="w-full text-left text-xs md:text-sm bg-slate-900/90">
        <thead class="bg-purple-950/80">{th_html}</thead>
        <tbody class="divide-y divide-slate-800">{''.join(tr_html)}</tbody>
      </table>
    </div>
    """


def markdown_to_html(md_text):
    lines = md_text.strip().split("\n")
    html_parts = []
    in_table = False
    table_rows = []

    for line in lines:
        if line.startswith("# "):
            continue
        elif line.startswith("## "):
            heading = line[3:].strip()
            html_parts.append(
                f'<h2 class="text-lg md:text-xl font-black text-white mt-8 mb-3 pb-2 border-b-2 border-fuchsia-500/70 flex items-center gap-2">'
                f'<span class="text-fuchsia-400">👿</span><span>{heading}</span></h2>'
            )
        elif line.startswith("### "):
            heading = line[4:].strip()
            html_parts.append(
                f'<h3 class="text-base font-bold text-fuchsia-200 mt-6 mb-2 flex items-center gap-2">'
                f'<span class="w-2 h-2 rounded-full bg-fuchsia-400 inline-block"></span><span>{heading}</span></h3>'
            )
        elif line.startswith("- "):
            item = line[2:].strip()
            item = re.sub(r'\*\*(.+?)\*\*', r'<strong class="text-white font-bold">\1</strong>', item)
            item = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" class="text-fuchsia-400 underline hover:text-fuchsia-300">\1</a>', item)
            html_parts.append(f'<li class="text-xs md:text-sm text-slate-300 leading-relaxed mb-1.5 ml-4 list-disc">{item}</li>')
        elif re.match(r'^\d+\.\s', line):
            item = re.sub(r'^\d+\.\s', '', line).strip()
            item = re.sub(r'\*\*(.+?)\*\*', r'<strong class="text-white font-bold">\1</strong>', item)
            item = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" class="text-fuchsia-400 underline hover:text-fuchsia-300">\1</a>', item)
            html_parts.append(f'<li class="text-xs md:text-sm text-slate-300 leading-relaxed mb-2 ml-4 list-decimal">{item}</li>')
        elif line.startswith("|"):
            in_table = True
            table_rows.append(line)
        else:
            if in_table:
                html_parts.append(render_table(table_rows))
                in_table = False
                table_rows = []

            if line.strip() == "---":
                html_parts.append('<hr class="my-6 border-purple-900/50">')
            elif line.strip():
                p = line.strip()
                p = re.sub(r'\*\*(.+?)\*\*', r'<strong class="text-fuchsia-300 font-bold">\1</strong>', p)
                p = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" class="text-fuchsia-400 underline hover:text-fuchsia-300 font-bold">\1</a>', p)
                html_parts.append(f'<p class="text-xs md:text-sm text-slate-300 leading-relaxed mb-4">{p}</p>')

    if in_table:
        html_parts.append(render_table(table_rows))

    return "\n".join(html_parts)


def build_article_page(article_meta, all_articles):
    slug = article_meta["slug"]
    md_path = os.path.join(ARTICLES_DIR, f"{slug}.md")
    if not os.path.exists(md_path):
        return

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    body_html = markdown_to_html(md_text)
    cta_card = get_fanza_cta_card(slug, article_meta["title"])

    related = [a for a in all_articles if a.get("slug") != slug][:4]
    related_html = ""
    for r_art in related:
        related_html += f"""
        <a href="/articles/{r_art['slug']}.html" class="block p-4 bg-slate-900 hover:bg-purple-950/60 border border-purple-800/40 hover:border-fuchsia-500/60 rounded-2xl transition group">
          <div class="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span class="px-2 py-0.5 rounded bg-purple-950 text-fuchsia-300 font-bold border border-purple-700/50">{r_art.get('category', '深夜レビュー')}</span>
            <span>{r_art['date']}</span>
          </div>
          <div class="text-xs md:text-sm font-bold text-white group-hover:text-fuchsia-300 leading-snug">{r_art['title']}</div>
        </a>
        """

    article_url = f"{SITE_URL}/articles/{slug}.html"
    encoded_title = urllib.parse.quote(f"{article_meta['title']} #オニゴンの夜更かしラボ #FANZA #深夜の癒やし")
    encoded_share_url = urllib.parse.quote(article_url)

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{article_meta['title']} | オニゴンの夜更かしラボ</title>
  <meta name="description" content="{article_meta['summary']}">
  <link rel="canonical" href="{article_url}">
  <link rel="icon" type="image/jpeg" href="/assets/onigon_avatar.jpg">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="オニゴンの夜更かしラボ">
  <meta property="og:title" content="{article_meta['title']}">
  <meta property="og:description" content="{article_meta['summary']}">
  <meta property="og:url" content="{article_url}">
  <meta property="og:image" content="{SITE_URL}/assets/onigon_avatar.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased font-sans min-h-screen">
  {AGE_GATE_MODAL}
  {get_header("article")}

  <main class="max-w-3xl mx-auto px-4 py-8">
    <article class="bg-slate-900/90 rounded-3xl p-6 md:p-10 border border-purple-500/30 shadow-2xl space-y-6">
      <div class="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
        <span class="px-3 py-1 rounded-full bg-purple-950 text-fuchsia-300 border border-fuchsia-500/40 font-bold">
          {article_meta.get('icon', '👿')} {article_meta.get('category', '深夜速報')}
        </span>
        <time datetime="{article_meta['date']}">{article_meta['date']}</time>
      </div>

      <h1 class="text-xl md:text-2xl font-black text-white leading-snug">
        {article_meta['title']}
      </h1>

      <!-- オニゴン要約ボックス -->
      <div class="p-4 bg-gradient-to-r from-purple-950/90 to-slate-900 rounded-2xl border border-fuchsia-500/40 flex items-start gap-3.5">
        <img src="/assets/onigon_avatar.jpg" alt="オニゴン" class="w-12 h-12 rounded-full border-2 border-fuchsia-400 shrink-0 object-cover shadow-md">
        <div class="text-xs space-y-1">
          <div class="font-bold text-fuchsia-300 flex items-center gap-1.5 flex-wrap">
            <span>深夜の案内人 オニゴンの3秒結論</span>
            <span class="text-[10px] px-1.5 py-0.5 bg-fuchsia-600/30 text-fuchsia-200 rounded border border-fuchsia-400/30">忖度なしレビュー</span>
          </div>
          <p class="text-slate-200 leading-relaxed">{article_meta['summary']}</p>
        </div>
      </div>

      {NINJA_AD_SCRIPT}

      <div class="prose max-w-none">
        {body_html}
      </div>

      {cta_card}

      {NINJA_AD_SCRIPT}

      <div class="pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
        <a href="/" class="text-xs font-bold text-fuchsia-400 hover:text-fuchsia-300">← トップページへ戻る</a>
        <div class="flex items-center gap-2.5">
          <a href="/newcomers.html" class="px-4 py-2 bg-purple-900/80 hover:bg-purple-800 text-fuchsia-200 border border-fuchsia-500/40 rounded-xl text-xs font-bold transition">
            🌟 新人図鑑を見る
          </a>
          <a href="https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_share_url}" target="_blank" rel="noopener noreferrer" class="px-4 py-2 bg-fuchsia-600 hover:bg-fuchsia-500 text-white rounded-xl text-xs font-bold transition">
            𝕏 でシェアする
          </a>
        </div>
      </div>

      <section class="pt-6 border-t border-slate-800 space-y-3">
        <h3 class="text-sm md:text-base font-black text-white flex items-center gap-1.5">
          <span>🔥</span> 深夜に読まれている人気記事
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {related_html}
        </div>
      </section>
    </article>
  </main>

  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_ARTICLES_DIR, f"{slug}.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"Built article: /home/antigravity/lilipat-step-bayarts/kouteki-lifehack/store3/dist/articles/{slug}.html")


def build_newcomers_page(newcomers):
    cards_html = "\n".join([render_newcomer_card(item) for item in newcomers])

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>【2026年最新】大型新人女優・注目ルーキー図鑑＆サムネイル一覧 | オニゴンの夜更かしラボ</title>
  <meta name="description" content="毎月デビューする大型専属新人女優や同人ASMRの新星サークルをオニゴンが徹底評価！ビジュアル・スタイル・没入感の3軸ステータスとサンプル導線まとめ。">
  <link rel="canonical" href="{SITE_URL}/newcomers.html">
  <link rel="icon" type="image/jpeg" href="/assets/onigon_avatar.jpg">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased font-sans min-h-screen">
  {AGE_GATE_MODAL}
  {get_header("newcomers")}

  <!-- ヒーローヘッダー -->
  <section class="relative bg-gradient-to-b from-purple-950/70 via-slate-950 to-slate-950 py-10 border-b border-purple-500/30">
    <div class="max-w-5xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-6">
      <div class="space-y-3 max-w-2xl">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-fuchsia-950 text-fuchsia-300 text-xs font-bold border border-fuchsia-500/40">
          <span>🌟</span><span>毎月更新・オニゴン厳選ルーキー図鑑</span>
        </div>
        <h1 class="text-2xl md:text-4xl font-black text-white leading-tight">
          今月の大型新人＆注目ルーキー<br>
          <span class="text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-400 via-pink-400 to-amber-300">サムネイル＆ステータス徹底解剖</span>
        </h1>
        <p class="text-xs md:text-sm text-slate-300 leading-relaxed">
          予約ランキング・お気に入り登録数・サンプル動画の完成度から、今月絶対に押さえておくべきSSR・S+ランクの大型新人＆新星同人クリエイターを厳選ピックアップ！<br>
          <span class="text-fuchsia-300 font-semibold">※DMMアフィリエイトAPI連携対応：公式パッケージサムネイル・高画質サンプル動画へワンタップでアクセスできます。</span>
        </p>
      </div>
      <div class="shrink-0 flex items-center gap-3 bg-slate-900/90 p-4 rounded-3xl border border-purple-500/40 shadow-xl">
        <img src="/assets/onigon_avatar.jpg" alt="オニゴン" class="w-20 h-20 rounded-2xl object-cover border-2 border-fuchsia-400">
        <div class="text-xs space-y-1">
          <span class="px-2 py-0.5 rounded bg-amber-400 text-slate-950 font-black text-[10px]">CURATOR</span>
          <div class="font-black text-white text-sm">案内人：オニゴン</div>
          <p class="text-slate-400 text-[11px] max-w-[160px]">「ティザーとサンプル動画の後半まで全部見た上で本物だけ推すよ👿✨」</p>
        </div>
      </div>
    </div>
  </section>

  <main class="max-w-5xl mx-auto px-4 py-8 space-y-8">
    {NINJA_AD_SCRIPT}

    <!-- 新人サムネイルカードグリッド -->
    <section class="space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <h2 class="text-lg md:text-xl font-black text-white flex items-center gap-2">
          <span>📸</span><span>注目ルーキー・ピックアップ一覧（全{len(newcomers)}枠）</span>
        </h2>
        <span class="text-xs text-fuchsia-300 font-mono">★ 評価基準：ティザー完成度・お気に入り数・初回特典</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {cards_html}
      </div>
    </section>

    <!-- 新人デビュー作の選び方記事への誘導 -->
    <section class="p-6 bg-gradient-to-r from-purple-950/90 via-slate-900 to-indigo-950/90 rounded-3xl border border-fuchsia-500/40 flex flex-col md:flex-row items-center justify-between gap-4">
      <div class="space-y-1.5">
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-black bg-fuchsia-600 text-white">あわせて読みたい攻略記事</span>
        <h3 class="text-base md:text-lg font-black text-white">【2026年最新】大型新人デビュー＆注目ルーキー徹底解剖！失敗しない予約特典・4K/VR版の見極め方</h3>
        <p class="text-xs text-slate-300">発売前の予約数やサンプル動画のどこを見れば「当たり新人」が分かるのか、3つのチェック指標を解説！</p>
      </div>
      <a href="/articles/newcomer-debut-spotlight-2026.html" class="shrink-0 px-5 py-3 bg-fuchsia-600 hover:bg-fuchsia-500 text-white rounded-xl text-xs font-black shadow-lg transition">
        攻略記事を読む →
      </a>
    </section>

    {NINJA_AD_SCRIPT}
  </main>

  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_DIR, "newcomers.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"Built newcomers page: {out_file}")


def build_home_page(articles, newcomers):
    # トップページにも新人特集サムネイルカードを上位2件表示
    spotlight_cards = "\n".join([render_newcomer_card(item) for item in newcomers[:2]])

    article_cards = []
    for art in articles:
        article_cards.append(f"""
        <a href="/articles/{art['slug']}.html" class="group bg-slate-900/90 rounded-2xl p-5 border border-purple-500/30 hover:border-fuchsia-400/70 shadow-lg hover:shadow-fuchsia-950/40 transition-all flex flex-col justify-between">
          <div class="space-y-2.5">
            <div class="flex items-center justify-between text-xs text-slate-400">
              <span class="px-2.5 py-0.5 rounded-full bg-purple-950 text-fuchsia-300 border border-purple-700/60 font-bold">
                {art.get('icon', '👿')} {art.get('category', '深夜速報')}
              </span>
              <time datetime="{art['date']}" class="font-mono">{art['date']}</time>
            </div>
            <h3 class="text-base font-black text-white group-hover:text-fuchsia-300 transition leading-snug">
              {art['title']}
            </h3>
            <p class="text-xs text-slate-300 line-clamp-2 leading-relaxed">
              {art['summary']}
            </p>
          </div>
          <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-fuchsia-400 font-bold">
            <span>オニゴンの徹底解説を読む →</span>
            <span class="text-slate-500 font-normal">約{art.get('reading_time', 4)}分</span>
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
  <link rel="alternate" type="application/rss+xml" title="オニゴンの夜更かしラボ RSS" href="/rss.xml">
  <link rel="icon" type="image/jpeg" href="/assets/onigon_avatar.jpg">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="オニゴンの夜更かしラボ">
  <meta property="og:title" content="{SITE_TITLE}">
  <meta property="og:description" content="{SITE_DESCRIPTION}">
  <meta property="og:url" content="{SITE_URL}/">
  <meta property="og:image" content="{SITE_URL}/assets/onigon_avatar.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased font-sans min-h-screen">
  {AGE_GATE_MODAL}
  {get_header("home")}

  <!-- ヒーローセクション -->
  <section class="relative bg-gradient-to-b from-purple-950/60 via-slate-950 to-slate-950 py-10 md:py-12 border-b border-purple-500/30">
    <div class="max-w-5xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-6">
      <div class="space-y-3.5 max-w-xl text-center md:text-left">
        <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-950 text-fuchsia-300 text-xs font-bold border border-fuchsia-500/40">
          <span>👿</span><span>深夜のエンタメ＆セール厳選ラボ（18+）</span>
        </div>
        <h1 class="text-2xl md:text-4xl font-black text-white leading-tight">
          今夜の「最高の一本」を、<br>
          <span class="text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-400 via-pink-400 to-amber-300">最安値＆ハズレなしで。</span>
        </h1>
        <p class="text-xs md:text-sm text-slate-300 leading-relaxed">
          深夜の案内人「オニゴン」が、FANZAの500円均一セール・大型新人デビュー作・KU100バイノーラル同人ASMRを忖度なしレビュー！ジャケット詐欺を回避して神作だけを発掘します。
        </p>
        <div class="flex flex-wrap justify-center md:justify-start gap-3 pt-1">
          <a href="/newcomers.html" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 text-white text-xs font-black shadow-lg shadow-fuchsia-600/30 transition flex items-center gap-1.5">
            <span>🌟 今月の大型新人・サムネ図鑑を見る</span>
            <span>→</span>
          </a>
          <a href="/articles/fanza-500yen-sale-guide.html" class="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-fuchsia-300 border border-purple-500/40 text-xs font-bold transition">
            🔥 500円セール攻略法
          </a>
        </div>
      </div>
      <div class="shrink-0 relative">
        <img src="/assets/onigon_avatar.jpg" alt="オニゴン" class="w-32 h-32 md:w-40 md:h-40 rounded-3xl border-2 border-fuchsia-400 shadow-2xl shadow-fuchsia-950 object-cover">
        <span class="absolute -bottom-2 -right-2 px-3 py-1 bg-gradient-to-r from-fuchsia-600 to-rose-600 text-white rounded-full text-xs font-black shadow-lg">
          案内人：オニゴン👿
        </span>
      </div>
    </div>
  </section>

  <!-- メインコンテンツ -->
  <main class="max-w-5xl mx-auto px-4 py-8 space-y-10">
    {NINJA_AD_SCRIPT}

    <!-- 🌟 新人女優・注目ルーキー サムネイル特集セクション -->
    <section class="space-y-4">
      <div class="flex items-center justify-between flex-wrap gap-2 border-b border-purple-900/60 pb-3">
        <div>
          <span class="text-[11px] font-bold text-fuchsia-400 tracking-wider uppercase block">NEWCOMER SPOTLIGHT</span>
          <h2 class="text-lg md:text-xl font-black text-white flex items-center gap-2">
            <span>🌟</span><span>今月の大型新人デビュー＆注目ルーキー特集</span>
          </h2>
        </div>
        <a href="/newcomers.html" class="px-3.5 py-1.5 rounded-xl bg-purple-950 hover:bg-purple-900 text-fuchsia-300 border border-fuchsia-500/40 text-xs font-bold transition">
          全{len(newcomers)}名のサムネ図鑑を見る →
        </a>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {spotlight_cards}
      </div>
    </section>

    <!-- 記事一覧セクション -->
    <section class="space-y-4">
      <div class="flex items-center justify-between border-b border-purple-900/60 pb-3">
        <div>
          <span class="text-[11px] font-bold text-purple-400 tracking-wider uppercase block">LATEST GUIDES & REVIEWS</span>
          <h2 class="text-lg md:text-xl font-black text-white flex items-center gap-2">
            <span>🔥</span><span>深夜のセール攻略・ASMR・高評価作品レビュー</span>
          </h2>
        </div>
        <span class="text-xs text-slate-400 font-mono">全{len(articles)}記事</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {''.join(article_cards)}
      </div>
    </section>

    {NINJA_AD_SCRIPT}
  </main>

  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_DIR, "index.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(home_html)
    print(f"Built index: {out_file}")


def build_about_page():
    about_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>オニゴンについて（運営者情報） | オニゴンの夜更かしラボ</title>
  <link rel="icon" type="image/jpeg" href="/assets/onigon_avatar.jpg">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased font-sans min-h-screen">
  {AGE_GATE_MODAL}
  {get_header("about")}

  <main class="max-w-3xl mx-auto px-4 py-8">
    <div class="bg-slate-900/90 rounded-3xl p-6 md:p-10 border border-purple-500/30 shadow-2xl space-y-6">
      <div class="text-center space-y-3">
        <img src="/assets/onigon_avatar.jpg" alt="オニゴン" class="w-28 h-28 rounded-full border-4 border-fuchsia-400 mx-auto shadow-lg object-cover">
        <h1 class="text-xl font-black text-white">深夜のエンタメ案内人「オニゴン」</h1>
        <p class="text-xs text-fuchsia-300 font-bold">FANZAセール分析 / 大型新人レビュー / 同人ASMRキュレーター</p>
      </div>

      <div class="text-xs md:text-sm text-slate-300 leading-relaxed space-y-4 pt-4 border-t border-slate-800">
        <p>
          こんばんは！深夜のキュレーションメディア「オニゴンの夜更かしラボ」案内人の<strong>オニゴン</strong>です👿🌙
        </p>
        <p>
          当サイトは、膨大な作品が日々リリースされるFANZA（DMM）・同人ASMR音声・見放題サブスクの中から、<strong>「本当に満足度の高い名作・大型新人デビュー作」</strong>や<strong>「500円均一セール・割引クーポンを活用した最安値購入術」</strong>を分かりやすく整理してお届けするレビューサイトです。
        </p>
        <h2 class="text-base font-bold text-white pt-2">編集方針・コンプライアンスについて</h2>
        <ul class="list-disc ml-5 space-y-1.5 text-slate-300">
          <li>当サイトは18歳以上の成人を対象としており、初回アクセス時の年齢確認を実施しています。</li>
          <li>公式に許諾されたアフィリエイトプログラム（DMMアフィリエイト等）および公式サンプル導線のみを使用し、違法アップロードサイトへの誘導や無断転載は一切行いません。</li>
        </ul>
      </div>
    </div>
  </main>

  {get_footer()}
</body>
</html>"""
    with open(os.path.join(DIST_DIR, "about.html"), "w", encoding="utf-8") as f:
        f.write(about_html)
    print("Built about: dist/about.html")


def build_privacy_page():
    privacy_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>プライバシーポリシー・広告開示・免責事項 | オニゴンの夜更かしラボ</title>
  <link rel="icon" type="image/jpeg" href="/assets/onigon_avatar.jpg">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased font-sans min-h-screen">
  {AGE_GATE_MODAL}
  {get_header("privacy")}

  <main class="max-w-3xl mx-auto px-4 py-8">
    <div class="bg-slate-900/90 rounded-3xl p-6 md:p-10 border border-purple-500/30 shadow-2xl space-y-6">
      <h1 class="text-xl font-black text-white border-b border-slate-800 pb-3">プライバシーポリシー及び広告掲載に関する表記</h1>
      <div class="text-xs md:text-sm text-slate-300 space-y-4 leading-relaxed">
        <h2 class="font-bold text-fuchsia-300 text-sm">1. 年齢制限（18歳未満の閲覧禁止）について</h2>
        <p>当サイト「オニゴンの夜更かしラボ」は、成人向けコンテンツ（FANZA / DMM等）に関するレビューおよびセール情報を取り扱っております。18歳未満の方の閲覧は固くお断りいたします。</p>

        <h2 class="font-bold text-fuchsia-300 text-sm">2. 広告の配信・アフィリエイトプログラムについて</h2>
        <p>当サイトは、DMMアフィリエイト、忍者AdMax等のアフィリエイトプログラムおよび第三者配信広告サービスに参加しています。記事内のリンクを経由して商品が購入された場合、当サイトに紹介料が支払われることがあります。</p>

        <h2 class="font-bold text-fuchsia-300 text-sm">3. 免責事項</h2>
        <p>当サイトに掲載しているセール期間、価格、ポイント還元率等の情報は記事執筆時点のものです。最新の価格やキャンペーン適用条件については、必ず遷移先のFANZA / DMM公式ページにてご確認ください。</p>
      </div>
    </div>
  </main>

  {get_footer()}
</body>
</html>"""
    with open(os.path.join(DIST_DIR, "privacy.html"), "w", encoding="utf-8") as f:
        f.write(privacy_html)
    print("Built privacy: dist/privacy.html")


def build_seo_files(articles):
    urls = [
        f"  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{SITE_URL}/newcomers.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>"
    ]
    for art in articles:
        urls.append(
            f"  <url><loc>{SITE_URL}/articles/{art['slug']}.html</loc><lastmod>{art['date']}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>"
        )
    sitemap_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    with open(os.path.join(DIST_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    robots_txt = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    with open(os.path.join(DIST_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots_txt)

    items = []
    for art in articles[:15]:
        items.append(
            f"    <item><title>{art['title']}</title><link>{SITE_URL}/articles/{art['slug']}.html</link><description>{art['summary']}</description><pubDate>{art['date']}</pubDate></item>"
        )
    rss_xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<rss version="2.0"><channel><title>{SITE_TITLE}</title><link>{SITE_URL}/</link><description>{SITE_DESCRIPTION}</description>\n'
        + "\n".join(items)
        + "\n</channel></rss>\n"
    )
    with open(os.path.join(DIST_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)


def main():
    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(DIST_ARTICLES_DIR, exist_ok=True)
    os.makedirs(DIST_ASSETS_DIR, exist_ok=True)

    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    newcomers = []
    if os.path.exists(NEWCOMERS_JSON):
        with open(NEWCOMERS_JSON, "r", encoding="utf-8") as f:
            newcomers = json.load(f)

    for art in articles:
        build_article_page(art, articles)

    build_newcomers_page(newcomers)
    build_home_page(articles, newcomers)
    build_about_page()
    build_privacy_page()
    build_seo_files(articles)

    print("✨ Successfully built Store 3 (Onigon Night Lab) static site with Newcomer Spotlight in dist/!")


if __name__ == "__main__":
    main()
