#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【高CTR特化】ヒロ@ヒロデザch流『意外な対比』サムネイル自動生成エンジン
- 規格: 1280 × 670 px (note.com公式推奨 & X Twitter Card 1.91:1 最適比率)
- 「世間の常識・思い込み」×「意外な現実・衝撃のパンチライン」の二段対比構造
- 1秒で目を引く極太文字・袋文字（フチ付き）・白座布団・高コントラスト配色
- Windows / Linux / macOS 完全クロスプラットフォーム（フォント自動検出・文字化けゼロ）
"""

import os
import sys
import re
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
        "badge": "【知らなきゃ大損！公的制度】",
        "sub_default": "★ 申請しないと国は教えてくれない合法的防衛マニュアル",
        "mascot_tag": "【公式】ほぽりん公的ライフハック速報",
        "badge_bg": (0, 160, 240, 255),       # シアンブルー
        "top_text_color": (210, 30, 30, 255),  # 赤（警告・不安）
        "bottom_text_color": (255, 235, 50, 255), # ネオンイエロー
        "bg_fallback": (15, 25, 45, 255),
        "local_card": os.path.join(ASSETS_DIR, "hoporin_infographic_card.jpg"),
        "remote_card": f"{GITHUB_RAW_BASE}/assets/hoporin_infographic_card.jpg"
    },
    "store2_ikero": {
        "name": "イケロ 🦊",
        "badge": "【皮膚科学・成分忖度なし比較】",
        "sub_default": "◆ 全成分表示を暴く！パッケージ代に騙されない賢い選び方",
        "mascot_tag": "【公式】知恵の白キツネ・イケロ コスメ成分ラボ",
        "badge_bg": (230, 45, 110, 255),      # マゼンタローズ
        "top_text_color": (30, 30, 30, 255),   # 引き締まった黒
        "bottom_text_color": (255, 235, 50, 255), # ネオンイエロー
        "bg_fallback": (35, 15, 25, 255),
        "local_card": os.path.join(ASSETS_DIR, "ikero_infographic_card.jpg"),
        "remote_card": f"{GITHUB_RAW_BASE}/store2/assets/ikero_infographic_card.jpg"
    }
}


def get_japanese_font(size=44, bold=True):
    """OS環境に応じた日本語フォントを安全に取得（Windows / Linux / macOS）"""
    candidates = [
        # Linux (Ubuntu / Debian / Docker)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
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
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_text_with_outline(draw, pos, text, font, fill_color, outline_color=(0, 0, 0, 255), outline_width=5):
    """フチ取り（袋文字）描画で背景に関係なく可読性を極大化"""
    x, y = pos
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx*dx + dy*dy <= outline_width*outline_width:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=fill_color)


def extract_contrast_phrases(store_key, article):
    """
    記事オブジェクトまたはタイトルから、ヒロ@ヒロデザch流の「意外な対比」フレーズを自動抽出
    - 記事内に明示された contrast_top / contrast_bottom があればそれを最優先
    - なければキーワード・カテゴリ・タイトルからスマート自動生成
    """
    # 1. 記事データに明示設定がある場合
    c_top = article.get("contrast_top")
    c_bottom = article.get("contrast_bottom")
    c_sub = article.get("contrast_sub")
    if c_top and c_bottom:
        return c_top, c_bottom, c_sub or STORE_CONFIGS[store_key]["sub_default"]

    title = article.get("title", "")
    summary = article.get("summary", "")
    benefit = article.get("benefit_amount", "")
    category = article.get("category", "")

    if store_key == "store1_hoporin":
        # ほぽりん：公的制度の常識 vs 衝撃の現実
        if "離職" in title or "退職" in title or "失業" in title or "特定理由" in title:
            top = "「自己都合退職」だから諦める…？"
            bottom = "待期ゼロで即日全額受給！"
            sub = "★ 会社都合に変更して国保税も7割免除する全手順"
        elif "家賃" in title or "住居確保" in title or "住宅" in title:
            top = "「家賃が払えず退去寸前…」"
            bottom = "国が3ヶ月全額肩代わり！"
            sub = "★ 返済不要！単身5万・世帯7万が直接大家に振り込まれる"
        elif "大学" in title or "学費" in title or "修学支援" in title or "多子" in title:
            top = "「子ども3人の大学学費が重い…」"
            bottom = "年収制限なしで全額タダ！？"
            sub = "★ 国公立54万・私立70万免除＋給付型奨学金の申請条件"
        elif "介護" in title or "親" in title:
            top = "「親の介護で仕事を辞める…？」"
            bottom = "給料の67%をもらって休業せよ！"
            sub = "★ 非課税・社保免除で最大93日間もらえる介護休業給付金"
        elif "高額療養費" in title or "入院" in title or "医療費" in title:
            top = "「入院費で数百万円の借金…！？」"
            bottom = "月8万円でピタッとストップ！"
            sub = "★ 窓口の立て替えをゼロにする限度額適用認定証の裏ワザ"
        elif "求職者" in title or "無職" in title or "訓練" in title:
            top = "「失業保険が切れて無収入…」"
            bottom = "月10万円もらいながら無料学習！"
            sub = "★ 国が生活費を支給する求職者支援制度の全貌"
        elif "障害年金" in title or "うつ" in title or "適応障害" in title:
            top = "「うつ病や休職で働けない…」"
            bottom = "国から年70万〜150万円支給！"
            sub = "★ 精神疾患でも働きながら受け取れる障害年金の真実"
        elif "年金" in title:
            top = "「年金は65歳からもらうのが正解？」"
            bottom = "受け取り時期で最大84%増額！"
            sub = "★ 繰り上げ・繰り下げで生涯手取りを最大化する計算表"
        else:
            # 汎用対比生成
            clean_title = re.sub(r"【.*?】", "", title).strip()
            top = "「知らずにスルーしていませんか？」"
            bottom = clean_title[:18] + ("！" if not clean_title.endswith(("！", "？")) else "")
            sub = benefit[:32] if benefit else STORE_CONFIGS[store_key]["sub_default"]

    else:
        # イケロ：コスメ成分の思い込み vs 科学的エビデンス
        if "銅ペプチド" in title or "GHK-Cu" in title or "青い" in title:
            top = "「レチノールで肌がボロボロ…」"
            bottom = "皮剥けゼロでハリ再生！？"
            sub = "◆ 青い美容液『GHK-Cu銅ペプチド』の創傷治癒メカニズム"
        elif "エクトイン" in title:
            top = "「塗ってもすぐ乾く砂漠肌…」"
            bottom = "砂漠の微生物が作る鉄壁バリア！"
            sub = "◆ ヒアルロン酸を超える高保水アミノ酸誘導体の科学"
        elif "幹細胞" in title or "エクソソーム" in title:
            top = "「ヒト幹細胞コスメ」の真実…"
            bottom = "実は細胞は1個も入っていない！？"
            sub = "◆ 10万円デパコスとプチプラを分ける『浸透技術』の差"
        elif "ビタミンC" in title or "APPS" in title:
            top = "「従来のビタミンCで効果ゼロ…」"
            bottom = "角質浸透100倍の両親媒性！"
            sub = "◆ 開き毛穴とくすみを根本ケアするAPPSの科学"
        elif "ニードル" in title or "スピキュール" in title or "針" in title:
            top = "「チクチク美容液で肌が若返る？」"
            bottom = "皮膚科が警告する角質断裂の罠！"
            sub = "◆ 美容針ブームの裏に潜む色素沈着リスクを忖度なし検証"
        elif "発酵" in title or "ガラクトミセス" in title or "ピテラ" in title:
            top = "「高級発酵化粧水に2万円…」"
            bottom = "成分原価は『2,000円プチプラ』と同じ！？"
            sub = "◆ 酵母培養液のエビデンスと賢いジェネリック選び"
        elif "セラミド" in title:
            top = "「ただのセラミド配合に騙されるな」"
            bottom = "本物は『ヒト型セラミド』だけ！"
            sub = "◆ EOP/NP/AP配合で見極めるバリア再構築の絶対ルール"
        elif "レチノール" in title:
            top = "「高級デパコスのシワ改善クリーム」"
            bottom = "ドラッグストアの名品で十分代用可能！"
            sub = "◆ 濃度とカプセル化技術で選ぶプチプラレチノール比較"
        else:
            # 汎用対比生成
            clean_title = re.sub(r"【.*?】", "", title).strip()
            top = "「ブランド名や広告に騙されるな」"
            bottom = clean_title[:18] + ("！" if not clean_title.endswith(("！", "？")) else "")
            sub = STORE_CONFIGS[store_key]["sub_default"]

    return top, bottom, sub


def ensure_base_image(store_key):
    """ローカルカード資産を確保（未存在時はGitHubから自動取得）"""
    cfg = STORE_CONFIGS.get(store_key, STORE_CONFIGS["store1_hoporin"])
    local_path = cfg["local_card"]
    if os.path.exists(local_path):
        return local_path

    remote_url = cfg.get("remote_card")
    if remote_url:
        try:
            os.makedirs(ASSETS_DIR, exist_ok=True)
            req = urllib.request.Request(remote_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp, open(local_path, "wb") as f_out:
                f_out.write(resp.read())
            if os.path.exists(local_path):
                return local_path
        except Exception:
            pass
    return None


def generate_contrast_eyecatch(store_key, article, output_path=None, article_id=None, base_image_path=None):
    """
    ヒロ@ヒロデザch流『意外な対比』サムネイル画像を生成
    - 出力サイズ: 1280 × 670 px
    """
    W, H = 1280, 670
    cfg = STORE_CONFIGS.get(store_key, STORE_CONFIGS["store1_hoporin"])
    safe_id = article_id or article.get("id") or article.get("slug") or "latest"

    if not output_path:
        os.makedirs(CACHE_DIR, exist_ok=True)
        output_path = os.path.join(CACHE_DIR, f"contrast_eyecatch_{store_key}_{safe_id}.jpg")

    # 1. 対比フレーズの取得・抽出
    top_phrase, bottom_punchline, sub_banner = extract_contrast_phrases(store_key, article)

    # 2. ベース背景（既存カード画像または単色グラデーション）
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
            canvas = Image.new("RGBA", (W, H), cfg["bg_fallback"])
    else:
        canvas = Image.new("RGBA", (W, H), cfg["bg_fallback"])

    # 3. テキスト可読性のためのダークグラデーション・オーバーレイ（右側のキャラクターを残しつつ左側を遮光）
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_grad = ImageDraw.Draw(grad)
    for x in range(W):
        alpha = int(225 - (x / W) * 165)
        d_grad.line([(x, 0), (x, H)], fill=(10, 15, 28, alpha) if store_key == "store1_hoporin" else (25, 10, 20, alpha))
    canvas = Image.alpha_composite(canvas, grad)

    # 4. 描画レイヤー
    draw = ImageDraw.Draw(canvas)

    # A. トピック・ジャンルバッジ（左上）
    f_badge = get_japanese_font(size=28, bold=True)
    badge_text = cfg["badge"]
    bbox_badge = draw.textbbox((0, 0), badge_text, font=f_badge)
    bw = bbox_badge[2] - bbox_badge[0] + 32
    bh = bbox_badge[3] - bbox_badge[1] + 16
    draw.rounded_rectangle([60, 45, 60 + bw, 45 + bh], radius=8, fill=cfg["badge_bg"])
    draw.text((76, 52), badge_text, font=f_badge, fill=(255, 255, 255, 255))

    # B. 上段【常識・一般論】（白座布団＋強調文字）
    f_top = get_japanese_font(size=46, bold=True)
    bbox_top = draw.textbbox((0, 0), top_phrase, font=f_top)
    tw = bbox_top[2] - bbox_top[0] + 36
    th = bbox_top[3] - bbox_top[1] + 20
    top_y = 135
    draw.rounded_rectangle([60, top_y, 60 + tw, top_y + th], radius=10, fill=(255, 255, 255, 255))
    draw.text((78, top_y + 8), top_phrase, font=f_top, fill=cfg["top_text_color"])

    # C. 対比フック表示
    f_vs = get_japanese_font(size=36, bold=True)
    draw_text_with_outline(draw, (75, top_y + th + 15), "▼ 実は…【衝撃の真実】", f_vs, (255, 220, 0, 255), (0, 0, 0, 255), outline_width=3)

    # D. 下段【意外な現実・パンチライン】（超特大文字 74px × ネオンカラー × 極太フチ）
    f_bottom = get_japanese_font(size=74, bold=True)
    bottom_y = top_y + th + 70
    draw_text_with_outline(
        draw,
        (60, bottom_y),
        bottom_punchline,
        f_bottom,
        cfg["bottom_text_color"],
        (0, 0, 0, 255),
        outline_width=6
    )

    # E. サブ帯（具体的メリット・手順・手取り額）
    f_sub = get_japanese_font(size=32, bold=True)
    sub_y = bottom_y + 115
    bbox_sub = draw.textbbox((0, 0), sub_banner, font=f_sub)
    sw = bbox_sub[2] - bbox_sub[0] + 32
    sh = bbox_sub[3] - bbox_sub[1] + 16
    draw.rounded_rectangle([60, sub_y, 60 + sw, sub_y + sh], radius=8, fill=(0, 0, 0, 200), outline=(255, 255, 255, 255), width=2)
    draw.text((76, sub_y + 6), sub_banner, font=f_sub, fill=(255, 255, 255, 255))

    # F. フッター署名（左下）
    f_foot = get_japanese_font(size=26, bold=True)
    draw_text_with_outline(draw, (60, H - 60), cfg["mascot_tag"], f_foot, (200, 230, 255, 255), (0, 0, 0, 255), outline_width=3)

    # 5. 保存
    final_img = canvas.convert("RGB")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_img.save(output_path, "JPEG", quality=95)
    print(f"✨ 対比型サムネイル生成完了: {output_path} (1280x670)")
    return output_path


# 既存の互換性用エイリアス
def generate_note_eyecatch(store_key, title, output_path=None, article_id=None, base_image_path=None):
    article = {"title": title, "id": article_id, "slug": article_id}
    return generate_contrast_eyecatch(store_key, article, output_path=output_path, article_id=article_id, base_image_path=base_image_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="高CTR対比サムネイル自動生成ツール")
    parser.add_argument("--store", default="store1_hoporin", choices=["store1_hoporin", "store2_ikero"], help="対象店舗")
    parser.add_argument("--title", default="テスト記事タイトル", help="記事タイトル")
    parser.add_argument("--output", default=None, help="保存先パス")
    parser.add_argument("--id", default="test", help="記事IDまたはslug")
    args = parser.parse_args()

    art = {"title": args.title, "id": args.id, "slug": args.id}
    out = generate_contrast_eyecatch(args.store, art, output_path=args.output, article_id=args.id)
    print("Output file:", out)
