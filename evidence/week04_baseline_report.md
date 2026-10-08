# Week 4 Baseline Report v1.0

學號：7114029015

姓名：黃柏瑜

> 本報告所有數字來自 `notebooks/week04_baseline.ipynb` 的實際執行輸出（`outputs/week04_*.csv`）。

## 1. Task & Dataset

本週沿用 W2 AI Problem Spec v0.2 與 W3 Dataset Spec v0.2，不重新定義題目或資料。

- **Task**：高空無人機長波紅外線單張影格的車輛偵測（object detection）。
- **Unit**：單張 640×512 IR 影格。
- **Input**：單張灰階影格像素。高度、角度、日期、檔名都不進入任何方法。
- **Target / Label**：`vehicle` 邊界框，由 `Car` + `OtherVehicle` 合併（W3 `vehicle_map_v0.2`）；`DontCare` 區域在評估時忽略。
- **Dataset version**：`hituav-vehicle-v0.2`，來源為 HIT-UAV `normal_json`。
- **Split**：沿用 W3 的 Group/Time Split，依 `date_captured` 切分，`flight_group` overlap = 0。

| split | dates | frames | vehicle boxes |
| --- | --- | ---: | ---: |
| train | 20201217, 20210114, 0115, 0116, 0118, 0120 | 1,954 | 3,707 |
| validation | 20210119 | 316 | 1,263 |
| test（locked） | 20210121, 20210123 | 628 | 2,489 |

Test 車輛的尺度分布：medium+（≥ 32²）1,802、small（16²–32²）674、tiny（< 16²）13。

**本週新發現的 Data Check**：比較每個車輛框內外的平均灰階，**70.6% 的車輛比周圍背景暗**（夜間 84.9%、白天 43.1%）。停放的車在畫面上多半是「冷」的。W2 假設「車輛是熱源亮點」，這在本資料上不成立，直接影響 Baseline 設計。

## 2. Baseline Plan

| Role | Method | 出處 | Why reasonable | Expected weakness |
| --- | --- | --- | --- | --- |
| Baseline 1（current / naive） | 全域 Otsu 門檻 + 連通元件（亮像素 = 目標），面積與長寬比範圍取自 Train GT 的第 1–99 百分位 | Otsu (1979)；W2 v0.2 定義的現行 baseline | 熱像儀韌體與地面站常見的「找熱點」做法，零訓練、極便宜，是 W2 已承諾的比較基準 | 只抓亮像素；冷車、日照路面都會出問題 |
| Baseline 2（credible simple） | 雙極性局部對比候選框 + HOG/幾何特徵 + 分類器 | 背景相減／Top-Hat 類紅外目標偵測（Rivest & Fortin, 1996）＋ HOG（Dalal & Triggs, 2005）＋ Gradient Boosting（Friedman, 2001；scikit-learn HistGradientBoosting） | 「不用深度學習時，合理的人會先試的」經典偵測流程：先用影像處理找候選區，再用 Train 學一個簡單分類器過濾。依據 Data Check，候選框**亮、暗兩個方向都抓**，所以不是故意做差的 strawman | 候選框召回率有上限（Val 約 0.68）；相鄰車輛容易被合成一個框；HOG 對斜視角與遮蔽不穩 |
| Candidate | YOLO11n（COCO 預訓練，在 Train 上微調 20 epochs） | Ultralytics YOLO11（Jocher & Qiu, 2024）；W2 定義的 AI 方法 | 邊緣端可部署的最小 YOLO，用來檢查深度學習是否有增量價值 | 需要 GPU/NPU 才能達到即時；小目標、斜視角仍可能失敗 |

Baseline 2 有兩個分類器版本：LR 的 Val AP@0.5 = 0.163，GB 的 Val AP@0.5 = 0.324。只依 Validation 選擇，最終採用 **B2b HOG+GB**。

本週不測更大的模型（YOLO11s/m、RT-DETR、Transformer）。W4 的目標是先確認 baseline evidence，以及邊緣端最小夠用的複雜度。

## 3. Fair Comparison / Experiment Spec

