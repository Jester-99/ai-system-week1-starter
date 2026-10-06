# Week 4 Baseline Report v1.0

學號：7114029015
姓名：黃柏瑜
專題名稱：紅外線無人機高空影像交通工具偵測（YOLO）

---

## 1. Task & Dataset

依據 Week 2 AI Problem Spec 與 Week 3 Dataset Spec，將任務型態與資料集規格整理如下表：

| 欄位 / 項目 | 專案設定與規格說明 |
| :--- | :--- |
| **Task** | 高空無人機長波紅外線（LWIR）單張影格「交通工具微小物件偵測（Small Object Detection）」 |
| **Unit** | 單張高空紅外線熱成像影格（Single IR Frame，解析度 640×512） |
| **Input / Feature** | 單通道/灰階熱影像矩陣（裁切畫面邊緣 16 像素以去除浮水印與 OSD 捷徑特徵，無事後回報資訊） |
| **Target / Label** | 交通工具真值外接矩形框與類別座標 (x, y, w, h, class)，類別固定為 `vehicle` |
| **Dataset Version** | `v0.2.0-yt-curated` |
| **Split Type** | Group Split（以視訊片段來源進行分組隔離，嚴禁隨機打散 Random Split） |
| **Split Rule / Boundary** | Train: Video 01–10 (65%, 2,275 幀) / Val: Video 11–13 (15%, 525 幀) / Test: Video 14–16 (20%, 700 幀) |
| **Group Key** | `video_id`（確保同視訊影格不跨集合，Group Overlap = 0） |
| **Seed** | `random_seed = 42` |
| **Test Lock** | Yes（測試集 700 影格全程鎖定，禁止調參或偷看） |
| **Information Boundary** | 僅允許推論當下無人機感測器直出之影像矩陣，嚴禁事後 GPS 標籤與機載未來中繼資料 |

---

## 2. Baseline Plan

### Baseline 1 (Naive / Current Process / Rule)

| 欄位項目 | 專案內容說明 |
| :--- | :--- |
| **名稱** | 全域 Otsu 雙峰閥值分割法 + 連通元件分析（Otsu Thresholding with Connected Component Analysis） |
| **輸入資訊** | 單張 640×512 灰階長波紅外線（LWIR）影像矩陣（裁切外圍 16 像素以消除浮水印與 OSD 捷徑，無任何中繼資料或事後 GPS） |
| **規則／做法** | 1. 計算全圖灰階直方圖，利用 Otsu 演算法尋找最大類間方差之全域亮度門檻值 T。<br>2. 將影像二值化：像素值大於 T 設為 1（熱源目標），其餘設為 0（背景）。<br>3. 使用 5×5 矩形核進行形態學閉合運算填補內部孔洞。<br>4. 執行連通元件標記，濾除面積小於 12 像素之雜訊，以其餘連通區外接矩形框 (x, y, w, h) 作為車輛偵測框。 |
| **為什麼合理** | 1. 行駛中車輛之引擎與排氣管溫度顯著高於周遭環境，在紅外線熱成像中呈現高亮熱點，直方圖具備天然雙峰特徵。<br>2. Otsu 為非 AI 經典統計方法（Otsu, 1979），無需模型訓練即可在超低算力微控制器上即時運作，是業界熱像儀韌體最普遍的無運算既有規則（Current Process）。 |
| **預期弱點** | 1. **全域過曝虛警**：夏季正午柏油路面與水泥護欄受日照蓄熱整片泛白時，全域門檻會將大面積地表誤判為目標，產生大量 False Positive 虛警。<br>2. **缺乏空間語義**：僅依賴亮度差，無法區分日照熱金屬設施、地表反光與真實車輛結構。<br>3. **低溫差冷車漏檢**：長時間熄火停放之冷車與地表溫差極小（ΔT ≤ 1.5°C），會被全域門檻直接切除，產生致命 False Negative 漏檢。 |

### Baseline 2 (Credible Simple Baseline)

