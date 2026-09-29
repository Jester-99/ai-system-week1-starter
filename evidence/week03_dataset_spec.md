# Week 3 - Dataset Spec v0.2 
# !重要備註!已更新 Week 1&2 - 內容改成我的論文研究
學號：7114029015
姓名：黃柏瑜
專題名稱：紅外線無人機高空影像交通工具偵測（YOLO）

---

## A. 資料怎麼形成

### 1. Source / Owner
- **資料來源**：網路 YouTube 公開無人機長波紅外線（LWIR / Thermal IR）航拍影片（透過合法合理使用原則進行學術研究檢索與取樣抽幀）。
- **擁有者 / 維護單位**：國立中興大學 詹永寬實驗室 - 黃柏瑜。
- **擷取日期**：2025 年 1 月至 2026 年（現今）。
- **授權與使用條款**：依據學術研究之合理使用（Fair Use）原則，影像僅供離線訓練與學術評測，不作商業發布。

### 2. Unit Alignment
- **W2 Unit of Analysis**：單張高空紅外線熱成像影格（Single IR Frame）。
- **Dataset 儲存型態**：
  - 影像檔案：每張影像代表自 YouTube 視訊抽幀出的獨立影格（解析度統一縮放/裁切為 640×512，灰階 PNG/JPG 格式）。
  - 標註檔案：標準 YOLO txt 格式，每列代表一個交通工具目標的外接矩形框，與影像透過 `frame_id` 嚴格一對一對齊。
- **對齊性確認**：一筆 Observation 即為單一影格，符合 Week 2 定義的影格層決策點。

### 3. Time Range
- **視訊蒐集區間**：涵蓋 2025 年至 2026 年間上傳之 16 支不同無人機拍攝視訊片段（Video Clips）。
- **時段涵蓋**：夜間道路巡檢（佔 55%）、日間城市/公路巡航（佔 35%）、黃昏/清晨環境（佔 10%）。

### 4. Fields
| 欄位名稱 | 型態 | 角色 | 決策當下可得性 | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| `frame_id` | String | ID Key | 是 | 影格唯一識別碼（如 `yt_clip03_f0120`） |
| `video_id` | String | Group Key | 是 | YouTube 來源視訊識別碼（用於 Group Split 隔離） |
| `image_array` | Array (640, 512) | Input | 是 | 自視訊解碼之單通道/三通道灰階影像矩陣 |
| `class_id` | Int | Target | 否（事後標註） | 物件類別代碼（固定為 `0: vehicle`） |
| `bbox_x_center` | Float | Target | 否（事後標註） | 歸一化目標中心點 X 座標 $[0, 1]$ |
| `bbox_y_center` | Float | Target | 否（事後標註） | 歸一化目標中心點 Y 座標 $[0, 1]$ |
| `bbox_width` | Float | Target | 否（事後標註） | 歸一化目標寬度 $[0, 1]$ |
| `bbox_height` | Float | Target | 否（事後標註） | 歸一化目標高度 $[0, 1]$ |
| `channel_watermark` | Image Region | 禁用（Leakage）| 否（視訊後製） | YouTube 頻道浮水印或 UI 疊加層，推論時嚴禁作為特徵 |

### 5. Label / Codebook
- **Target 定義**：高空俯視或大傾角視野下的**交通工具類別（`vehicle`）**，包含轎車（Sedan）、休旅車（SUV）、卡車（Truck）及行駛中的機車等機動車輛。
- **標註機制**：由詹永寬實驗室研究員利用 CVAT 進行人工精細邊界框標註，並由第二人抽檢驗證。
- **Codebook 規範**：
  - 熱源判定：以車輛引擎蓋、排氣管散熱或車身金屬反光形成的高對比熱輪廓為基準標註邊界框。
  - 熄火冷車：若車輛已長時間停放且與地面無可辨溫差（缺乏熱特徵），不予標註，避免模型混淆。
  - 密集車流：若車輛間距極小，仍依車體結構各自獨立框選，重疊區域不刻意合併。