- Dataset version = `hituav-vehicle-v0.2`（HIT-UAV normal_json；Car + OtherVehicle → vehicle）
- Split = Group/Time split by `date_captured`；Seed / Boundary = seed 42（B2 負樣本抽樣、YOLO 訓練）／Train = 6 個較早日期、Val = 20210119、Test = 20210121 + 20210123
- Baseline 1 = Global Otsu + CCA（hot pixels）
- Baseline 2 = Bi-polar local-contrast proposals + HOG/geometry + HistGradientBoosting（LR 版本於 Val 淘汰）
- Primary Metric = vehicle AP@0.5（Test，越高越好）
- Failure Metric = vehicle Miss Rate = FN / GT（於 Val 選定門檻，越低越好）；輔助指標為 False alarms per 100 frames（越低越好）
- Threshold policy = 每個方法都在 Validation 上取 F1 最大的 score 門檻；Test 鎖定，不調參
- Information boundary = 只用單張灰階影格像素；不使用高度、角度、日期、檔名；`DontCare` 只在評估時忽略（與它重疊 ≥ 50% 的預測不計為 FP）
- Runtime / Cost 記錄方式 = 同一台 2-core CPU（無 GPU），計算每張影格平均 ms，包含偵測與分類、不含讀檔；YOLO 先 warm-up 再計時

其他固定條件：

- **Evaluation unit**：單一車輛框，IoU ≥ 0.5 才算命中，每張影格依分數高低做 greedy matching。
- **相同 test set**：三個方法使用同一份 628 張 locked test。
- **訓練資料**：B2 用 Train 全部影格產生的候選框（正樣本全取、負樣本抽 15%）；YOLO 用 Train 中全部 617 張含車影格加 300 張隨機無車影格。這是因為 CPU 訓練時間有限，屬於只動 Train 的設計選擇，**不影響 Test 公平性**。

## 4. Results

Locked Test set（628 frames、2,489 vehicles）：

| Method | Dataset / Information | Primary：Test AP@0.5 ↑ | Failure：Miss Rate ↓ | False alarms / 100 frames ↓ | Recall | Precision | Runtime（ms/frame，CPU） | Complexity | Note |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| B1 Otsu + CCA | IR pixels only; date split v0.2 | 0.0081 | 0.9534 | 244.4 | 0.047 | 0.070 | 6.1 | Low | W2 current baseline |
| B2 Local-contrast + HOG + GB | IR pixels only; date split v0.2 | 0.3637 | 0.5496 | 201.4 | 0.450 | 0.470 | 86.2 | Low–Mid | Credible simple baseline |
| YOLO11n（Candidate） | IR pixels only; date split v0.2 | **0.7832** | **0.2929** | **56.8** | 0.707 | 0.831 | 56.9 | Mid | 20 epochs, imgsz 512 |

Validation AP@0.5：B1 0.0004、B2 0.3242、YOLO11n 0.7186。

**穩定性**：Test 的兩個日期分開計算 AP@0.5。

| Method | 2021-01-21（1,725 vehicles） | 2021-01-23（764 vehicles） |
| --- | ---: | ---: |
| B1 | 0.004 | 0.017 |
| B2 | 0.329 | 0.457 |
| YOLO11n | 0.810 | 0.730 |

兩天的排名都是 YOLO11n > B2 > B1，差距也遠大於日期間的波動。

**分組 Recall**（在各自的 Val 門檻下）：

| Subgroup | n_gt | B1 | B2 | YOLO11n | YOLO − B2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 冷車（比背景暗） | 1,436 | 0.001 | 0.410 | 0.670 | +0.26 |
| 熱車（比背景亮） | 1,053 | 0.108 | 0.506 | 0.758 | +0.25 |
| 夜間 | 1,132 | 0.026 | 0.400 | 0.653 | +0.25 |
| 白天 | 1,357 | 0.063 | 0.492 | 0.752 | +0.26 |
| small（16²–32²） | 674 | 0.025 | 0.203 | 0.539 | **+0.34** |
| medium+（≥ 32²） | 1,802 | 0.054 | 0.546 | 0.774 | +0.23 |
| tiny（< 16²） | 13 | 0.077 | 0.000 | 0.154 | 樣本太少 |
| 相機俯角 30° | 610 | 0.018 | 0.159 | **0.405** | +0.25 |
| 相機俯角 60–90° | 1,139 | 0.06–0.08 | 0.60–0.72 | 0.80–0.91 | +0.14–0.30 |
| 高度 110 m | 571 | 0.007 | 0.282 | 0.718 | **+0.44** |
| 高度 130 m | 381 | 0.032 | 0.323 | 0.491 | +0.17 |

Interpretation：

