#!/usr/bin/env python3
"""
コスメ成分ラボ・プチプラ速報 (2号店) 静的Webサイトビルダースクリプト
知恵のマスコット「イケロ」を前面に出したクリーンな美容サイエンスデザイン。
忍者AdMax（ビュー報酬）＋ A8.net・楽天・Amazon物販アフィリエイト（成約報酬）の二刀流構造。
"""

import os
import json
import re
import urllib.parse
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

def get_unlocked_slots_store2(now_jst):
    """
    2号店（イケロ）投稿時間（07:30, 10:30, 12:45, 18:30, 21:30 JST ※30分ずらし）に基づく公開解放スロット
    指定時刻になるまで、未来のスロット記事はサイト（index, rss）に掲載しない
    """
    total_min = now_jst.hour * 60 + now_jst.minute
    if total_min < 450: # 07:30 JST 未満
        return []
    elif total_min < 630: # 10:30 JST 未満
        return ["slot1"]
    elif total_min < 765: # 12:45 JST 未満
        return ["slot1", "slot2"]
    elif total_min < 1110: # 18:30 JST 未満
        return ["slot1", "slot2", "slot3"]
    elif total_min < 1290: # 21:30 JST 未満
        return ["slot1", "slot2", "slot3", "slot4"]
    else: # 21:30 JST 以降
        return ["slot1", "slot2", "slot3", "slot4", "slot5"]

def is_article_unlocked_store2(article, now_jst):
    art_date = article.get("date", "")
    today_str = now_jst.strftime("%Y-%m-%d")
    if not art_date or art_date < today_str:
        return True # 過去の記事は全公開
    if art_date > today_str:
        return False # 未来日付は非公開
    # 当日記事の場合
    slot = article.get("slot")
    if not slot:
        return True
    return slot in get_unlocked_slots_store2(now_jst)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
ARTICLES_JSON = os.path.join(ARTICLES_DIR, "articles.json")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
DIST_ARTICLES_DIR = os.path.join(DIST_DIR, "articles")
DIST_ASSETS_DIR = os.path.join(DIST_DIR, "assets")

SITE_TITLE = "コスメ成分ラボ・プチプラ速報 | 知恵の案内人イケロが忖度なし比較"
SITE_DESCRIPTION = "高いデパコスと何が違う？レチノール、ナイアシンアミド、ヒト型セラミド、ビタミンCなどの有効成分を、知恵のマスコット『イケロ』が科学的根拠に基づいて徹底比較・解説する美容情報メディア。"
SITE_URL = "https://lilipat-cosme-bayarts.com"

AMAZON_TAG = "ikerocosme-22"
RAKUTEN_AF_ID = "597f29ed.f305c9f6.597f29ee.8555f86c"

# 広告コード（スマホ: 忍者AdMax / PC: 楽天・Amazon公認コスメ特集バナー）
NINJA_AD_SCRIPT = f"""
<!-- スポンサーユニット -->
<div class="my-6 p-3 md:p-4 bg-gradient-to-br from-rose-50/70 via-pink-50/40 to-amber-50/30 rounded-2xl border border-rose-200 text-center shadow-2xs overflow-hidden">
  <div class="flex items-center justify-between mb-2 pb-1 border-b border-rose-100 text-[10px] font-bold text-rose-500 uppercase tracking-wider">
    <span class="flex items-center gap-1 font-bold">🌸 スポンサーリンク（コスメ・美容特集）</span>
    <span class="bg-rose-100 text-rose-800 px-2 py-0.5 rounded-full text-[9px] font-medium">公式キャンペーン</span>
  </div>

  <!-- 忍者AdMax：全端末共通で確実に表示・インプレッション計測 -->
  <div class="my-3 flex justify-center items-center overflow-hidden">
    <script src="https://adm.shinobi.jp/s/b133ea03dc5417daa8dc029d6b6b4816"></script>
  </div>

  <!-- 楽天・Amazonコスメ公式特集カード -->
  <div class="mt-3 flex flex-col md:flex-row items-center justify-between gap-4 p-4 bg-white/95 rounded-xl border border-rose-200 shadow-2xs text-left">
    <div class="space-y-1.5 flex-1">
      <div class="flex items-center gap-2">
        <span class="px-2 py-0.5 rounded bg-rose-600 text-white font-extrabold text-[11px]">楽天公式</span>
        <h3 class="text-sm md:text-base font-extrabold text-slate-900 leading-snug">
          【コスメ・スキンケア】今月売れてるベストコスメ＆ポイント最大20倍特集
        </h3>
      </div>
      <p class="text-xs text-slate-600 leading-relaxed">
        美容成分マニアが厳選！デパコス級のプチプラ化粧水から最新の韓国コスメまで、楽天・Amazonのリアルタイム売れ筋ランキングをチェック。
      </p>
    </div>
    <div class="shrink-0 flex flex-col gap-2 w-full md:w-auto">
      <a href="https://hb.afl.rakuten.co.jp/hgc/597f29ed.f305c9f6.597f29ee.8555f86c/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F%25E3%2582%25B9%25E3%2582%25AD%25E3%2583%25B3%25E3%2582%25B1%25E3%2582%25A2%2B%25E7%25BE%258E%25E5%25AE%25B9%25E6%25B6%25B2%2F&link_type=text" target="_blank" rel="noopener noreferrer sponsored" class="px-5 py-3 bg-gradient-to-r from-rose-500 to-pink-500 hover:from-rose-400 hover:to-pink-400 text-white font-black text-xs rounded-xl shadow-sm hover:shadow transition flex items-center justify-center gap-2 whitespace-nowrap">
        <span>✨ 楽天市場で人気コスメランキングを見る ↗</span>
      </a>
      <a href="https://www.amazon.co.jp/s?k=%E3%82%B9%E3%82%AD%E3%83%B3%E3%82%B1%E3%82%A2+%E7%BE%8E%E5%AE%B9%E6%B6%B2&tag=ikerocosme-22" target="_blank" rel="noopener noreferrer sponsored" class="text-[11px] text-rose-700 hover:underline font-bold text-center">
        Amazonで最新コスメ・スキンケアを探す ↗
      </a>
    </div>
  </div>
</div>
"""

