import os
import qrcode
import qrcode.image.svg
import logging
from urllib.parse import urlparse
from tqdm import tqdm

# ===================== 全域設定 =====================

# --- 輸出設定 ---
OUTPUT_FORMAT = "svg"   # 固定為 svg
ADD_BORDER    = True    # 是否保留 QR Code 的安全邊距 (建議 True 避免被切到)
BORDER_SIZE   = 4       # 安全邊距的格數

RGB_HEX = "#002A65"   # Hex

# --- 路徑設定 ---
VCF_FOLDER      = "vcf"
URL_TXT_FILE    = "url/urls.txt"
VCF_OUTPUT      = "vcf_svg"
URL_OUTPUT      = "url_svg"

# ======================================================

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
            filename='error.log', level=logging.ERROR,
            format='%(asctime)s - %(message)s', filemode='w'
        )
    logging.error(msg)

def generate_qr_from_data(data, name_hint, output_dir):
    """
    產生單一 QR Code SVG 檔案 (透明背景)
    """
    try:
        if not data.strip():
            raise ValueError("資料為空")

        # 定義自訂的 SVG Factory 來控制顏色與背景
        class CustomSvgPathImage(qrcode.image.svg.SvgPathImage):
            # 設定 QR Code 的路徑顏色 (填色)
            # 使用 fill 屬性來設定顏色
            QR_PATH_STYLE = {'fill': RGB_HEX, 'fill-opacity': '1'}
            
            # 透明背景
            background = None 

        # 建立 QR Code 物件
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=BORDER_SIZE if ADD_BORDER else 0,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # 產生 SVG 圖片
        img = qr.make_image(image_factory=CustomSvgPathImage)

        # 安全處理檔名
        safe_name = "".join(c if c.isalnum() or c in " ._-" else '_' for c in name_hint)[:50].strip(' ._')
        if not safe_name: safe_name = "unnamed"
        
        out_path = os.path.join(output_dir, f"{safe_name}.svg")

        # 存檔
        with open(out_path, 'wb') as f:
            img.save(f)

        tqdm.write(f"成功: {safe_name} → {os.path.basename(out_path)}")
        return True

    except Exception as e:
        error_msg = f"失敗: {name_hint} → {e}"
        tqdm.write(error_msg)
        log_error(error_msg)
        return False

def process_vcf(vcf_dir, output_dir):
    if not os.path.isdir(vcf_dir):
        tqdm.write(f"資訊: 找不到 '{VCF_FOLDER}' 資料夾")
        return 0
    vcf_files = [f for f in os.listdir(vcf_dir) if f.lower().endswith(".vcf")]
    if not vcf_files:
        return 0
    os.makedirs(output_dir, exist_ok=True)
    success = 0
    for vcf_file in tqdm(vcf_files, desc="VCF", unit="個", ncols=70, leave=False):
        filepath = os.path.join(vcf_dir, vcf_file)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
            name = os.path.splitext(vcf_file)[0]
            if generate_qr_from_data(data, name, output_dir):
                success += 1
        except Exception as e:
            log_error(f"VCF 讀取錯誤 {filepath}: {e}")
    return success

def process_urls(txt_path, output_dir):
    if not os.path.isfile(txt_path):
        tqdm.write(f"資訊: 找不到 '{txt_path}'")
        return 0
    try:
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    except Exception as e:
        log_error(f"urls.txt 讀取錯誤: {e}")
        return 0
    if not urls: return 0
    
    os.makedirs(output_dir, exist_ok=True)
    success = 0
    for url in tqdm(urls, desc="URL", unit="個", ncols=70, leave=False):
        domain = url_to_filename(url)
        if generate_qr_from_data(url, domain, output_dir):
            success += 1
    return success

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    url_txt_path = os.path.join(base_dir, URL_TXT_FILE)
    
    # 建立必要的資料夾
    os.makedirs(os.path.join(base_dir, "url"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "vcf"), exist_ok=True)

    print(f"=== QR Code 產生器 (SVG 向量版) ===")
    print(f"模式: 透明背景 SVG | 顏色: {RGB_HEX} (CMYK: {CMYK_C}, {CMYK_M}, {CMYK_Y}, {CMYK_K})")
    
    total = 0
    total += process_vcf(os.path.join(base_dir, VCF_FOLDER), os.path.join(base_dir, VCF_OUTPUT))
    total += process_urls(url_txt_path, os.path.join(base_dir, URL_OUTPUT))

    print(f"\n完成！共輸出 {total} 個 SVG 檔案")
    if os.path.exists('error.log') and os.path.getsize('error.log') == 0:
        os.remove('error.log')

if __name__ == "__main__":
    main()