- **B1 幾乎完全失效**（AP 0.008）。原因不是門檻沒調好，而是假設錯了：70.6% 的車是冷的，冷車的 B1 recall 只有 0.001。全域 Otsu 抓到的多是大片建物或路面，被尺寸規則濾掉後就什麼都不剩。
- **B2 是有意義的比較線**：AP 0.364，冷車 recall 0.410，證明雙極性設計有效；但仍漏掉 55% 的車，每 100 張影格有 201 次誤報。
- **YOLO11n 在 Primary 與 Failure 指標上都大幅領先**：AP 0.364 → 0.783，miss rate 0.550 → 0.293，誤報 201 → 57 次／100 張。在本次 CPU 上也比 B2 更快（56.9 vs 86.2 ms），因為 B2 每張影格要對約 200 多個候選框算 HOG。
- **YOLO 仍未完全達到 W2 Success**：
  - 整體 AP 0.783 ≥ 0.75，有達標。
  - small 車輛 recall 只有 0.539，30° 斜視角只有 0.405，130 m 只有 0.491。
  - CPU 上約 17.6 FPS，**尚未在 Jetson 等邊緣裝置驗證 ≥ 30 FPS**。

## 5. Failure Analysis

代表性案例由 notebook 依規則自動挑選，圖片存在 `outputs/week04_failure_cases/`（綠 = 命中、紅 = 漏檢、黃 = 誤報）。

| Case | Method | Unit（frame） | Ground Truth | Prediction | Failure type | Possible cause | Decision impact |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | B1 Otsu+CCA | `1_110_30_0_09028.jpg`（夜、110 m、30°） | 13 輛停放車輛，13 輛都比背景暗 | 0 個偵測 | 冷目標全漏（polarity failure） | **Feature／假設錯誤**：停放車輛的引擎已冷，熱像上比柏油暗；Otsu 只切亮像素，亮區是建物與地面大區塊，被尺寸規則濾掉 | 整個停車場被判定「沒有車」，不會觸發任何警報。對應 W2 Failure「連續漏檢」 |
| 2 | B2 HOG+GB | `1_130_30_0_09965.jpg`（夜、130 m、30°） | 9 輛小型車，大多擠在畫面上方同一排 | 1 命中、8 漏檢、3 誤報（其中一框把相鄰兩車合成一個，另兩框落在暗色長方形建物結構上） | 相鄰目標合併 ＋ 結構誤報 | **Model／Proposal 限制**：局部對比門檻把相鄰暗車連成同一個連通元件，框過大導致 IoU < 0.5；HOG 無法分辨「暗色長方形建物」和「暗色車」。全 Test 中有 70 個 B2 誤報框同時蓋住 ≥ 2 輛車 | 車輛數被低估，同時在無車處報警。地面站人員要花時間確認假警報 |
| 3 | YOLO11n | `0_100_30_0_08087.jpg`（日、100 m、30°） | 18 輛，多數在畫面遠端的停車場 | 3 命中、15 漏檢、1 誤報 | 斜視角遠景小目標漏檢 | **Data／Resolution**：30° 斜視下遠端車輛只有約 15–30 px，部分被樹遮或被畫面右緣截斷；訓練輸入縮到 512，小目標再被縮小。15 個漏檢中 13 個是 small 或 tiny，且多數其實比背景亮，所以不是 polarity 問題 | 斜視巡檢時遠處車輛看不到。30° 俯角整體 recall 只有 0.405，是 Candidate 最大的剩餘 failure |
| 4 | YOLO11n | `0_110_30_0_08339.jpg`（日、110 m、30°） | 28 輛（停車場） | 25 命中、3 漏檢、11 誤報 | 規則紋理誤報 ＋ 框偏移 | **Data（缺 hard negatives）＋ Localization**：建物窗戶、路燈底座等方形高對比紋理被當成車（分數 0.27–0.44）；最高分的誤報（0.80、0.70）緊貼在畫面右下的漏檢車旁，屬於框位置偏移造成 IoU < 0.5，不是看錯物體 | 車在畫面中大多有抓到，但每張影格多出約 10 個框。若直接接到警報，會違反 W2「虛警過多迫使飛手關閉系統」的 Failure Criteria |

Failure interpretation：

- **B1 的失敗是假設錯誤，不是調參問題**：冷車占漏檢的大宗。W2 的 Baseline 定義要修正為「雙極性」。
- **B2 的失敗集中在 proposal 品質**：相鄰合併、結構誤報，而且候選框召回率上限只有約 0.68。
- **YOLO 的剩餘失敗集中在三類**：small 目標、30° 斜視角遠景、規則紋理誤報。前兩者屬於解析度與資料問題，第三者屬於 hard negative 不足。三者都不直接指向「模型容量不足」。
- YOLO 漏掉的車中，65.0% 是冷車；冷車占全部 Test 車輛的 57.7%。可見冷車仍略偏難，但已經不是主因。

