# Week 3 - Dataset Spec v0.2

學號：7114029015
姓名：黃柏瑜
專題名稱：高空紅外線無人機影像車輛偵測（YOLO，邊緣端即時）

> 本文件所有數字都來自 `notebooks/week03_dataset_audit.ipynb` 的實際輸出。

---

## A. 資料怎麼形成

### 1. Source / Owner

| 項目 | 內容 |
| --- | --- |
| Source | HIT-UAV: A high-altitude infrared thermal dataset for UAV-based object detection（Suo et al., *Scientific Data* 10, 227, 2023） |
| 形成方式 | 研究團隊以 DJI Zenmuse XT2（FLIR 長波紅外線 640×512、25 mm 鏡頭）實際飛行錄影，7 FPS 影片每 15 frames 取 1 張，共 2,898 張；3 位標註者以修改版 LabelImg 人工標註並互相檢查 |
| Owner / Provider | 原作者團隊（Jiashun Suo, Tianyi Wang 等）；GitHub `suojiashun/HIT-UAV-Infrared-Thermal-Dataset` |
| 本研究取得的部分 | `normal_json/annotations/{train,val,test}.json`（標準 bbox）；影像本體尚未下載 |
| Extract / Download date | 2026-10-08 |
| License / Permission | GitHub repo LICENSE 為 CC BY 4.0（第三方鏡像站標為 CC0，以原 repo 為準）；學術使用需引用原論文 |

注意：JSON 只是檔案格式，Source 是「原作者團隊的實機飛行錄影 + 人工標註」。

### 2. Unit Alignment（承接 W2，不修改 W2 v0.2）

| W2 定義 | Dataset 對應 | 是否對齊 |
| --- | --- | --- |
| Unit：單張高空 IR 影格 | 一筆 `images` 紀錄 = 一張 640×512 影格（2,898 張，解析度 100% 為 640×512） | 對齊 |
| Input：即時單通道熱影像矩陣 | 影像 JPG（8-bit，非輻射溫度值） | 部分對齊：沒有原始 14-bit 溫度 |
| Input（後處理）：飛行高度、焦距 | 檔名編碼 `altitude_m`（60–130 m）、`angle_deg`（30–90°）；焦距固定 25 mm | 對齊（可做 W2 規劃的尺寸過濾） |
| Target：目標 bbox + class | `annotation.bbox` + `category_id`；`Car` + `OtherVehicle` → `vehicle` | 對齊 |
| W2 Target class 含 `person` | 本研究 Target 已縮為只做 `vehicle`；`Person` 標註保留但不作為 Target | **落差**：需回到 W2 註記範圍調整 |
| W2 假設「目標常 < 16×16 px」 | 車輛框中 tiny 只有 2.5%（見 Finding 2） | **不對齊** |

### 3. Time Range

- 拍攝日期：2020-12-17 至 2021-01-23，共 9 個拍攝日（`date_captured`）。
- 季節：只有冬季（12 月–1 月）。
- 日夜：夜間 1,981 張（68.4%）、白天 917 張（31.6%）。2020-12-17、2021-01-14、2021-01-18 這 3 天只有夜間資料。

### 4. Fields

| 欄位 | 來源 | 角色 | 決策當下可得？ | 說明 |
| --- | --- | --- | --- | --- |
| image pixels | JPG | **Input** | 是 | 640×512 單通道熱影像 |
| `altitude_m` | 檔名第 2 欄 | 後處理 only | 是（飛控即時） | 只用於物理尺寸過濾，不進神經網路 |
| `angle_deg` | 檔名第 3 欄 | 後處理 / 分組評估 | 是（雲台即時） | 不進神經網路 |
| `daynight` | 檔名第 1 欄（0=日、1=夜） | 分組評估 | 可推得 | 只用來分組回報 Recall |
| `weather` | 檔名第 4 欄 | Coverage 檢查 | — | 全部為 `0`（只有非雨天） |
| `serial` | 檔名第 5 欄 | ID／順序 | 否 | 取樣序號，編碼拍攝順序，禁止當特徵 |
| `date_captured` | JSON | **Split key** | 否 | 用於切分 |
| `flight_group` | 衍生：date + daynight + altitude + angle | **Group key**（影片 proxy） | 否 | 資料集沒有 `video_id`，以此近似「同一段飛行影片」 |
| `bbox` `[x, y, w, h]` | 人工標註 | **Target** | 否（事後標註） | 像素座標 |
| `category_id` | 人工標註 | **Target** | 否 | 0 Person／1 Car／2 Bicycle／3 OtherVehicle／4 DontCare |
| `official_split` | JSON 所在檔案 | 禁用 | 否 | 官方切分有洩漏（Finding 1） |

