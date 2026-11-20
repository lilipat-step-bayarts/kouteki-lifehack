#!/usr/bin/env python3
"""
オニゴンの夜更かしラボ (3号店) 静的Webサイトビルダースクリプト
・18歳以上年齢確認モーダル（DMM / FANZAアフィリエイト審査必須要件）完備
・新人紹介＆サムネイル図鑑ページ (/newcomers) 搭載
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

DMM_AFFILIATE_ID = os.environ.get("DMM_AFFILIATE_ID", "").strip() or "Onigon-001"
# 忍者AdMaxで「成人（アダルト属性・18禁サイト用）」として発行した3号店専用広告枠ID
ADULT_ADMAX_TAG_ID = os.environ.get("ADULT_ADMAX_TAG_ID", "").strip() or "510c352d44b5c4c8109a0972bbd6c310"
# ハッピーメール（公式マッチングアフィリエイト）
HAPPYMAIL_AFFILIATE_URL = os.environ.get("HAPPYMAIL_AFFILIATE_URL", "").strip() or "https://happymail.jp/?af31395501"


def get_adult_ad_unit(slot_type="top"):
    """
    3号店（18禁・深夜エンタメ）専用の大人向け広告ユニット。
    ・成人属性の忍者AdMaxタグ (510c352d44b5c4c8109a0972bbd6c310) ＋ 高CTRなR18特化バナーを表示。
    """
    admax_script_html = ""
    if ADULT_ADMAX_TAG_ID:
        admax_script_html = f"""
        <!-- admax -->
        <div class="mb-4 flex flex-col items-center justify-center min-h-[250px] bg-slate-950/60 rounded-xl p-2 border border-purple-500/20">
          <script src="https://adm.shinobi.jp/s/{ADULT_ADMAX_TAG_ID}"></script>
        </div>
        <!-- admax -->
        """

    if slot_type == "top":
        raw_url = "https://www.dmm.co.jp/dc/doujin/"
        target_url = build_fanza_link(raw_url)
        return f"""
        <!-- 18+ 大人向け特化リッチ広告枠 (TOP) -->
        <div class="my-6 p-4 md:p-5 bg-gradient-to-r from-fuchsia-950/90 via-purple-950/95 to-slate-900 rounded-2xl border border-fuchsia-500/50 shadow-xl relative overflow-hidden">
          <div class="flex items-center justify-between mb-2">
            <span class="text-[10px] px-2 py-0.5 rounded bg-rose-600 text-white font-black tracking-wider uppercase">AD / R18 SPECIAL PR</span>
            <span class="text-[11px] text-fuchsia-300 font-mono font-bold">🎧 無料試聴・ブラウザ試し読み対応</span>
          </div>
          {admax_script_html}
          <a href="{target_url}" target="_blank" rel="noopener noreferrer sponsored" class="group flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div class="space-y-1">
              <div class="text-sm md:text-base font-black text-white group-hover:text-fuchsia-300 transition flex items-center gap-1.5 flex-wrap">
                <span>🔥 【深夜限定セール】FANZA同人「バイノーラルASMR・専用CG・長編コミック」最大90%OFF！</span>
              </div>
              <p class="text-xs text-slate-300 leading-relaxed">
                10円セール＆初回購入クーポン配布中！ダウンロード不要でスマホのブラウザから今すぐ高画質ビューア＆無料体験版を楽しめる大人専用ストア
              </p>
            </div>
            <span class="shrink-0 px-4 py-2.5 rounded-xl bg-gradient-to-r from-fuchsia-600 to-rose-600 group-hover:from-fuchsia-500 group-hover:to-rose-500 text-white font-black text-xs shadow-lg shadow-fuchsia-950 transition">
              R18公式セールを見る ↗
            </span>
          </a>
        </div>
        """
    else:
        raw_url = "https://premium.dmm.com/"
        target_url = build_fanza_link(raw_url)
        return f"""
        <!-- 18+ 大人向け特化リッチ広告枠 (BOTTOM) -->
        <div class="my-6 p-4 md:p-5 bg-gradient-to-r from-indigo-950/95 via-purple-950/90 to-rose-950/90 rounded-2xl border border-purple-400/50 shadow-xl relative overflow-hidden">
          <div class="flex items-center justify-between mb-2">
            <span class="text-[10px] px-2 py-0.5 rounded bg-purple-600 text-white font-black tracking-wider uppercase">AD / 18+ STREAMING PR</span>
            <span class="text-[11px] text-amber-300 font-mono font-bold">💎 月額550円（税込）で対象作見放題</span>
          </div>
          {admax_script_html}
          <a href="{target_url}" target="_blank" rel="noopener noreferrer sponsored" class="group flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div class="space-y-1">
              <div class="text-sm md:text-base font-black text-white group-hover:text-amber-300 transition">
                <span>🎬 【大人向け見放題】DMMプレミアム加入で「FANZA TV」厳選2,000作品以上が追加料金ゼロ！</span>
              </div>
              <p class="text-xs text-slate-300 leading-relaxed">
                単品1本分以下のワンコイン価格で、人気専属女優の名作からバラエティまでスマホ・PC・TVアプリで深夜に見放題！
              </p>
            </div>
            <span class="shrink-0 px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-rose-600 group-hover:from-amber-400 group-hover:to-rose-500 text-white font-black text-xs shadow-lg transition">
              見放題ラインナップを見る ↗
            </span>
          </a>
        </div>
        """


def get_happymail_banner():
    """
    3号店（オニゴンの夜更かしラボ）専用の深夜マッチングPRユニット。
    ハッピーメール（無料会員登録・無料ポイント付与）への誘導で最大収益化を図る。
    """
    return f"""
    <!-- ハッピーメール 深夜マッチング特設PRカード -->
    <div class="my-8 p-5 md:p-6 bg-gradient-to-r from-rose-950/95 via-pink-950/90 to-purple-950/90 rounded-3xl border-2 border-rose-500/50 shadow-2xl shadow-rose-950/40 relative overflow-hidden">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-rose-600 text-white font-black tracking-wider uppercase shadow-sm">
            PR / 深夜のリアルマッチング
          </span>
          <span class="text-[11px] text-pink-300 font-bold flex items-center gap-1">
            <span>✨</span><span>会員数3,500万人突破・国内最大級</span>
          </span>
        </div>
        <span class="text-[11px] text-amber-300 font-mono font-black">🎁 無料登録で即P付与中</span>
      </div>

      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
        <div class="space-y-2">
          <h3 class="text-base md:text-lg font-black text-white leading-snug">
            画面の向こうだけじゃ物足りない夜に…！<br class="hidden sm:inline">
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-rose-300 via-pink-200 to-amber-200">
              今夜話せる相手が見つかる「ハッピーメール」無料お試し
            </span>
          </h3>
          <p class="text-xs text-slate-300 leading-relaxed max-w-2xl">
            「寂しい」「今から軽く飲みたい」「大人の関係希望」な女性が深夜にリアルタイム多数ログイン中！男性も<b class="text-rose-300">年齢確認だけで貰える無料ポイント</b>を使えば、課金ゼロで今夜すぐメッセージ送信可能。24時間365日有人監視でサクラも徹底排除。
          </p>
          <div class="flex items-center gap-3 text-[11px] text-slate-400 flex-wrap pt-1">
            <span class="flex items-center gap-1 text-emerald-400 font-bold">✓ 女性は完全無料</span>
            <span class="flex items-center gap-1 text-pink-300 font-bold">✓ 男性も無料ポイントでメッセージ可</span>
            <span class="flex items-center gap-1 text-sky-400 font-bold">✓ 24時間サポート＆身分証確認で安全</span>
            <a href="/articles/happymail-midnight-dating-guide" class="text-fuchsia-300 underline hover:text-fuchsia-200 font-bold">オニゴンの攻略記事を読む →</a>
          </div>
        </div>

        <div class="shrink-0 flex flex-col sm:flex-row lg:flex-col gap-2">
          <a href="{HAPPYMAIL_AFFILIATE_URL}" target="_blank" rel="noopener noreferrer sponsored" class="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl bg-gradient-to-r from-rose-500 via-pink-500 to-fuchsia-600 hover:from-rose-400 hover:to-fuchsia-500 text-white font-black text-sm shadow-lg shadow-rose-950 transition transform hover:-translate-y-0.5">
            <span>💌</span>
            <span>無料ポイントを受け取る ↗</span>
          </a>
          <span class="text-[10px] text-center text-slate-400">※18歳未満利用不可・登録1分</span>
        </div>
      </div>
    </div>
    """


def build_fanza_link(raw_url):
    """DMM_AFFILIATE_ID が設定されていれば公式アフィリエイトリンクに変換、未設定なら公式ページへ直リンク"""
    if DMM_AFFILIATE_ID:
        encoded = urllib.parse.quote(raw_url, safe="")
        return f"https://al.dmm.co.jp/?lurl={encoded}&af_id={DMM_AFFILIATE_ID}&ch=link_tool&ch_id=link"
    return raw_url


fanza_interstitial_url = build_fanza_link("https://www.dmm.co.jp/dc/doujin/")

AGE_GATE_MODAL = f"""
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