## 6. Minimum Sufficient Solution

- **Minimum Sufficient Solution**：YOLO11n（imgsz 512、Val 選定門檻 0.25）。這是暫定選擇，目前只有它在本資料上接近 W2 Success。
- **Evidence**：在相同 Dataset、Split、Metric、Information boundary 下：
  - Test AP@0.5 = 0.783（B2 0.364、B1 0.008）
  - Miss Rate = 0.293（B2 0.550）
  - 誤報 = 56.8 次／100 frames（B2 201.4）
  - 兩個 Test 日期都是相同排名
- **Cost / Risk**：
  - 需要深度學習的訓練與部署流程；本次 CPU 訓練約 1.5 小時。
  - 模型檔 5.4 MB。
  - CPU 推論 56.9 ms/frame，比 B2 還快，但仍需在邊緣 GPU/NPU 驗證 ≥ 30 FPS。
  - 黑盒模型需要監控資料漂移，尤其是季節變化與不同相機。
- **目前是否需要升級到更複雜的模型（例如 YOLO11s/m、Transformer）**：No。
- **理由**：剩餘 failure 是 small、斜視角遠景、紋理誤報，原因落在 Data（解析度、hard negatives、訓練量）與 Decision（門檻、時間濾波）。在用同樣的 YOLO11n 補完這些之前，沒有 evidence 顯示問題出在模型容量。

## 7. Solution Choice Note

- **Current evidence**：YOLO11n 在 Primary（AP 0.783 vs 0.364）與 Failure（miss 0.293 vs 0.550）上都明顯優於 credible baseline B2，而且兩個 Test 日期一致。W2 定義的 Otsu baseline 因為 70.6% 的車是冷目標而完全失效。
- **Remaining failure**：
  - small 車輛 recall 0.539
  - 30° 斜視角 recall 0.405
  - 130 m recall 0.491
  - 建物窗戶、路燈底座等規則紋理誤報，每 100 張約 57 個
- **Minimum solution**：YOLO11n（暫定）。
- **Next candidate**：仍是 YOLO11n，但要先排除 Data 與 Decision 這兩個原因：
  1. 輸入解析度改為 640，或用 tiling（切片推論）處理遠景小目標。
  2. 用 Train 全部無車影格加上紋理類 hard negatives，訓練更多 epochs。
  3. 加入跨影格時間濾波（同一位置連續 N 幀才警報）來壓低虛警。

  只有在上述做完後 small／30° recall 仍明顯不足，才測 YOLO11s，並以相同 split 與 metric 比較。
- **Justification（Complexity Gate）**：
  1. Baseline 未達 W2 Success，失敗原因主要是 Data 和 Feature 層面（解析度、斜視角、負樣本）。
  2. 解析度與 tiling 直接對應 small 與遠景 failure，有機會解決。
  3. YOLO11s 的運算量約為 n 的 3 倍，會壓縮邊緣端 30 FPS 的預算，必須有集中在高風險子群的增益才值得。
  4. 可以用同一 split、metric、門檻政策公平測試。

詳細內容另見 `evidence/week04_solution_choice_note.md`。

## 8. Reproducibility / Run Record

- **Notebook**：`notebooks/week04_baseline.ipynb`（已執行並保留輸出；預設 `TRAIN_YOLO=False`，直接載入已訓練權重）
- **Code**：`src/week04_baselines.py`（資料載入、B1/B2 演算法、共用評估：matching、AP、門檻政策）
- **Data**：
  - 標註：`data/hit_uav/normal_json/{train,val,test}.json`
  - 影像：`data/hit_uav/images/`，notebook 會自動從 HIT-UAV GitHub 下載，不 commit
- **Model**：`models/week04_yolo11n_hituav_v02.pt`
  - 起點：COCO 預訓練 `yolo11n.pt`
  - 設定：20 epochs、imgsz 512、batch 16、seed 42、`deterministic=True`、CPU
- **Output artifacts**：
  - 結果：`outputs/week04_results.csv`
  - 分組 recall：`outputs/week04_subgroup_recall.csv`
  - 依日期的 AP：`outputs/week04_test_by_date.csv`
  - Failure cases：`outputs/week04_failure_cases.csv` 與 `outputs/week04_failure_cases/*.jpg`
  - Run records：`outputs/week04_run_records.csv`（記錄 run_name、data version、split、seed、threshold、feature set、metrics、runtime）