部署時拿不到的欄位：`bbox`、`category_id`、`date_captured`、`serial`、`official_split`，全部不可作為 Input。

### 5. Label / Codebook

- **Target**：影格中每一台機動車輛的 bbox 與類別 `vehicle`。
- **Label field**：`category_id`，映射規則 `vehicle_map_v0.2`：

| 原始類別 | 數量 | v0.2 處理 |
| --- | ---: | --- |
| Car | 7,311 | → `vehicle` |
| OtherVehicle | 148 | → `vehicle`（只佔車輛框 2.0%） |
| Bicycle | 4,980 | 非 Target，訓練時不標為 vehicle |
| DontCare | 148 | 評估時設為忽略區，不算 FP/FN |
| Person | 12,312 | 非 Target |

- **Label source**：原作者 3 人人工標註並互相檢查（Existing human label），本研究沒有重新標註。
- **Codebook 缺口**：原論文沒有給 `OtherVehicle` 的定義，也沒有說明**機車**要標成 Bicycle 還是 OtherVehicle。若機車被標成 Bicycle，依 v0.2 映射會被當成「非車輛」。
- **Known label error**：自動檢查沒有發現重複框、越界框、退化框（w 或 h ≤ 2 px），也沒有發現 area ≠ w×h 的紀錄；長寬比 > 4 的車輛框有 18 個，需目視複核。人工錯標率**未知**，需在拿到影像後抽樣複核（TODO）。

### 6. Inclusion / Exclusion

- **Include**：HIT-UAV 全部 2,898 張影格，包含沒有車輛的影格（1,474 張），作為負樣本用來檢驗誤報。
- **Exclude**：v0.2 不排除任何影格。32 張完全沒有標註的影格先保留為負樣本，待拿到影像後目視確認不是漏標。
- **排除理由**：目前只有標註檔，無法用畫質判斷排除；先不排除，避免為了讓資料變漂亮而丟掉困難樣本。
- **可能 Bias**：資料集本身已只收非雨天（`weather` 全為 0），而且原作者的取樣方式（每 15 frames 取 1 張、部分飛行段只留 2–10 張）可能已經過濾掉模糊或困難畫面。

---

## B. 證據怎麼驗證

### 7. Population / Coverage

- **Target Population**：無人機在 60–130 m 高空、以長波紅外線巡檢道路與停車場時，畫面中出現的所有機動車輛，日夜、四季、各種天候都包含在內。
- **Observed Coverage**：
  - 單一團隊、單一台相機（FLIR 640×512、25 mm）、9 個冬季拍攝日。
  - 高度 60–130 m（8 個等級）、俯角 30–90°（7 個等級）。
  - 日／夜都有，夜間佔 68.4%；車輛框 65.9% 來自夜間（4,914 / 7,459）。
  - 場景包含校園、停車場、道路、操場（依原論文描述，metadata 沒有場景欄位）。
- **Missing Coverage**：
  - 沒有雨、霧、雪（weather 只有 `0`）。
  - 沒有夏季，也沒有熱交叉時段。冬季車輛與地面溫差通常較大，偵測可能比夏季容易。
  - 沒有 > 130 m 的高度；tiny 車輛（< 16×16）只有 184 個框。
  - 大型車與機車的樣本極少，或者類別定義不清（OtherVehicle 只有 148 個）。
  - 沒有其他相機型號，也沒有 YouTube 類型的二次壓縮影像。
- **對結論的影響**：在此資料上得到的結果，只能代表「冬季、非雨天、同型 FLIR 相機、≤ 130 m」條件下的中大型車輛偵測。