# 執筆・監修者プロフィールカード（最高峰E-E-A-T対策）
IKERO_AUTHOR_CARD = """
      <!-- 執筆・監修者プロフィール（最高峰E-E-A-T対策） -->
      <div class="mt-8 p-5 bg-gradient-to-r from-emerald-50/90 via-teal-50/70 to-emerald-50/90 border border-emerald-200 rounded-2xl space-y-3.5 shadow-sm">
        <div class="flex items-start sm:items-center gap-3.5 flex-col sm:flex-row">
          <img src="/assets/ikero_avatar.jpg" alt="イケロ" class="w-16 h-16 rounded-full border-2 border-emerald-500 shadow-md object-cover shrink-0">
          <div class="space-y-1 w-full">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">記事執筆・監修</span>
                <span class="font-black text-slate-900 text-base">知恵の白キツネ研究員「イケロ」</span>
              </div>
              <a href="https://x.com/ikero_lab" target="_blank" rel="noopener noreferrer" class="text-[11px] px-3 py-1 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-full transition flex items-center gap-1 shadow-sm">
                <svg class="w-3 h-3 fill-current" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                @ikero_lab をフォロー
              </a>
            </div>
            <p class="text-xs font-bold text-emerald-900">化粧品業界長年勤務 × 薬機・景表法務＆成分最上位プロフェッショナル</p>
          </div>
        </div>

        <div class="bg-white/90 rounded-xl p-3.5 border border-emerald-100 space-y-2.5 text-xs">
          <div class="font-bold text-slate-800 flex items-center gap-1.5 text-xs">
            <span>🎓</span> 監修者保有資格＆専門領域
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[11px] text-slate-700">
            <div class="flex items-center gap-1.5 bg-emerald-50/50 px-2.5 py-1.5 rounded-lg border border-emerald-100">
              <span class="text-emerald-600 font-bold">✔</span>
              <span><strong>日本化粧品検定最上位</strong> コスメコンシェルジュインストラクター</span>
            </div>
            <div class="flex items-center gap-1.5 bg-emerald-50/50 px-2.5 py-1.5 rounded-lg border border-emerald-100">
              <span class="text-emerald-600 font-bold">✔</span>
              <span><strong>化粧品成分検定スペシャリスト</strong>（1級・全成分解析）</span>
            </div>
            <div class="flex items-center gap-1.5 bg-emerald-50/50 px-2.5 py-1.5 rounded-lg border border-emerald-100">
              <span class="text-emerald-600 font-bold">✔</span>
              <span><strong>コスメ薬機法管理者</strong>（医薬部外品・効能表現監修）</span>
            </div>
            <div class="flex items-center gap-1.5 bg-emerald-50/50 px-2.5 py-1.5 rounded-lg border border-emerald-100">
              <span class="text-emerald-600 font-bold">✔</span>
              <span><strong>消費者庁 景品表示法務検定資格者</strong>（適正広告評価）</span>
            </div>
          </div>
          <p class="text-[11px] text-slate-600 leading-relaxed pt-1.5 border-t border-emerald-100">
            化粧品業界で長年培った開発・処方の知見と、薬機法・景品表示法の徹底した法務コンプライアンスに基づき、ブランドの誇大広告やSNSのバズに惑わされない「全成分表示と科学的根拠（エビデンス）」に特化した忖度なしの比較情報をお届けしています。
          </p>
        </div>
      </div>
"""

AMAZON_TAG = "ikerocosme-22"
RAKUTEN_AF_ID = "597f29ed.f305c9f6.597f29ee.8555f86c"

# A8.net / 物販成約型アフィリエイト商品カードテンプレート（実稼働リンク＋Amazon＆楽天アソシエイトID搭載）
def get_affiliate_card(product_name, category, price, key_ingredients, merit, search_keyword=None, official_url="https://www.jcia.org/", official_name="メーカー公式製品ページ"):
    query = urllib.parse.quote(search_keyword or product_name)
    amazon_url = f"https://www.amazon.co.jp/s?k={query}&tag={AMAZON_TAG}"
    rakuten_search_url = f"https://search.rakuten.co.jp/search/mall/{query}/"
    rakuten_pc = urllib.parse.quote(rakuten_search_url, safe="")
    rakuten_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_AF_ID}/?pc={rakuten_pc}&link_type=text"

    trial_query = urllib.parse.quote("オルビス ファンケル キュレル トライアルセット 医薬部外品")
    trial_amazon_url = f"https://www.amazon.co.jp/s?k={trial_query}&tag={AMAZON_TAG}"
    trial_rakuten_search = f"https://search.rakuten.co.jp/search/mall/{urllib.parse.quote('医薬部外品 スキンケア トライアルセット 公式')}/"
    trial_rakuten_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_AF_ID}/?pc={urllib.parse.quote(trial_rakuten_search, safe='')}&link_type=text"

    return f"""
    <div class="my-6 p-5 bg-gradient-to-r from-emerald-50/70 to-teal-50/70 rounded-2xl border border-emerald-200/80 shadow-sm">
      <div class="flex items-center justify-between mb-2">
        <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-600 text-white">イケロ太鼓判・成分解析ピックアップ</span>
        <span class="text-xs font-medium text-emerald-800 font-mono">参考価格: {price}</span>
      </div>
      <h4 class="text-base font-bold text-slate-800 mb-1">{product_name}</h4>
      <div class="flex flex-wrap gap-1.5 mb-3">
        {' '.join([f'<span class="text-[11px] px-2 py-0.5 bg-white text-emerald-700 border border-emerald-200 rounded-md font-medium">#{tag}</span>' for tag in key_ingredients])}
      </div>
      <p class="text-xs text-slate-600 leading-relaxed mb-4">{merit}</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        <a href="{amazon_url}" target="_blank" rel="noopener noreferrer sponsored" class="py-2.5 px-4 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white text-center rounded-xl font-bold text-xs shadow-sm transition-all flex items-center justify-center gap-1.5">
          <span>Amazonで成分詳細・価格を見る</span>
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
        </a>
        <a href="{rakuten_url}" target="_blank" rel="noopener noreferrer sponsored" class="py-2.5 px-4 bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white text-center rounded-xl font-bold text-xs shadow-sm transition-all flex items-center justify-center gap-1.5">
          <span>楽天市場で最安値ショップを比較</span>
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
        </a>
      </div>
      <div class="mt-2.5 text-right">
        <a href="{official_url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-[11px] text-emerald-700 hover:text-emerald-900 hover:underline font-medium">
          <span>🏛️ {official_name}で全成分表示を確認する</span>
          <span>↗</span>
        </a>
      </div>
    </div>

    <!-- 💎 高成約枠：デパコス・薬用コスメの初回1,000円台トライアルセット比較枠 -->
    <div class="my-6 p-5 bg-gradient-to-br from-rose-50 via-pink-50/70 to-amber-50/60 rounded-2xl border-2 border-rose-200 shadow-sm space-y-3">
      <div class="flex items-center justify-between flex-wrap gap-2">
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-rose-600 text-white">💎 失敗しないための初回限定・お試し比較</span>
        <span class="text-[10px] text-rose-700 font-bold">PR・薬用/デパコス 1,000円台〜トライアル</span>
      </div>
      <h4 class="text-sm md:text-base font-black text-slate-900 leading-snug">
        いきなり現品を買って肌に合わないのが不安な方へ｜薬用・敏感肌トライアルセット比較
      </h4>
      <p class="text-xs text-slate-600 leading-relaxed">
        高濃度成分や医薬部外品は、まず<strong>1,000円〜1,500円台のミニサイズ（7日〜14日間トライアルセット）</strong>で自分の肌との相性をテストするのが美肌への最短ルートです。オルビス・ファンケル・キュレル等の公式お試しセットを一覧で比較できます。
      </p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
        <a href="{trial_amazon_url}" target="_blank" rel="noopener noreferrer sponsored" class="py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white text-center rounded-xl font-bold text-xs shadow-sm transition-all flex items-center justify-center gap-1.5">
          <span>🎁 Amazonで1,000円台〜の薬用トライアルセットを見る</span>
          <span>↗</span>
        </a>
        <a href="{trial_rakuten_url}" target="_blank" rel="noopener noreferrer sponsored" class="py-2.5 px-4 bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white text-center rounded-xl font-bold text-xs shadow-sm transition-all flex items-center justify-center gap-1.5">
          <span>✨ 楽天の公式ショップ限定お試しセットを比較する</span>
          <span>↗</span>
        </a>
      </div>
    </div>
    """