| 欄位項目 | 專案內容說明 |
| :--- | :--- |
| **方法** | 形態學白 Top-Hat 濾波 + 局部自適應分割（Morphological White Top-Hat Transform + Local Adaptive Thresholding） |
| **需要 Feature** | 單張 640×512 灰階熱輻射矩陣經空間形態學濾波後萃取之局部高頻熱斑響應值 |
| **訓練方式** | 無監督傳統演算法（無神經網路權重更新）；結構元素形狀（9×9 橢圓核）與局部自適應視窗（15×15）統一於 Validation 集以最佳 F1-score 網格搜尋決定，禁止於 Test 集調參 |
| **為何 credible** | 出處為 Rivest & Fortin (1996) 與 Deshpande 等人 (1999) 的微小熱目標檢測經典論文，利用高空微小目標符合局部高斯點擴散函數（PSF）的物理特性，能有效抑制平緩背景雜波，為學術界近三十年來最具公信力的非深度學習標準參考線 |
| **與 Baseline 1 差在哪** | 1. **空間濾波 vs 全域統計**：Baseline 1 只看全圖直方圖亮度；Baseline 2 透過形態學消除低頻平緩背景，能有效壓抑大面積受熱路面。<br>2. **局部動態門檻 vs 單一全域門檻**：Baseline 2 採滑動視窗局部自適應計算門檻，抗背景熱雜波能力遠優於 Baseline 1。 |

### Complex Candidate: 輕量化神經網路 YOLOv11n (Nano)
- **方法概述**：專為邊緣端微調之輕量化單階段物件偵測架構，具備多尺度特徵融合（FPN/PAN）與空間幾何注意力機制。

---

## 3. Fair Comparison / Experiment Spec

### Fair Comparison Contract
- **Dataset version** = `v0.2.0-yt-curated`
- **Split** = Group Split by `video_id` ; **Seed / Boundary** = `random_seed = 42`，Test 集 700 幀全程鎖定
- **Baseline 1** = 全域 Otsu 雙峰閥值分割 + 連通元件分析（Otsu, 1979）
- **Baseline 2** = 形態學 Top-Hat 濾波 + 局部自適應分割（Rivest & Fortin, 1996）
- **Primary Metric** = mAP@0.5 (↑)
- **Failure Metric** = 微小目標漏檢率 Tiny Miss Rate（面積 < 16×16 像素之 FN 率, ↓）
- **Threshold policy** = 二值化與幾何過濾門檻統一於 Validation 集決定最佳 F1-score，禁止於 Test 集調參
- **Information boundary** = 單通道 640×512 灰階影像，裁切邊緣 16 像素遮罩，無任何額外外部特徵
- **Runtime / Cost 記錄方式** = 統一於 NVIDIA RTX 4060 Laptop (8GB) / Intel i7-13700H 記錄單張推論延遲 (ms) 與 FPS

---

## 4. Results

| Method | Dataset / Information | Primary Metric | Failure Metric | Runtime / Cost | Complexity | Note |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Baseline 1** | `v0.2.0-yt-curated` (640×512 灰階，無中繼) | 0.214 (mAP@0.5) | 71.8% (Tiny Miss Rate) | 4.2 ms (238 FPS) | Low | 背景日照雜波引發大量全域過曝虛警 |
| **Baseline 2** | `v0.2.0-yt-curated` (640×512 灰階，無中繼) | 0.528 (mAP@0.5) | 46.3% (Tiny Miss Rate) | 11.8 ms (85 FPS) | Low-Mid | 背景抑制顯著提升，但低對比目標漏檢嚴重 |
| **Candidate\*** | `v0.2.0-yt-curated` (640×512 灰階，無中繼) | **0.812** (mAP@0.5) | **14.2%** (Tiny Miss Rate) | 8.6 ms (116 FPS) | Mid | 具備幾何特徵，大幅降低虛警與漏檢 |

*\*Candidate 依據研究問題與複雜度門檻（Complexity Gate）納入評測。*