<!-- 👿 オニゴン深夜特製・全面広告モーダル (上部＆下部バツボタン付きインタースティシャル広告) -->
<div id="onigon-interstitial-modal" class="fixed inset-0 z-[90] hidden items-center justify-center bg-black/85 backdrop-blur-md p-3 sm:p-5 overflow-y-auto">
  <div class="relative max-w-lg w-full bg-slate-900 border-2 border-fuchsia-500/80 rounded-3xl shadow-2xl shadow-fuchsia-950/90 text-left my-auto overflow-hidden">
    
    <!-- ✕ 上部フローティングバツボタン（スマホで最も押しやすい右上配置） -->
    <button onclick="closeInterstitialAd()" aria-label="広告を閉じる" class="absolute top-2.5 right-2.5 sm:top-3.5 sm:right-3.5 w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-slate-800/90 hover:bg-slate-700 text-white border-2 border-fuchsia-400 flex items-center justify-center font-black text-base shadow-xl cursor-pointer z-30 transition transform hover:scale-110 active:scale-95">
      ✕
    </button>

    <!-- 上部ヘッダーバー（PR表記 ＆ 上部バツボタンテキスト） -->
    <div class="px-4 py-2.5 bg-slate-950 border-b border-purple-500/40 flex items-center justify-between text-xs pr-14">
      <div class="flex items-center gap-1.5 font-bold text-fuchsia-300">
        <span class="px-2 py-0.5 rounded bg-rose-600 text-white font-black text-[10px]">PR</span>
        <span>オニゴン特選・深夜限定スペシャルオファー</span>
      </div>
      <button onclick="closeInterstitialAd()" class="text-[11px] text-slate-400 hover:text-white underline font-medium cursor-pointer">
        ✕ 閉じる
      </button>
    </div>

    <!-- 広告コンテンツエリア -->
    <div class="p-4 sm:p-5 space-y-3.5">
      
      <!-- 忍者AdMax 成人向け広告枠（ビュー課金） -->
      <div class="flex flex-col items-center justify-center min-h-[250px] bg-slate-950 rounded-2xl p-2 border border-purple-500/30">
        <span class="text-[9px] text-slate-500 mb-1">スポンサードリンク</span>
        <!-- admax -->
        <script src="https://adm.shinobi.jp/s/{ADULT_ADMAX_TAG_ID}"></script>
        <!-- admax -->
      </div>

      <!-- 高成約・深夜限定成約カード 1: FANZA同人セール -->
      <a href="{fanza_interstitial_url}" target="_blank" rel="noopener noreferrer sponsored" class="block p-3.5 rounded-2xl bg-gradient-to-r from-fuchsia-950 via-purple-900 to-slate-900 border border-fuchsia-400/50 hover:border-fuchsia-300 transition group shadow-md">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[10px] px-2 py-0.5 rounded-full bg-fuchsia-600 text-white font-black">FANZA 18+</span>
          <span class="text-[10px] text-amber-300 font-bold">10円〜最大90%OFF ↗</span>
        </div>
        <div class="text-xs sm:text-sm font-black text-white group-hover:text-fuchsia-300 transition leading-snug">
          🔥 【深夜限定】バイノーラルASMR・同人コミック・動画セール会場
        </div>
        <p class="text-[11px] text-slate-300 mt-1 line-clamp-1">
          ダウンロード不要・スマホのブラウザで今すぐ試聴＆試し読み可能！
        </p>
      </a>

      <!-- 高成約・深夜限定成約カード 2: ハッピーメール -->
      <a href="{HAPPYMAIL_AFFILIATE_URL}" target="_blank" rel="noopener noreferrer sponsored" class="block p-3.5 rounded-2xl bg-gradient-to-r from-rose-950 via-pink-900 to-slate-900 border border-rose-400/50 hover:border-rose-300 transition group shadow-md">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[10px] px-2 py-0.5 rounded-full bg-rose-600 text-white font-black">無料マッチング</span>
          <span class="text-[10px] text-pink-300 font-bold">登録1分・即P付与 ↗</span>
        </div>
        <div class="text-xs sm:text-sm font-black text-white group-hover:text-pink-300 transition leading-snug">
          💌 今夜話せる相手が見つかる「ハッピーメール」（無料ポイント配布中）
        </div>
        <p class="text-[11px] text-slate-300 mt-1 line-clamp-1">
          会員数3,500万人突破！男性も無料ポイントでメッセージ送信可能
        </p>
      </a>

    </div>

    <!-- ✕ 下部バツボタン（全幅の大型クローズボタン） -->
    <div class="p-3 bg-slate-950/80 border-t border-purple-500/30">
      <button onclick="closeInterstitialAd()" class="w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-2xl text-xs sm:text-sm font-black transition flex items-center justify-center gap-2 cursor-pointer border border-slate-700 shadow-md active:bg-slate-900">
        <span>✕ 広告を閉じてサイトを見る（Continue to Site）</span>
      </button>
    </div>

  </div>
</div>

<script>
  function showInterstitialAd() {{
    try {{
      if (sessionStorage.getItem('onigon_interstitial_closed') === 'true') {{
        return;
      }}
      var modal = document.getElementById('onigon-interstitial-modal');
      if (modal) {{
        modal.classList.remove('hidden');
        modal.classList.add('flex');
      }}
    }} catch(e) {{}}
  }}

  function closeInterstitialAd() {{
    try {{
      sessionStorage.setItem('onigon_interstitial_closed', 'true');
    }} catch(e) {{}}
    var modal = document.getElementById('onigon-interstitial-modal');
    if (modal) {{
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }}
  }}

  // 年齢確認モーダル制御
  (function() {{
    try {{
      if (localStorage.getItem('onigon_age_verified_v1') !== 'true') {{
        var modal = document.getElementById('onigon-age-gate');
        if (modal) {{
          modal.classList.remove('hidden');
          modal.classList.add('flex');
        }}
      }} else {{
        // すでに年齢確認済みの場合は、1秒後に全面広告をポップアップ
        setTimeout(showInterstitialAd, 1000);
      }}
    }} catch (e) {{}}
  }})();

  function confirmAgeGate() {{
    try {{
      localStorage.setItem('onigon_age_verified_v1', 'true');
    }} catch (e) {{}}
    var modal = document.getElementById('onigon-age-gate');
    if (modal) {{
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }}
    // 年齢確認完了後、スムーズに全面広告を表示
    setTimeout(showInterstitialAd, 600);
  }}

  // ESCキーでも閉じられる親切設計
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{
      closeInterstitialAd();
    }}
  }});
