# Week 1 Evidence

學號：7114029021
姓名：陳羿婷

## 1. Dataset 在哪裡？

`data/customer_intent_demo.csv`

本次實驗使用客服問題意圖分類資料集，共有 100 筆資料，
包含 4 種意圖類別，每個類別各 25 筆。

---

## 2. Baseline 在哪裡？

`src/rule_baseline.py`

本次使用 Rule-based Baseline，
透過預先設定的文字規則判斷客服訊息所屬的問題類別。

---

## 3. 本次 Accuracy

Accuracy = 0.950

代表 100 筆資料中，有 95 筆被 Baseline 正確分類，
另外有 5 筆分類錯誤。

---

## 4. Failure Case

Input：

`退貨物流已收走但沒有更新`

Ground Truth：

`refund_return`

Baseline Prediction：

`order_delivery`

---

## 5. 為什麼 Baseline 會錯？

這筆訊息同時包含「退貨」與「物流」相關資訊，
Rule-based Baseline 依賴固定的文字規則進行判斷，
因此將訊息判斷為配送問題，而沒有正確辨識出使用者真正想詢問的是退貨問題。

---

## 6. 這是否代表現在一定要使用更複雜的 AI？為什麼？

不一定。

目前 Baseline 的 Accuracy 已達 0.950，
應先分析錯誤案例並確認是否可以透過調整規則改善。
如果未來遇到更多語意模糊、同時包含多種意圖，
或無法單靠固定規則處理的訊息，
再考慮使用較複雜的 AI 模型。