def get_header(current_page="home"):
    return f"""
  <header class="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-rose-100 shadow-sm">
    <div class="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
      <a href="/" class="flex items-center gap-2.5 group">
        <img src="/assets/ikero_avatar.jpg" alt="イケロ" class="w-10 h-10 rounded-full border-2 border-emerald-400 shadow-sm object-cover group-hover:scale-105 transition-transform">
        <div>
          <span class="text-xs font-bold text-emerald-600 tracking-wider block">知恵のコスメ解析</span>
          <span class="text-base font-black text-slate-800 tracking-tight">イケロのコスメ成分ラボ</span>
        </div>
      </a>
      <nav class="flex items-center gap-4 text-xs font-semibold text-slate-600">
        <a href="/" class="hover:text-emerald-600 transition {'text-emerald-600' if current_page == 'home' else ''}">新着記事</a>
        <a href="/about" class="hover:text-emerald-600 transition {'text-emerald-600' if current_page == 'about' else ''}">イケロとは？</a>
        <a href="/privacy" class="hover:text-emerald-600 transition {'text-emerald-600' if current_page == 'privacy' else ''}">免責・プライバシー</a>
      </nav>
    </div>
  </header>
"""

def get_footer():
    return f"""
  <footer class="bg-slate-900 text-slate-400 py-12 mt-16 border-t border-slate-800">
    <div class="max-w-4xl mx-auto px-4 text-center space-y-4">
      <div class="flex items-center justify-center gap-2">
        <img src="/assets/ikero_avatar.jpg" alt="イケロ" class="w-8 h-8 rounded-full border border-emerald-400 object-cover">
        <span class="font-bold text-white text-sm">イケロのコスメ成分ラボ・プチプラ速報</span>
      </div>
      <p class="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
        当サイトは、知恵と科学の案内人「イケロ」が客観的な化粧品成分・医薬部外品データに基づいて比較情報を提供する専門メディアです。
      </p>
      <div class="text-[11px] text-slate-600 space-x-3 pt-2">
        <a href="/" class="hover:text-slate-300">トップ</a>
        <span>•</span>
        <a href="/about" class="hover:text-slate-300">サイトについて</a>
        <span>•</span>
        <a href="/privacy" class="hover:text-slate-300">プライバシーポリシー・広告開示</a>
      </div>
      <div class="text-[11px] text-slate-600 font-mono">
        © 2026 Ikero Cosme Lab. All Rights Reserved.
      </div>
    </div>
  </footer>
"""

def markdown_to_html(md_text):
    lines = md_text.strip().split("\n")
    html_parts = []
    in_table = False
    table_rows = []

    for line in lines:
        if line.startswith("# "):
            continue  # タイトルは別で出力
        elif line.startswith("## "):
            heading = line[3:].strip()
            html_parts.append(f'<h2 class="text-lg md:text-xl font-bold text-slate-800 mt-8 mb-3 pb-2 border-b-2 border-emerald-400 flex items-center gap-2"><span class="text-emerald-500">🧪</span>{heading}</h2>')
        elif line.startswith("### "):
            heading = line[4:].strip()
            html_parts.append(f'<h3 class="text-base font-bold text-slate-800 mt-6 mb-2 flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>{heading}</h3>')
        elif line.startswith("- "):
            item = line[2:].strip()
            item = re.sub(r'\*\*(.+?)\*\*', r'<strong class="text-slate-900">\1</strong>', item)
            item = re.sub(r'`(.+?)`', r'<code class="px-1.5 py-0.5 bg-slate-100 rounded text-emerald-700 font-mono text-xs">\1</code>', item)
            html_parts.append(f'<li class="text-xs md:text-sm text-slate-600 leading-relaxed mb-1.5 ml-4 list-disc">{item}</li>')
        elif line.startswith("1. ") or line.startswith("2. ") or line.startswith("3. ") or line.startswith("4. "):
            item = line[3:].strip()
            item = re.sub(r'\*\*(.+?)\*\*', r'<strong class="text-slate-900">\1</strong>', item)
            item = re.sub(r'`(.+?)`', r'<code class="px-1.5 py-0.5 bg-slate-100 rounded text-emerald-700 font-mono text-xs">\1</code>', item)
            html_parts.append(f'<li class="text-xs md:text-sm text-slate-600 leading-relaxed mb-1.5 ml-4 list-decimal">{item}</li>')
        elif line.startswith("|"):
            in_table = True
            table_rows.append(line)
        else:
            if in_table:
                # テーブルを終了して描画
                html_parts.append(render_table(table_rows))
                in_table = False
                table_rows = []

            if line.strip() == "---":
                html_parts.append('<hr class="my-6 border-rose-100">')
            elif line.strip():
                p = line.strip()
                p = re.sub(r'\*\*(.+?)\*\*', r'<strong class="text-slate-900 font-bold">\1</strong>', p)
                p = re.sub(r'`(.+?)`', r'<code class="px-1.5 py-0.5 bg-slate-100 rounded text-emerald-700 font-mono text-xs">\1</code>', p)
                html_parts.append(f'<p class="text-xs md:text-sm text-slate-600 leading-relaxed mb-4">{p}</p>')

    if in_table:
        html_parts.append(render_table(table_rows))

    return "\n".join(html_parts)

def render_table(rows):
    if len(rows) < 2:
        return ""
    header_cols = [c.strip() for c in rows[0].split("|")[1:-1]]
    data_rows = rows[2:]

    th_html = "".join([f'<th class="py-2.5 px-3 text-left font-bold text-slate-700 border-b border-emerald-200">{col}</th>' for col in header_cols])
    tr_html = []
    for r in data_rows:
        cols = [c.strip() for c in r.split("|")[1:-1]]
        td_items = []
        for col in cols:
            formatted_col = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', col)
            td_items.append(f'<td class="py-2.5 px-3 text-slate-600 border-b border-slate-100 text-xs md:text-sm">{formatted_col}</td>')
        tds = "".join(td_items)
        tr_html.append(f'<tr class="hover:bg-emerald-50/40 transition">{tds}</tr>')

    return f"""
    <div class="my-6 overflow-x-auto rounded-xl border border-emerald-100 shadow-sm">
      <table class="w-full text-left text-xs md:text-sm bg-white">
        <thead class="bg-emerald-50/70 text-slate-700">{th_html}</thead>
        <tbody class="divide-y divide-slate-100">{''.join(tr_html)}</tbody>
      </table>
    </div>
    """

