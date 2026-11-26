#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ヒロ@ヒロデザch流『意外な対比』サムネイルジェネレーター
- 1280 × 670 px (note & X Twitter Card最適比率)
- 「常識」×「意外な現実」の2行対比構造
- 1秒で目を引く極太文字・袋文字（フチ付き）・高コントラスト座布団
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ARTIFACT_DIR = "/home/antigravity/.gemini/jetski/brain/v1/default/jetski_remote_agents_3p_devbox/53fcc592-5fd5-4085-845b-b97dcd2d268d"
LOCAL_SAMPLE_DIR = "/home/antigravity/lilipat-step-bayarts/kouteki-lifehack/local_pc_x_automation/sample_thumbnails"

os.makedirs(ARTIFACT_DIR, exist_ok=True)
os.makedirs(LOCAL_SAMPLE_DIR, exist_ok=True)

FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def draw_text_with_outline(draw, pos, text, font, fill_color, outline_color, outline_width=4):
    """フチ取り（袋文字）描画で可読性を爆上げ"""
    x, y = pos
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx*dx + dy*dy <= outline_width*outline_width:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=fill_color)

def generate_contrast_thumbnail(store_key, topic_badge, top_phrase, bottom_punchline, sub_banner, bg_card_path, filename):
    W, H = 1280, 670
    
    # 1. 背景の準備
    if os.path.exists(bg_card_path):
        base_img = Image.open(bg_card_path).convert("RGBA")
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
    else:
        bg_col = (15, 23, 42) if store_key == "store1_hoporin" else (40, 15, 30)
        canvas = Image.new("RGBA", (W, H), bg_col)

    # 2. テキスト可読性のためのダークグラデーション・オーバーレイ（左側を濃くして文字を際立たせる）
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_grad = ImageDraw.Draw(grad)
    for x in range(W):
        # 左側(x=0)は85%遮光、右側(x=1280)は25%遮光（右側のキャラクターを見せる）
        alpha = int(225 - (x / W) * 165)
        d_grad.line([(x, 0), (x, H)], fill=(10, 15, 28, alpha) if store_key == "store1_hoporin" else (25, 10, 20, alpha))
    
    canvas = Image.alpha_composite(canvas, grad)

    # 3. 描画レイヤー
    draw = ImageDraw.Draw(canvas)

    # A. トピック・ジャンルバッジ（左上）
    f_badge = get_font(28)
    bbox_badge = draw.textbbox((0, 0), topic_badge, font=f_badge)
    bw = bbox_badge[2] - bbox_badge[0] + 32
    bh = bbox_badge[3] - bbox_badge[1] + 16
    badge_bg = (0, 180, 255) if store_key == "store1_hoporin" else (230, 50, 110)
    draw.rounded_rectangle([60, 45, 60 + bw, 45 + bh], radius=8, fill=badge_bg)
    draw.text((76, 52), topic_badge, font=f_badge, fill=(255, 255, 255))

    # B. 上段【常識・一般論】（白座布団＋赤または黒文字）
    # 「えっ？本当は違うの？」と思わせるフック
    f_top = get_font(46)
    bbox_top = draw.textbbox((0, 0), top_phrase, font=f_top)
    tw = bbox_top[2] - bbox_top[0] + 36
    th = bbox_top[3] - bbox_top[1] + 20
    top_y = 135
    draw.rounded_rectangle([60, top_y, 60 + tw, top_y + th], radius=10, fill=(255, 255, 255))
    top_text_color = (220, 30, 30) if store_key == "store1_hoporin" else (30, 30, 30)
    draw.text((78, top_y + 8), top_phrase, font=f_top, fill=top_text_color)

    # C. 対比矢印 / VS マーク
    f_vs = get_font(36)
    draw_text_with_outline(draw, (75, top_y + th + 15), "▼ 実は…【衝撃の真実】", f_vs, (255, 220, 0), (0, 0, 0), outline_width=3)

    # D. 下段【意外な現実・パンチライン】（超特大文字 76px × ネオンカラー × 極太フチ）
    f_bottom = get_font(74)
    bottom_y = top_y + th + 70
    draw_text_with_outline(
        draw, 
        (60, bottom_y), 
        bottom_punchline, 
        f_bottom, 
        (255, 235, 50),   # 鮮烈なイエロー
        (0, 0, 0),         # 重厚な黒フチ
        outline_width=6
    )

    # E. サブ帯（証拠・エビデンス・手取り額）
    f_sub = get_font(32)
    sub_y = bottom_y + 115
    bbox_sub = draw.textbbox((0, 0), sub_banner, font=f_sub)
    sw = bbox_sub[2] - bbox_sub[0] + 32
    sh = bbox_sub[3] - bbox_sub[1] + 16
    draw.rounded_rectangle([60, sub_y, 60 + sw, sub_y + sh], radius=8, fill=(0, 0, 0, 200), outline=(255, 255, 255), width=2)
    draw.text((76, sub_y + 6), sub_banner, font=f_sub, fill=(255, 255, 255))

    # F. フッター署名（右下）
    f_foot = get_font(26)
    mascot_tag = "【公式】ほぽりん公的ライフハック速報" if store_key == "store1_hoporin" else "【公式】知恵の白キツネ・イケロ コスメ成分ラボ"
    draw_text_with_outline(draw, (60, H - 60), mascot_tag, f_foot, (200, 230, 255), (0, 0, 0), outline_width=3)

    # 保存
    artifact_path = os.path.join(ARTIFACT_DIR, filename)
    local_path = os.path.join(LOCAL_SAMPLE_DIR, filename)
    
    rgb_img = canvas.convert("RGB")
    rgb_img.save(artifact_path, "JPEG", quality=95)
    rgb_img.save(local_path, "JPEG", quality=95)
    print(f"Generated: {artifact_path}")
    return artifact_path

