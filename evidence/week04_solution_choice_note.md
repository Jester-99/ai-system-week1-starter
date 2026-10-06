# Week 4 Solution Choice Note

學號：7114029015

姓名：黃柏瑜

## Current Evidence

在相同 Dataset、Split、Metric 與 Information Boundary 下，輕量神經網路 YOLOv11n 是目前最好且唯一達到實用標準的方案。

| method | dataset_information | map50 | tiny_miss_rate | fp_per_frame | runtime_seconds | complexity | note |
|:---|:---|---:|---:|---:|---:|:---|:---|
| Otsu + CCA (Baseline 1) | 640×512 gray; group split by video_id seed=42 | 0.2140 | 0.7180 | 8.42 | 0.0042 | Low | Naive baseline; 背景日照雜波引發大量全域過曝虛警。 |
| Top-Hat + Adaptive (Baseline 2) | 640×512 gray; group split by video_id seed=42 | 0.5280 | 0.4630 | 2.15 | 0.0118 | Low-Mid | Credible baseline; 背景抑制顯著提升，但低對比冷車漏檢嚴重。 |
| YOLOv11n (Candidate*) | 640×512 gray; group split by video_id seed=42 | 0.8120 | 0.1420 | 0.31 | 0.0086 | Mid | Candidate; 具備幾何語義特徵，大幅降低虛警與微小目標漏檢。 |

## Remaining Failure

本次 locked test set 中 YOLOv11n 表現優異，但仍存在少量極端案例失誤：
1. 長時間熄火且與地表溫差趨近零度（$\Delta T \le 1.5^\circ\text{C}$）的冷車，缺乏足夠熱特徵對比。
2. YouTube 視訊高壓縮比下引發之區塊效應（Macroblocking），造成超遠景微小車輛邊緣模糊退化。

## Minimum Sufficient Solution

目前選擇輕量神經網路 YOLOv11n 作為 minimum sufficient solution。

理由：兩套傳統 Baseline 在高空微小目標上的漏檢率高達 71.8% 與 46.3%，每影格虛警均超過 2 次，無法支援巡檢決策。YOLOv11n 達到 mAP = 0.8120、微小漏檢率降至 14.2%，且單幀推論僅需 0.0086 秒（116 FPS），顯存低於 800MB，完全符合無人機邊緣運算板卡之即時推論與功耗限制。

## Next Candidate

目前不建議升級到更大規模之重型架構（如大型 Vision Transformer 或 RT-DETR），因其參數量增加數倍但帶來的邊際增益有限，反而會破壞邊緣推論延遲。
下一步應測試微架構改良方案：
1. **微小目標專用檢測頭（YOLOv11-P2 Head）**：保留高解析度特徵圖以提升 $< 16 \times 16$ 像素微小車輛感知。
2. **跨影格時序運動熱訊號融合（ByteTrack）**：利用航拍時序關聯性，以極低算力補償單影格微弱熱訊號漏檢。

## Complexity Justification

傳統 Baseline 2 的 mAP 僅 0.5280 且每幀誤報 2.15 次，證明純亮度與空間濾波不足以應對非結構化高空環境。YOLOv11n 提供 +28.4% mAP 的顯著增量 evidence，並將每影格誤報降低 85%（0.31 次），成功跨過 Complexity Gate 檢驗。增加至輕量級神經網路之複雜度完全合理且必要。