import os
import qrcode
import logging
from PIL import Image
from urllib.parse import urlparse
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, CircleModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from tqdm import tqdm

# ===================== 全域設定 =====================
TARGET_SIZE     = 1000
LOGO_RATIO      = 0.175
BORDER          = 4
MAX_BOX_SIZE    = 25
MIN_BOX_SIZE    = 8
USE_CIRCLE_FOR_LARGE = False
CIRCLE_THRESHOLD     = 20

FRONT_COLOR_HEX = "#FFFFFF"
BACK_COLOR_HEX  = "#FFFFFF00"  # 透明背景
FRAME_COLOR_HEX = "#002A65"
FRAME_WIDTH     = 20

ADD_FRAME       = False
ADD_LOGO        = False  # 設為 False，避免 Logo 問題
OUTPUT_FORMAT   = "png"

LOGO_FILENAME   = "logo.png"
VCF_FOLDER      = "vcf"
URL_TXT_FILE    = "url/urls.txt"
VCF_OUTPUT      = "vcf_img"
URL_OUTPUT      = "url_img"
# ======================================================

# HEX to RGBA
def hex_to_rgba(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 6:
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4)) + (255,)
    elif len(hex_str) == 8:
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4, 6))
    return (255, 255, 255, 255)

FRONT_COLOR = hex_to_rgba(FRONT_COLOR_HEX)
BACK_COLOR  = hex_to_rgba(BACK_COLOR_HEX)
FRAME_COLOR = hex_to_rgba(FRAME_COLOR_HEX)