### 8. Train / Validation / Test Rule

- **Test 模擬的未知**：**未見過的新飛行任務日**。部署時無人機一定是在新的一天、新的一次起降、新的光照與溫度條件下飛行，所以 Test 不能和 Train 共用同一次飛行。
- **Split 決策樹**：

| 問題 | 答案 | 理由 |
| --- | --- | --- |
| Q1 Test 是未來資料嗎？ | 是 | 模型是先訓練再部署到之後的任務 |
| Q2 同一 group 會重複出現嗎？ | 是 | 每個 `flight_group` 平均 11 張、最多 150 張連續取樣影格 |
| Q3 樣本近似 i.i.d.？ | 否 | 同一段飛行的相鄰影格只差約 2 秒，背景幾乎相同 |

- **最終 Split**：依 `date_captured` 做 **Group + Time Split**，不使用官方 split，也不使用 random split。

| Split | 日期 | 影像 | 含車影像 | vehicle 框 | 日／夜影像 |
| --- | --- | ---: | ---: | ---: | --- |
| Train | 2020-12-17、2021-01-14、15、16、18、20 | 1,954（67.4%） | 617 | 3,707 | 466 / 1,488 |
| Val | 2021-01-19 | 316（10.9%） | 310 | 1,263 | 148 / 168 |
| Test | 2021-01-21、2021-01-23（最後兩天） | 628（21.7%） | 497 | 2,489 | 303 / 325 |

- **檢查結果**：Train∩Test 的 flight_group overlap = 0，日期 overlap = 0；Test 影像在 Train 中有相鄰取樣影格的比例 = 0.0%。
- **選擇理由**：Test 取最後兩天，同時滿足「未來」與「新飛行」。這兩天都有日／夜資料，可以分開回報結果。Val 選 01-19 也是因為它日夜都有。

### 9. Leakage Risks

| 類型 | 本資料中的具體來源 | 預防方式 |
| --- | --- | --- |
| **Split Leakage** | 官方 split 中 264 個 flight_group 有 240 個跨 split；官方 Test 100% 的影像在 Train 有同一段飛行，31.3% 有相鄰取樣影格（約 2 秒內） | 改用日期 Group／Time Split，group overlap = 0 |
| **Metadata／檔名 Leakage** | 檔名編碼日期順序、高度、角度、日夜；`serial` 與拍攝順序相關 | 模型 Input 只用像素；檔名欄位只用於切分與分組報告 |
| **Target-derived** | `DontCare` 是標註者看完答案後才畫的區域；若用它遮掉 Test 影像，等於提前知道困難位置 | DontCare 只在評估時忽略，不能在推論前遮罩 Input |
| **Tuning Leakage** | 用 Test 調 NMS、信心度門檻，或依 altitude 調尺寸過濾門檻 | 門檻只在 Val（01-19）上搜尋，Test 鎖定 |
| **Preprocessing Leakage** | 全資料計算影像 mean/std 正規化或 anchor 聚類（YOLO autoanchor 會掃 label 尺寸） | 先切分；normalization 統計值與 anchor 只用 Train fit，再套到 Val／Test |

### 10. Quality Issues

| 檢查 | 結果 |
| --- | --- |
| Missing values | 0（影像與標註欄位皆無缺值） |
| Duplicate filename／image id／serial | 0／0／0 |
| Duplicate boxes（同影像同座標） | 0 |
| Out-of-bound boxes | 0 |
| Degenerate vehicle boxes（w 或 h ≤ 2 px） | 0 |
| 無任何標註的影像 | 32 張 |
| 無車輛的影像 | 1,474 張（50.9%），其中 2020-12-17 整天 587 張都沒有車 |
| 車輛類別不平衡 | Car 7,311 vs OtherVehicle 148（2.0%） |
| 尺度分布 | tiny < 16² 為 2.5%、small 16²–32² 為 22.1%、≥ 32² 為 75.5%；車輛框邊長中位數 46.8 px |
| 近重複 | 同一 flight_group 的連續取樣影格（約 2 秒間隔）屬於近重複，以 Group Split 處理 |