def build_article_page(article_meta):
    slug = article_meta["slug"]
    md_path = os.path.join(ARTICLES_DIR, f"{slug}.md")
    if not os.path.exists(md_path):
        return

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    body_html = markdown_to_html(md_text)

    # 記事ごとのアフィリエイト商品カードの選定（Amazon・楽天・公式サイト実稼働リンク付き）
    affiliate_card = ""
    if "retinol" in slug:
        affiliate_card = get_affiliate_card(
            product_name="なめらか本舗 リンクルアイクリーム N (ピュアレチノール配合)",
            category="アイケア・美容液",
            price="¥1,045 (税込)",
            key_ingredients=["ピュアレチノール", "豆乳発酵液", "ビタミンE誘導体"],
            merit="1,000円前後のプチプラとは思えないピュアレチノールのカプセル化技術を採用。目元やほうれい線のピンポイントケアに最適です。",
            search_keyword="なめらか本舗 リンクルアイクリーム N",
            official_url="https://nameraka.jp/",
            official_name="常盤薬品工業「なめらか本舗」公式サイト"
        )
    elif "niacinamide" in slug:
        affiliate_card = get_affiliate_card(
            product_name="肌ラボ 極潤薬用エイジングケア 化粧水 (医薬部外品)",
            category="薬用美白・シワ改善化粧水",
            price="¥1,100 (税込)",
            key_ingredients=["ナイアシンアミド", "3種のヒアルロン酸", "アセチルヒアルロン酸"],
            merit="厚生労働省承認の有効成分ナイアシンアミドを贅沢配合。顔だけでなく首・デコルテまでたっぷり使えるコスパ最強の美白・シワ改善化粧水。",
            search_keyword="肌ラボ 極潤 薬用エイジングケア 化粧水",
            official_url="https://jp.rohto.com/hadalabo/",
            official_name="ロート製薬「肌ラボ」公式ブランドサイト"
        )
    elif "ceramide" in slug:
        affiliate_card = get_affiliate_card(
            product_name="セザンヌ スキンコンディショナー高保湿 (500ml)",
            category="高保湿セラミド化粧水",
            price="¥715 (税込)",
            key_ingredients=["ヒト型セラミドNP", "ヒト型セラミドAP", "ヒト型セラミドEOP"],
            merit="なんと700円台で『3種類のヒト型セラミド』を網羅。インナードライに悩む全ての乾燥肌におすすめの神コスパ品。",
            search_keyword="セザンヌ スキンコンディショナー 高保湿",
            official_url="https://www.cezanne.co.jp/",
            official_name="セザンヌ化粧品 公式商品情報"
        )
    elif "tranexamic" in slug:
        affiliate_card = get_affiliate_card(
            product_name="肌ラボ 白潤プレミアム 薬用浸透美白化粧水 (医薬部外品)",
            category="薬用美白・抗炎症化粧水",
            price="¥990 (税込)",
            key_ingredients=["ホワイトトラネキサム酸", "グリチルリチン酸2K", "ビタミンC・E"],
            merit="美白有効成分トラネキサム酸と肌荒れ防止成分グリチルリチン酸2KのW有効成分を配合。デパコス級の処方骨格が1,000円以下で手に入る名品。",
            search_keyword="肌ラボ 白潤プレミアム 薬用浸透美白化粧水",
            official_url="https://jp.rohto.com/hadalabo/",
            official_name="ロート製薬「肌ラボ 白潤プレミアム」公式"
        )
    elif "glutathione" in slug:
        affiliate_card = get_affiliate_card(
            product_name="ナンバーズイン(numbuzin) 5番 白玉グルタチオンC美容液",
            category="高濃度グルタチオン・ビタミンC美容液",
            price="¥2,400 (税込)",
            key_ingredients=["リポソームグルタチオン", "ナイアシンアミド5%", "ビタミンC誘導体"],
            merit="抗酸化ネットワークを形成するグルタチオン×ビタミンC×ナイアシンアミドの黄金比率。くすみや色ムラに多角的にアプローチ。",
            search_keyword="ナンバーズイン 5番 白玉グルタチオンC美容液",
            official_url="https://www.cosme.net/",
            official_name="アットコスメ（@cosme）公式製品データベース"
        )
    elif "glycylglycine" in slug:
        affiliate_card = get_affiliate_card(
            product_name="トゥヴェール バランシングGAローション (グリシルグリシン6%配合)",
            category="開き毛穴・キメ整肌プレ化粧水",
            price="¥2,000 (税込)",
            key_ingredients=["グリシルグリシン6%", "アゼライン酸誘導体", "アロエベラ葉エキス"],
            merit="すり鉢毛穴の原因にアプローチするグリシルグリシンを高濃度6%配合。さらに皮脂トラブルを防ぐアゼライン酸誘導体も同時配合した本格派。",
            search_keyword="トゥヴェール バランシングGAローション",
            official_url="https://www.tvert.jp/",
            official_name="トゥヴェール（TOUT VERT）公式オンラインストア"
        )
    elif "azelaic" in slug:
        affiliate_card = get_affiliate_card(
            product_name="コスデバハ(Cos De BAHA) AZアゼライン酸10%美容液 / トゥヴェール ケアナノパック",
            category="皮脂・毛穴ケア美容液",
            price="¥1,890 (税込)",
            key_ingredients=["アゼライン酸", "ナイアシンアミド", "パンテノール"],
            merit="皮脂トラブルやTゾーンのテカリ・毛穴詰まりを穏やかに整えるアゼライン酸配合セラム。ナイアシンアミドやヒアルロン酸との相乗効果でなめらかな肌へ。",
            search_keyword="アゼライン酸 美容液 スキンケア",
            official_url="https://www.tvert.jp/",
            official_name="トゥヴェール 成分解析・公式ページ"
        )
    elif "bakuchiol" in slug:
        affiliate_card = get_affiliate_card(
            product_name="コスアールエックス(COSRX) RXザ・レチノール / バクチオールセラム",
            category="敏感肌向け次世代エイジングケア",
            price="¥2,180 (税込)",
            key_ingredients=["バクチオール", "パンテノール", "トコトリエノール(スーパービタミンE)"],
            merit="A反応（皮剥け・赤み）が起きにくい植物由来バクチオールを採用。朝晩使えて敏感肌のハリ・弾力ケアに最適。",
            search_keyword="バクチオール 美容液 レチノール",
            official_url="https://www.cosme.net/",
            official_name="アットコスメ（@cosme）公式製品データベース"
        )
    elif "panthenol" in slug:
        affiliate_card = get_affiliate_card(
            product_name="ラ ロッシュ ポゼ シカプラスト リペアクリーム B5+ (パンテノール配合)",
            category="肌荒れ・バリア機能サポートクリーム",
            price="¥2,970 (税込)",
            key_ingredients=["パンテノール(プロビタミンB5)", "マデカッソシド(CICA)", "シアバター"],
            merit="乾燥や摩擦でゆらいだ角質バリアを素早くサポートするパンテノール高配合バーム。敏感肌の常備レスキュー保湿に最適。",
            search_keyword="ラロッシュポゼ シカプラスト リペアクリーム B5",
            official_url="https://www.laroche-posay.jp/",
            official_name="ラ ロッシュ ポゼ 公式ブランドサイト"
        )
    else:
        affiliate_card = get_affiliate_card(
            product_name="メラノCC 薬用しみ集中対策プレミアム美容液 (医薬部外品)",
            category="高浸透ビタミンC美容液",
            price="¥1,628 (税込)",
            key_ingredients=["活性型ビタミンC", "3種のビタミンC誘導体", "ビタミンB6"],
            merit="独自の酸化防止容器で新鮮なビタミンCが角質奥まで浸透。毛穴の引き締めと紫外線ダメージケアの王道アイテム。",
            search_keyword="メラノCC 薬用しみ集中対策 プレミアム美容液",
            official_url="https://jp.rohto.com/melanocc/",
            official_name="ロート製薬「メラノCC」公式ブランドサイト"
        )

    # 関連記事（自記事以外から最大4件）
    all_articles = []
    if os.path.exists(ARTICLES_JSON):
        try:
            with open(ARTICLES_JSON, "r", encoding="utf-8") as af:
                all_articles = json.load(af)
        except Exception:
            all_articles = []

    related = [a for a in all_articles if a.get("slug") != slug][:4]
    related_html = ""
    for r_art in related:
        related_html += f"""
        <a href="/articles/{r_art['slug']}" class="block p-4 bg-rose-50/40 hover:bg-emerald-50/60 border border-rose-100 hover:border-emerald-300 rounded-2xl transition group">
          <div class="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">{r_art.get('category', '成分解析')}</span>
            <span>{r_art['date']}</span>
          </div>
          <div class="text-xs md:text-sm font-bold text-slate-900 group-hover:text-emerald-700 leading-snug">{r_art['title']}</div>
        </a>
        """
    next_art = related[0] if related else article_meta

    article_url = f"{SITE_URL}/articles/{slug}"
    encoded_title = urllib.parse.quote(f"{article_meta['title']} #コスメ成分 #プチプラコスメ #イケロ")
    encoded_share_url = urllib.parse.quote(article_url)

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article_meta['title'],
        "description": article_meta['summary'],
        "image": [f"{SITE_URL}/assets/ikero_banner.jpg"],
        "datePublished": article_meta['date'],
        "dateModified": article_meta['date'],
        "author": [{"@type": "Person", "name": "イケロ (コスメ成分ラボ)", "url": f"{SITE_URL}/about"}]
    }, ensure_ascii=False)

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{article_meta['title']} | イケロのコスメ成分ラボ</title>
  <meta name="description" content="{article_meta['summary']}">
  <link rel="canonical" href="{article_url}">
  <link rel="alternate" type="application/rss+xml" title="イケロのコスメ成分ラボ RSS" href="/rss.xml">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="イケロのコスメ成分ラボ">
  <meta property="og:title" content="{article_meta['title']}">
  <meta property="og:description" content="{article_meta['summary']}">
  <meta property="og:url" content="{article_url}">
  <meta property="og:image" content="{SITE_URL}/assets/ikero_banner.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@ikero_lab">
  <meta name="twitter:title" content="{article_meta['title']}">
  <meta name="twitter:description" content="{article_meta['summary']}">
  <meta name="twitter:image" content="{SITE_URL}/assets/ikero_banner.jpg">
  <script type="application/ld+json">{json_ld}</script>
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3133098627249534" crossorigin="anonymous"></script>
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    (function() {{
      var ua = navigator.userAgent || '';
      var isTwitter = /Twitter/i.test(ua) || /FBAN|FBAV|Instagram/i.test(ua);
      if (isTwitter) {{
        document.addEventListener('DOMContentLoaded', function() {{
          var guide = document.createElement('div');
          guide.id = 'x-inapp-guide';
          guide.className = 'bg-gradient-to-r from-rose-700 via-pink-700 to-rose-800 text-white text-xs px-3 py-2.5 flex items-center justify-between shadow-md sticky top-0 z-50';
          guide.innerHTML = '<div class="flex items-center gap-1.5 font-medium leading-tight"><span>📱</span><span><b>全画面で開く</b>：中央の「⁝」から「Safariで開く」または画面を上にスワイプ</span></div><button onclick="this.parentElement.remove()" class="ml-2 font-bold px-2 py-0.5 bg-white/20 hover:bg-white/30 rounded text-[11px] shrink-0">閉じる ✕</button>';
          document.body.insertBefore(guide, document.body.firstChild);
        }});
      }}
    }})();
  </script>
