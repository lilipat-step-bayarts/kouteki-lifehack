#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
note.com & SNS 見出し画像（アイキャッチ画像）自動生成モジュール
- note推奨規格: 1280 × 670 px (アスペクト比 約 1.91:1)
- 1号店（ほぽりん🐧） / 2号店（イケロ🦊）のブランドデザイン自動適用
- X投稿用グラフィックカードの転用 & ダイナミックタイトル合成
- 完全無料・ローカル完結（Pillow）
"""

import os
import sys
import argparse
import tempfile
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/lilipat-step-bayarts/kouteki-lifehack/main"

STORE_CONFIGS = {
    "store1_hoporin": {
        "name": "ほぽりん 🐧",
        "badge": "【ほぽりん 公的制度・給付金ハック】",
        "footer": "公式ブログ連動・知って得する最新データ＆申請手順まとめ",
        "card_bg": (11, 25, 44, 220),       # 濃紺ガラス
        "border_color": (0, 210, 255, 255),  # サイアンネオン
        "tag_bg": (0, 119, 182, 255),       # ブルー
        "bg_fallback": (15, 32, 67, 255),
        "local_card": os.path.join(ASSETS_DIR, "hoporin_infographic_card.jpg"),
        "remote_card": f"{GITHUB_RAW_BASE}/assets/hoporin_infographic_card.jpg"
    },
    "store2_ikero": {
        "name": "イケロ 🦊",
        "badge": "【イケロ コスメ成分分析室】",
        "footer": "科学的エビデンスに基づく名品比較＆効果検証まとめ",
        "card_bg": (32, 16, 26, 220),       # ディープワインガラス
        "border_color": (255, 182, 193, 255), # ローズゴールド
        "tag_bg": (190, 75, 100, 255),      # プラムローズ
        "bg_fallback": (45, 18, 38, 255),
        "local_card": os.path.join(ASSETS_DIR, "ikero_infographic_card.jpg"),
        "remote_card": f"{GITHUB_RAW_BASE}/store2/assets/ikero_infographic_card.jpg"
    }
}


def get_japanese_font(size=44, bold=True):
    """
    OS環境（Linux / Windows / macOS）に応じた日本語フォントを安全に取得
    """
    font_candidates = [
        # Linux / Docker
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        # Windows (Meiryo / Yu Gothic)
        "C:/Windows/Fonts/meiryob.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/YuGothB.ttc",
        "C:/Windows/Fonts/YuGothM.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
        "C:\\Windows\\Fonts\\meiryob.ttc",
        "C:\\Windows\\Fonts\\meiryo.ttc",
        "C:\\Windows\\Fonts\\YuGothB.ttc",
        # macOS
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for p in font_candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    """
    指定幅に合わせて日本語テキストを安全に改行分割
    """
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
    return lines


def ensure_base_image(store_key):
    """
    ローカルカード資産を確保（未存在時はGitHubから自動取得）
    """
    cfg = STORE_CONFIGS.get(store_key, STORE_CONFIGS["store1_hoporin"])
    local_path = cfg["local_card"]
    if os.path.exists(local_path):
        return local_path

    # GitHub Remoteからダウンロード
    remote_url = cfg.get("remote_card")
    if remote_url:
        try:
            os.makedirs(ASSETS_DIR, exist_ok=True)
            print(f"📥 リモート資産を取得中: {remote_url}")
            req = urllib.request.Request(remote_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp, open(local_path, "wb") as f_out:
                f_out.write(resp.read())
            if os.path.exists(local_path):
                print(f"✅ ローカルカード保存完了: {local_path}")
                return local_path
        except Exception as e:
            print(f"⚠️ リモートカード取得失敗 ({e})。グラデーション背景を使用します。")

    return None


def generate_note_eyecatch(store_key, title, output_path=None, article_id=None, base_image_path=None):
    """
    note.com公式推奨 1280 × 670 px のアイキャッチ画像を自動生成
    """
    W, H = 1280, 670
    cfg = STORE_CONFIGS.get(store_key, STORE_CONFIGS["store1_hoporin"])

    # 出力パスの決定
    if not output_path:
        os.makedirs(CACHE_DIR, exist_ok=True)
        safe_id = article_id or "latest"
        output_path = os.path.join(CACHE_DIR, f"note_eyecatch_{store_key}_{safe_id}.jpg")

    # 1. ベース背景（既存カード転用 or 単色グラデーション）
    card_source = base_image_path or ensure_base_image(store_key)
    if card_source and os.path.exists(card_source):
        try:
            base_img = Image.open(card_source).convert("RGBA")
            img_w, img_h = base_img.size
            target_ratio = W / H
            curr_ratio = img_w / img_h
            if curr_ratio > target_ratio:
                new_w = int(img_h * target_ratio)
                left = (img_w - new_w) // 2
                base_img = base_img.crop((left, 0, left + new_w, img_h))
            else:
                new_h = int(img_w / target_ratio)
                top = (img_h - new_h) // 2
                base_img = base_img.crop((0, top, img_w, top + new_h))
            canvas = base_img.resize((W, H), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"⚠️ ベース画像読み込みエラー: {e}")
            canvas = Image.new("RGBA", (W, H), cfg["bg_fallback"])
    else:
        canvas = Image.new("RGBA", (W, H), cfg["bg_fallback"])

    # 2. 半透明グラスモーフィズムカードの重畳
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_overlay = ImageDraw.Draw(overlay)

    card_x1, card_y1, card_x2, card_y2 = 50, 40, W - 50, H - 40
    card_bg = cfg["card_bg"]
    border_color = cfg["border_color"]
    tag_bg = cfg["tag_bg"]

    # 角丸カード枠
    d_overlay.rounded_rectangle(
        [card_x1, card_y1, card_x2, card_y2],
        radius=24,
        fill=card_bg,
        outline=border_color,
        width=3
    )

    # 3. ブランドバッジ（ヘッダー上部）
    f_badge = get_japanese_font(size=28, bold=True)
    badge_text = cfg["badge"]
    badge_bbox = d_overlay.textbbox((0, 0), badge_text, font=f_badge)
    badge_w = (badge_bbox[2] - badge_bbox[0]) + 36
    d_overlay.rounded_rectangle(
        [card_x1 + 35, card_y1 + 35, card_x1 + 35 + badge_w, card_y1 + 85],
        radius=12,
        fill=tag_bg
    )
    d_overlay.text(
        (card_x1 + 53, card_y1 + 45),
        badge_text,
        font=f_badge,
        fill=(255, 255, 255, 255)
    )

    # 4. タイトル描画（自動折り返し & シャドウ付き）
    f_title = get_japanese_font(size=46, bold=True)
    draw_temp = ImageDraw.Draw(canvas)
    max_title_w = (card_x2 - card_x1) - 90
    title_lines = wrap_text(title, f_title, max_title_w, draw_temp)

    # 最大3行まで、溢れたら省略記号
    if len(title_lines) > 3:
        title_lines = title_lines[:3]
        if len(title_lines[-1]) > 2:
            title_lines[-1] = title_lines[-1][:-2] + "…"

    start_y = card_y1 + 130
    line_height = 70
    for i, line in enumerate(title_lines):
        y_pos = start_y + (i * line_height)
        # ドロップシャドウ
        d_overlay.text((card_x1 + 38, y_pos + 2), line, font=f_title, fill=(0, 0, 0, 200))
        # 白文字
        d_overlay.text((card_x1 + 36, y_pos), line, font=f_title, fill=(255, 255, 255, 255))

    # 5. フッター情報
    f_footer = get_japanese_font(size=24, bold=False)
    footer_text = f"{cfg['footer']} | note推奨 1280x670"
    d_overlay.text((card_x1 + 38, card_y2 - 55), footer_text, font=f_footer, fill=(210, 225, 240, 230))

    # 6. 画像合成 & 保存
    final_img = Image.alpha_composite(canvas, overlay).convert("RGB")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_img.save(output_path, "JPEG", quality=92)
    print(f"✨ note見出し画像生成完了: {output_path} (1280x670)")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="note見出し画像自動生成ツール")
    parser.add_argument("--store", default="store2_ikero", choices=["store1_hoporin", "store2_ikero"], help="対象店舗")
    parser.add_argument("--title", default="テストタイトル：美容成分と効果の真実", help="記事タイトル")
    parser.add_argument("--output", default=None, help="保存先パス")
    parser.add_argument("--id", default="test", help="記事IDまたはslug")
    args = parser.parse_args()

    out = generate_note_eyecatch(args.store, args.title, output_path=args.output, article_id=args.id)
    print("Output file:", out)
