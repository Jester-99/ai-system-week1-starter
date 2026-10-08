# Week 4 Solution Choice Note

學號：7114029015

姓名：黃柏瑜

## Current Evidence

比較條件：相同 Dataset（`hituav-vehicle-v0.2`）、相同 Split（依日期切分，Test = 2021-01-21、01-23，共 628 frames）、相同 Metric、相同 Information Boundary（只用 IR 像素）。

| method | Test AP@0.5 ↑ | Miss Rate ↓ | False alarms / 100 frames ↓ | ms/frame (CPU) | complexity |
| --- | ---: | ---: | ---: | ---: | --- |
| B1 Otsu + CCA | 0.0081 | 0.9534 | 244.4 | 6.1 | Low |
| B2 Local-contrast + HOG + GB | 0.3637 | 0.5496 | 201.4 | 86.2 | Low–Mid |
| YOLO11n | **0.7832** | **0.2929** | **56.8** | 56.9 | Mid |

- B1 失效的原因：70.6% 的車輛在熱像中比背景暗（冷車）。W2 的「熱點」假設不成立。
- YOLO11n 在兩個 Test 日期都最好：2021-01-21 的 AP 為 0.810，2021-01-23 為 0.730。

## Remaining Failure

YOLO11n 仍然失敗的地方：

- small 車輛（16²–32²）recall 0.539。
- 30° 斜視角 recall 0.405，130 m 高度 recall 0.491（Failure Case 3）。
- 建物窗戶、路燈底座等規則紋理造成誤報，另有框位置偏移（Failure Case 4）。
- 尚未在邊緣裝置驗證 ≥ 30 FPS。

## Minimum Sufficient Solution

暫定採用 YOLO11n（imgsz 512，Val 選定門檻 0.25）。它是目前唯一接近 W2 Success 的方法，而且在 CPU 上比 B2 更快。

## Next Candidate

下一輪仍然使用 YOLO11n，先處理 Data 和 Decision 層面的問題：

1. 提高輸入解析度到 imgsz 640，或改用 tiling 推論，針對遠景與小目標。
2. 用 Train 全部無車影格，加上窗戶、路燈底座等紋理 hard negatives，並增加 epochs。
3. 加入跨影格時間濾波（連續 N 幀都偵測到才觸發警報），降低虛警。

上述都做完後，如果 small 或 30° 子群的 recall 仍然不足，才測試 YOLO11s。

## Complexity Justification

- 從 B2 升級到 YOLO11n 是值得的：AP 增加 42 個百分點，miss rate 下降 26 個百分點，誤報減少約 72%（201 → 57 次／100 frames），而且推論比 B2 更快。
- 目前不升級到更大模型。剩餘 failure 指向的是解析度、斜視角與 hard negatives，不是模型容量。YOLO11s 的運算量約為 n 的 3 倍，會壓縮邊緣端 30 FPS 的預算。因此只有當它在高風險子群（30°、small）上帶來明顯增益，並且通過延遲測試時，才值得採用。
