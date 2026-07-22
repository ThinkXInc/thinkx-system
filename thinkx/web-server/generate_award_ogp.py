"""受賞企業の og:image(1200x630 PNG)を award_companies/*.json から生成する。

SNS シェア時のカード画像。会社ロゴ・認定シール・会社名・tier を固定レイアウトで
合成する。新しい企業を追加したら再実行して1枚増やす(手書き sitemap と同じ運用)。

使い方:
    python generate_award_ogp.py --font <NotoSansJP.ttf 等の和文フォント>

フォントは本番 requirements に入れない開発時ツール依存のため、パスで受け取る。
ロゴが SVG のとき(revorn)は <style> の CSS 色を fill 属性へ展開してから PyMuPDF で
ラスタライズする。PyMuPDF は CSS を解釈せず、素のままだと色が黒に落ちるため。
"""
from __future__ import annotations

import argparse
import json
import os
import re

import fitz
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
COMPANIES_DIR = os.path.join(HERE, 'views/templates/truetechjapan/award_companies')
IMG_DIR = os.path.join(HERE, 'views/img/truetechjapan/award_companies')
OUT_DIR = os.path.join(IMG_DIR, 'ogp')
SEAL_PATH = os.path.join(IMG_DIR, 'best-tech-100-seal.png')

WIDTH, HEIGHT = 1200, 630
PAD_X, PAD_TOP, PAD_BOT = 64, 56, 56
SEAL_SIZE = 128
LOGO_MAX_W, LOGO_MAX_H = 620, 232

LIGHT_BG, LIGHT_INK = (255, 255, 255, 255), (26, 26, 23, 255)
DARK_BG, DARK_INK = (20, 20, 16, 255), (243, 241, 230, 255)
CHIP_BG, CHIP_INK = (233, 205, 106, 255), (122, 95, 8, 255)


def rasterize_svg(path):
    """SVG を RGBA 画像へ。<style> の class→fill を属性へ展開して色を保つ。"""
    svg = open(path, encoding='utf-8').read()
    for cls, color in re.findall(r'\.([\w-]+)\s*\{\s*fill:\s*(#[0-9a-fA-F]+)', svg):
        svg = re.sub(rf'class="{re.escape(cls)}"', f'class="{cls}" fill="{color}"', svg)
    page = fitz.open('svg', svg.encode('utf-8'))[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(6, 6), alpha=True)
    return Image.frombytes('RGBA', (pix.width, pix.height), pix.samples)


def load_logo(filename):
    path = os.path.join(IMG_DIR, filename)
    if filename.lower().endswith('.svg'):
        return rasterize_svg(path)
    return Image.open(path).convert('RGBA')


def fit_font(draw, text, font_path, start_size, min_size, max_width):
    """max_width に収まる最大のフォント(Bold)を返す。"""
    size = start_size
    while size > min_size:
        font = ImageFont.truetype(font_path, size)
        font.set_variation_by_name('Bold')
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 2
    font = ImageFont.truetype(font_path, min_size)
    font.set_variation_by_name('Bold')
    return font


def render(company, font_path, out_path):
    dark = company['logo'].get('background') == 'dark'
    bg, ink = (DARK_BG, DARK_INK) if dark else (LIGHT_BG, LIGHT_INK)
    canvas = Image.new('RGBA', (WIDTH, HEIGHT), bg)
    draw = ImageDraw.Draw(canvas)

    # 認定シール(右上)。
    seal = Image.open(SEAL_PATH).convert('RGBA').resize((SEAL_SIZE, SEAL_SIZE))
    canvas.alpha_composite(seal, (WIDTH - PAD_X - SEAL_SIZE, PAD_TOP - 4))

    # 会社名(下部左)。tier があれば右にチップ。長い社名はフォントを縮めて収める。
    name = company['company_name']
    name_font = fit_font(draw, name, font_path, 48, 30, WIDTH - PAD_X * 2 - 220)
    nb = draw.textbbox((0, 0), name, font=name_font)
    name_h = nb[3] - nb[1]
    name_y = HEIGHT - PAD_BOT - name_h
    draw.text((PAD_X, name_y - nb[1]), name, font=name_font, fill=ink)

    if company.get('tier'):
        tier_font = ImageFont.truetype(font_path, 24)
        tier_font.set_variation_by_name('Bold')
        tb = draw.textbbox((0, 0), company['tier'], font=tier_font)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        cx = PAD_X + draw.textlength(name, font=name_font) + 22
        cy = name_y + (name_h - th) // 2 - 6
        draw.rounded_rectangle(
            [cx, cy, cx + tw + 28, cy + th + 12], radius=(th + 12) // 2, fill=CHIP_BG)
        draw.text((cx + 14, cy + 6 - tb[1]), company['tier'], font=tier_font, fill=CHIP_INK)

    # ロゴ(上部左、シールと会社名の間に中央寄せ)。アスペクト維持で縮小。
    logo = load_logo(company['logo']['src'].split('/')[-1])
    region_top, region_bot = PAD_TOP, name_y - 28
    scale = min(LOGO_MAX_W / logo.width, LOGO_MAX_H / logo.height,
                (region_bot - region_top) / logo.height)
    logo = logo.resize((max(1, int(logo.width * scale)), max(1, int(logo.height * scale))))
    ly = region_top + (region_bot - region_top - logo.height) // 2
    canvas.alpha_composite(logo, (PAD_X, ly))

    canvas.convert('RGB').save(out_path, 'PNG')
    return out_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', required=True, help='和文フォント(ttf/otf)のパス')
    parser.add_argument('--keys', nargs='*', help='対象キー(省略時は全社)')
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    keys = args.keys or sorted(
        f[:-5] for f in os.listdir(COMPANIES_DIR) if f.endswith('.json'))
    for key in keys:
        company = json.load(open(os.path.join(COMPANIES_DIR, f'{key}.json'), encoding='utf-8'))
        # 会社名は日本語(ロゴ・和文名)。多言語フィールドは ja を採る。
        company['company_name'] = company['company_name'].get('ja') \
            if isinstance(company['company_name'], dict) else company['company_name']
        out = render(company, args.font, os.path.join(OUT_DIR, f'{key}.png'))
        print(f'generated: {out}')


if __name__ == '__main__':
    main()
