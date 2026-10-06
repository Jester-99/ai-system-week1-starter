# Week 4 Baseline Report v1.0

學號：7114029015

姓名：黃柏瑜

## 1. Task & Dataset

本週沿用 Week 2 與 Week 3 已確認的無人機高空紅外線影像交通工具偵測任務。

- Task：高空無人機長波紅外線（LWIR）單張影格微小交通工具偵測（Small Object Detection）。
- Unit：單張高空熱成像影格（Single IR Frame, 640×512）。
- Input：單通道灰階熱影像矩陣（裁切邊緣 16 像素以去除 YouTube 浮水印與 OSD 捷徑特徵）。
- Target：交通工具真值外接矩形框與類別座標 $(x, y, w, h, class)$。
- Dataset version：`v0.2.0-yt-curated`，來源為 16 支獨立無人機熱成像視訊抽幀。
- Dataset size：3,500 frames（Train 2,275、Val 525、Test 700），共 4,820 個標註目標。
- Labels：`vehicle`（包含轎車、SUV、卡車、行駛中機車等機動車輛）。

Label distribution：

| category / scale | scale_range (pixels) | count | percentage |
|:---|:---|---:|---:|
| tiny_vehicle | $< 16 \times 16$ | 1,860 | 38.6% |
| medium_vehicle | $16 \times 16 \sim 32 \times 32$ | 2,029 | 42.1% |
| large_vehicle | $> 32 \times 32$ | 931 | 19.3% |

## 2. Baseline Plan

本週建立 baseline ladder，先看簡單方法是否已足夠支援決策。

| Role | Method | Why reasonable | Expected weakness |
| --- | --- | --- | --- |
| Baseline 1 | Otsu Thresholding + CCA | 最便宜的 naive / current reference；直方圖雙峰自動求閥值，熱像儀韌體直出零運算開銷 | 僅依賴全圖亮度，正午路面受熱時嚴重全域過曝；缺乏空間幾何語義 |
| Baseline 2 | Morphological Top-Hat + Adaptive Thresholding | 紅外微小目標檢測（IRSTD）經典 credible baseline；利用微小目標高斯亮斑特性抑制背景 | 極低溫差冷車（熱平衡）仍會漏檢；密集相鄰目標易黏合 |
| Candidate | YOLOv11n (Nano) | 具備多尺度特徵融合與幾何語義之輕量深度學習候選模型，專為邊緣即時推論設計 | 需動用邊緣 GPU/NPU 算力；超遠景重度壓縮馬賽克影格仍具挑戰 |

本週不加入大型 Vision Transformer（如 RT-DETR）或多模態大模型，因為 Week 4 目標是先確認 baseline evidence 並驗證邊緣端最低足夠複雜度。

## 3. Fair Comparison / Experiment Spec

- Dataset：所有方法使用 `data/v0.2.0-yt-curated/manifest.csv`。
- Split：沿用 Week 3 確認的 Group Split by `video_id`，確保同視訊影格不跨集合（Group Overlap = 0）。
- Split ratio：Train 約 65%（10 支影片）、Validation 約 15%（3 支影片）、Test 約 20%（3 支影片）。
- Random seed：42。
- Test lock：Yes，同一份 700 幀 locked test set 比較所有方法。
- Information boundary：所有方法只能使用單通道 640×512 灰階熱矩陣（裁切外圍 16 像素）；不能使用事後 GPS、高度中繼資料或任何未來影格資訊。
- Primary Metric：mAP@0.5，方向越高越好。
- Failure Metric：微小目標漏檢率 Tiny Miss Rate（面積 $< 16 \times 16$ 之 FN 率），方向越低越好。
- Threshold policy：Baseline 傳統演算法之形態學核與自適應閥值於 Validation 集搜尋最佳 F1-score；YOLOv11n 採信心度 0.25、NMS IoU 0.45，禁止於 Test 集調參。
- Runtime / Cost：統一於 NVIDIA RTX 4060 Laptop (8GB) / Intel i7-13700H 記錄單張推論延遲（秒 / 毫秒）與 FPS。

Split rows：

| split | video_clips | frames | vehicle_boxes |
|:---|:---|---:|---:|
| train | Video 01–10 | 2,275 | 3,120 |
| validation | Video 11–13 | 525 | 740 |
| test | Video 14–16 | 700 | 960 |

## 4. Results

