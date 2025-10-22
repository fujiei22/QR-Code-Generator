# QR Code Generator

## 描述

這個 Python 程式用來批量將 `.vcf` 檔案或網址文字檔轉換成自訂樣式的 QR Code 圖片。

- 支援 `.vcf` 名片檔 → QR Code（儲存聯絡人資訊）
- 支援 `urls.txt` 網址清單 → QR Code（每行一個網址）
- 自訂樣式：圓角模組、顏色、Logo、邊框
- 自動補白到 1000x1000 像素
- 批量處理，進度條顯示
- 錯誤記錄到 `error.log`

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
│   └── avalue.png      # 預設檔名，可改 LOGO_FILENAME
├── vcf_img/            # 自動產生：vcf QR 輸出
└── url_img/            # 自動產生：url QR 輸出
```

- 如果 `url/urls.txt` 不存在，程式會自動建立範本。

## 使用方式

1. **準備檔案**：
   - vcf/：放 .vcf 名片檔（每檔一個人）
   - url/urls.txt：每行一個網址，例如：
     ```
     https://google.com
     https://facebook.com
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
- `FRONT_COLOR = (0, 64, 152)`：前景色（藍色）
- `BACK_COLOR = (255, 255, 255)`：背景色（白色）
- `RANDOM_COLOR = False`：隨機顏色（True 開啟）

### 邊框與輸出
- `ADD_FRAME = False`：加外框（True 開啟）
- `FRAME_COLOR = (0, 64, 152)`：外框顏色
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
https://google.com
https://facebook.com
https://github.com
```

### 執行輸出範例
```
VCF: 100%|██████████| 2/2
Success: example1 → example1_qr.png
Success: example2 → example2_qr.png
URL: 100%|██████████| 3/3
Success: google.com → google.com_qr.png
Success: facebook.com → facebook.com_qr.png
Success: github.com → github.com_qr.png

Completed! 總共成功 5 個 QR Code
   - vcf_img/   ← .vcf 轉出的圖
   - url_img/   ← urls.txt 轉出的圖
```

## 注意事項
- Logo 必須是 PNG 或 JPG，支援透明背景。
- 如果 QR 碼掃描失敗，檢查錯誤修正級別（ERROR_CORRECT_H 為最高）。
- 程式自動處理中文字元，但檔名只支援英文/數字/._-。
- 錯誤會記錄到 `error.log`，無錯自動刪除。