---

## 5. Failure Analysis

### Failure Case 1: 日照熱路面與高溫柏油引發連續大面積虛警
- **Case ID / Unit**：`yt_clip_14_f0088`（正午高速公路路段）
- **Input 摘要**：夏季正午高空俯視，柏油路面因日照蓄熱整片泛白，伴隨車道白色標線與反光護欄。
- **Ground Truth**：車道上有 3 輛行駛車輛。
- **Prediction**：
  - *Baseline 1*：框出 14 個目標（全域過曝，整段反光路面與護欄皆被連通為巨大錯誤框）。
  - *Baseline 2*：框出 6 個目標（抑制了大面積路面，但在護欄高頻邊緣產生 3 處虛警）。
  - *Candidate*：精確框出 3 輛車，但護欄端點仍有 1 處邊緣誤判。
- **錯誤類型**：背景熱雜波引發連續 False Positive。
- **可能原因**：傳統閥值法僅依賴亮度差，缺乏車輛形狀與結構之高階空間語義，無法區分日照反光結構與真實車輛。
- **對 Decision 的影響**：造成無人機地面站系統警報持續響起，操作員在 10 秒內即會因警報疲勞而將告警系統手動關閉。

### Failure Case 2: 熄火停放冷車與環境熱平衡漏檢
- **Case ID / Unit**：`yt_clip_15_f0312`（黃昏戶外露天停車場）
- **Input 摘要**：無人機大傾角視角，地面停車場停放多輛長時間熄火之車輛，車體溫度已降至與水泥地面接近（溫差 ΔT ≤ 1.5°C）。
- **Ground Truth**：停車格內有 5 輛靜態停放車輛。
- **Prediction**：
  - *Baseline 1*：0 輛（全數漏檢，暗淡熱訊號被全域門檻直接切除）。
  - *Baseline 2*：檢出 1 輛（其餘 4 輛因與鄰近水泥地無明顯峰值反差而漏檢，漏檢率 80%）。
  - *Candidate*：檢出 4 輛（成功依據車窗玻璃冷反光與車框長寬比識別，但最暗處 1 輛漏檢）。
- **錯誤類型**：極低熱反差目標發生致命 False Negative。
- **可能原因**：傳統影像處理本質為「熱訊號對比強化」，當熱對比趨近於零時演算法徹底失效；神經網路能利用幾何邊緣特徵補償熱特徵不足。
- **對 Decision 的影響**：若任務涉及清查路旁停放可疑車輛，傳統 Baseline 將產生系統性盲區，導致巡檢任務失敗。

### Failure Case 3: 密集停放與相鄰車流連體黏合
- **Case ID / Unit**：`yt_clip_16_f0205`（立體交會處塞車路段）
- **Input 摘要**：高空垂直俯視，兩輛小型自小客車前後緊貼停等紅燈，間距小於 3 個像素。
- **Ground Truth**：2 輛獨立車輛（各約 14×12 像素）。
- **Prediction**：
  - *Baseline 1 & 2*：均框出 1 個巨大長方形邊界框，將兩台車合為一體（IoU 均小於 0.35，被判定為 1 次 FP + 2 次 FN）。
  - *Candidate*：精確分開框出 2 個獨立邊界框，IoU 分別為 0.72 與 0.68。
- **錯誤類型**：目標黏合欠分割（Segmentation Under-merging）。
- **可能原因**：傳統連通元件分析依賴空間相鄰性，像素黏合即視為同一物體；YOLO 具備預設錨框與 NMS 機制，能分開預測中心點。
- **對 Decision 的影響**：導致交通車流量統計系統嚴重少算車輛數，交通壅塞判定失準。

---

## 6. Minimum Sufficient Solution

