# AQI 避難所風險分析專案

## 專案概述

本專案分析台灣避難所與空氣品質監測站的空間關聯，評估避難所在空氣污染事件中的風險等級，為應急決策提供支援。

## 檔案結構

```
aqi-analysis/
├── data/
│   └── shelters_cleaned.csv          # 清理後的避難所數據
├── outputs/
│   ├── audit_report.md               # 避難所數據審核報告
│   ├── shelter_aqi_analysis.csv     # 風險分析結果
│   └── reflection.md                # 專案反思報告
├── scripts/
│   ├── shelter_data_analysis.py      # 避難所數據清理與分析
│   ├── shelter_risk_analysis.py      # 風險標籤分析
│   ├── spatial_overlay_analysis.py    # 空間疊圖分析
│   ├── main.py                     # 主程式入口
│   ├── aqi_map.py                 # AQI 地圖生成
│   └── cwa_weather_map.py          # CWA 天氣地圖
└── README.md                        # 專案說明文件
```

### 目錄說明

#### `/scripts` - 主要程式
- **shelter_data_analysis.py**: 避難所數據清理、座標驗證、室內外屬性推斷
- **shelter_risk_analysis.py**: 風險標籤作業、Haversine 距離計算、模擬功能
- **spatial_overlay_analysis.py**: 空間疊圖分析、互動式地圖生成
- **main.py**: 統一程式入口，整合 AQI 和 CWA 功能

#### `/tests` - 測試與驗證（專案根目錄）
- **quality_check.py**: 品質檢查腳本
- **check_*.py**: 各項數據驗證腳本
- **test_*.py**: 模擬測試腳本

#### `/data` - 處理後數據
- **shelters_cleaned.csv**: 清理後的避難所數據（5048 筆）

#### `/outputs` - 分析結果
- **audit_report.md**: 數據審核報告
- **shelter_aqi_analysis.csv**: 風險分析結果
- **reflection.md**: 專案反思與技術分析

## 主要功能

### 1. 數據清理與審核
- 座標異常檢測與修正
- 區域座標合理性驗證
- 室內/室外屬性推斷
- 地址定位服務整合

### 2. 空間分析
- Haversine 距離計算
- 最近 AQI 測站搜尋
- 風險標籤分類
- 地理分布分析

### 3. 風險評估
- **High Risk**: 最近 AQI 測站 > 100
- **Warning**: 最近 AQI 測站 > 50 且為室外設施
- **Medium Risk**: 最近 AQI 測站 > 50 且為室內設施
- **Low Risk**: 其他情況

## 技術特點

### 算法實現
- **Haversine Formula**: 精確計算兩點間距離
- **空間索引**: 高效的最近測站搜尋
- **多層次風險分類**: 基於 AQI 值和設施類型

### 數據處理
- **自動化清理**: 異常座標檢測與修正
- **地理編碼**: OpenStreetMap API 整合
- **邊界驗證**: 台灣本島地理邊界檢查

## 使用方法

### 環境需求
```bash
pip install pandas numpy requests python-dotenv folium
```

### 執行分析
```bash
cd aqi-analysis/scripts
python shelter_aqi_analysis.py
```

### 輸出檔案
- `../outputs/shelter_aqi_analysis.csv`: 風險分析結果
- `../outputs/reflection.md`: 專案反思報告

## 數據來源

### AQI 監測數據
- **來源**: 環境部空氣品質監測網
- **更新頻率**: 即時
- **測站數量**: 85 個監測站

### 避難所數據
- **來源**: 內政部避難收容處所點位檔案
- **記錄數量**: 5,048 筆清理後記錄
- **覆蓋範圍**: 台灣本島

## 分析結果

### 風險分布（鳳山 AQI=150 模擬）
- **High Risk**: 1,481 所 (29.3%)
- **Medium Risk**: 1,783 所 (35.3%)
- **Warning**: 1,199 所 (23.8%)
- **Low Risk**: 585 所 (11.6%)

### 高風險避難所分布
- **桃園地區**: 152 所
- **大園地區**: 110 所
- **鳳山地區**: 109 所（模擬影響）

## 技術限制與改進方向

### 當前限制
1. **靜態分析**: 未考慮時間動態變化
2. **單一指標**: 主要依賴 AQI
3. **地理簡化**: 未充分考慮地形影響

### 未來改進
1. **動態模擬**: 加入時間維度預測
2. **多指標整合**: 綜合環境指標
3. **機器學習**: 歷史資料訓練模型
4. **即時更新**: 整合即時監測系統

## 反思與學習

詳細的專案反思請參考 `outputs/reflection.md`，包含：

- **資料完整性**: 原始資料問題與處理方法
- **AI 協作**: Cascade 表現與 CRS 幻覺問題
- **空間推理**: 最近測站指標的合理性評估
- **技術架構**: 系統優勢與改進方向

## 授權與引用

本專案遵循開源原則，歡迎學術研究與實務應用引用。

---
*AQI 避難所風險分析系統 v1.0*  
*最後更新: 2026-03-03*