def url_to_filename(url):
    try:
        parsed = urlparse(url.strip())
        domain = parsed.netloc or parsed.path
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

        # 初始化 QR 碼
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=1,
            border=BORDER,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # 計算模組大小
        modules = qr.modules_count
        total_modules = modules + 2 * BORDER
        ideal_box_size = TARGET_SIZE // total_modules
        box_size = min(MAX_BOX_SIZE, max(MIN_BOX_SIZE, ideal_box_size))

        # 選擇模組樣式
        module_drawer = CircleModuleDrawer() if USE_CIRCLE_FOR_LARGE and box_size >= CIRCLE_THRESHOLD else RoundedModuleDrawer()
        eye_drawer = module_drawer

        qr.box_size = box_size
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            eye_drawer=eye_drawer,
            color_mask=SolidFillColorMask(back_color=BACK_COLOR, front_color=FRONT_COLOR)
        )

        if hasattr(img, "get_image"):
            img = img.get_image()

        # 置中
        actual_w = modules * box_size + 2 * BORDER * box_size
        if actual_w < TARGET_SIZE:
            canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), BACK_COLOR)
            offset = ((TARGET_SIZE - actual_w) // 2, (TARGET_SIZE - actual_w) // 2)
            canvas.paste(img, offset)
            img = canvas

        # 縮放
        final_w = img.width + (2 * FRAME_WIDTH if ADD_FRAME else 0)
        if final_w > TARGET_SIZE:
            tqdm.write(f"警告: {name_hint} 資料過大，縮小至 {TARGET_SIZE}x{TARGET_SIZE}")
            scale = TARGET_SIZE / final_w
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), BACK_COLOR)
            offset = ((TARGET_SIZE - new_size[0]) // 2, (TARGET_SIZE - new_size[1]) // 2)
            canvas.paste(img, offset)
            img = canvas

        # 加邊框
        final_size = TARGET_SIZE
        if ADD_FRAME:
            framed = Image.new("RGBA", (TARGET_SIZE + 2 * FRAME_WIDTH, TARGET_SIZE + 2 * FRAME_WIDTH), FRAME_COLOR)
            framed.paste(img, (FRAME_WIDTH, FRAME_WIDTH))
            img = framed
            final_size = TARGET_SIZE + 2 * FRAME_WIDTH

        # 貼 Logo（加上嚴格檢查）
        if ADD_LOGO and logo_path and os.path.isfile(logo_path):
            try:
                logo = Image.open(logo_path).convert("RGBA")
                logo_target = int(final_size * LOGO_RATIO)
                if logo_target <= 0:
                    raise ValueError("Logo 尺寸無效")
                logo = logo.resize((logo_target, logo_target), Image.Resampling.LANCZOS)
                left = (final_size - logo_target) // 2
                top = (final_size - logo_target) // 2
                right = left + logo_target
                bottom = top + logo_target
                box = (left, top, right, bottom)
                # 確保 box 是有效的 4 項 tuple
                if not (isinstance(box, tuple) and len(box) == 4 and all(isinstance(x, int) for x in box)):
                    raise ValueError(f"無效的 box 參數: {box}")
                img.paste(logo, box, mask=logo)
                tqdm.write(f"Logo 成功貼上: {name_hint}")
            except Exception as e:
                tqdm.write(f"貼 Logo 失敗: {name_hint} → {e}")
                log_error(f"貼 Logo 失敗: {name_hint} → {e}")
                # 即使 Logo 失敗，繼續儲存 QR 碼

        # 儲存
        safe_name = "".join(c for c in name_hint if c.isalnum() or c in "._-")[:50]
        img_path = os.path.join(output_dir, f"{safe_name}.png")
        img.save(img_path, dpi=(300, 300), compress_level=1)
        tqdm.write(f"Success: {safe_name}.png")
        return True

    except Exception as e:
        error_msg = f"Failed: {name_hint} → {e}"
        tqdm.write(error_msg)
        log_error(error_msg)
        return False

def process_vcf(vcf_dir, output_dir, logo_path):
    if not os.path.isdir(vcf_dir):
        tqdm.write(f"Info: 找不到 '{VCF_FOLDER}' 資料夾")
        return 0

    vcf_files = [f for f in os.listdir(vcf_dir) if f.lower().endswith(".vcf")]
    if not vcf_files:
        tqdm.write(f"Info: '{VCF_FOLDER}' 內無 .vcf 檔案")
        return 0

    os.makedirs(output_dir, exist_ok=True)
    success = 0
    for vcf_file in tqdm(vcf_files, desc="VCF", unit="個"):
        path = os.path.join(vcf_dir, vcf_file)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
            name = os.path.splitext(vcf_file)[0]
            if generate_qr_from_data(data, name, output_dir, logo_path):
                success += 1
        except Exception as e:
            log_error(f"VCF read fail {path}: {e}")
    return success

def process_urls(txt_path, output_dir, logo_path):
    if not os.path.isfile(txt_path):
        tqdm.write(f"Info: 找不到 '{txt_path}'")
        return 0

    try:
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception as e:
        tqdm.write(f"錯誤: 讀取 {txt_path} 失敗: {e}")
        log_error(f"URL read fail {txt_path}: {e}")
        return 0

    if not urls:
        tqdm.write(f"Info: '{txt_path}' 內無有效網址")
        return 0

    os.makedirs(output_dir, exist_ok=True)
    success = 0
    for url in tqdm(urls, desc="URL", unit="個"):
        domain = url_to_filename(url)
        if generate_qr_from_data(url, domain, output_dir, logo_path):
            success += 1
    return success

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "logo", LOGO_FILENAME)
    url_txt = os.path.join(base_dir, URL_TXT_FILE)

    total = 0
    total += process_vcf(os.path.join(base_dir, VCF_FOLDER), os.path.join(base_dir, VCF_OUTPUT), logo_path)
    total += process_urls(url_txt, os.path.join(base_dir, URL_OUTPUT), logo_path)

    print(f"\n完成！成功產生 {total} 個 QR Code")
    print(f"   - {VCF_OUTPUT}/")
    print(f"   - {URL_OUTPUT}/")

    if os.path.exists('error.log') and os.path.getsize('error.log') == 0:
        os.remove('error.log')

if __name__ == "__main__":
    main()