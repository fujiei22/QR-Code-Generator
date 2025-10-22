import os
import qrcode
import logging
from PIL import Image, ImageDraw
from urllib.parse import urlparse
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, CircleModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from tqdm import tqdm

# ===================== 全域設定 =====================
TARGET_SIZE     = 1000
LOGO_RATIO      = 0.20
BORDER          = 4

MAX_BOX_SIZE    = 25
MIN_BOX_SIZE    = 8

USE_CIRCLE_FOR_LARGE = False
CIRCLE_THRESHOLD     = 20

FRONT_COLOR     = (0, 64, 152)
BACK_COLOR      = (255, 255, 255)
RANDOM_COLOR    = False

ADD_FRAME       = False
FRAME_COLOR     = (0, 64, 152)
FRAME_WIDTH     = 20

OUTPUT_PNG      = True

LOGO_FILENAME   = "avalue.png"

VCF_FOLDER      = "vcf"
URL_TXT_FILE    = "url/urls.txt"
VCF_OUTPUT      = "vcf_img"
URL_OUTPUT      = "url_img"
# ======================================================


def random_front_color():
    import random
    return (random.randint(0, 100), random.randint(50, 150), random.randint(100, 200))


def url_to_filename(url):
    try:
        parsed = urlparse(url.strip())
        domain = parsed.netloc or parsed.path
        # domain = domain.replace('www.', '').split('/')[0].split(':')[0]
        return domain or "url"
    except:
        return "url"


def log_error(msg):
    if not logging.getLogger().handlers:
        logging.basicConfig(
            filename='error.log',
            level=logging.ERROR,
            format='%(asctime)s - %(message)s',
            filemode='w'
        )
    logging.error(msg)