- **已知標籤誤差**：地表大型金屬設施（如變壓箱、反光鐵皮）偶有約 2.5% 邊界雜訊。

### 6. Inclusion / Exclusion
- **納入條件（Include）**：
  - 攝影角度介於 45° 至 90°（俯視/大傾角）的高空無人機視角。
  - 影像中目標具備清楚可辨之熱特徵或輪廓線。
- **排除條件（Exclude）**：
  - YouTube 視訊畫質低於 720p、壓縮區塊效應（Macroblocking）嚴重失真之影格。
  - 畫面視角包含大面積無效天空或無人機起降地面極低空影像。
  - 包含大面積頻道片頭文字特效或全螢幕動畫覆蓋之影格。
- **偏差影響評估**：排除嚴重壓縮失真的影像能保障訓練品質，但限制了模型對超低頻寬劣化串流的容忍度。

---

## B. 證據怎麼驗證

### 7. Population / Coverage
- **Target Population**：現實世界中無人機在高空對各類道路、停車場、樞紐交會處進行交通監控時出現的所有機動車輛。
- **Observed Coverage**：
  - 場景涵蓋：高速公路車流、市區十字路口、戶外露天停車場、夜間鄉村公路。
  - 光熱環境：深色熱（White-Hot）與淺色熱（Black-Hot）兩種熱成像極性模式。
- **Missing Coverage**：
  - 缺乏暴雪、暴雨天候下的車輛熱衰減樣本。
  - 缺乏林道與密林樹冠遮蔽下的隱蔽車輛樣本。
- **外推限制**：本資料集訓練之模型，不主張可直接泛化至重度植被遮蔽或越野山區的偽裝車輛偵測。

### 8. Train / Validation / Test Rule
- **Test 模擬的未知**：**「全新 YouTube 視訊剪輯片段（未見過的拍攝設備、全新拍攝地理環境與相機感測器特性）」**。
- **Split 策略**：**Group Split by `video_id`（嚴禁依 Frame 進行 Random Split）**。
- **具體分配規則**：
  - 共採集 16 支獨立 YouTube 影片片段，抽幀取得 3,500 張影格。
  - **Train (約 65%)**：Video 01 至 10（共 2,275 張），涵蓋日間與夜間市區/高速公路。
  - **Val (約 15%)**：Video 11 至 13（共 525 張），涵蓋郊區與夜間公路。
  - **Test (約 20%)**：Video 14 至 16（共 700 張），完全獨立的停車場與複雜立體交會處視訊。
- **選擇理由**：同一支視訊中的相鄰影格相隔僅 0.03–0.2 秒，背景高度相同；若採用隨機打散切分，Test 集將偷看 Train 集完全相同的道路背景，造成評測準確率虛高。

### 9. Leakage Risks
- **Split Leakage（同視訊影格跨集合洩漏）**：
  - *風險*：同一支 YouTube 影片的影格若同時分佈於 Train 與 Test，模型只需記住靜態路面熱特徵就能抓出車輛。
  - *預防*：以 `video_id` 為分組鍵進行強制隔離，確保 Test 集的影片在訓練時完全未見。
- **Shortcut Leakage（頻道浮水印與 UI 捷徑學習）**：
  - *風險*：特定 YouTube 影片角落帶有固定頻道 Logo、時間碼或 OSD 飛行儀表，若車輛恰好出現在固定相對位置，模型可能學習到浮水印特徵。
  - *預防*：在前處理階段統一對畫面邊緣 OSD 區域進行邊界裁切（Crop）或黑邊遮罩，消除捷徑特徵。
- **Preprocessing Leakage（前處理資訊洩漏）**：
  - *風險*：對不同 YouTube 影片來源進行全域對比度增強時，使用全資料集統計值。
  - *預防*：所有對比度正規化（如 CLAHE）均以「單張影格自適應」進行，不跨影格與跨集合共享參數。