</head>
<body class="bg-[#fafafa] text-slate-800 antialiased font-sans pb-16 md:pb-0">
  {get_header("article")}

  <main class="max-w-3xl mx-auto px-4 py-8">
    <article class="bg-white rounded-3xl p-6 md:p-10 border border-rose-100 shadow-sm space-y-6">
      
      <!-- カテゴリ & 日付 -->
      <div class="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-100">
        <span class="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
          {article_meta.get('category', 'スキンケア')}
        </span>
        <time datetime="{article_meta['date']}">{article_meta['date']}</time>
      </div>

      <!-- タイトル -->
      <h1 class="text-xl md:text-2xl font-black text-slate-900 leading-snug">
        {article_meta['title']}
      </h1>

      <!-- イケロの忖度なしチェックBOX -->
      <div class="p-4 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-2xl border border-emerald-200 flex items-start gap-3">
        <img src="/assets/ikero_avatar.jpg" alt="イケロ" class="w-12 h-12 rounded-full border-2 border-emerald-400 shrink-0 shadow-sm object-cover">
        <div class="text-xs space-y-1">
          <div class="font-bold text-emerald-900 flex items-center gap-1 flex-wrap">
            <span>知恵の案内人 イケロの忖度なし成分チェック</span>
            <span class="text-[10px] px-1.5 py-0.2 bg-emerald-200 text-emerald-800 rounded">科学的視点</span>
          </div>
          <p class="text-slate-700 leading-relaxed">
            {article_meta['summary']}
          </p>
        </div>
      </div>

      <!-- 本文 -->
      <div class="prose max-w-none text-slate-700">
        {body_html}
      </div>

      <!-- 👑 特設ハブ導線：成分スペシャリスト厳選・神プチプラ特集 -->
      <div class="my-6 p-4 md:p-5 bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-700 text-white rounded-2xl shadow-md flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="space-y-1 text-center sm:text-left">
          <div class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white/20 text-emerald-100 text-[11px] font-black">
            <span>🔬 イケロのガチ厳選</span>
          </div>
          <h3 class="text-sm md:text-base font-black leading-snug">
            デパコスに1万円払う前に！1,000円台の神プチプラ成分比較ランキング
          </h3>
          <p class="text-[11px] text-emerald-100">
            レチノール・ナイアシンアミド・ヒト型セラミド配合の科学的根拠ある名品だけをピックアップ
          </p>
        </div>
        <a href="/articles/retinol-puchipura-hikaku" class="shrink-0 px-4 py-2.5 bg-white hover:bg-emerald-50 text-emerald-700 font-black text-xs rounded-xl shadow transition transform hover:scale-105 flex items-center gap-1.5">
          <span>殿堂入り比較を見る →</span>
        </a>
      </div>

      {NINJA_AD_SCRIPT}

      <!-- 物販アフィリエイトカード（高成約導線） -->
      {affiliate_card}

      <!-- 一次情報・公的/業界データベース引用元（E-E-A-T対策） -->
      <div class="p-4 bg-slate-50 border border-slate-200 rounded-2xl text-xs space-y-1.5">
        <div class="font-bold text-slate-800">🔬 一次情報・化粧品成分リファレンス</div>
        <p class="text-slate-500 leading-relaxed">当ラボの記事は、薬機法（旧薬事法）および化粧品全成分表示ルールに基づき、以下の公的機関・業界団体の公開情報を参照して作成しています。</p>
        <div class="flex flex-wrap gap-3 pt-1">
          <a href="https://www.jcia.org/" target="_blank" rel="noopener noreferrer" class="text-emerald-700 hover:underline font-medium">
            日本化粧品工業連合会（JCIA）成分表示名称 ↗
          </a>
          <a href="https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/keshouhin/index.html" target="_blank" rel="noopener noreferrer" class="text-emerald-700 hover:underline font-medium">
            厚生労働省「化粧品・医薬部外品情報」 ↗
          </a>
        </div>
      </div>

      {IKERO_AUTHOR_CARD}

      {NINJA_AD_SCRIPT}

      <!-- シェア & フォロー & 戻る -->
      <div class="pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
        <a href="/" class="text-xs font-bold text-emerald-700 hover:text-emerald-800 flex items-center gap-1">
          ← 記事一覧に戻る
        </a>
        <div class="flex items-center gap-2">
          <a href="https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_share_url}" target="_blank" rel="noopener noreferrer" class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-sm transition">
            <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            Xでシェア
          </a>
          <a href="https://x.com/ikero_lab" target="_blank" rel="noopener noreferrer" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-sm transition">
            🦊 @ikero_lab をフォロー
          </a>
        </div>
      </div>

      <!-- 🔥 サイト内回遊（PV倍増用・関連成分記事レコメンド） -->
      <section class="pt-6 border-t border-rose-100 space-y-3">
        <h3 class="text-sm md:text-base font-black text-slate-900 flex items-center gap-1.5">
          <span>🔥</span> あわせて読みたい！今もっとも読まれている成分解析
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {related_html}
        </div>
      </section>

      <!-- 🐧 姉妹サイト相互送客カード -->
      <div class="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="text-xs space-y-1">
          <span class="px-2 py-0.5 rounded bg-blue-600 text-white font-bold text-[10px]">姉妹メディア人気記事</span>
          <div class="font-bold text-slate-900 text-sm">🐧 公的ライフハック速報 by ほぽりん</div>
          <div class="text-slate-600">ドラッグストアの市販薬レシートで税金が戻る「セルフメディケーション税制」や給付金まとめ！</div>
        </div>
        <a href="https://hoporin.lilipat-cosme-bayarts.com" target="_blank" rel="noopener" class="shrink-0 px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition">
          お得制度を見る →
        </a>
      </div>

    </article>
  </main>

  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_ARTICLES_DIR, f"{slug}.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"Built article: dist/articles/{slug}")