- **Random seed**：42
- **Runtime 環境**：2-core x86 CPU，無 GPU；Python 3.13、ultralytics 8.4、scikit-learn、opencv-python-headless、scikit-image
- **Commit message suggestion**：`Complete Week 4 baseline report`

## 9. Mini Defense

### Q1. 為什麼你的 Baseline 是合理的？以及 Baseline 的出處

我的 Task 是高空 IR 單張影格的車輛偵測，所有方法都只使用同一張灰階影格的像素。

- **Baseline 1：全域 Otsu + 連通元件**
  - 出處：Otsu (1979)，以及 W2 v0.2 中定義的現行做法。
  - 合理的原因：「找熱點」是熱像儀與地面站最常見、零訓練成本的方法，也是 W2 已承諾要比較的基準。它的尺寸範圍取自 Train GT，並沒有被故意做弱。
- **Baseline 2：雙極性局部對比候選框 + HOG + Gradient Boosting**
  - 出處：紅外目標偵測常用的背景相減／Top-Hat 思路（Rivest & Fortin, 1996）、HOG 特徵（Dalal & Triggs, 2005）、Gradient Boosting（Friedman, 2001）。
  - 合理的原因：這是「不用深度學習時，合理研究者會先試的」經典流程。我也根據 Data Check（70.6% 的車比背景暗）把候選框改成亮暗兩個方向都抓。
  - 分類器版本只在 Validation 上選擇（LR 0.163 vs GB 0.324）。

所以 B2 是 credible baseline，不是為了襯托 YOLO 的 strawman。

### Q2. 複雜模型增加的效益主要集中在哪些案例？

相較 B2，YOLO11n 的 AP 從 0.364 提升到 0.783，miss rate 從 0.550 降到 0.293，誤報從每 100 張 201 次降到 57 次。

- **增益最大的子群**：
  - small 車輛（16²–32²）：recall 0.203 → 0.539（+0.34）
  - 110 m 高度：0.282 → 0.718（+0.44）
  - 冷車：0.410 → 0.670（+0.26）
  - 夜間：0.400 → 0.653（+0.25）

  這些正是 B2 的候選框與 HOG 處理不好的案例：相鄰合併、暗色結構誤報。
- **仍未解決**：30° 斜視角遠景（recall 0.405）、130 m（0.491）、tiny 目標（13 個只抓到 2 個），以及建物窗戶類的紋理誤報（Failure Case 3、4）。

因此，增益的決策價值在於：漏檢與誤報同時大幅下降，從「不可用」變成「接近 W2 Success」。剩下的風險集中在斜視遠景與小目標。

### Q3. 如果複雜模型只提升 1–2%，你還會選它嗎？為什麼？

先說明：本週 YOLO11n 相對 B2 的提升是 +42 個 AP 百分點，不是 1–2%，所以本週選擇 YOLO11n 是有 evidence 的。

至於下一步是否要從 YOLO11n 升到 YOLO11s：

- **如果只是整體 AP 提升 1–2%，我不會選。** YOLO11s 的運算量約為 n 的 3 倍，會吃掉邊緣端 30 FPS 的延遲預算，也會增加功耗與發熱。W2 Failure Criteria 明確寫到「推論 < 15 FPS 即為系統失敗」，對搜救或巡檢來說，畫面卡頓的代價比 1–2% AP 更大。
- **我會改選的條件**：1–2% 的整體提升如果集中在高風險子群，例如 30° 斜視角或 small 車輛的 recall 明顯上升（這些是目前 miss rate 最高的地方）；或者連續漏檢的影格數下降，而且在 Jetson 上仍能 ≥ 30 FPS。在這種情況下，增益直接降低真正的 Failure Cost，我會選它。

所以決策看的是「增益落在哪裡」以及「延遲成本是否在預算內」，不是只看平均分數。

---

### References

- Otsu, N. (1979). A threshold selection method from gray-level histograms. *IEEE Trans. Systems, Man, and Cybernetics*, 9(1), 62–66.
- Rivest, J.-F., & Fortin, R. (1996). Detection of dim targets in digital infrared imagery by morphological image processing. *Optical Engineering*, 35(7).
- Dalal, N., & Triggs, B. (2005). Histograms of oriented gradients for human detection. *CVPR*.
- Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. *Annals of Statistics*, 29(5).
- Jocher, G., & Qiu, J. (2024). Ultralytics YOLO11. https://github.com/ultralytics/ultralytics
- Suo, J. et al. (2023). HIT-UAV: A high-altitude infrared thermal dataset for UAV-based object detection. *Scientific Data*, 10, 227.