| method | dataset_information | map50 | tiny_miss_rate | fp_per_frame | runtime_seconds | complexity | note |
|:---|:---|---:|---:|---:|---:|:---|:---|
| Otsu + CCA (Baseline 1) | 640×512 gray; group split by video_id seed=42 | 0.2140 | 0.7180 | 8.42 | 0.0042 | Low | Naive baseline; 背景日照雜波引發大量全域過曝虛警。 |
| Top-Hat + Adaptive (Baseline 2) | 640×512 gray; group split by video_id seed=42 | 0.5280 | 0.4630 | 2.15 | 0.0118 | Low-Mid | Credible baseline; 背景抑制顯著提升，但低對比冷車漏檢嚴重。 |
| YOLOv11n (Candidate*) | 640×512 gray; group split by video_id seed=42 | 0.8120 | 0.1420 | 0.31 | 0.0086 | Mid | Candidate; 具備幾何語義特徵，大幅降低虛警與微小目標漏檢。 |

Interpretation：

- Otsu + CCA 表現極低（mAP 0.2140），微小目標漏檢高達 71.8%，每影格高達 8.42 個虛警，顯示光靠全圖灰階分佈完全無法處理高空熱雜波。
- Top-Hat + Adaptive 在抑制平緩受熱地表上有顯著進步（mAP 0.5280），但微小目標漏檢仍達 46.3%，每影格仍有 2.15 次虛警，未達可用門檻。
- YOLOv11n 達到 mAP = 0.8120，Tiny Miss Rate 驟降至 14.2%，每影格虛警壓制至 0.31 次，且 GPU 推論僅需 0.0086 秒（116 FPS），顯著超越兩套傳統 baseline。

## 5. Failure Analysis

Representative failure cases：

| method | case_id | input_summary | ground_truth | prediction | failure_type | possible_cause | decision_impact |
|:---|---:|:---|:---|:---|:---|:---|:---|
| Otsu + CCA | 88 | 正午高速公路夏季強烈日照路面 | 3 輛行駛車輛 | 14 框（全域大面積過曝連通） | false-positive burst | 傳統門檻僅依賴亮度差，缺乏空間幾何語義，無法區分日照蓄熱路面與車輛。 | 地面站警報持續頻繁誤報，操作員將因警報疲勞被迫手動關閉系統。 |
| Top-Hat + Adaptive | 312 | 黃昏露天停車場長時間熄火冷車 | 5 輛靜態停放車輛 | 1 輛（漏檢 4 輛，漏檢率 80%） | severe false-negative | 車體與水泥地溫差 $\le 1.5^\circ\text{C}$ 趨近熱平衡，純對比演算法徹底失靈。 | 靜態目標排查巡檢任務產生系統性盲區，導致可疑車輛漏查。 |
| Top-Hat + Adaptive | 205 | 立體交會處停等紅燈密集塞車車流 | 2 輛緊貼小客車（間距 $< 3$ px） | 1 巨大框（IoU $< 0.35$） | segmentation under-merging | 連通元件分析依賴像素空間相鄰性，黏合像素被視為單一巨大物體。 | 車流量統計嚴重少算車輛數，立體樞紐壅塞判定失準。 |
| YOLOv11n | 421 | 遠景超微小車輛且受視訊壓縮失真 | 1 輛微小車輛（$10 \times 8$ px） | 0 輛（漏檢） | compression artifact miss | YouTube 平台二次壓縮造成高頻邊界塊狀模糊，單幀特徵響應不足。 | 造成極遠景微弱目標單影格閃爍漏檢，需仰賴跨影格追蹤補償。 |

Failure interpretation：

- Baseline 1 (Otsu) 的錯誤主要是日照地表引發的 false-positive burst，因為它不具備幾何特徵，把發燙的柏油與護欄全數二值化為前景。
- Baseline 2 (Top-Hat) 的錯誤集中在極低溫差冷車（熱平衡）與相鄰車流黏合，純訊號增強在目標無溫差時物理上限受限。
- YOLOv11n 成功解決絕大多數熱雜波與相鄰目標分離問題，剩餘錯誤集中在極遠景壓縮劣化與完全無溫差之邊界案例。

## 6. Minimum Sufficient Solution

Minimum Sufficient Solution：目前採用輕量神經網路 YOLOv11n。

Evidence：在相同 dataset、split、metric 與 information boundary 下，Baseline 1 與 Baseline 2 的微小目標漏檢率分別高達 71.8% 與 46.3%，每影格虛警均超過 2 次，無法滿足無人機巡檢決策底線。YOLOv11n 達到 mAP = 0.8120，漏檢率降至 14.2%，且推論僅需 0.0086 秒（116 FPS），顯存低於 800MB。

