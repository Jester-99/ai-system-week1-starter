# Week 3 Dataset Audit Summary

學號：7114029015

姓名：黃柏瑜

## Dataset

```text
D:\thesis_experiments\ir_mtd_dataset   (碩論 YouTube 空拍紅外線影片資料集，外部唯讀掛載)
outputs/week03_audit_metrics.csv       (納入 Gitea 版本控制之結構化稽核統計表)
```

## Audit Results

| Check | Result |
| --- | --- |
| Shots (分鏡數) | $62$（訓練 $50$／測試 $12$，時長 $1.0\text{ s} \sim 4.17\text{ s}$，$30\text{ FPS}$） |
| Raw IR Images (Units) | $2,852$（訓練 $2,454$／測試 $398$，$600 \times 450 \to 640 \times 640$） |
| 3-Channel Valid Images (IR+SD+Flow) | $2,531$（訓練 $2,209$／測試 $322$） |
| Missing values (光流／SD 缺失影格) | $321$（訓練缺 $245$ 張佔 $10.0\%$／測試缺 $76$ 張佔 $19.1\%$） |
| Duplicate shot_id / box | $0$ / $0$（已於本機外部實驗目錄確認；同分鏡 $30\text{ FPS}$ 相鄰幀為時序連續近重複） |
| Out-of-bound / Degenerate boxes | $0$ / $0$（已於本機外部實驗目錄掃描確認；評估匹配門檻為 $\text{IoU} = 0.1$） |
| Target category | 單一類別 `0: 目標物`（含動態與靜態目標物，每分鏡 $1 \sim 5$ 個目標） |
| Stage 2 Dynamic Frame Boxes ($\text{conf}=0.05$) | $1,239$ 框（TP $383$／FP $856$，另有漏檢 FN $70$） |
| Stage 2 Filter ($\epsilon = 2^\circ$) | 濾除 $156$ 框（正確濾除 FP $134$ 佔 $15.7\%$／誤刪 TP $22$ 佔 $5.7\%$） |
| Stage 3 Crops ($299 \times 299$) | 過濾前 $1,653$（背景 $1,156$／目標 $497$）$\to$ 過濾後 $1,497$（背景 $976$／目標 $521$） |
| Background SCR (局部信雜比) | 單純背景平均 $2.54$／複雜背景平均 $0.43$ |
| Group field | `shot_id`（$62$ 組）與來源影片 `video_id`（$16$ 組影片 proxy） |
| Thesis split / tuning leakage | 無獨立驗證集（門檻於評估集選定）；全域正規化統計整組影像；同影片分鏡可能跨 split |
| v0.2 split overlap | Train ($40$) $\cap$ Val ($10$) $\cap$ Test ($12$) 之 `shot_id` 與 `video_id` overlap $= 0$ |

## One Data Quality Issue

標註檔本身無格式越界或重複框（皆為 $0$），但三通道特徵轉換時，因各分鏡前 $6$ 幀時序窗口不足或無法生成光流圖，導致訓練集流失 $245$ 張（$10.0\%$）、測試集流失 $76$ 張（$19.1\%$），直接剔除會使三通道模型（$322$ 張）與原始 IR Baseline（$398$ 張）評估分母不一致而產生存活者偏差；此外第三階段過濾後人工額外補入 $100$ 張背景且目標子影像反增 $24$ 張（$497 \to 521$），母體並非單純刪減。

## One Leakage / Split Risk

原論文僅以分鏡切分（$50$ 訓練／$12$ 測試）而未綁定來源 `video_id`，且未設獨立 Validation set，直接在評估資料上比較選定信心閾值（$0.05$）、動靜態門檻（$\theta_{\text{SD}}=15, \theta_{\text{OF}}=1$）與方向容忍度（$2^\circ$），同時對整組影像做全域正規化。v0.2 改採依 `video_id` 的 Group Split（$40$ Train／$10$ Val／$12$ Test 分鏡），規定正規化極值僅由 Train 統計、門檻僅在 Val 決定，驗證後 group overlap $= 0$。

## One Label Quality Risk

全部資料由單人以 LabelImg 標註單一類別「目標物」，缺乏「移動」的書面位移門檻，將完全靜止的停放車輛與移動目標混標為同類；且 SD 與光流圖經 $4$ 次形態學膨脹後使亮區外擴，迫使評估採用極寬鬆的 $\text{IoU} = 0.1$，無法反映精準定位品質。

## Week 3 Conclusion

本機實驗目錄之論文資料集足以支持「空拍紅外線連續影格移動目標偵測」的三階段架構驗證，但目前僅涵蓋單一 YouTube 壓縮來源（$600 \times 450$）與夜間場景，且在「多目標小物件＋單純背景」Recall 僅 $64.5\%$、「少目標大物件＋複雜背景」Precision 僅 $62.2\%$。後續實驗將固定光流缺失幀之單幀 IR Fallback 機制、依獨立 Validation 分鏡重驗門檻，並按 Codebook 分層回報動靜態與子場景指標。