**目前最重要的 Quality Risk**：資料本身很乾淨，風險不在髒資料，而在**資料分布和研究主張不一致**，也就是 tiny 目標太少（見 Finding 2）。

### 11. Version / Provenance

| 項目 | 內容 |
| --- | --- |
| Dataset version | `hituav-vehicle-v0.2`（本研究映射版） |
| Upstream version | HIT-UAV JSON `info.version = 1.0`，GitHub `main` 分支 `normal_json/annotations` |
| Extract date | 2026-10-08 |
| Cleaning rule | 不刪任何影格；`Car`、`OtherVehicle` → `vehicle`；`DontCare` → ignore；`Bicycle`、`Person` → 非 Target |
| Label version | 原作者人工標註（未修改）＋ `vehicle_map_v0.2` |
| Split rule / seed | 依 `date_captured`：Test = 20210121、20210123；Val = 20210119；其餘為 Train。規則是確定性的，不需要 random seed |
| 重現方式 | 執行 `notebooks/week03_dataset_audit.ipynb`，若本機沒有資料會自動從 GitHub 下載 JSON |
| 停用的舊版 | `data/v0.2.0-yt-curated/manifest.csv`、`data/datagenerate.py`（隨機生成，非真實資料） |

### 12. Known Limitations

| Limitation | Evidence | 影響 | 因此不主張 |
| --- | --- | --- | --- |
| 微小車輛樣本不足 | tiny（< 16×16）只有 184 框（2.5%），其中 130 m 也只佔 9.5% | 無法可靠驗證 W2 的 tiny-object 指標（IoU ≥ 0.3 輔助驗收） | 不主張模型能偵測 < 16×16 px 的車輛 |
| 只有冬季、非雨天 | 9 個拍攝日都在 12–1 月；weather 全為 0 | 冬季溫差大，結果可能偏樂觀 | 不主張適用夏季、熱交叉、雨霧雪 |
| 單一相機、無原始溫度 | 只有 8-bit JPG，同一台 FLIR 640×512 | 無法用攝氏溫度門檻；換相機可能掉分 | 不主張可直接遷移到其他熱像儀或 YouTube 壓縮影像 |
| 車輛子類別定義不清 | OtherVehicle 148 框、無定義；機車歸類未知 | 「vehicle」實際上主要是小客車 | 不主張能偵測大型車與機車 |
| 場景未知 | metadata 沒有地點欄位 | 日期切分無法保證 Test 是全新地點，同一校園可能在不同天重複出現 | 不主張已驗證「全新地理場景」泛化 |

---

## C. Dataset Audit Summary（Problem → Evidence → Impact → Decision）

### Finding 1 — Leakage / Split Risk：官方 Split 跨飛行段洩漏
- **Problem**：HIT-UAV 官方 train/val/test 是依影格切分。同一段飛行影片的連續取樣影格分散在不同 split。
- **Evidence**：264 個 flight_group 中有 240 個跨越 2 個以上 split；官方 Test 579 張影像 100% 能在 Train 找到同一 flight_group，31.3% 在 Train 有相鄰取樣影格（serial 差 1，約 2 秒），49.4% 的 serial 差 ≤ 2。
- **Impact**：Test 只是在測「同一段影片的下一張」，模型可以靠背景記憶得分，分數會高估部署到新任務日的表現。
- **Decision**：不使用官方 split，改用依日期的 Group／Time Split。結果是 group overlap = 0、date overlap = 0、相鄰影格比例 0.0%。W4 baseline 一律使用 v0.2 split。

### Finding 2 — Label / Coverage：資料不支持 W2 的「微小目標」主張
- **Problem**：W2 把問題定義為微小目標偵測，Success Criteria 也針對 < 16×16 px 目標，但資料中的車輛大多是中大型。
- **Evidence**：7,459 個車輛框中，tiny（< 16²）184 個（2.5%）、small 1,645 個（22.1%）、≥ 32² 有 5,630 個（75.5%），邊長中位數 46.8 px。即使在 130 m，tiny 也只佔 9.5%；60 m 邊長中位數 76.9 px，130 m 為 29.6 px。
- **Impact**：tiny 只有 184 框，加上切分後 Test 只剩其中一部分，Recall 的信賴區間會很寬，無法驗證 W2 的 tiny 指標。若只看整體 mAP，結果主要反映中大型車輛的表現。
- **Decision**：主要指標改為整體 vehicle mAP@0.5，並依尺度（tiny/small/medium+）與高度分層回報。tiny 指標標記為「樣本不足、僅供參考」。下一版需要補充更高空或更小目標的資料，或回頭修正 W2 的問題範圍。

