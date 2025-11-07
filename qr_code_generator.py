import os  # 檔案路徑處理與資料夾建立
import qrcode  # 產生 QR Code
import logging  # 錯誤記錄
from PIL import Image, ImageDraw  # 圖片處理與繪製（如貼 Logo）
from urllib.parse import urlparse  # 解析 URL 取出網域
from qrcode.image.styledpil import StyledPilImage  # 自訂 QR 圖片樣式
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, CircleModuleDrawer  # module 樣式繪製器
from qrcode.image.styles.colormasks import SolidFillColorMask  # 前景色與背景色遮罩
from tqdm import tqdm  # 進度條

# ===================== 全域設定 =====================

TARGET_SIZE     = 1000  # 最終圖片尺寸（正方形，單位：像素）
LOGO_RATIO      = 0.175  # Logo 佔 QR 碼比例
BORDER          = 4     # QR 碼邊框格數（標準為 4，確保掃描穩定）

MAX_BOX_SIZE    = 25    # 單一模組最大尺寸（避免過大模糊）
MIN_BOX_SIZE    = 8     # 單一模組最小尺寸（確保清晰可掃）

USE_CIRCLE_FOR_LARGE = False  # 若為 True，模組大時使用圓形避免鋸齒
CIRCLE_THRESHOLD     = 20     # 切換圓形模組的尺寸門檻

FRONT_COLOR_HEX = "#002A65"  # QR 碼前景色（RGB，預設深藍）
BACK_COLOR_HEX  = "#FFFFFF"  # QR 碼背景色（RGB，預設白色）

ADD_FRAME       = False  # 若為 True，圖片外圍加上邊框
FRAME_COLOR_HEX = "#002A65"  # 邊框顏色
FRAME_WIDTH     = 20    # 邊框寬度（像素）

OUTPUT_PNG      = True  # 是否輸出為 PNG 格式

LOGO_FILENAME   = "logo1.png"  # Logo 檔案名稱（放在 logo/ 資料夾）

VCF_FOLDER      = "vcf"         # 輸入 .vcf 檔案的資料夾
URL_TXT_FILE    = "url/urls.txt"  # 網址清單檔案路徑
VCF_OUTPUT      = "vcf_img"     # .vcf 轉出的 QR 碼儲存資料夾
URL_OUTPUT      = "url_img"     # 網址轉出的 QR 碼儲存資料夾
# ======================================================

# HEX to RGB
def hex_to_rgb(hex_str):
    """HEX → RGB 轉換"""
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

FRONT_COLOR = hex_to_rgb(FRONT_COLOR_HEX)
BACK_COLOR  = hex_to_rgb(BACK_COLOR_HEX)
FRAME_COLOR = hex_to_rgb(FRAME_COLOR_HEX)

def url_to_filename(url):
    # 從網址中提取安全檔名（通常為網域）
    try:
        parsed = urlparse(url.strip())
        domain = parsed.netloc or parsed.path
        return domain or "url"
    except:
        return "url"


def log_error(msg):
    # 將錯誤訊息寫入 error.log 檔案（若尚未初始化則設定 logger）
    if not logging.getLogger().handlers:
        logging.basicConfig(
            filename='error.log',
            level=logging.ERROR,
            format='%(asctime)s - %(message)s',
            filemode='w'  # 每次執行覆蓋舊檔
        )
    logging.error(msg)