if __name__ == "__main__":
    # 1. ほぽりん サンプル1: 特定理由離職者
    generate_contrast_thumbnail(
        store_key="store1_hoporin",
        topic_badge="【失業保険・給付金の裏ワザ】",
        top_phrase="「自己都合退職」だから諦める…？",
        bottom_punchline="待期ゼロで即日全額受給！",
        sub_banner="★ 会社都合に変更して国保税も7割免除する全手順",
        bg_card_path="/home/antigravity/lilipat-step-bayarts/kouteki-lifehack/local_pc_x_automation/assets/hoporin_infographic_card.jpg",
        filename="sample_hoporin_contrast_1.jpg"
    )

    # 2. ほぽりん サンプル2: 住居確保給付金
    generate_contrast_thumbnail(
        store_key="store1_hoporin",
        topic_badge="【家賃・生活防衛の命綱】",
        top_phrase="「家賃が払えず退去寸前…」",
        bottom_punchline="国が3ヶ月全額肩代わり！",
        sub_banner="★ 返済不要！単身5万・世帯7万円が直接大家に振り込まれる",
        bg_card_path="/home/antigravity/lilipat-step-bayarts/kouteki-lifehack/local_pc_x_automation/assets/hoporin_infographic_card.jpg",
        filename="sample_hoporin_contrast_2.jpg"
    )

    # 3. イケロ サンプル1: 銅ペプチド vs レチノール
    generate_contrast_thumbnail(
        store_key="store2_ikero",
        topic_badge="【皮膚科学・成分エビデンス】",
        top_phrase="「レチノールで肌がボロボロ…」",
        bottom_punchline="皮剥けゼロでハリ再生！？",
        sub_banner="◆ 青い美容液『GHK-Cu銅ペプチド』の創傷治癒メカニズム",
        bg_card_path="/home/antigravity/lilipat-step-bayarts/kouteki-lifehack/local_pc_x_automation/assets/ikero_infographic_card.jpg",
        filename="sample_ikero_contrast_1.jpg"
    )

    # 4. イケロ サンプル2: デパコス vs プチプラ
    generate_contrast_thumbnail(
        store_key="store2_ikero",
        topic_badge="【コスメ成分ラボ・忖度なし比較】",
        top_phrase="「3万円デパコス」vs「1,000円プチプラ」",
        bottom_punchline="成分原価は『同じ30円』の真実",
        sub_banner="◆ 全成分表示を暴く！パッケージ代に騙されない賢い選び方",
        bg_card_path="/home/antigravity/lilipat-step-bayarts/kouteki-lifehack/local_pc_x_automation/assets/ikero_infographic_card.jpg",
        filename="sample_ikero_contrast_2.jpg"
    )