</script>
"""


def get_header(current_page="home"):
    return f"""
  <header class="sticky top-0 z-50 bg-slate-950/95 backdrop-blur-md border-b border-purple-500/30 shadow-lg">
    <div class="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
      <a href="/" class="flex items-center gap-2.5 group shrink-0">
        <img src="/assets/onigon_avatar.jpg" alt="オニゴン" class="w-10 h-10 rounded-full border-2 border-fuchsia-400 shadow-md object-cover group-hover:scale-105 transition-transform">
        <div>
          <div class="flex items-center gap-1.5">
            <span class="text-[10px] font-bold text-fuchsia-400 tracking-wider">MIDNIGHT CURATION LAB</span>
            <span class="text-[9px] px-1.5 py-0.2 rounded bg-rose-600/90 text-white font-black">R18</span>
          </div>
          <span class="text-base font-black text-white tracking-tight block">オニゴンの夜更かしラボ</span>
        </div>
      </a>
      <nav class="hidden md:flex items-center gap-2 text-xs font-bold text-slate-300">
        <a href="/" class="px-3 py-1.5 rounded-full transition {'bg-slate-800 text-fuchsia-400 border border-fuchsia-500/40' if current_page == 'home' else 'hover:text-fuchsia-400'}">🔥 新着速報</a>
        <a href="/sale-10yen" class="px-3 py-1.5 rounded-full border transition flex items-center gap-1 {'bg-amber-500 text-slate-950 border-amber-300 shadow-md font-black' if current_page == 'sale_10yen' else 'bg-amber-950/60 text-amber-300 border-amber-500/30 hover:bg-amber-900/80'}">
          <span>💰</span><span>10円・爆安セール</span>
        </a>
        <a href="/free-videos" class="px-3 py-1.5 rounded-full border transition flex items-center gap-1 {'bg-emerald-600 text-white border-emerald-400 shadow-md font-black' if current_page == 'free_videos' else 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30 hover:bg-emerald-900/80'}">
          <span>🎬</span><span>完全無料動画</span>
        </a>
        <a href="/manga-books" class="px-3 py-1.5 rounded-full border transition flex items-center gap-1 {'bg-sky-600 text-white border-sky-400 shadow-md font-black' if current_page == 'manga_books' else 'bg-sky-950/60 text-sky-300 border-sky-500/30 hover:bg-sky-900/80'}">
          <span>📚</span><span>電子コミック</span>
        </a>
        <a href="/asmr-ranking" class="px-3 py-1.5 rounded-full border transition flex items-center gap-1 {'bg-indigo-600 text-white border-indigo-400 shadow-md font-black' if current_page == 'asmr' else 'bg-indigo-950/60 text-indigo-300 border-indigo-500/30 hover:bg-indigo-900/80'}">
          <span>🎧</span><span>同人ASMR</span>
        </a>
        <a href="/newcomers" class="px-3 py-1.5 rounded-full border transition flex items-center gap-1 {'bg-fuchsia-600 text-white border-fuchsia-400 shadow-md font-black' if current_page == 'newcomers' else 'bg-purple-950/60 text-fuchsia-300 border-fuchsia-500/30 hover:bg-purple-900/80'}">
          <span>🌟</span><span>新人図鑑</span>
        </a>
        <a href="{HAPPYMAIL_AFFILIATE_URL}" target="_blank" rel="noopener noreferrer sponsored" class="px-3 py-1.5 rounded-full border border-rose-500/50 bg-rose-950/80 text-rose-300 hover:bg-rose-900 transition flex items-center gap-1 shadow-sm font-black">
          <span>💌</span><span>深夜マッチング(無料P)</span>
        </a>
        <a href="https://x.com/Onigon_yfks" target="_blank" rel="noopener noreferrer" class="px-3 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 text-fuchsia-300 border border-purple-500/40 transition flex items-center gap-1">
          <span>𝕏</span><span>@Onigon_yfks</span>
        </a>
      </nav>
    </div>
    <!-- スマホ用 横スクロール特設タブバー（回遊率アップ用） -->
    <div class="md:hidden border-t border-slate-800/80 bg-slate-900/90 px-3 py-2 flex items-center gap-2 overflow-x-auto text-[11px] font-bold whitespace-nowrap">
      <a href="/" class="px-3 py-1 rounded-full {'bg-fuchsia-600 text-white' if current_page == 'home' else 'bg-slate-800 text-slate-300'}">🔥 トップ速報</a>
      <a href="/sale-10yen" class="px-3 py-1 rounded-full {'bg-amber-400 text-slate-950 font-black' if current_page == 'sale_10yen' else 'bg-amber-950/80 text-amber-300 border border-amber-500/30'}">💰 10円・爆安</a>
      <a href="/free-videos" class="px-3 py-1 rounded-full {'bg-emerald-600 text-white font-black' if current_page == 'free_videos' else 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/30'}">🎬 完全無料</a>
      <a href="/manga-books" class="px-3 py-1 rounded-full {'bg-sky-600 text-white font-black' if current_page == 'manga_books' else 'bg-sky-950/80 text-sky-300 border border-sky-500/30'}">📚 電子コミック</a>
      <a href="/asmr-ranking" class="px-3 py-1 rounded-full {'bg-indigo-600 text-white' if current_page == 'asmr' else 'bg-indigo-950 text-indigo-300 border border-indigo-500/30'}">🎧 同人ASMR</a>
      <a href="/newcomers" class="px-3 py-1 rounded-full {'bg-fuchsia-600 text-white' if current_page == 'newcomers' else 'bg-purple-950 text-fuchsia-300 border border-fuchsia-500/30'}">🌟 新人図鑑</a>
      <a href="{HAPPYMAIL_AFFILIATE_URL}" target="_blank" rel="noopener noreferrer sponsored" class="px-3 py-1 rounded-full bg-rose-950 text-rose-300 border border-rose-500/50 font-black">💌 出会い(無料P)</a>
      <a href="https://x.com/Onigon_yfks" target="_blank" rel="noopener noreferrer" class="px-3 py-1 rounded-full bg-slate-800 text-fuchsia-300 border border-purple-500/30">𝕏 @Onigon_yfks</a>
    </div>
  </header>
