# QR Code Generator

## 描述

這個 Python 程式用來批量將 `.vcf` 檔案或網址文字檔轉換成自訂樣式的 QR Code 圖片。

- 支援 `.vcf` 名片檔 → QR Code（儲存聯絡人資訊）
- 支援 `urls.txt` 網址清單 → QR Code（每行一個網址）
- 自訂樣式：圓角模組、顏色、Logo、邊框
- QR Code 圖片 1000x1000 像素
- 批量處理，進度條顯示
- 錯誤記錄到 `error.log`

### venv
```bash
python -m venv myenv
.\myenv\Scripts\activate
```

### 套件需求
執行以下指令安裝：
```bash
pip install qrcode[pil] pillow tqdm urllib3
```

### 檔案結構
```
qr_code_generator.py    # 主程式
├── vcf/                # 放 .vcf 檔案
│   └── example.vcf
├── url/                # 放 urls.txt
│   └── urls.txt
├── logo/               # 放 logo 圖片
│   └── logo.png        # 預設檔名，可改 LOGO_FILENAME
├── vcf_img/            # 自動產生：vcf QR 輸出
└── url_img/            # 自動產生：url QR 輸出
```

## 使用方式

1. **準備檔案**：
   - vcf/：放 .vcf 名片檔（每檔一個人）
   - url/urls.txt：每行一個網址，例如：
     ```
     https://www.google.com
     https://www.facebook.com
     # 註解行會忽略
     ```

2. **執行程式**：
   ```bash
   python qr_code_generator.py
   ```

3. **輸出**：
   - vcf_img/：如 `example_qr.png`
   - url_img/：如 `www.google.com_qr.png`
   - 如果重複，會覆蓋舊檔

## 自訂設定（修改程式內變數）

### 基本設定
- `TARGET_SIZE = 1000`：QR 圖片大小（像素）
- `LOGO_RATIO = 0.20`：Logo 佔 QR 比例（0.2 = 20%）
- `BORDER = 4`：QR 邊框格數

### 樣式設定
- `USE_CIRCLE_FOR_LARGE = False`：資料少時用圓點模組（True 開啟）
- `CIRCLE_THRESHOLD = 20`：box_size >= 20 時切換圓點
- `FRONT_COLOR_HEX = (0, 64, 152)`：前景色（藍色）
- `BACK_COLOR_HEX = (255, 255, 255)`：背景色（白色）

### 邊框與輸出
- `ADD_FRAME = False`：加外框（True 開啟）
- `FRAME_COLOR_HEX = (0, 64, 152)`：外框顏色
- `FRAME_WIDTH = 20`：外框寬度（像素）
- `OUTPUT_PNG = True`：輸出 PNG

### 路徑設定
- `LOGO_FILENAME = "avalue.png"`：Logo 檔名
- `VCF_FOLDER = "vcf"`：vcf 輸入資料夾
- `URL_TXT_FILE = "url/urls.txt"`：網址檔
- `VCF_OUTPUT = "vcf_img"`：vcf 輸出資料夾
- `URL_OUTPUT = "url_img"`：url 輸出資料夾

## 範例

### urls.txt 範例
```
https://www.google.com
https://www.facebook.com
https://www.github.com
```

## 注意事項
- Logo 必須是 PNG 或 JPG。
- 如果 QR 碼掃描失敗，檢查錯誤修正級別（ERROR_CORRECT_H 為最高）。
- 錯誤會記錄到 `error.log`，無錯自動刪除。