def generate_qr_from_data(data, name_hint, output_dir, logo_path):
    """
    產生單一 QR 碼圖片
    
    參數：
    - data: 要編碼的內容（字串）
    - name_hint: 輸出檔名的提示（通常為原始檔名去副檔名）
    - output_dir: 儲存圖片的資料夾
    - logo_path: Logo 圖片路徑（可選）
    
    回傳：成功則 True，失敗則 False
    """
    try:
        if not data.strip():
            raise ValueError("資料為空")

        # 建立 QR 碼物件
        qr = qrcode.QRCode(
            version=None,  # 自動選擇最適版本
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # 容錯率(L=7%, M=15%, Q=25%, H=30%)
            box_size=1,  # 暫時尺寸，後續調整
            border=BORDER,
        )
        qr.add_data(data)
        qr.make(fit=True)  # 自動調整尺寸以容納資料

        # 計算最佳模組尺寸（讓圖片填滿 TARGET_SIZE）
        modules = qr.modules_count
        total_modules = modules + 2 * BORDER
        ideal_box_size = TARGET_SIZE // total_modules
        box_size = min(MAX_BOX_SIZE, max(MIN_BOX_SIZE, ideal_box_size))

        # 根據尺寸選擇模組樣式
        if USE_CIRCLE_FOR_LARGE and box_size >= CIRCLE_THRESHOLD:
            module_drawer = CircleModuleDrawer()  # 大尺寸用圓形
            eye_drawer = CircleModuleDrawer()
        else:
            module_drawer = RoundedModuleDrawer()  # 預設圓角方塊
            eye_drawer = RoundedModuleDrawer()

        # 產生樣式化 QR 圖片
        qr.box_size = box_size
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            eye_drawer=eye_drawer,
            color_mask=SolidFillColorMask(back_color=BACK_COLOR, front_color=FRONT_COLOR)
        ).convert("RGB")

        # 計算實際 QR 碼尺寸（含邊框）
        actual_w = modules * box_size + 2 * BORDER * box_size

        # 若小於目標尺寸，補白至中央
        if actual_w < TARGET_SIZE:
            canvas = Image.new("RGB", (TARGET_SIZE, TARGET_SIZE), BACK_COLOR)
            offset = ((TARGET_SIZE - actual_w) // 2, (TARGET_SIZE - actual_w) // 2)
            canvas.paste(img, offset)
            img = canvas

        # 若圖片太大（含邊框），自動縮小至 TARGET_SIZE
        final_w = img.width
        if ADD_FRAME:
            final_w += 2 * FRAME_WIDTH  # 加上邊框後的總寬度

        if final_w > TARGET_SIZE:
            # 顯示縮小警告訊息
            tqdm.write(f"警告: {name_hint} 資料過大，已自動縮小至 {TARGET_SIZE}x{TARGET_SIZE}")
            
            # 計算縮放比例
            scale = TARGET_SIZE / final_w
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)  # 縮放

            # 縮小後再補白置中
            canvas = Image.new("RGB", (TARGET_SIZE, TARGET_SIZE), BACK_COLOR)
            offset = ((TARGET_SIZE - new_size[0]) // 2, (TARGET_SIZE - new_size[1]) // 2)
            canvas.paste(img, offset)
            img = canvas

        # 加上外框（若啟用）
        if ADD_FRAME:
            framed = Image.new("RGB", (TARGET_SIZE + 2 * FRAME_WIDTH, TARGET_SIZE + 2 * FRAME_WIDTH), FRAME_COLOR)
            framed.paste(img, (FRAME_WIDTH, FRAME_WIDTH))
            img = framed
            final_size = TARGET_SIZE + 2 * FRAME_WIDTH
        else:
            final_size = TARGET_SIZE

        # 嵌入 Logo（若檔案存在）
        if logo_path and os.path.isfile(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
            logo_target = int(final_size * LOGO_RATIO)
            logo = logo.resize((logo_target, logo_target), Image.Resampling.LANCZOS)

            # 將 Logo 置中貼上
            pos = ((final_size - logo_target) // 2, (final_size - logo_target) // 2)
            img.paste(logo, pos, logo)

        # 安全處理檔名：保留空格，只移除危險字元
        safe_name = "".join(c if c.isalnum() or c in " ._-" else '_' for c in name_hint)[:50]
        safe_name = safe_name.strip(' ._')  # 移除首尾空格與點
        if not safe_name:
            safe_name = "unnamed"
        png_path = os.path.join(output_dir, f"{safe_name}.png")

        # 儲存圖片
        if OUTPUT_PNG:
            img.save(png_path, dpi=(300, 300), compress_level=1)

        tqdm.write(f"成功: {safe_name} → {os.path.basename(png_path)}")
        return True

    except Exception as e:
        error_msg = f"失敗: {name_hint} → {e}"
        tqdm.write(error_msg)
        log_error(error_msg)
        return False


def process_vcf(vcf_dir, output_dir, logo_path):
    """
    處理 vcf/ 資料夾內所有 .vcf 檔案
    
    參數：
    - vcf_dir: 輸入資料夾路徑
    - output_dir: 輸出資料夾路徑
    - logo_path: Logo 路徑
    
    回傳：成功轉換的數量
    """
    if not os.path.isdir(vcf_dir):
        tqdm.write(f"資訊: 找不到 '{VCF_FOLDER}' 資料夾，跳過 vcf 處理")
        return 0

    vcf_files = [f for f in os.listdir(vcf_dir) if f.lower().endswith(".vcf")]
    if not vcf_files:
        tqdm.write(f"資訊: '{VCF_FOLDER}' 內無 .vcf 檔案")
        return 0

    os.makedirs(output_dir, exist_ok=True)
    success = 0
    for vcf_file in tqdm(vcf_files, desc="VCF", unit="個", ncols=70, leave=False, position=0, dynamic_ncols=False, bar_format="{l_bar}{bar}| {n}/{total}"):
        filepath = os.path.join(vcf_dir, vcf_file)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
            name = os.path.splitext(vcf_file)[0]  # 使用原始檔名（去掉 .vcf）
            if generate_qr_from_data(data, name, output_dir, logo_path):
                success += 1
        except Exception as e:
            log_error(f"VCF 讀取錯誤 {filepath}: {e}")
    return success


def process_urls(txt_path, output_dir, logo_path):
    """
    處理 url/urls.txt 內的網址
    
    參數：
    - txt_path: urls.txt 檔案路徑
    - output_dir: 輸出資料夾路徑
    - logo_path: Logo 路徑
    
    回傳：成功轉換的數量
    """
    if not os.path.isfile(txt_path):
        tqdm.write(f"資訊: 找不到 '{txt_path}'，跳過 URL 處理")
        return 0

    try:
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    except Exception as e:
        tqdm.write(f"錯誤: 讀取 {txt_path} 失敗：{e}")
        log_error(f"urls.txt 讀取錯誤 {txt_path}: {e}")
        return 0

    if not urls:
        tqdm.write(f"資訊: '{txt_path}' 內無有效網址")
        return 0

    os.makedirs(output_dir, exist_ok=True)
    success = 0
    for url in tqdm(urls, desc="URL", unit="個", ncols=70, leave=False, position=0, dynamic_ncols=False, bar_format="{l_bar}{bar}| {n}/{total}"):
        domain = url_to_filename(url)
        if generate_qr_from_data(url, domain, output_dir, logo_path):
            success += 1
    return success


def main():
    # 程式主流程：設定路徑、處理 vcf 與 urls
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "logo", LOGO_FILENAME)
    url_txt_path = os.path.join(base_dir, URL_TXT_FILE)

    total_success = 0

    # 處理 .vcf 檔案
    vcf_success = process_vcf(
        os.path.join(base_dir, VCF_FOLDER),
        os.path.join(base_dir, VCF_OUTPUT),
        logo_path
    )
    total_success += vcf_success

    # 處理 urls.txt
    url_success = process_urls(
        url_txt_path,
        os.path.join(base_dir, URL_OUTPUT),
        logo_path
    )
    total_success += url_success

    # 總結輸出
    print(f"\n完成！成功輸出 {total_success} 個 QR Code")
    print(f"   - {VCF_OUTPUT}/   ← .vcf QR Code")
    print(f"   - {URL_OUTPUT}/   ← urls.txt QR Code")

    # 清除空的 error.log
    if os.path.exists('error.log') and os.path.getsize('error.log') == 0:
        os.remove('error.log')


if __name__ == "__main__":
    main()