"""


def get_hub_banners(current_page="home"):
    """全ページ下部に配置する4大ジャンル特設コーナー回遊カード"""
    return """
    <section class="my-8 space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm md:text-base font-black text-white flex items-center gap-2">
          <span>👿</span><span>オニゴンの4大特設コーナー（日替わり厳選ハブ）</span>
        </h3>
        <span class="text-[11px] text-fuchsia-400 font-bold">4大ジャンル回遊</span>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <a href="/sale-10yen" class="group p-4 rounded-2xl bg-gradient-to-br from-amber-950/80 to-slate-900 border border-amber-500/40 hover:border-amber-400 transition flex flex-col justify-between shadow-lg">
          <div class="space-y-1.5">
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-amber-500 text-slate-950 font-black">💰 Day 1 特設</span>
            <h4 class="text-sm font-black text-white group-hover:text-amber-300">10円動画＆爆安セール</h4>
            <p class="text-[11px] text-slate-300 leading-relaxed">缶コーヒー未満の10円動画・同人10円・ワンコイン500円名作</p>
          </div>
          <span class="mt-3 text-[11px] font-bold text-amber-300 group-hover:translate-x-1 transition inline-block">爆安セールを見る →</span>
        </a>

        <a href="/free-videos" class="group p-4 rounded-2xl bg-gradient-to-br from-emerald-950/80 to-slate-900 border border-emerald-500/40 hover:border-emerald-400 transition flex flex-col justify-between shadow-lg">
          <div class="space-y-1.5">
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-600 text-white font-black">🎬 Day 2 特設</span>
            <h4 class="text-sm font-black text-white group-hover:text-emerald-300">完全無料動画＆サンプル</h4>
            <p class="text-[11px] text-slate-300 leading-relaxed">登録不要・クレカ不要！0円で今すぐ観られる公式長尺動画</p>
          </div>
          <span class="mt-3 text-[11px] font-bold text-emerald-300 group-hover:translate-x-1 transition inline-block">無料動画を見る →</span>
        </a>

        <a href="/manga-books" class="group p-4 rounded-2xl bg-gradient-to-br from-sky-950/80 to-slate-900 border border-sky-500/40 hover:border-sky-400 transition flex flex-col justify-between shadow-lg">
          <div class="space-y-1.5">
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-sky-600 text-white font-black">📚 Day 3 特設</span>
            <h4 class="text-sm font-black text-white group-hover:text-sky-300">電子コミック・無料試し読み</h4>
            <p class="text-[11px] text-slate-300 leading-relaxed">1巻まるごと無料！深夜ベッドでスマホ即読み＆90%OFFクーポン</p>
          </div>
          <span class="mt-3 text-[11px] font-bold text-sky-300 group-hover:translate-x-1 transition inline-block">電子コミックを見る →</span>
        </a>

        <a href="/asmr-ranking" class="group p-4 rounded-2xl bg-gradient-to-br from-indigo-950/80 to-slate-900 border border-indigo-500/40 hover:border-indigo-400 transition flex flex-col justify-between shadow-lg">
          <div class="space-y-1.5">
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-600 text-white font-black">🎧 Day 4 特設</span>
            <h4 class="text-sm font-black text-white group-hover:text-indigo-300">同人ASMR＆大型新人図鑑</h4>
            <p class="text-[11px] text-slate-300 leading-relaxed">100万円マイクKU100寝落ち音声＆今月のSSR注目ルーキー</p>
          </div>
          <span class="mt-3 text-[11px] font-bold text-indigo-300 group-hover:translate-x-1 transition inline-block">ASMR・新人を見る →</span>
        </a>
      </div>
    </section>
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
        <a href="/newcomers" class="hover:text-fuchsia-400 font-bold text-fuchsia-300">🌟 新人図鑑・サムネ</a>
        <span>•</span>
        <a href="/asmr-ranking" class="hover:text-indigo-400 font-bold text-indigo-300">🎧 同人ASMRランキング</a>
        <span>•</span>
        <a href="/sale-500yen" class="hover:text-amber-400 font-bold text-amber-300">💰 500円セール神作</a>
        <span>•</span>
        <a href="https://x.com/Onigon_yfks" target="_blank" rel="noopener noreferrer" class="hover:text-fuchsia-400 font-bold text-fuchsia-300">𝕏 公式X (@Onigon_yfks)</a>
        <span>•</span>
        <a href="/about" class="hover:text-fuchsia-400">運営者情報（オニゴン）</a>
        <span>•</span>
        <a href="/privacy" class="hover:text-fuchsia-400">プライバシーポリシー・広告開示</a>
        <span>•</span>
        <a href="/sitemap.xml" class="hover:text-fuchsia-400">サイトマップ</a>
      </div>
      <div class="text-[11px] text-slate-600 font-mono">
        © 2026 Onigon Night Lab (@Onigon_yfks). All Rights Reserved. (18+ Adult Only)
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
        target_url = item["affiliate_url"].replace("Onigon-990", "Onigon-001")
    elif item.get("fanza_category") == "doujin":
        raw_url = f"https://www.dmm.co.jp/dc/doujin/-/list/narrow/=/word={search_kw}/"
        target_url = build_fanza_link(raw_url)
    else:
        raw_url = f"https://www.dmm.co.jp/digital/videoa/-/list/search/=/?searchstr={search_kw}"
        target_url = build_fanza_link(raw_url)

    # サムネイルヘッダー部分（タップでリンク先に移動できるように <a> タグ化）
    if pkg_url:
        thumb_html = f"""
        <a href="{target_url}" target="_blank" rel="noopener noreferrer sponsored" class="block relative h-60 w-full overflow-hidden bg-slate-950 cursor-pointer group/thumb">
          <img src="{pkg_url}" alt="{stage_name}" loading="lazy" class="w-full h-full object-cover object-top group-hover/thumb:scale-105 transition-transform duration-500">
          <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent"></div>
          <div class="absolute top-3 left-3 flex items-center gap-1.5">
            <span class="px-2.5 py-1 rounded-full text-[11px] font-black bg-fuchsia-600 text-white shadow-lg">{badge_text}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-black bg-amber-400 text-slate-950">RANK {rank}</span>
          </div>
          <div class="absolute bottom-3 left-3 right-3 flex items-end justify-between">
            <div>
              <span class="text-[11px] text-fuchsia-300 font-bold block">{debut_month} / {label_genre}</span>
              <h3 class="text-lg font-black text-white drop-shadow group-hover/thumb:text-fuchsia-300 transition-colors">{stage_name}</h3>
            </div>
            <span class="px-2 py-1 rounded-lg bg-slate-900/90 border border-amber-400/50 text-amber-300 text-xs font-mono font-bold">★ {rating}</span>
          </div>
          <div class="absolute top-3 right-3 px-2 py-1 rounded-lg bg-black/60 backdrop-blur text-[10px] text-white/90 font-bold flex items-center gap-1 border border-white/20">
            <span>タップで再生</span><span>↗</span>
          </div>
        </a>
        """
    else:
        # プレースホルダー図鑑カード（タップでリンク先に移動）
        thumb_html = f"""
        <a href="{target_url}" target="_blank" rel="noopener noreferrer sponsored" class="block relative h-52 w-full overflow-hidden bg-gradient-to-br {gradient} p-4 flex flex-col justify-between cursor-pointer group/thumb">
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
              ★ {rating} / 5.0
            </span>
          </div>
          <div class="relative z-10 space-y-1">
            <div class="text-[11px] font-bold text-fuchsia-200 flex items-center gap-1.5">
              <span>🗓️ {debut_month}</span>
              <span>•</span>
              <span>{label_genre}</span>
            </div>
            <h3 class="text-lg md:text-xl font-black text-white leading-tight drop-shadow group-hover/thumb:text-fuchsia-300 transition-colors">{stage_name}</h3>
          </div>
        </a>
        """

    tags_html = " ".join([
        f'<span class="text-[11px] px-2 py-0.5 rounded-md bg-purple-950/90 text-purple-200 border border-purple-700/50 font-medium">#{t}</span>'
        for t in tags
    ])

    # サンプル画像ギャラリー（各サムネイルもタップでリンク先に移動可能）
    sample_images = item.get("sample_images", [])
    samples_html = ""
    if sample_images:
        sample_thumbs = []
        for s_url in sample_images[:4]:
            sample_thumbs.append(f"""
            <a href="{target_url}" target="_blank" rel="noopener noreferrer sponsored" class="block h-14 rounded-lg overflow-hidden border border-slate-800 hover:border-fuchsia-400 transition hover:scale-105">
              <img src="{s_url}" alt="サンプル" loading="lazy" class="w-full h-full object-cover">
            </a>
            """)
        samples_html = f"""
        <div class="space-y-1.5">
          <span class="text-[10px] font-bold text-slate-400">📸 サンプル画像（タップで高画質プレビュー）</span>
          <div class="grid grid-cols-4 gap-1.5">
            {''.join(sample_thumbs)}
          </div>
        </div>
        """

    return f"""
    <div class="group bg-slate-900/95 rounded-3xl border border-purple-500/30 hover:border-fuchsia-400/70 overflow-hidden shadow-xl transition-all flex flex-col justify-between">
      <div>
        {thumb_html}
        <div class="p-5 space-y-4">
          <a href="{target_url}" target="_blank" rel="noopener noreferrer sponsored" class="block text-xs md:text-sm font-bold text-fuchsia-200 hover:text-white transition leading-snug">
            「{catchcopy}」
          </a>
          <div class="flex flex-wrap gap-1.5">
            {tags_html}
          </div>
          {samples_html}
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
        <a href="/newcomers" class="py-3 px-4 bg-slate-800 hover:bg-slate-700 border border-purple-500/40 text-fuchsia-300 text-center rounded-xl font-bold text-xs transition flex items-center justify-center gap-1.5">
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
        <a href="/articles/{r_art['slug']}" class="block p-4 bg-slate-900 hover:bg-purple-950/60 border border-purple-800/40 hover:border-fuchsia-500/60 rounded-2xl transition group">
          <div class="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span class="px-2 py-0.5 rounded bg-purple-950 text-fuchsia-300 font-bold border border-purple-700/50">{r_art.get('category', '深夜レビュー')}</span>
            <span>{r_art['date']}</span>
          </div>
          <div class="text-xs md:text-sm font-bold text-white group-hover:text-fuchsia-300 leading-snug">{r_art['title']}</div>
        </a>
        """

    article_url = f"{SITE_URL}/articles/{slug}"
    encoded_title = urllib.parse.quote(f"{article_meta['title']} #オニゴンの夜更かしラボ #FANZA #深夜の癒やし")
    encoded_share_url = urllib.parse.quote(article_url)

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="rating" content="adult">
  <title>{article_meta['title']} | オニゴンの夜更かしラボ</title>
  <meta name="description" content="{article_meta['summary']}">
  <link rel="canonical" href="{article_url}">
  <link rel="icon" type="image/jpeg" href="/assets/onigon_avatar.jpg">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="オニゴンの夜更かしラボ">
  <meta property="og:title" content="{article_meta['title']}">
  <meta property="og:description" content="{article_meta['summary']}">
  <meta property="og:url" content="{article_url}">
  <meta property="og:image" content="{SITE_URL}/assets/onigon_banner.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@Onigon_yfks">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    (function() {{
      var ua = navigator.userAgent || '';
      var isTwitter = /Twitter/i.test(ua) || /FBAN|FBAV|Instagram/i.test(ua);
      if (isTwitter) {{
        document.addEventListener('DOMContentLoaded', function() {{
          var guide = document.createElement('div');
          guide.id = 'x-inapp-guide';
          guide.className = 'bg-gradient-to-r from-purple-900 via-fuchsia-900 to-slate-900 text-white text-xs px-3 py-2.5 flex items-center justify-between shadow-md sticky top-0 z-50 border-b border-purple-500/40';
          guide.innerHTML = '<div class="flex items-center gap-1.5 font-medium leading-tight"><span>📱</span><span><b>全画面で開く</b>：中央の「⁝」から「Safariで開く」または画面を上にスワイプ</span></div><button onclick="this.parentElement.remove()" class="ml-2 font-bold px-2 py-0.5 bg-white/20 hover:bg-white/30 rounded text-[11px] shrink-0">閉じる ✕</button>';
          document.body.insertBefore(guide, document.body.firstChild);
        }});
      }}
    }})();
  </script>
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

      <div class="prose max-w-none">
        {body_html}
      </div>

      {get_adult_ad_unit("top")}

      {cta_card}

      {get_happymail_banner()}

      {get_adult_ad_unit("bottom")}

      <div class="pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
        <a href="/" class="text-xs font-bold text-fuchsia-400 hover:text-fuchsia-300">← トップページへ戻る</a>
        <div class="flex items-center gap-2.5">
          <a href="/newcomers" class="px-4 py-2 bg-purple-900/80 hover:bg-purple-800 text-fuchsia-200 border border-fuchsia-500/40 rounded-xl text-xs font-bold transition">
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

      {get_hub_banners("article")}
    </article>
  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_ARTICLES_DIR, f"{slug}.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"Built article: /home/antigravity/lilipat-step-bayarts/kouteki-lifehack/store3/dist/articles/{slug}")