### Finding 3 — Quality：資料乾淨但類別與日夜不平衡
- **Problem**：自動檢查沒有缺值和錯誤框，但 Target 內部與條件分布不均。
- **Evidence**：缺值、重複框、越界框、退化框都是 0；OtherVehicle 只佔車輛框 2.0%；車輛框 65.9% 來自夜間；2020-12-17 的 587 張影像沒有任何車輛；v0.2 Train 只有 617 張含車影像，比 Test 的 497 張多不了多少。
- **Impact**：模型主要學到夜間小客車。Train 中含車影像偏少，可能限制 YOLO 微調效果。
- **Decision**：保留無車影像作為負樣本，用來測虛警。評估時分日／夜回報；不對 OtherVehicle 單獨下結論。若 Train 含車影像不足，W4 再評估 Train／Val 日期配置（只能動 Train／Val，Test 鎖定）。

---

## D. Mini Defense

**Q1｜Test set 要模擬哪一種 Unknown？**
我的 Test set 模擬「未見過的新飛行任務日」，所以採用依日期的 Group／Time Split。具體切法是把最後兩個拍攝日（2021-01-21、01-23，628 張、2,489 個車輛框，日夜都有）當 Test，01-19 當 Val，其餘 6 天當 Train。

**Q2｜為什麼選擇目前的 Split Strategy？**
因為同一段飛行影片的相鄰影格只差約 2 秒，背景幾乎一樣，不是 i.i.d.。Audit 顯示官方 split 的 Test 影像 100% 和 Train 共用同一段飛行，31.3% 在 Train 裡有相鄰影格，Random Split 也會有同樣問題。部署時無人機一定是在新的一天起飛，所以要按日期整天切開，而且 Test 放最後的日期。驗證結果：flight_group overlap = 0。

**Q3｜最可能造成 Leakage 的欄位或資料流程是什麼？**
最主要的是資料流程：直接沿用 HIT-UAV 官方 split，同一飛行段會跨 Train／Test。欄位方面，檔名與 `serial` 編碼了拍攝日期順序、高度、日夜，部署時這些標註 metadata 不會以這種形式存在，不能進模型；`DontCare` 是看過答案才畫的區域，只能在評估時忽略，不能拿來遮 Input。

**Q4｜目前 Dataset 最重要的 Coverage Limitation 是什麼？**
目前資料只涵蓋冬季、非雨天、單一 FLIR 相機、60–130 m 高度下以中大型小客車為主的車輛，沒有夏季與熱交叉時段，也沒有足夠的 < 16×16 px 微小車輛（只有 2.5%）。因此結果不能直接泛化到微小目標偵測、夏季或雨霧天候、或其他相機與 YouTube 壓縮影像。

---

## 附：v0.1 → v0.2 修改紀錄

| v0.1（舊稿） | v0.2 | 依據 |
| --- | --- | --- |
| Source：YouTube 16 支影片 3,500 張 | Source：HIT-UAV 2,898 張（真實公開資料） | 舊稿資料不存在；manifest 為隨機生成 |
| Group key：`video_id` | Group key：`flight_group` proxy＋日期切分 | HIT-UAV 沒有 video_id；serial 區間互不重疊，支持此 proxy |
| tiny 車輛 38.6% | tiny 車輛 2.5% | Notebook 第 6 節 |
| Random split 洩漏 89.2%（模擬） | 官方 split：同 group 100%、相鄰影格 31.3% | Notebook 第 8 節 |
| 刪除 8 個退化框 | 退化框 0，不需刪除 | Notebook 第 5 節 |
| 浮水印裁切 16 px | 不適用（HIT-UAV 為原始相機輸出，無頻道浮水印） | 資料來源改變 |