Cost / Risk：相較於 CPU 傳統方法，YOLOv11n 需依賴邊緣板卡（如 Jetson Orin Nano）之微型 GPU 算力，需在無人機載台評估散熱與功耗（SWaP 限制）。

目前是否需要升級：Yes。

理由：傳統演算法缺乏空間幾何語義，無法克服高空日照雜波與熱平衡漏檢；YOLOv11n 提供了 +28.4% mAP 的實質增量 evidence，且延遲完全符合即時飛行規格。

## 7. Solution Choice Note

Current evidence：YOLOv11n (mAP 0.8120) 顯著優於 Credible Baseline Top-Hat + Adaptive (mAP 0.5280)，更遠優於 Otsu (mAP 0.2140)。

Remaining failure：極端無溫差冷車及 YouTube 視訊高壓縮比下的超遠景塊狀模糊目標仍存在少量單幀漏檢。

Minimum solution：YOLOv11n 為當前系統之 minimum sufficient solution。現階段暫不升級至參數量龐大之大型 Transformer 偵測架構（如 RT-DETR）。

Next candidate：微架構小目標偵測頭改良（YOLOv11-P2 Head）或跨影格 ByteTrack 時序運動熱訊號融合。

Justification：無人機航拍影格具備高時序相關性，透過時序關聯能以極低算力補償單幀微弱目標漏檢，比起盲目擴大模型參數量更具工程可行性。

## 8. Reproducibility / Run Record

- Notebook：`notebooks/week04_baseline.ipynb`
- Data：`data/v0.2.0-yt-curated/manifest.csv`
- Output artifacts：`mlflow_artifacts/run_records.csv`、`mlflow_artifacts/failure_cases.csv`
- Random seed：42
- Python packages：numpy, pandas, opencv-python, ultralytics (PyTorch)
- Commit message suggestion：`Complete Week 4 baseline report`

## 9. Mini Defense

### Q1. 為什麼你的 Baseline 是合理的？以及 Baseline 的出處

我的 baseline 合理，因為本週任務是高空無人機長波紅外線（LWIR）單幀微小交通工具偵測，必須在不使用深度學習前建立嚴謹的參考線。Baseline 1 是 Otsu 雙峰閥值分割法，出處為 Otsu (1979, IEEE SMC)，是目前光電熱像儀硬體直出、零運算開銷的最基本警報邏輯。Baseline 2 是形態學白 Top-Hat 濾波配合局部自適應分割，出處為 Rivest & Fortin (1996, Optical Engineering) 與 Deshpande et al. (1999, SPIE)，利用高空微小熱目標呈局部高斯亮斑之物理特性抑制背景，為紅外微小目標檢測（IRSTD）領域近三十年公認的標準對照基準。YOLOv11n 則是輕量神經網路 candidate。三者使用完全相同的 640×512 灰階影格、相同的 locked test set 與資訊邊界，比較完全公平。

### Q2. 複雜模型增加的效益主要集中在哪些案例？

YOLOv11n 相較傳統 Baseline 帶來的 +28.4% mAP 增益並非平均分佈，而是精準解決傳統方法必然失靈的兩大盲區：
1. **正午日照蓄熱的柏油路與護欄**：傳統演算法僅看亮度，正午時大面積地表蓄熱引發每影格 2 至 8 次連續誤報；YOLO 具備幾何特徵，將每影格虛警壓至 0.31 次，消除操作員警報疲勞。
2. **熄火停放冷車與密集塞車車流**：冷車與地面溫差小於 1.5°C，傳統方法漏檢率高達 46.3% 且塞車時目標互相黏合；YOLO 依賴邊界幾何與獨立中心點回歸，將微小目標漏檢率降至 14.2% 並精確分割相鄰車輛。

### Q3. 如果複雜模型只提升 1–2%，你還會選它嗎？為什麼？

我不會選它。因為無人機邊緣部署具備極為嚴苛的 SWaP 限制（體積、重量、散熱與電池續航）。傳統 Baseline 2 僅使用 CPU 即可在 11.8 毫秒內推論完成且耗能極低；若換成神經網路必須動用邊緣 GPU，耗電量大增會直接縮短飛行航時，並增加過熱降頻風險。如果複雜模型只帶來 1–2% 的整體微幅提升，且沒有集中解決高風險的漏檢或虛警問題，其邊際效益完全不足以彌補硬體功耗與維運代價，留在傳統方法才是理性的工程決策。