def build_home_page(articles):
    cards_html = []
    for art in articles:
        cards_html.append(f"""
        <a href="/articles/{art['slug']}" class="group bg-white rounded-2xl p-5 border border-rose-100 hover:border-emerald-300 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
          <div class="space-y-2">
            <div class="flex items-center justify-between text-xs text-slate-400">
              <span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
                {art.get('category', '成分解説')}
              </span>
              <time datetime="{art['date']}">{art['date']}</time>
            </div>
            <h3 class="text-base font-bold text-slate-900 group-hover:text-emerald-700 transition leading-snug">
              {art['title']}
            </h3>
            <p class="text-xs text-slate-600 line-clamp-2 leading-relaxed">
              {art['summary']}
            </p>
          </div>
          <div class="mt-4 pt-3 border-t border-slate-50 flex items-center justify-between text-[11px] text-emerald-700 font-semibold">
            <span>成分解析を読む →</span>
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
  <link rel="alternate" type="application/rss+xml" title="イケロのコスメ成分ラボ RSS" href="/rss.xml">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="イケロのコスメ成分ラボ">
  <meta property="og:title" content="{SITE_TITLE}">
  <meta property="og:description" content="{SITE_DESCRIPTION}">
  <meta property="og:url" content="{SITE_URL}/">
  <meta property="og:image" content="{SITE_URL}/assets/ikero_banner.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@ikero_lab">
  <meta name="twitter:title" content="{SITE_TITLE}">
  <meta name="twitter:description" content="{SITE_DESCRIPTION}">
  <meta name="twitter:image" content="{SITE_URL}/assets/ikero_banner.jpg">
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3133098627249534" crossorigin="anonymous"></script>
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#fafafa] text-slate-800 antialiased font-sans">
  {get_header("home")}

  <!-- ヒーローセクション -->
  <section class="relative bg-gradient-to-b from-rose-50/60 to-transparent py-10 border-b border-rose-100">
    <div class="max-w-4xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-6">
      <div class="space-y-3 max-w-xl text-center md:text-left">
        <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold border border-emerald-300">
          <span>🔬</span> コスメコンシェルジュインストラクター＆成分スペシャリスト監修
        </div>
        <h1 class="text-2xl md:text-3xl font-black text-slate-900 leading-tight">
          高いデパコスと何が違う？<br>
          <span class="text-emerald-600">成分で選ぶ、本当に効くプチプラ。</span>
        </h1>
        <p class="text-xs md:text-sm text-slate-600 leading-relaxed font-medium">
          化粧品業界で長年勤務する現役専門家が、レチノール・ナイアシンアミド・セラミド等の注目成分を全成分表示と科学的根拠に基づいてガチ解説。広告に騙されないコスメ選びをサポートします。
        </p>
        <div class="flex flex-wrap gap-1.5 justify-center md:justify-start pt-1 text-[11px] font-semibold text-slate-700">
          <span class="px-2.5 py-1 rounded-full bg-white border border-emerald-200 shadow-2xs">🎓 コスメコンシェルジュインストラクター</span>
          <span class="px-2.5 py-1 rounded-full bg-white border border-emerald-200 shadow-2xs">🔬 化粧品成分検定スペシャリスト</span>
          <span class="px-2.5 py-1 rounded-full bg-white border border-emerald-200 shadow-2xs">⚖️ コスメ薬機法管理者</span>
          <span class="px-2.5 py-1 rounded-full bg-white border border-emerald-200 shadow-2xs">📜 景品表示法務検定</span>
        </div>
      </div>
      <div class="shrink-0 relative">
        <img src="/assets/ikero_avatar.jpg" alt="イケロ" class="w-28 h-28 md:w-36 md:h-36 rounded-3xl border-4 border-white shadow-xl object-cover">
        <span class="absolute -bottom-2 -right-2 px-2.5 py-1 bg-emerald-600 text-white rounded-full text-[11px] font-bold shadow">
          イケロ研究員 🦊
        </span>
      </div>
    </div>
  </section>

  <!-- メインコンテンツ -->
  <main class="max-w-4xl mx-auto px-4 py-8 space-y-6">
    {NINJA_AD_SCRIPT}

    <!-- 👑 イケロの殿堂入り・成分別プチプラ比較特設バナー -->
    <section class="p-6 bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-700 text-white rounded-3xl shadow-lg relative overflow-hidden">
      <div class="space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 text-emerald-100 text-xs font-black shadow-2xs">
            <span>👑 専門家ガチ厳選</span> 殿堂入りコスメ成分特集
          </span>
          <span class="text-xs text-emerald-100 font-bold">デパコス級プチプラ比較</span>
        </div>
        <div class="space-y-1">
          <h2 class="text-xl md:text-2xl font-black text-white leading-tight">
            1個3万円のデパコスと同成分？！<br class="hidden sm:inline">
            1,000円台で肌が変わる神プチプラ徹底比較BEST3
          </h2>
          <p class="text-xs md:text-sm text-emerald-50 leading-relaxed max-w-2xl">
            「高い化粧品ほど効果がある」は本当か？成分スペシャリストが全成分表示を解剖し、本当に買う価値のある1,000円台の医薬部外品・薬用プチプラだけを厳選。
          </p>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
          <a href="/articles/retinol-puchipura-hikaku" class="p-3.5 bg-white/10 hover:bg-white/20 backdrop-blur border border-white/20 rounded-2xl transition flex flex-col justify-between group">
            <div class="space-y-1">
              <span class="text-[10px] font-black px-2 py-0.5 rounded bg-emerald-400 text-slate-950">ハリ・シワ改善</span>
              <h3 class="text-xs font-bold text-white group-hover:text-emerald-200">ピュアレチノール神プチプラ比較</h3>
              <p class="text-[10px] text-emerald-100 line-clamp-2">無印 vs なめらか本舗の純粋レチノール配合率をガチ検証</p>
            </div>
            <span class="text-[11px] font-bold text-yellow-300 mt-2">比較を読む →</span>
          </a>
          <a href="/articles/niacinamide-whitening-dupe" class="p-3.5 bg-white/10 hover:bg-white/20 backdrop-blur border border-white/20 rounded-2xl transition flex flex-col justify-between group">
            <div class="space-y-1">
              <span class="text-[10px] font-black px-2 py-0.5 rounded bg-teal-300 text-slate-950">美白・くすみ</span>
              <h3 class="text-xs font-bold text-white group-hover:text-teal-200">ナイアシンアミド5%配合神3選</h3>
              <p class="text-[10px] text-emerald-100 line-clamp-2">デパコス激似とバズった1,000円台の医薬部外品を厳選</p>
            </div>
            <span class="text-[11px] font-bold text-yellow-300 mt-2">比較を読む →</span>
          </a>
          <a href="/articles/ceramide-skin-barrier-guide" class="p-3.5 bg-white/10 hover:bg-white/20 backdrop-blur border border-white/20 rounded-2xl transition flex flex-col justify-between group">
            <div class="space-y-1">
              <span class="text-[10px] font-black px-2 py-0.5 rounded bg-cyan-300 text-slate-950">冬の重度乾燥</span>
              <h3 class="text-xs font-bold text-white group-hover:text-cyan-200">ヒト型セラミド名品化粧水</h3>
              <p class="text-[10px] text-emerald-100 line-clamp-2">角質バリアを立て直すドラッグストアで買える名品</p>
            </div>
            <span class="text-[11px] font-bold text-yellow-300 mt-2">比較を読む →</span>
          </a>
        </div>
      </div>
    </section>

    <div class="flex items-center justify-between">
      <h2 class="text-lg font-bold text-slate-900 flex items-center gap-2">
        <span>✨</span> 最新の成分解析・プチプラ比較速報
      </h2>
      <span class="text-xs text-slate-500 font-medium">{len(articles)}件の記事</span>
    </div>

    <!-- 記事グリッド -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {''.join(cards_html)}
    </div>

    <!-- 姉妹店クロス送客バナー -->
    <section class="p-5 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4">
      <div class="space-y-1">
        <span class="text-[11px] font-bold px-2 py-0.5 rounded bg-blue-600 text-white">姉妹メディアのご案内</span>
        <h3 class="text-sm md:text-base font-bold text-slate-900">🐧 公的ライフハック速報 by ほぽりん</h3>
        <p class="text-xs text-slate-600">申請しないと損する国の給付金・補助金・医療費控除を3秒図解で解説！</p>
      </div>
      <a href="https://hoporin.lilipat-cosme-bayarts.com" target="_blank" rel="noopener" class="shrink-0 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl shadow-sm transition">
        公的ライフハック速報を見る →
      </a>
    </section>

    {NINJA_AD_SCRIPT}
  </main>

  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_DIR, "index.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(home_html)
    print("Built index: dist/index.html")

def build_about_page():
    about_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>イケロについて・監修者プロフィール | イケロのコスメ成分ラボ</title>
  <meta name="description" content="知恵の白キツネ研究員「イケロ」の運営方針と監修者プロフィール。化粧品業界で長年勤務し、コスメコンシェルジュインストラクター・化粧品成分検定スペシャリスト・コスメ薬機法管理者・景品表示法務検定資格者が科学的エビデンスに基づいて忖度なし監修。">
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3133098627249534" crossorigin="anonymous"></script>
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#fafafa] text-slate-800 antialiased font-sans">
  {get_header("about")}

  <main class="max-w-3xl mx-auto px-4 py-8">
    <div class="bg-white rounded-3xl p-6 md:p-10 border border-rose-100 shadow-sm space-y-8">
      
      <!-- メインヘッダー -->
      <div class="text-center space-y-3 pb-6 border-b border-slate-100">
        <img src="/assets/ikero_avatar.jpg" alt="イケロ" class="w-28 h-28 rounded-full border-4 border-emerald-400 mx-auto shadow-md object-cover">
        <h1 class="text-2xl font-black text-slate-900">知恵の白キツネ研究員「イケロ」</h1>
        <p class="text-xs md:text-sm text-emerald-800 font-bold">コスメ成分アナリスト / 科学的スキンケアアドバイザー / 薬機法・景表法コンプライアンス監修</p>
        <div class="pt-2">
          <a href="https://x.com/ikero_lab" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-full text-xs font-bold shadow transition">
            <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            X (@ikero_lab) をフォロー
          </a>
        </div>
      </div>

      <!-- 監修者・運営者の専門資格・経歴（最高峰の箔・E-E-A-T） -->
      <section class="space-y-4">
        <div class="flex items-center gap-2 border-b-2 border-emerald-400 pb-2">
          <span class="text-lg">🎓</span>
          <h2 class="text-lg font-black text-slate-900">監修者プロフィール＆保有専門資格</h2>
        </div>
        
        <div class="bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-50 border border-emerald-200 rounded-2xl p-5 space-y-4">
          <div>
            <div class="text-xs font-bold text-emerald-900 uppercase tracking-wider mb-1">実務経歴</div>
            <p class="text-xs md:text-sm text-slate-700 leading-relaxed font-medium">
              化粧品業界で長年にわたり勤務。化粧品の処方開発現場、商品企画、マーケティング、そして広告法務コンプライアンスの最前線に深く携わってまいりました。現場で培った「全成分表示の裏にある処方意図」「原価とブランド価格の構造」「医薬品・医薬部外品・化粧品の境界線」に関する生きた知見をベースに情報発信を行っています。
            </p>
          </div>

          <div>
            <div class="text-xs font-bold text-emerald-900 uppercase tracking-wider mb-2">保有資格・認定（公的・業界最高峰資格）</div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              
              <div class="p-3.5 bg-white rounded-xl border border-emerald-200 shadow-2xs space-y-1">
                <div class="flex items-center gap-1.5 text-emerald-800 font-bold text-xs">
                  <span>🥇</span>
                  <span>コスメコンシェルジュインストラクター</span>
                </div>
                <div class="text-[11px] text-slate-500 font-medium leading-relaxed">
                  日本化粧品検定協会認定の最上位指導者資格。化粧品の成分・効能・安全性に関する高度な専門知識を有し、指導を行うスペシャリスト。
                </div>
              </div>

              <div class="p-3.5 bg-white rounded-xl border border-emerald-200 shadow-2xs space-y-1">
                <div class="flex items-center gap-1.5 text-emerald-800 font-bold text-xs">
                  <span>🔬</span>
                  <span>化粧品成分検定スペシャリスト</span>
                </div>
                <div class="text-[11px] text-slate-500 font-medium leading-relaxed">
                  化粧品成分検定協会認定（1級合格者）。パッケージの全成分表示を読み解き、個々の成分の配合目的・効果・科学的エビデンスを客観分析。
                </div>
              </div>

              <div class="p-3.5 bg-white rounded-xl border border-emerald-200 shadow-2xs space-y-1">
                <div class="flex items-center gap-1.5 text-emerald-800 font-bold text-xs">
                  <span>⚖️</span>
                  <span>コスメ薬機法管理者</span>
                </div>
                <div class="text-[11px] text-slate-500 font-medium leading-relaxed">
                  医薬品医療機器等法（薬機法）に基づく化粧品・医薬部外品の効能効果表現および適正広告基準を熟知・管理する法務資格。
                </div>
              </div>

              <div class="p-3.5 bg-white rounded-xl border border-emerald-200 shadow-2xs space-y-1">
                <div class="flex items-center gap-1.5 text-emerald-800 font-bold text-xs">
                  <span>📜</span>
                  <span>景品表示法務検定資格者</span>
                </div>
                <div class="text-[11px] text-slate-500 font-medium leading-relaxed">
                  消費者庁所管の不当景品類及び不当表示防止法（景表法）の法務知識を有し、優良誤認・有利誤認等の不当表示を排除する専門資格。
                </div>
              </div>

            </div>
          </div>
        </div>
      </section>

      <!-- サイト理念・なぜイケロなのか -->
      <section class="space-y-3">
        <div class="flex items-center gap-2 border-b-2 border-emerald-400 pb-2">
          <span class="text-lg">🦊</span>
          <h2 class="text-lg font-black text-slate-900">「イケロのコスメ成分ラボ」立ち上げの背景</h2>
        </div>
        <div class="text-xs md:text-sm text-slate-600 leading-relaxed space-y-3">
          <p>
            世の中には「高いから効きそう」「SNSで有名人が紹介していたから」という理由だけで、高額な化粧品を買い続けている方が大勢います。<br>
            しかし、化粧品の真実は<strong>「パッケージ裏の全成分表示」</strong>にすべて書かれています。
          </p>
          <p>
            「イケロ」という名前は、知恵と知力を象徴する神秘の「白狐（キツネ）」と、古代ギリシャの知恵と医学の賢者「ケイロン」に由来します。<br>
            ブランドの過剰な宣伝広告やインフルエンサーのステマに惑わされることなく、<strong>「科学的根拠（エビデンス）と成分濃度に基づいて、本当に肌を変える価値のあるプチプラ名品」</strong>を発掘し、生活者の皆様の美容代を賢く最適化することをお約束します。
          </p>
        </div>
      </section>

      <!-- 執筆・比較・コンプライアンス方針 -->
      <section class="space-y-3">
        <div class="flex items-center gap-2 border-b-2 border-emerald-400 pb-2">
          <span class="text-lg">🛡️</span>
          <h2 class="text-lg font-black text-slate-900">成分解析＆広告コンプライアンス方針</h2>
        </div>
        <div class="bg-slate-50 rounded-2xl p-5 space-y-3 text-xs md:text-sm text-slate-700">
          <div>
            <div class="font-bold text-slate-900 mb-0.5">1. 一次情報・学術エビデンスの徹底</div>
            <p class="text-slate-600 text-xs leading-relaxed">
              厚生労働省、日本化粧品工業連合会（JCIA）、PubChem、各種皮膚科学論文等の客観的データに基づき、成分の作用機序を正しく解説します。
            </p>
          </div>
          <div>
            <div class="font-bold text-slate-900 mb-0.5">2. 薬機法・景品表示法の徹底遵守</div>
            <p class="text-slate-600 text-xs leading-relaxed">
              コスメ薬機法管理者および景品表示法務検定資格者の知見に基づき、誇大広告・虚偽表現・ステマを一切排除し、消費者の誤認を招かない誠実な表記を徹底します。
            </p>
          </div>
          <div>
            <div class="font-bold text-slate-900 mb-0.5">3. 広告主への忖度なし・中立な成分比較</div>
            <p class="text-slate-600 text-xs leading-relaxed">
              アフィリエイト報酬の多寡によって評価を曲げることは一切ありません。「有効成分の配合濃度」「基剤の処方設計」「コスパ」の3軸で真に優秀な製品のみを推奨します。
            </p>
          </div>
        </div>
      </section>

    </div>
  </main>

  {get_footer()}
</body>
</html>"""
    with open(os.path.join(DIST_DIR, "about.html"), "w", encoding="utf-8") as f:
        f.write(about_html)
    print("Built about: dist/about")

def build_privacy_page():
    privacy_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>プライバシーポリシー・広告開示 | イケロのコスメ成分ラボ</title>
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3133098627249534" crossorigin="anonymous"></script>
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#fafafa] text-slate-800 antialiased font-sans">
  {get_header("privacy")}

  <main class="max-w-3xl mx-auto px-4 py-8">
    <div class="bg-white rounded-3xl p-6 md:p-10 border border-rose-100 shadow-sm space-y-6">
      <h1 class="text-xl font-bold text-slate-900 border-b pb-3">プライバシーポリシー及び広告掲載に関する表記</h1>
      
      <div class="text-xs md:text-sm text-slate-600 space-y-4 leading-relaxed">
        <h2 class="font-bold text-slate-800 text-sm">1. 広告の配信について</h2>
        <p>当サイトでは、第三者配信事業者（Google AdSense、忍者AdMax、A8.net、楽天アフィリエイト、Amazonアソシエイト等）の広告サービスを利用しています。これらの広告配信事業者は、利用者の興味に応じた商品やサービスの広告を表示するため、Cookie（クッキー）を使用することがあります。</p>
        <p>Amazonのアソシエイトとして、イケロのコスメ成分ラボは適格販売により収入を得ています。</p>

        <h2 class="font-bold text-slate-800 text-sm">2. 免責事項</h2>
        <p>当サイトで掲載している化粧品成分や効果に関する情報は、執筆時点での科学的知見や公的文献に基づき作成しておりますが、効果には個人差があります。お肌に合わない場合は直ちに使用を中止し、皮膚科専門医等にご相談ください。</p>
      </div>
    </div>
  </main>

  {get_footer()}
</body>
</html>"""
    with open(os.path.join(DIST_DIR, "privacy.html"), "w", encoding="utf-8") as f:
        f.write(privacy_html)
    print("Built privacy: dist/privacy")

def build_seo_files(articles):
    urls = [f"  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>"]
    for art in articles:
        urls.append(f"  <url><loc>{SITE_URL}/articles/{art['slug']}</loc><lastmod>{art['date']}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>")
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    with open(os.path.join(DIST_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    robots_txt = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    with open(os.path.join(DIST_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots_txt)

    items = []
    for art in articles[:15]:
        items.append(f"    <item><title>{art['title']}</title><link>{SITE_URL}/articles/{art['slug']}</link><description>{art['summary']}</description><pubDate>{art['date']}</pubDate></item>")
    rss_xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{SITE_TITLE}</title><link>{SITE_URL}/</link><description>{SITE_DESCRIPTION}</description>\n' + "\n".join(items) + "\n</channel></rss>\n"
    with open(os.path.join(DIST_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

    # Google Search Console 所有権確認ファイル
    gsc_file = "google38f9457e5c7ef474.html"
    with open(os.path.join(DIST_DIR, gsc_file), "w", encoding="utf-8") as f:
        f.write(f"google-site-verification: {gsc_file}")

def main():
    print("Building Store 2: イケロのコスメ成分ラボ...")
    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    now_jst = datetime.now(JST)
    unlocked_slots = get_unlocked_slots_store2(now_jst)
    published_articles = [a for a in articles if is_article_unlocked_store2(a, now_jst)]
    print(f"🕒 [Store 2] 現在JST: {now_jst.strftime('%H:%M')} | 解放スロット: {unlocked_slots} | 公開記事数: {len(published_articles)}/{len(articles)}")

    # 1. 各記事ページ生成（全記事HTML）
    for art in articles:
        build_article_page(art)

    # 2. トップページ生成（解放済み記事のみ掲載）
    build_home_page(published_articles)

    # 3. 固定ページ＆SEOファイル生成
    build_about_page()
    build_privacy_page()
    build_seo_files(published_articles)

    print("✨ Successfully built Store 2 static site with OGP cards and SEO sitemaps in dist/!")

if __name__ == "__main__":
    main()