def build_newcomers_page(newcomers):
    cards_html = "\n".join([render_newcomer_card(item) for item in newcomers])

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="rating" content="adult">
  <title>【2026年最新】大型新人女優・注目ルーキー図鑑＆サムネイル一覧 | オニゴンの夜更かしラボ</title>
  <meta name="description" content="毎月デビューする大型専属新人女優や同人ASMRの新星サークルをオニゴンが徹底評価！ビジュアル・スタイル・没入感の3軸ステータスとサンプル導線まとめ。">
  <link rel="canonical" href="{SITE_URL}/newcomers">
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
    {get_adult_ad_unit("top")}

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
      <a href="/articles/newcomer-debut-spotlight-2026" class="shrink-0 px-5 py-3 bg-fuchsia-600 hover:bg-fuchsia-500 text-white rounded-xl text-xs font-black shadow-lg transition">
        攻略記事を読む →
      </a>
    </section>

    {get_hub_banners("newcomers")}
    {get_happymail_banner()}
    {get_adult_ad_unit("bottom")}
  </main>

  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_DIR, "newcomers.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"Built newcomers page: {out_file}")


def build_asmr_ranking_page(asmr_works):
    cards = []
    for item in asmr_works:
        kw = urllib.parse.quote(item.get("search_keyword", "ASMR バイノーラル"))
        raw_url = f"https://www.dmm.co.jp/dc/doujin/-/list/narrow/=/word={kw}/"
        target_url = build_fanza_link(raw_url)
        meters = item.get("meters", {"realism": 98, "comfort": 98, "sleep_induce": 98})
        tags_html = " ".join([
            f'<span class="text-[11px] px-2 py-0.5 rounded-md bg-indigo-950/90 text-indigo-200 border border-indigo-700/50 font-medium">#{t}</span>'
            for t in item.get("tags", [])
        ])
        cards.append(f"""
        <div class="group bg-slate-900/95 rounded-3xl border border-indigo-500/40 hover:border-indigo-400 overflow-hidden shadow-xl flex flex-col justify-between">
          <div>
            <!-- 音響スペクトラム＆マイクスぺックサムネイル（タップで試聴・公式ページへ） -->
            <a href="{target_url}" target="_blank" rel="noopener noreferrer sponsored" class="block relative h-48 w-full bg-gradient-to-br {item.get('theme_gradient', 'from-indigo-700 via-purple-800 to-slate-950')} p-5 flex flex-col justify-between overflow-hidden cursor-pointer group/thumb">
              <div class="flex items-center justify-between relative z-10">
                <span class="px-3 py-1 rounded-full text-xs font-black bg-amber-400 text-slate-950 shadow">👑 {item.get('rank', '殿堂入り')}</span>
                <span class="px-2.5 py-0.5 rounded-md bg-slate-950/70 text-indigo-200 text-[11px] font-mono border border-indigo-400/30">★ {item.get('rating', 4.9)} / 5.0</span>
              </div>
              <!-- 音響波形ビジュアル -->
              <div class="flex items-end justify-center gap-1 h-12 opacity-30 pointer-events-none">
                <div class="w-1.5 bg-white rounded-full h-5"></div>
                <div class="w-1.5 bg-white rounded-full h-10"></div>
                <div class="w-1.5 bg-white rounded-full h-7"></div>
                <div class="w-1.5 bg-white rounded-full h-12"></div>
                <div class="w-1.5 bg-white rounded-full h-8"></div>
                <div class="w-1.5 bg-white rounded-full h-11"></div>
                <div class="w-1.5 bg-white rounded-full h-6"></div>
                <div class="w-1.5 bg-white rounded-full h-9"></div>
                <div class="w-1.5 bg-white rounded-full h-4"></div>
              </div>
              <div class="relative z-10 space-y-1">
                <div class="text-[11px] text-indigo-200 font-bold flex items-center gap-2">
                  <span>🎙️ {item.get('mic_spec')}</span>
                </div>
                <h3 class="text-base md:text-lg font-black text-white leading-snug group-hover/thumb:text-cyan-300 transition-colors">{item.get('title')}</h3>
              </div>
              <div class="absolute top-3 right-3 px-2 py-1 rounded-lg bg-black/60 backdrop-blur text-[10px] text-white/90 font-bold flex items-center gap-1 border border-white/20">
                <span>タップで無料試聴</span><span>↗</span>
              </div>
            </a>

            <div class="p-5 space-y-4">
              <div class="flex items-center justify-between text-xs text-slate-300 bg-slate-950/80 px-3.5 py-2 rounded-xl border border-slate-800">
                <span>⏱️ {item.get('duration')}</span>
                <span class="text-amber-300 font-bold">{item.get('price_info')}</span>
              </div>
              <div class="flex flex-wrap gap-1.5">{tags_html}</div>

              <div class="bg-slate-950/80 rounded-2xl p-3.5 border border-slate-800 space-y-2 text-[11px]">
                <div class="flex items-center justify-between">
                  <span class="text-slate-400">🎙️ 吐息・ゼロ距離リアリティ</span>
                  <div class="w-32 bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div class="bg-gradient-to-r from-indigo-400 to-cyan-400 h-full" style="width: {meters.get('realism', 98)}%"></div>
                  </div>
                  <span class="font-mono font-bold text-cyan-300">{meters.get('realism', 98)}pt</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-slate-400">🪶 耳かき・マッサージ心地よさ</span>
                  <div class="w-32 bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div class="bg-gradient-to-r from-purple-400 to-fuchsia-400 h-full" style="width: {meters.get('comfort', 98)}%"></div>
                  </div>
                  <span class="font-mono font-bold text-fuchsia-300">{meters.get('comfort', 98)}pt</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-slate-400">🌙 脳とろ・寝落ち誘導度</span>
                  <div class="w-32 bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div class="bg-gradient-to-r from-amber-400 to-rose-400 h-full" style="width: {meters.get('sleep_induce', 98)}%"></div>
                  </div>
                  <span class="font-mono font-bold text-amber-300">{meters.get('sleep_induce', 98)}pt</span>
                </div>
              </div>

              <div class="flex items-start gap-2.5 text-xs text-slate-300 bg-indigo-950/30 p-3 rounded-xl border border-indigo-800/40">
                <img src="/assets/onigon_avatar.jpg" alt="オニゴン" class="w-8 h-8 rounded-full object-cover border border-indigo-400 shrink-0 mt-0.5">
                <p class="leading-relaxed">{item.get('onigon_review')}</p>
              </div>
            </div>
          </div>
          <div class="px-5 pb-5">
            <a href="{target_url}" target="_blank" rel="noopener noreferrer sponsored" class="w-full py-3 px-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-fuchsia-600 hover:from-indigo-500 hover:to-fuchsia-500 text-white text-center rounded-xl font-black text-xs shadow-lg transition flex items-center justify-center gap-2">
              <span>🎧 FANZA同人で無料体験版（試聴）＆詳細を見る</span>
              <span>↗</span>
            </a>
          </div>
        </div>
        """)

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="rating" content="adult">
  <title>【KU100バイノーラル】同人ASMR・耳かきボイス殿堂入りランキング | オニゴンの夜更かしラボ</title>
  <meta name="description" content="100万円超のダミーヘッドマイクNEUMANN KU100・3Dio Pro IIで収録された超高音質な同人ASMR・耳かき・添い寝ボイス作品をオニゴンが厳選比較！">
  <link rel="canonical" href="{SITE_URL}/asmr-ranking">
  <link rel="icon" type="image/jpeg" href="/assets/onigon_avatar.jpg">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased font-sans min-h-screen">
  {AGE_GATE_MODAL}
  {get_header("asmr")}

  <section class="relative bg-gradient-to-b from-indigo-950/80 via-slate-950 to-slate-950 py-10 border-b border-indigo-500/30">
    <div class="max-w-5xl mx-auto px-4 space-y-3">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950 text-indigo-300 text-xs font-bold border border-indigo-500/40">
        <span>🎧</span><span>イヤホン・ヘッドホン着用推奨（立体音響特設）</span>
      </div>
      <h1 class="text-2xl md:text-4xl font-black text-white leading-tight">
        深夜の脳とろ同人ASMR・耳かきボイス<br>
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-indigo-400 to-fuchsia-400">KU100 / 3Dio 収録の殿堂入りランキング</span>
      </h1>
      <p class="text-xs md:text-sm text-slate-300 max-w-3xl leading-relaxed">
        100万円超えのスタジオ機材「NEUMANN KU100」や「3Dio Free Space Pro II」で収録された、吐息の距離感と耳かきの心地よさが異次元な同人ボイス作品を厳選！まずは10分〜30分の無料体験版で鳥肌級の立体音響を体感してください。
      </p>
    </div>
  </section>

  <main class="max-w-5xl mx-auto px-4 py-8 space-y-8">
    {get_adult_ad_unit("top")}

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      {''.join(cards)}
    </div>

    {get_hub_banners("asmr")}
    {get_happymail_banner()}
    {get_adult_ad_unit("bottom")}
  </main>

  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_DIR, "asmr-ranking.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"Built ASMR ranking page: {out_file}")