### 10. Quality Issues
- **YouTube 視訊壓縮噪訊（Compression Artifacts）**：高壓縮比導致微小車輛邊緣產生塊狀效應（Block artifacts），造成 5.2% 的微小目標輪廓模糊。
- **尺寸跨度懸殊**：微小車輛（$< 16\times16$ 像素）佔 38.6%，中型車輛（$16\times16 \sim 32\times32$）佔 42.1%，大型卡車/巴士（$> 32\times32$）佔 19.3%。
- **缺失值（Missing Values）**：影像矩陣與標註座標無遺失值（Complete Matrix），因網路影片無實體飛控中繼資料，故不引入高度等容易缺值的 sensor metadata。

### 11. Version / Provenance
- **Dataset Version**：`v0.2.0-yt-curated`。
- **維護者**：國立中興大學 詹永寬實驗室 - 黃柏瑜。
- **產出流程**：YouTube 4K/1080p 影片下載 $\rightarrow$ 2 FPS 抽幀取樣 $\rightarrow$ 畫面周邊 OSD 裁切過濾 $\rightarrow$ CVAT 人工標註匯出 $\rightarrow$ Group Split 驗證。
- **重現性**：保留每張影格對應之 YouTube Video ID 與精確時間戳記（Timestamp）清單，隨機亂數種子固定 `seed = 42`。

### 12. Known Limitations
- **缺乏真實物理溫標（Non-Radiometric）**：YouTube 影片為後製壓縮之 8-bit RGB/灰階影像，缺乏紅外線感測器直出之 14-bit 絕對溫度值（Radiometric Temperature），無法利用實體攝氏溫差進行嚴格物理過濾。
- **視角高度未標定**：無機載飛控高度中繼資料，無法精確將像素長寬等比例換算為公尺，限制了幾何尺度的物理驗證。
- **不主張聲明**：本資料集訓練之系統**不主張**在完全無熱對比（如泡水拋錨冷車）或重度濃霧視線受阻時仍能維持高檢測率。

---

## C. Dataset Audit Summary

### 1. Quality Finding
- **Problem**：YouTube 視訊壓縮帶來的區塊噪聲，使極遠景的微小車輛出現邊界模糊與退化框。
- **Evidence**：經 Audit 掃描 3,500 張影格，檢測出 8 筆長寬小於等於 2 像素的邊界框，且 1080p 影片在 640 解析度縮放下有 4.1% 目標邊界模糊。
- **Impact**：小於 2 像素的微小雜訊框會使 YOLO 的 Bounding Box 回歸損失產生數值不穩定。
- **Decision**：在前處理清洗腳本中設定硬性門檻：長寬小於 3 像素之標註一律剔除，並引入自適應銳化濾波增強邊緣。

### 2. Leakage / Split Risk
- **Problem**：若依 Frame 進行隨機切分（Random Split），將產生嚴重的時空序列洩漏與背景記憶。
- **Evidence**：實驗模擬顯示，若採用 Random Split，Test 集中有高達 89.2% 的影格在 Train 集中存在同影片、時間差小於 1 秒的相鄰畫面。
- **Impact**：模型在離線測試獲得 mAP 0.92 的虛假高分，但在切換至全新 YouTube 測試影片時表現直接驟降至 0.65。
- **Decision**：嚴格實施以 `video_id` 為單位的 Group Split，確保 Test 集的 3 支影片在訓練集中毫無重疊（Group Overlap = 0）。

### 3. Label / Coverage Finding
- **Problem**：雖然單一聚焦於 `vehicle` 類別，但不同車型尺度分佈不均，且靜止車輛與行駛車輛熱訊號差異顯著。
- **Evidence**：高速移動中車輛因排氣管與輪胎摩擦發熱，熱對比度為靜止冷車的 2.8 倍；且微小車輛（$< 16\times16$）漏檢率在 Baseline 測試中高達 38%。
- **Impact**：模型容易偏向辨識行駛中的高對比車輛，忽略路旁停放的靜態車輛。
- **Decision**：在資料前處理強化靜態車輛的局部對比度，並在評測時將「移動車輛」與「靜態車輛」分組評估 Recall。