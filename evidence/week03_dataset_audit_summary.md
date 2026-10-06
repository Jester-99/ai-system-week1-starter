# Week 3 - Dataset Audit Summary

學號：7114029015
姓名：黃柏瑜
專題：紅外線無人機高空影像交通工具偵測（YOLO）
實驗室：國立中興大學 詹永寬實驗室

---

### 1. 資料集基本特徵（Dataset Profile）
- **資料來源**：網路 YouTube 公開無人機熱成像視訊（2025–2026 現今擷取）。
- **總規模**：16 支獨立視訊片段，共抽幀出 3,500 張高空熱成像影格（640×512 解析度）。
- **標註目標**：專注於單一交通工具類別（`vehicle`），總計 4,820 個車輛邊界框。
- **切分方式**：Group Split by `video_id`（Train: 10 支影片、Val: 3 支影片、Test: 3 支影片，Group Overlap = 0）。

---

### 2. 審計發現與處置決策（Audit Findings: Problem → Evidence → Impact → Decision）

#### Finding 1: 時空序列與 Split Leakage 風險
- **Problem**：YouTube 連續視訊前後影格高度重疊，若採隨機打散切分會使模型直接記憶測試集背景。
- **Evidence**：Random Split 模擬下，Test 集中有 89.2% 的影格在 Train 集中存在前後 1 秒內的相鄰畫面。
- **Impact**：導致離線評估產生虛假高分，無法驗證面對全新空域影片時的真實泛化能力。
- **Decision**：採用以 `video_id` 為單位的 **Group Split**，確保測試影片從未參與訓練（Group Overlap = 0）。

#### Finding 2: 網路視訊壓縮失真與微小目標退化
- **Problem**：YouTube 平台二次編碼壓縮造成遠景微小車輛出現區塊效應與邊界模糊。
- **Evidence**：檢測出 8 筆長寬小於等於 2 像素之無效退化邊界框，且 4.1% 的目標熱邊緣嚴重羽化。
- **Impact**：極微小退化框會使 YOLO 的 Bounding Box 損失函數計算異常。
- **Decision**：在前處理清洗腳本中設定硬性門檻，剔除小於 3 像素之標註框，並套用自適應對比增強。

#### Finding 3: 頻道浮水印引發捷徑學習（Shortcut Leakage）
- **Problem**：部分 YouTube 視訊角落包含頻道固定 Logo 或航拍 OSD 儀表疊加層。
- **Evidence**：稽核發現有 3 支影片在畫面邊緣帶有固定半透明浮水印圖標。
- **Impact**：卷積神經網路可能將浮水印視為特定道路特徵，引發非因果關係的捷徑特徵學習。
- **Decision**：資料載入階段強制將畫面外圍 16 像素邊緣進行統一黑邊裁切遮罩。

#### Finding 4: 缺乏原生輻射溫標與熱交叉之 Coverage 限制
- **Limitation**：缺乏原生 14-bit 物理輻射溫標（Non-Radiometric）、無精確機載高度中繼資料，且極端天候與熱交叉樣本不足。
- **Evidence**：資料來源為 YouTube 壓縮 8-bit 影像，遺失原始溫度矩陣；且環境溫差小於 1°C 樣本僅佔 1.8%。
- **Impact**：無法透過真實攝氏溫度門檻過濾虛警，清晨地熱平衡時可能發生系統性漏檢。
- **Decision / 不主張**：於 Spec 第 12 條明訂本系統**不主張**在無熱對比（如泡水拋錨冷車）或大霧環境下仍能維持高檢測率。