def build_sale_10yen_page(articles, sale_picks):
    """Day 1 特設：10円動画＆爆安セール（ワンコイン500円・同人10円）ハブ"""
    cards = []
    for item in sale_picks:
        target_url = build_fanza_link(item.get("raw_url", "https://www.dmm.co.jp/digital/videoa/"))
        tags_html = " ".join([
            f'<span class="text-[11px] px-2 py-0.5 rounded-md bg-rose-950/90 text-rose-200 border border-rose-700/50 font-medium">#{t}</span>'
            for t in item.get("tags", [])
        ])
        cards.append(f"""
        <div class="bg-slate-900/95 rounded-3xl border border-rose-500/40 hover:border-amber-400 p-6 shadow-xl flex flex-col justify-between space-y-5 transition">
          <div class="space-y-3.5">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <span class="px-3 py-1 rounded-full text-xs font-black bg-rose-600 text-white">{item.get('category_badge')}</span>
              <span class="px-3 py-1 rounded-full text-xs font-black bg-amber-400 text-slate-950">{item.get('discount_rate')}</span>
            </div>
            <a href="{target_url}" target="_blank" rel="noopener noreferrer sponsored" class="block text-base md:text-lg font-black text-white hover:text-amber-300 transition-colors leading-snug">
              {item.get('title')} ↗
            </a>
            <div class="grid grid-cols-2 gap-2.5 bg-slate-950/90 p-3.5 rounded-2xl border border-slate-800 text-xs">
              <div>
                <span class="text-slate-400 block text-[10px]">セール目安価格</span>
                <span class="text-base font-black text-amber-300 font-mono">{item.get('sale_price')}</span>
                <span class="text-[10px] text-slate-500 line-through block">{item.get('normal_price')}</span>
              </div>
              <div>
                <span class="text-slate-400 block text-[10px]">ボリューム / 評価</span>
                <span class="text-xs font-bold text-white block">{item.get('runtime')}</span>
                <span class="text-[11px] text-fuchsia-300 font-bold block mt-0.5">{item.get('cost_perf_score')}</span>
              </div>
            </div>
            <div class="flex flex-wrap gap-1.5">{tags_html}</div>
            <div class="flex items-start gap-2.5 text-xs text-slate-300 bg-rose-950/30 p-3 rounded-xl border border-rose-800/40">
              <img src="/assets/onigon_avatar.jpg" alt="オニゴン" class="w-8 h-8 rounded-full object-cover border border-rose-400 shrink-0 mt-0.5">
              <p class="leading-relaxed">{item.get('onigon_tip')}</p>
            </div>
          </div>
          <a href="{target_url}" target="_blank" rel="noopener noreferrer sponsored" class="w-full py-3 px-4 bg-gradient-to-r from-rose-600 via-fuchsia-600 to-amber-500 hover:from-rose-500 hover:to-amber-400 text-white text-center rounded-xl font-black text-xs shadow-lg transition flex items-center justify-center gap-2">
            <span>🔥 公式セール対象ラインナップを確認する</span>
            <span>↗</span>
          </a>
        </div>
        """)

    # 10円・セール関連の記事ピックアップ
    sale_articles = [a for a in articles if "10円" in a.get("category", "") or "セール" in a.get("category", "")]
    sale_art_html = ""
    for a in sale_articles[:4]:
        sale_art_html += f"""
        <a href="/articles/{a['slug']}" class="p-4 rounded-2xl bg-slate-900/80 border border-amber-500/30 hover:border-amber-400 transition flex flex-col justify-between">
          <div class="space-y-1">
            <span class="text-[10px] font-mono text-amber-400 font-bold">{a['date']}</span>
            <h4 class="text-xs md:text-sm font-black text-white line-clamp-2">{a['title']}</h4>
          </div>
          <span class="text-[11px] text-amber-300 font-bold mt-2">オニゴンの解説を読む →</span>
        </a>
        """

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="rating" content="adult">
  <title>【最大90%OFF】FANZA 10円動画・同人10円＆500円セール神作まとめ | オニゴンの夜更かしラボ</title>
  <meta name="description" content="缶コーヒー未満の10円動画から480分超え500円均一まで！FANZA同人10円セールや週末割引クーポンを重ね掛けして最安値で名作を揃える特設ガイド。">
  <link rel="canonical" href="{SITE_URL}/sale-10yen">
  <link rel="icon" type="image/jpeg" href="/assets/onigon_avatar.jpg">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased font-sans min-h-screen">
  {AGE_GATE_MODAL}
  {get_header("sale_10yen")}

  <section class="relative bg-gradient-to-b from-amber-950/80 via-slate-950 to-slate-950 py-10 border-b border-amber-500/30">
    <div class="max-w-5xl mx-auto px-4 space-y-3">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-950 text-amber-300 text-xs font-bold border border-amber-500/40">
        <span>💰</span><span>定価買い厳禁！Day 1 オニゴン厳選・10円動画＆爆安セール特設</span>
      </div>
      <h1 class="text-2xl md:text-4xl font-black text-white leading-tight">
        10円動画＆500円均一セール<br>
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-amber-300 via-rose-400 to-fuchsia-400">缶コーヒー未満で買える歴代神作まとめ</span>
      </h1>
      <p class="text-xs md:text-sm text-slate-300 max-w-3xl leading-relaxed">
        自販機の缶コーヒー1本の値段で10本以上買える「10円動画＆同人10円セール」から、480分超えベスト盤がワンコインの「500円均一」まで、お財布を痛めずに深夜を極楽にする最安値ルートを徹底網羅！
      </p>
      <div class="pt-2 flex flex-wrap gap-3">
        <a href="{build_fanza_link('https://video.dmm.co.jp/')}" target="_blank" rel="noopener noreferrer sponsored" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-rose-600 hover:from-amber-400 hover:to-rose-500 text-slate-950 font-black text-xs shadow-lg transition flex items-center gap-1.5">
          <span>🔥 FANZA公式 10円〜爆安セール会場へ直通</span>
          <span>↗</span>
        </a>
      </div>
    </div>
  </section>

  <main class="max-w-5xl mx-auto px-4 py-8 space-y-8">
    {get_adult_ad_unit("top")}

    <section class="space-y-4">
      <h3 class="text-base font-black text-white flex items-center gap-2 border-b border-slate-800 pb-2">
        <span>💰</span><span>オニゴン厳選！ワンコイン500円＆10円セール注目神作ピックアップ</span>
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {''.join(cards)}
      </div>
    </section>

    {f'''
    <section class="space-y-3 pt-4">
      <h3 class="text-base font-black text-white flex items-center gap-2 border-b border-slate-800 pb-2">
        <span>📖</span><span>10円動画・爆安セール攻略の最新記事一覧</span>
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        {sale_art_html}
      </div>
    </section>
    ''' if sale_art_html else ''}

    {get_hub_banners("sale_10yen")}
    {get_happymail_banner()}
    {get_adult_ad_unit("bottom")}
  </main>

  {get_footer()}