- **Minimum Sufficient Solution**：輕量化深度學習模型 **YOLOv11n**。
- **Evidence**：
  1. Baseline 1 與 2 均無法跨過可用性門檻：Baseline 2 在高空微小目標（< 16×16）上的漏檢率高達 46.3%，且平均每張影格有超過 2 次虛警，違反了 Week 2 規格書中「每分鐘虛警 ≤ 3 次」的可用性底線。
  2. 複雜度代價完全在容許預算內：YOLOv11n 參數量僅 2.6M，推論時間為 8.6ms（116 FPS），顯存佔用低於 800MB，完全符合無人機邊緣運算板卡（如 Jetson Orin Nano）的硬體限制，且帶來了 +28.4% mAP 與漏檢率下降 32.1% 的實質增益。
- **Cost / Risk**：相較於 CPU 傳統方法，需要邊緣晶片具備微型 GPU/NPU 運算支援，並需留意長時間飛行時邊緣模組的散熱功耗。
- **目前是否需要升級**：**Yes**。純傳統影像處理不足以支撐決策，採用輕量神經網路具備充分且必要的 Evidence。

---

## 7. Solution Choice Note

- **Current evidence**：在完全隔離的測試集評測下，Credible Baseline（Top-Hat + Adaptive）達到 mAP 0.528，而 YOLOv11n 達到 mAP 0.812。兩者在 Primary Metric 存在顯著差距，且 YOLOv11n 在微小目標召回與抑制地表反光雜波上呈現大幅優勢。
- **Remaining failure**：YOLOv11n 目前仍存在少數失敗情境，主要集中在：(1) 極端低溫差且完全無光澤之靜止冷車；(2) YouTube 視訊高壓縮比下產生嚴重塊狀馬賽克（Blocky Artifacts）的超遠景車輛。
- **Minimum solution**：輕量神經網路 YOLOv11n 暫為當前系統之 minimum sufficient solution。現階段暫不需要盲目升級至參數量龐大之大型 Transformer 偵測架構（如 RT-DETR）。
- **Next candidate**：微架構小目標偵測頭改良（YOLOv11-P2 Head）或跨影格運動熱訊號融合（ByteTrack 時序後處理）。
- **Justification**：Failure Analysis 顯示殘餘漏檢多因單張影格對比不足引起，無人機視訊具備時序關聯性，透過跨影格運動熱訊號融合，能以最低的算力開銷有效挽救單幀微弱熱源漏檢。

### Complexity Gate 檢驗
1. **Baseline 是否達標？** No。Baseline 2 漏檢率 46.3% 且每影格虛警 > 2 次，失敗原因為傳統模型缺乏高階空間幾何特徵。
2. **Candidate 是否能解此 Failure？** Yes。YOLOv11n 依賴幾何輪廓與多尺度特徵，將微小目標漏檢率降至 14.2%，每影格虛警壓至 0.31 次。
3. **預期增益是否值得額外成本？** Yes。增益達 +28.4% mAP，推論僅需 8.6ms (116 FPS)，完全符合無人機 SWaP 即時功耗預算。
4. **能否同一條件公平測試？** Yes。完全使用同一組鎖定測試集、同一資訊輸入與成對指標進行比較。
-> 結論：①–④ 全數通過，Candidate (YOLOv11n) 具備充分的正當性進入實用部署。

---

## 8. Reproducibility / Run Record

- **Git Commit Hash**：`w04-baseline-v1`
- **實驗 Notebook**：`notebooks/week04_baseline.ipynb`
- **隨機種子（Random Seed）**：`42`（套用於 NumPy、PyTorch 與資料切分）
- **關鍵超參數設定**：
  - *Baseline 1*：Otsu 雙峰閥值，形態學閉合核 5×5，最小連通面積門檻 12 像素。
  - *Baseline 2*：Top-Hat 結構元素形狀 `cv2.MORPH_ELLIPSE`，大小 9×9，局部自適應區塊大小 15×15，偏置常數 C=3。
  - *Candidate (YOLOv11n)*：輸入尺寸 640×640，訓練輪數 50 epochs，初始學習率 0.001，Cosine 退火，信心度門檻 0.25，NMS IoU 門檻 0.45。

---