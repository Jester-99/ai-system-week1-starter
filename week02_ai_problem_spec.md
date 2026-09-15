# Week 2 AI Problem Spec v0.2

學號：7114029021

姓名：陳羿婷

## 1. Business / System Problem

客服訊息可能來自訂單配送、退款退貨、帳號登入與商品資訊等不同問題類型。若客服人員需要先人工判斷每則訊息的類別，會增加初步分流時間，也可能造成後續處理流程不一致。

本週延續 Week 1 的「客服問題意圖分類」案例，目標是先把問題定義成可驗證的 AI Problem，而不是直接決定要使用複雜模型。

## 2. Decision Point

收到一則客服訊息後，系統要先判斷這則訊息應該分到哪一類客服流程。

此決策會影響後續處理方式，例如：

- 訂單／配送問題交給物流或訂單查詢流程。
- 退款／退貨問題交給退換貨流程。
- 帳號／登入問題交給會員帳號處理流程。
- 商品資訊問題交給商品諮詢流程。

## 3. Unit of Analysis

一筆資料是一則客服訊息。

每筆資料包含：

- `message`：客服訊息文字。
- `intent`：正確意圖類別。

目前資料集共有 100 筆合成客服訊息，四個類別各 25 筆。

## 4. Input

部署當下可以取得的輸入是客服訊息文字，也就是 `message` 欄位。

本任務不使用事後才產生的資訊，例如客服人員最後如何處理、客戶是否滿意、後續是否退款成功等欄位。這樣可以避免模型在訓練或評估時偷看未來資訊。

## 5. Target

Target 是客服訊息的正確意圖類別，也就是 `intent` 欄位。

本任務目前定義四個類別：

- `order_delivery`：訂單／配送
- `refund_return`：退款／退貨
- `account_login`：帳號／登入
- `product_info`：商品資訊

## 6. Output

系統輸出是一個意圖分類結果。

目前 baseline 的輸出格式是一個類別名稱，例如：

```text
refund_return
```

若未來進一步改善系統，可以考慮增加 confidence 或規則命中原因，但 Week 2 的重點先放在問題規格與可驗證任務。

## 7. Baseline

Baseline 使用 Week 1 已建立的 Rule-based keyword classifier。

程式位置：

```text
src/rule_baseline.py
```

Baseline 根據客服訊息中的關鍵字判斷意圖類別。例如看到「訂單」「物流」「配送」等詞時，容易判斷為 `order_delivery`。

目前 Week 1 實驗結果：

```text
Accuracy = 0.950
```

這代表 100 筆資料中有 95 筆被正確分類，5 筆分類錯誤。

## 8. Success Criteria

本任務的成功條件如下：

- Accuracy 至少達到 0.90。
- 四個類別都必須能被分類，不能只偏向單一類別。
- Failure Cases 需要能被列出並解釋錯誤原因。
- 錯誤不能集中在高風險類別，例如退款／退貨問題。

目前 baseline Accuracy 為 0.950，已達到基本門檻。不過仍需要檢查錯誤分布，特別是退款／退貨類別是否容易被誤判成配送問題。

## 9. Failure Criteria

即使整體 Accuracy 看起來很高，若出現以下情況，仍可判定系統失敗：

- 退款／退貨問題被大量誤判成訂單／配送問題。
- 帳號登入問題被誤判後，導致使用者無法進入正確支援流程。
- 同一句話同時包含多個關鍵字時，規則固定順序造成系統性誤判。
- 新的客服訊息沒有明顯關鍵字時，baseline 只能使用預設分類，導致錯誤。
- 錯誤案例無法被人工理解或追蹤。

Week 1 的 Failure Case：

```text
Input：退貨物流已收走但沒有更新
Ground Truth：refund_return
Baseline Prediction：order_delivery
```

這筆錯誤顯示訊息同時包含「退貨」與「物流」時，rule-based baseline 可能優先命中配送相關規則，而忽略使用者真正想處理的是退貨流程。

## 10. HITL / Fallback

當系統遇到不確定或高風險情況時，應交由人工客服覆核。

需要人工覆核的情況包括：

- 訊息同時命中多個類別的關鍵字。
- 訊息包含退款、退貨、扣款、帳號鎖定等高風險詞。
- 系統無法命中任何明確規則。
- 使用者訊息太短或語意不完整。

Fallback 可以先採用「標記為需人工確認」，而不是直接進入錯誤流程。

## 11. 最大 Assumption

目前最大的假設是：合成客服訊息可以代表真實客服訊息的語言型態。

這個假設仍需要驗證。真實客服資料可能包含錯字、口語、省略句、混合多個問題、情緒性文字，或同一則訊息同時詢問多件事。因此目前的 baseline 成績不能直接代表真實部署表現。

## 12. AI Reviewer Record

### AI Reviewer 提出的問題

1. Target 是否可驗證？
2. Input 是否可能包含未來資訊或不應取得的欄位？
3. Success / Failure 是否可驗收？
4. Baseline 是否合理？
5. 是否有未定義的 failure case？

### Accept

- 採用「Target 必須可驗證」的建議，因此明確定義 target 為 `intent` 欄位中的四類客服意圖。
- 採用「Input 要避免未來資訊」的建議，因此本任務只使用部署當下可取得的 `message` 欄位。
- 採用「Failure 不能只看整體 Accuracy」的建議，因此補上退款／退貨被誤判成配送問題的 failure criteria。

### Reject

- 不採用直接加入 LLM 或 RAG 的建議。Week 2 的目標是完成 AI Problem Spec，而不是更換模型方法。
- 不採用把所有客戶資料都當成 input 的建議，因為目前任務只需要客服訊息文字，加入過多欄位會讓 input 定義變模糊，也可能引入不應取得的資訊。

### Modify

- AI reviewer 建議加入 confidence，本版本先不實作 confidence，但在 Output 區段註明未來可以加入 confidence 或規則命中原因。
- AI reviewer 建議更細分退款與退貨，本版本先維持 Week 1 的四類分類，因為目前資料集與 baseline 都依照四類設計。未來若真實流程需要更細分，可以在 Dataset Spec 階段重新定義 label。

## 13. v0.2 修改摘要

相較於 Week 1，本版本把「客服問題意圖分類」整理成可驗證的 AI Problem Spec：

- 明確定義一筆資料是一則客服訊息。
- 明確區分 Input、Target 與 Output。
- 保留 Rule-based Baseline 作為最小可行比較基準。
- 補上 Success Criteria 與 Failure Criteria。
- 補上 HITL / Fallback，避免高風險錯誤直接進入錯誤流程。
- 補上 AI reviewer 的 Accept / Reject / Modify 紀錄。