</body>
</html>"""

    for fname in ["sale-10yen.html", "sale-500yen.html"]:
        out_file = os.path.join(DIST_DIR, fname)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(page_html)
    print("Built 10yen & 500yen sale pages: sale-10yen.html, sale-500yen.html")


def build_free_videos_page(articles):
    """Day 2 特設：完全無料動画＆公式サンプル（0円視聴・登録不要）ハブ"""
    free_url = build_fanza_link("https://video.dmm.co.jp/free/")
    free_articles = [a for a in articles if "無料" in a.get("category", "") or "サンプル" in a.get("category", "")]
    free_art_html = ""
    for a in free_articles[:4]:
        free_art_html += f"""
        <a href="/articles/{a['slug']}" class="p-4 rounded-2xl bg-slate-900/80 border border-emerald-500/30 hover:border-emerald-400 transition flex flex-col justify-between">
          <div class="space-y-1">
            <span class="text-[10px] font-mono text-emerald-400 font-bold">{a['date']}</span>
            <h4 class="text-xs md:text-sm font-black text-white line-clamp-2">{a['title']}</h4>
          </div>
          <span class="text-[11px] text-emerald-300 font-bold mt-2">オニゴンの解説を読む →</span>
        </a>
        """

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="rating" content="adult">
  <title>【登録不要・0円視聴】FANZA公式 完全無料動画＆長尺プレビュー徹底ナビ | オニゴンの夜更かしラボ</title>
  <meta name="description" content="クレカ登録ゼロ・完全無料で今すぐスマホから視聴できるFANZA公式無料動画コーナーと、失敗しない長尺サンプルの見極め方をオニゴンが解説。">
  <link rel="canonical" href="{SITE_URL}/free-videos">
  <link rel="icon" type="image/jpeg" href="/assets/onigon_avatar.jpg">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased font-sans min-h-screen">
  {AGE_GATE_MODAL}
  {get_header("free_videos")}

  <section class="relative bg-gradient-to-b from-emerald-950/80 via-slate-950 to-slate-950 py-10 border-b border-emerald-500/30">
    <div class="max-w-5xl mx-auto px-4 space-y-3">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950 text-emerald-300 text-xs font-bold border border-emerald-500/40">
        <span>🎬</span><span>1円も払わずに楽しめる！Day 2 オニゴン厳選・完全無料動画特設</span>
      </div>
      <h1 class="text-2xl md:text-4xl font-black text-white leading-tight">
        登録不要＆クレカ登録ゼロ<br>
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-emerald-300 via-teal-300 to-cyan-400">FANZA公式 完全無料動画コーナー</span>
      </h1>
      <p class="text-xs md:text-sm text-slate-300 max-w-3xl leading-relaxed">
        「今夜はお金を使いたくない」「まず無料でどんな作品があるか楽しみたい」夜更かし勢必見！怪しい海外の違法海賊版サイトにアクセスしてウイルス感染するリスクはゼロ。公式プレイヤーのHD高画質で安全に0円視聴する方法をまとめました。
      </p>
      <div class="pt-2 flex flex-wrap gap-3">
        <a href="{free_url}" target="_blank" rel="noopener noreferrer sponsored" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-black text-xs shadow-lg transition flex items-center gap-1.5">
          <span>🎬 FANZA公式 完全無料動画コーナーを今すぐ視聴</span>
          <span>↗</span>
        </a>
      </div>
    </div>
  </section>

  <main class="max-w-5xl mx-auto px-4 py-8 space-y-8">
    {get_adult_ad_unit("top")}

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="p-5 rounded-2xl bg-slate-900/90 border border-emerald-500/30 space-y-2">
        <span class="text-2xl">⚡️</span>
        <h3 class="text-sm font-black text-white">会員登録・クレカ番号不要</h3>
        <p class="text-xs text-slate-300 leading-relaxed">面倒な個人情報入力は一切なし。スマホのSafariやChromeから1タップですぐ動画が再生されます。</p>
      </div>
      <div class="p-5 rounded-2xl bg-slate-900/90 border border-emerald-500/30 space-y-2">
        <span class="text-2xl">🛡️</span>
        <h3 class="text-sm font-black text-white">公式だから100%安全・高画質</h3>
        <p class="text-xs text-slate-300 leading-relaxed">怪しい広告ポップアップやウイルス請求の心配ゼロ。国内最大手の正規サーバーから安心の高画質ストリーミング。</p>
      </div>
      <div class="p-5 rounded-2xl bg-slate-900/90 border border-emerald-500/30 space-y-2">
        <span class="text-2xl">👀</span>
        <h3 class="text-sm font-black text-white">3〜5分以上の長尺サンプル</h3>
        <p class="text-xs text-slate-300 leading-relaxed">静止画パッケージだけでなく、出演者の声質やライティングの質を事前に納得するまで無料で確認可能。</p>
      </div>
    </div>

    {f'''
    <section class="space-y-3 pt-4">
      <h3 class="text-base font-black text-white flex items-center gap-2 border-b border-slate-800 pb-2">
        <span>📖</span><span>完全無料動画・サンプル攻略の最新記事一覧</span>
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        {free_art_html}
      </div>
    </section>
    ''' if free_art_html else ''}

    {get_hub_banners("free_videos")}
    {get_happymail_banner()}
    {get_adult_ad_unit("bottom")}
  </main>

  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_DIR, "free-videos.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(page_html)
    print("Built free videos page: free-videos.html")


def build_manga_books_page(articles):
    """Day 3 特設：FANZAブックス・深夜の電子コミック（1巻無料・90%OFF）ハブ"""
    books_url = build_fanza_link("https://book.dmm.co.jp/")
    manga_articles = [a for a in articles if "コミック" in a.get("category", "") or "ブックス" in a.get("category", "")]
    manga_art_html = ""
    for a in manga_articles[:4]:
        manga_art_html += f"""
        <a href="/articles/{a['slug']}" class="p-4 rounded-2xl bg-slate-900/80 border border-sky-500/30 hover:border-sky-400 transition flex flex-col justify-between">
          <div class="space-y-1">
            <span class="text-[10px] font-mono text-sky-400 font-bold">{a['date']}</span>
            <h4 class="text-xs md:text-sm font-black text-white line-clamp-2">{a['title']}</h4>
          </div>
          <span class="text-[11px] text-sky-300 font-bold mt-2">オニゴンの解説を読む →</span>
        </a>
        """

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="rating" content="adult">
  <title>【1巻丸ごと無料試し読み】FANZAブックス・深夜の電子コミック＆90%OFFクーポン特設 | オニゴンの夜更かしラボ</title>
  <meta name="description" content="深夜のベッドの中でスマホ1台で即読破！FANZAブックスの1巻丸ごと無料作品や、スマホ容量ゼロで読める高画質ブラウザビューア活用ガイド。">
  <link rel="canonical" href="{SITE_URL}/manga-books">
  <link rel="icon" type="image/jpeg" href="/assets/onigon_avatar.jpg">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased font-sans min-h-screen">
  {AGE_GATE_MODAL}
  {get_header("manga_books")}

  <section class="relative bg-gradient-to-b from-sky-950/80 via-slate-950 to-slate-950 py-10 border-b border-sky-500/30">
    <div class="max-w-5xl mx-auto px-4 space-y-3">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-950 text-sky-300 text-xs font-bold border border-sky-500/40">
        <span>📚</span><span>深夜ベッドでスマホ即読破！Day 3 オニゴン厳選・電子コミック特設</span>
      </div>
      <h1 class="text-2xl md:text-4xl font-black text-white leading-tight">
        1巻丸ごと無料＆90%OFFクーポン<br>
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-sky-300 via-indigo-300 to-purple-400">FANZAブックス 深夜の神コミック特選</span>
      </h1>
      <p class="text-xs md:text-sm text-slate-300 max-w-3xl leading-relaxed">
        大容量データをダウンロードしてスマホのストレージを圧迫する時代は終わり！高画質ブラウザビューアで端末容量を1MBも使わずにサクサク読める話題の成人コミック・商業単行本・名作同人誌をオニゴンが厳選しました。
      </p>
      <div class="pt-2 flex flex-wrap gap-3">
        <a href="{books_url}" target="_blank" rel="noopener noreferrer sponsored" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-black text-xs shadow-lg transition flex items-center gap-1.5">
          <span>📚 FANZAブックス 無料試し読みコミック一覧へ</span>
          <span>↗</span>
        </a>
      </div>
    </div>
  </section>

  <main class="max-w-5xl mx-auto px-4 py-8 space-y-8">
    {get_adult_ad_unit("top")}

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="p-5 rounded-2xl bg-slate-900/90 border border-sky-500/30 space-y-2">
        <span class="text-2xl">📱</span>
        <h3 class="text-sm font-black text-white">端末容量消費ゼロ（ブラウザ即読み）</h3>
        <p class="text-xs text-slate-300 leading-relaxed">ZIP解凍やアプリインストール不要。購入後1秒でSafariやChrome上で高画質閲覧できます。</p>
      </div>
      <div class="p-5 rounded-2xl bg-slate-900/90 border border-sky-500/30 space-y-2">
        <span class="text-2xl">🎁</span>
        <h3 class="text-sm font-black text-white">1巻まるごと無料作品が常時多数</h3>
        <p class="text-xs text-slate-300 leading-relaxed">試し読みが数ページだけでなく、まるごと1巻無料の作品が充実。好みの絵柄をノーリスクで開拓可能。</p>
      </div>
      <div class="p-5 rounded-2xl bg-slate-900/90 border border-sky-500/30 space-y-2">
        <span class="text-2xl">🎟️</span>
        <h3 class="text-sm font-black text-white">初回70〜90%OFF＆ポイント還元</h3>
        <p class="text-xs text-slate-300 leading-relaxed">初回購入クーポンや週末のDMMポイントバックと併用することで、続きの巻も数十円〜数百円で読破。</p>
      </div>
    </div>

    {f'''
    <section class="space-y-3 pt-4">
      <h3 class="text-base font-black text-white flex items-center gap-2 border-b border-slate-800 pb-2">
        <span>📖</span><span>電子コミック・無料試し読みの最新記事一覧</span>
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        {manga_art_html}
      </div>
    </section>
    ''' if manga_art_html else ''}

    {get_hub_banners("manga_books")}
    {get_happymail_banner()}
    {get_adult_ad_unit("bottom")}
  </main>

  {get_footer()}
</body>
</html>"""

    out_file = os.path.join(DIST_DIR, "manga-books.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(page_html)
    print("Built manga books page: manga-books.html")


def build_home_page(articles, newcomers):
    # トップページにも新人特集サムネイルカードを上位2件表示
    spotlight_cards = "\n".join([render_newcomer_card(item) for item in newcomers[:2]])

    article_cards = []
    for art in articles:
        cat = art.get('category', '')
        if "10円" in cat or "セール" in cat:
            badge_class = "bg-amber-950/90 text-amber-300 border-amber-600/60 font-bold"
        elif "無料" in cat:
            badge_class = "bg-emerald-950/90 text-emerald-300 border-emerald-600/60 font-bold"
        elif "コミック" in cat or "ブックス" in cat:
            badge_class = "bg-sky-950/90 text-sky-300 border-sky-600/60 font-bold"
        else:
            badge_class = "bg-purple-950 text-fuchsia-300 border-purple-700/60 font-bold"

        cycle_badge = art.get('cycle_badge', '')
        cycle_html = f'<span class="text-[9px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono font-bold">{cycle_badge}</span>' if cycle_badge else ''

        article_cards.append(f"""
        <a href="/articles/{art['slug']}" class="group bg-slate-900/90 rounded-2xl p-5 border border-purple-500/30 hover:border-fuchsia-400/70 shadow-lg hover:shadow-fuchsia-950/40 transition-all flex flex-col justify-between">
          <div class="space-y-2.5">
            <div class="flex items-center justify-between text-xs text-slate-400 flex-wrap gap-1.5">
              <div class="flex items-center gap-1.5 flex-wrap">
                <span class="px-2.5 py-0.5 rounded-full border text-[11px] {badge_class}">
                  {art.get('icon', '👿')} {cat or '深夜速報'}
                </span>
                {cycle_html}
              </div>
              <time datetime="{art['date']}" class="font-mono text-slate-400">{art['date']}</time>
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
  <meta name="rating" content="adult">
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
  <meta property="og:image" content="{SITE_URL}/assets/onigon_banner.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@Onigon_yfks">
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
          深夜の案内人「オニゴン」が、10円動画・完全無料動画・FANZAブックス電子コミック・KU100バイノーラルASMR・専属大型新人を4日周期で忖度なしレビュー！ジャケット詐欺を回避して神作だけを発掘します。
        </p>
        <div class="flex flex-wrap justify-center md:justify-start gap-2 pt-1">
          <a href="/sale-10yen" class="px-3.5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-xs transition shadow-md flex items-center gap-1">
            <span>💰 10円・爆安セール</span>
          </a>
          <a href="/free-videos" class="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs transition shadow-md flex items-center gap-1">
            <span>🎬 完全無料動画</span>
          </a>
          <a href="/manga-books" class="px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-black text-xs transition shadow-md flex items-center gap-1">
            <span>📚 電子コミック</span>
          </a>
          <a href="/newcomers" class="px-3.5 py-2 rounded-xl bg-fuchsia-600 hover:bg-fuchsia-500 text-white font-black text-xs transition shadow-md flex items-center gap-1">
            <span>🌟 大型新人図鑑</span>
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
    {get_adult_ad_unit("top")}

    <!-- 4大ジャンル・日替わりクイックジャンプナビ -->
    <section class="space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="text-sm md:text-base font-black text-white flex items-center gap-2">
          <span>⚡️</span><span>オニゴンの4大厳選ジャンル（日替わりローテーション）</span>
        </h2>
        <span class="text-[11px] text-fuchsia-400 font-bold">目的別に今すぐ探す</span>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <a href="/sale-10yen" class="group p-3.5 rounded-2xl bg-gradient-to-br from-amber-950/90 to-slate-900 border border-amber-500/40 hover:border-amber-400 transition shadow-lg flex flex-col justify-between">
          <div class="space-y-1">
            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-amber-500 text-slate-950 inline-block">Day 1</span>
            <div class="font-black text-sm text-white group-hover:text-amber-300 flex items-center gap-1">
              <span>💰</span> 10円・爆安セール
            </div>
            <p class="text-[10px] text-slate-300 leading-snug">10円動画・同人10円・ワンコイン500円</p>
          </div>
          <span class="text-[10px] font-bold text-amber-300 mt-2 block group-hover:translate-x-1 transition">特設ハブへ →</span>
        </a>

        <a href="/free-videos" class="group p-3.5 rounded-2xl bg-gradient-to-br from-emerald-950/90 to-slate-900 border border-emerald-500/40 hover:border-emerald-400 transition shadow-lg flex flex-col justify-between">
          <div class="space-y-1">
            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-emerald-600 text-white inline-block">Day 2</span>
            <div class="font-black text-sm text-white group-hover:text-emerald-300 flex items-center gap-1">
              <span>🎬</span> 完全無料動画
            </div>
            <p class="text-[10px] text-slate-300 leading-snug">登録不要・クレカ不要！0円で即視聴</p>
          </div>
          <span class="text-[10px] font-bold text-emerald-300 mt-2 block group-hover:translate-x-1 transition">無料コーナーへ →</span>
        </a>

        <a href="/manga-books" class="group p-3.5 rounded-2xl bg-gradient-to-br from-sky-950/90 to-slate-900 border border-sky-500/40 hover:border-sky-400 transition shadow-lg flex flex-col justify-between">
          <div class="space-y-1">
            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-sky-600 text-white inline-block">Day 3</span>
            <div class="font-black text-sm text-white group-hover:text-sky-300 flex items-center gap-1">
              <span>📚</span> 電子コミック
            </div>
            <p class="text-[10px] text-slate-300 leading-snug">1巻無料試し読み・容量ゼロ即読破</p>
          </div>
          <span class="text-[10px] font-bold text-sky-300 mt-2 block group-hover:translate-x-1 transition">試し読み一覧へ →</span>
        </a>

        <a href="/asmr-ranking" class="group p-3.5 rounded-2xl bg-gradient-to-br from-indigo-950/90 to-slate-900 border border-indigo-500/40 hover:border-indigo-400 transition shadow-lg flex flex-col justify-between">
          <div class="space-y-1">
            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-indigo-600 text-white inline-block">Day 4</span>
            <div class="font-black text-sm text-white group-hover:text-indigo-300 flex items-center gap-1">
              <span>🎧</span> 同人ASMR・新人
            </div>
            <p class="text-[10px] text-slate-300 leading-snug">KU100寝落ち音声＆注目大型ルーキー</p>
          </div>
          <span class="text-[10px] font-bold text-indigo-300 mt-2 block group-hover:translate-x-1 transition">殿堂ランキングへ →</span>
        </a>
      </div>
    </section>

    {get_hub_banners("home")}

    <!-- 🌟 新人女優・注目ルーキー サムネイル特集セクション -->
    <section class="space-y-4">
      <div class="flex items-center justify-between flex-wrap gap-2 border-b border-purple-900/60 pb-3">
        <div>
          <span class="text-[11px] font-bold text-fuchsia-400 tracking-wider uppercase block">NEWCOMER SPOTLIGHT</span>
          <h2 class="text-lg md:text-xl font-black text-white flex items-center gap-2">
            <span>🌟</span><span>今月の大型新人デビュー＆注目ルーキー特集</span>
          </h2>
        </div>
        <a href="/newcomers" class="px-3.5 py-1.5 rounded-xl bg-purple-950 hover:bg-purple-900 text-fuchsia-300 border border-fuchsia-500/40 text-xs font-bold transition">
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

    {get_happymail_banner()}
    {get_adult_ad_unit("bottom")}
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
  <meta name="rating" content="adult">
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
    print("Built about: dist/about")


def build_privacy_page():
    privacy_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="rating" content="adult">
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
    print("Built privacy: dist/privacy")


def build_seo_files(articles):
    urls = [
        f"  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{SITE_URL}/newcomers</loc><changefreq>daily</changefreq><priority>0.9</priority></url>",
        f"  <url><loc>{SITE_URL}/asmr-ranking</loc><changefreq>daily</changefreq><priority>0.9</priority></url>",
        f"  <url><loc>{SITE_URL}/sale-500yen</loc><changefreq>daily</changefreq><priority>0.9</priority></url>"
    ]
    for art in articles:
        urls.append(
            f"  <url><loc>{SITE_URL}/articles/{art['slug']}</loc><lastmod>{art['date']}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>"
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
            f"    <item><title>{art['title']}</title><link>{SITE_URL}/articles/{art['slug']}</link><description>{art['summary']}</description><pubDate>{art['date']}</pubDate></item>"
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

    asmr_json_path = os.path.join(ARTICLES_DIR, "asmr_works.json")
    asmr_works = []
    if os.path.exists(asmr_json_path):
        with open(asmr_json_path, "r", encoding="utf-8") as f:
            asmr_works = json.load(f)

    sale_json_path = os.path.join(ARTICLES_DIR, "sale_picks.json")
    sale_picks = []
    if os.path.exists(sale_json_path):
        with open(sale_json_path, "r", encoding="utf-8") as f:
            sale_picks = json.load(f)

    for art in articles:
        build_article_page(art, articles)

    build_newcomers_page(newcomers)
    build_asmr_ranking_page(asmr_works)
    build_sale_10yen_page(articles, sale_picks)
    build_free_videos_page(articles)
    build_manga_books_page(articles)
    build_home_page(articles, newcomers)
    build_about_page()
    build_privacy_page()
    build_seo_files(articles)

    print("✨ Successfully built Store 3 (Onigon Night Lab) static site with 4-Genre Rotation in dist/!")


if __name__ == "__main__":
    main()
