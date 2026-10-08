# Week 3 Dataset Audit Summary

學號：7114029015

姓名：黃柏瑜

## Dataset

```text
data/hit_uav/normal_json/{train,val,test}.json   (HIT-UAV, Suo et al., Scientific Data 2023)
```

## Audit Results

| Check | Result |
| --- | --- |
| Images (Units) | 2,898（640×512） |
| Annotations（全類別） | 24,899 |
| Vehicle boxes（Car + OtherVehicle） | 7,459（Car 7,311／OtherVehicle 148） |
| Missing values | 0 |
| Duplicate filename / box | 0 / 0 |
| Out-of-bound / degenerate boxes | 0 / 0 |
| Images with vehicle | 1,424（49.1%） |
| Images without any annotation | 32 |
| Vehicle scale | tiny < 16² 2.5%／small 22.1%／≥ 32² 75.5% |
| Date range | 2020-12-17 → 2021-01-23（9 天） |
| Day / Night images | 917 / 1,981 |
| Group field | `flight_group` proxy（date + daynight + altitude + angle），264 組 |
| Official split leakage | Test 100% 同 group 在 Train；31.3% 有相鄰取樣影格 |
| v0.2 split overlap | train∩test group = 0、date = 0 |

## One Data Quality Issue

資料表面上很乾淨（缺值、重複、越界框都是 0），但類別與條件不平衡：OtherVehicle 只佔車輛框 2.0%，65.9% 的車輛框來自夜間，而且 2020-12-17 的 587 張影像沒有任何車輛。乾淨不代表能代表部署情境。

## One Leakage / Split Risk

官方 split 是依影格切分，264 個飛行段有 240 個跨 split，官方 Test 有 31.3% 在 Train 中有約 2 秒內的相鄰影格。因此改用依日期的 Group／Time Split（Test = 2021-01-21、01-23），驗證後 group overlap = 0。

## One Label Quality Risk

原論文沒有定義 `OtherVehicle`，也沒說明機車該歸到 Bicycle 還是 OtherVehicle；v0.2 將 Car + OtherVehicle 映射為 `vehicle`，機車可能被錯分為非 Target。此外 tiny 車輛只有 2.5%，不支持 W2 的微小目標主張。

## Week 3 Conclusion

HIT-UAV 足以支持「高空 IR 影格車輛偵測」的 pilot baseline，但只能代表冬季、非雨天、單一 FLIR 相機、中大型小客車為主的情境。下一版 Dataset 需補充微小目標、其他季節與天候的資料，並確認車輛子類別的 codebook。
