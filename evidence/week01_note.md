# Week 1 Evidence

學號：7114029015
姓名：黃柏瑜

## 1. Dataset 在哪裡？

`data/customer_intent_demo.csv`

<!-- 本次實驗使用客服問題意圖分類資料集，共有 100 筆資料，
包含 4 種意圖類別，每個類別各 25 筆。 -->

---

## 2. Baseline 在哪裡？

`src/rule_baseline.py`

<!-- 本次使用 Rule-based Baseline，
透過預先設定的文字規則判斷客服訊息所屬的問題類別。 -->

---

## 3. 本次 Accuracy

Accuracy = 0.950

<!-- 代表 100 筆資料中，有 95 筆被 Baseline 正確分類，
另外有 5 筆分類錯誤。 -->

---

## 4. Failure Case

Input：

`我想退貨但包裹已送達還能辦嗎`

Ground Truth：

`refund_return`

Baseline Prediction：

`order_delivery`

---

## 5. 為什麼 Baseline 會錯？

因為這個 rule-based baseline 看到「包裹」（或「送達」）就優先判成 order_delivery，但整句真正的意圖是在詢問「退貨」流程。

---

## 6. 這是否代表現在一定要使用更複雜的 AI？為什麼？

不一定，這個錯誤也可以先透過調整關鍵字順序、加入更明確的規則或檢查多個關鍵字來改善。