def generate_qr_from_data(data, name_hint, output_dir, logo_path):
    try:
        if not data.strip():
            raise ValueError("資料為空")

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=1,
            border=BORDER,
        )
        qr.add_data(data)
        qr.make(fit=True)

        modules = qr.modules_count
        total_modules = modules + 2 * BORDER
        ideal_box_size = TARGET_SIZE // total_modules
        box_size = min(MAX_BOX_SIZE, max(MIN_BOX_SIZE, ideal_box_size))

        if USE_CIRCLE_FOR_LARGE and box_size >= CIRCLE_THRESHOLD:
            module_drawer = CircleModuleDrawer()
            eye_drawer = CircleModuleDrawer()
        else:
            module_drawer = RoundedModuleDrawer()
            eye_drawer = RoundedModuleDrawer()

        front_color = random_front_color() if RANDOM_COLOR else FRONT_COLOR

        qr.box_size = box_size
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            eye_drawer=eye_drawer,
            color_mask=SolidFillColorMask(back_color=BACK_COLOR, front_color=front_color)
        ).convert("RGB")

        actual_w = modules * box_size + 2 * BORDER * box_size
        if actual_w < TARGET_SIZE:
            canvas = Image.new("RGB", (TARGET_SIZE, TARGET_SIZE), BACK_COLOR)
            offset = ((TARGET_SIZE - actual_w) // 2, (TARGET_SIZE - actual_w) // 2)
            canvas.paste(img, offset)
            img = canvas

        if ADD_FRAME:
            framed = Image.new("RGB", (TARGET_SIZE + 2 * FRAME_WIDTH, TARGET_SIZE + 2 * FRAME_WIDTH), FRAME_COLOR)
            framed.paste(img, (FRAME_WIDTH, FRAME_WIDTH))
            img = framed
            final_size = TARGET_SIZE + 2 * FRAME_WIDTH
        else:
            final_size = TARGET_SIZE

        if logo_path and os.path.isfile(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
            logo_target = int(final_size * LOGO_RATIO)
            logo = logo.resize((logo_target, logo_target), Image.Resampling.LANCZOS)

            mask = Image.new("L", logo.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle([(0, 0), logo.size], radius=int(logo_target * 0.1), fill=255)
            logo.putalpha(mask)

            pos = ((final_size - logo_target) // 2, (final_size - logo_target) // 2)
            img.paste(logo, pos, logo)

        safe_name = "".join(c for c in name_hint if c.isalnum() or c in "._-")[:50]
        png_path = os.path.join(output_dir, f"{safe_name}_qr.png")

        if OUTPUT_PNG:
            img.save(png_path, dpi=(300, 300), compress_level=1)

        tqdm.write(f"Success: {safe_name} → {os.path.basename(png_path)}")
        return True

    except Exception as e:
        error_msg = f"Failed: {name_hint} → {e}"
        tqdm.write(error_msg)
        log_error(error_msg)
        return False


def process_vcf(vcf_dir, output_dir, logo_path):
    if not os.path.isdir(vcf_dir):
        tqdm.write(f"Info: 找不到 '{VCF_FOLDER}' 資料夾，跳過 vcf 處理")
        return 0

    vcf_files = [f for f in os.listdir(vcf_dir) if f.lower().endswith(".vcf")]
    if not vcf_files:
        tqdm.write(f"Info: '{VCF_FOLDER}' 內無 .vcf 檔案")
        return 0

    os.makedirs(output_dir, exist_ok=True)
    success = 0
    for vcf_file in tqdm(vcf_files, desc="VCF", unit="file", ncols=70, leave=False, position=0, dynamic_ncols=False, bar_format="{l_bar}{bar}| {n}/{total}"):
        filepath = os.path.join(vcf_dir, vcf_file)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
            name = os.path.splitext(vcf_file)[0]
            if generate_qr_from_data(data, name, output_dir, logo_path):
                success += 1
        except Exception as e:
            log_error(f"VCF Read Error {filepath}: {e}")
    return success


def process_urls(txt_path, output_dir, logo_path):
    if not os.path.isfile(txt_path):
        tqdm.write(f"Info: 找不到 '{txt_path}'，跳過 URL 處理")
        return 0

    try:
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    except Exception as e:
        tqdm.write(f"Error: 讀取 {txt_path} 失敗：{e}")
        log_error(f"URL TXT Read Error {txt_path}: {e}")
        return 0

    if not urls:
        tqdm.write(f"Info: '{txt_path}' 內無有效網址")
        return 0

    os.makedirs(output_dir, exist_ok=True)
    success = 0
    for url in tqdm(urls, desc="URL", unit="url", ncols=70, leave=False, position=0, dynamic_ncols=False, bar_format="{l_bar}{bar}| {n}/{total}"):
        domain = url_to_filename(url)
        if generate_qr_from_data(url, domain, output_dir, logo_path):
            success += 1
    return success


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "logo", LOGO_FILENAME)
    url_txt_path = os.path.join(base_dir, URL_TXT_FILE)

    # === 自動建立 url/urls.txt 範本 ===
    os.makedirs(os.path.dirname(url_txt_path), exist_ok=True)
    if not os.path.exists(url_txt_path):
        template = """# 每行一個網址，支援 http:// 或 https://
https://google.com
https://facebook.com
https://github.com
# https://your-website.com
"""
        with open(url_txt_path, "w", encoding="utf-8") as f:
            f.write(template.strip() + "\n")
        tqdm.write(f"已建立範本：{URL_TXT_FILE}")

    total_success = 0

    vcf_success = process_vcf(
        os.path.join(base_dir, VCF_FOLDER),
        os.path.join(base_dir, VCF_OUTPUT),
        logo_path
    )
    total_success += vcf_success

    url_success = process_urls(
        url_txt_path,
        os.path.join(base_dir, URL_OUTPUT),
        logo_path
    )
    total_success += url_success

    print(f"\nCompleted! 總共成功 {total_success} 個 QR Code")
    print(f"   - vcf_img/   ← .vcf 轉出的圖")
    print(f"   - url_img/   ← urls.txt 轉出的圖")

    if os.path.exists('error.log') and os.path.getsize('error.log') > 0:
        print("Failed: 失敗紀錄已寫入 error.log")
    else:
        if os.path.exists('error.log'):
            os.remove('error.log')


if __name__ == "__main__":
    main()