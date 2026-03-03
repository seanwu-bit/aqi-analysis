#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
避難所風險標籤分析
模擬 AQI 測站並進行避難所風險評估
"""

import os
import pandas as pd
import numpy as np
import math
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class ShelterRiskAnalyzer:
    """避難所風險分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.output_dir = 'outputs'
        os.makedirs(self.output_dir, exist_ok=True)
        
        print("避難所風險分析器初始化完成")
    
    def load_aqi_data(self):
        """載入 AQI 數據"""
        try:
            aqi_files = [f for f in os.listdir(self.output_dir) if f.startswith('aqi_data_with_distance_') and f.endswith('.csv')]
            if not aqi_files:
                print("未找到 AQI 數據檔案，創建模擬數據")
                return self.create_sample_aqi_data()
            
            latest_file = sorted(aqi_files)[-1]
            aqi_file = os.path.join(self.output_dir, latest_file)
            
            df = pd.read_csv(aqi_file, encoding='utf-8-sig')
            print(f"載入 AQI 數據: {latest_file} ({len(df)} 筆)")
            
            # 檢查目前空氣品質
            avg_aqi = df['AQI'].mean()
            print(f"目前全台平均 AQI: {avg_aqi:.1f}")
            
            if avg_aqi < 50:
                print("全台空氣品質良好，進行模擬...")
                df = self.simulate_high_aqi(df)
            
            return df
        except Exception as e:
            print(f"載入 AQI 數據失敗: {e}")
            return self.create_sample_aqi_data()
    
    def create_sample_aqi_data(self):
        """創建模擬 AQI 數據"""
        print("創建模擬 AQI 數據...")
        sample_data = [
            {'測站名稱': '台北', '經度': 121.5170, '緯度': 25.0478, 'AQI': 45},
            {'測站名稱': '新竹', '經度': 120.9647, '緯度': 24.8138, 'AQI': 40},
            {'測站名稱': '台中', '經度': 120.6736, '緯度': 24.1477, 'AQI': 42},
            {'測站名稱': '台南', '經度': 120.2650, '緯度': 23.0116, 'AQI': 38},
            {'測站名稱': '高雄', '經度': 120.3014, '緯度': 22.6273, 'AQI': 150},  # 模擬高 AQI
            {'測站名稱': '林口', '經度': 121.3524, '緯度': 25.0777, 'AQI': 41},
            {'測站名稱': '基隆', '經度': 121.7462, '緯度': 25.1276, 'AQI': 43},
            {'測站名稱': '花蓮', '經度': 121.6069, '緯度': 23.9821, 'AQI': 39},
            {'測站名稱': '宜蘭', '經度': 121.7562, '緯度': 24.7700, 'AQI': 37},
        ]
        
        return pd.DataFrame(sample_data)
    
    def simulate_high_aqi(self, df):
        """模擬特定測站高 AQI"""
        print("\n=== AQI 模擬 ===")
        
        # 模擬鳳山測站（高雄地區）
        target_station = '鳳山'
        
        station_data = df[df['測站名稱'] == target_station]
        if not station_data.empty:
            original_aqi = station_data['AQI'].iloc[0]
            new_aqi = 150  # 鳳山設為 150
            
            df.loc[df['測站名稱'] == target_station, 'AQI'] = new_aqi
            print(f"模擬: {target_station} AQI {original_aqi} -> {new_aqi}")
        else:
            print(f"未找到測站: {target_station}")
        
        print(f"模擬後平均 AQI: {df['AQI'].mean():.1f}")
        return df
    
    def load_shelter_data(self):
        """載入避難所數據"""
        try:
            shelter_files = [f for f in os.listdir(self.output_dir) if f.startswith('shelter_data_cleaned_') and f.endswith('.csv')]
            if not shelter_files:
                print("未找到清理後的避難所數據")
                return None
            
            latest_file = sorted(shelter_files)[-1]
            shelter_file = os.path.join(self.output_dir, latest_file)
            
            df = pd.read_csv(shelter_file, encoding='utf-8-sig')
            print(f"載入避難所數據: {latest_file} ({len(df)} 筆)")
            return df
        except Exception as e:
            print(f"載入避難所數據失敗: {e}")
            return None
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """計算兩點間的距離（Haversine 公式）"""
        # 將經緯度轉換為弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine 公式
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半徑（公里）
        r = 6371
        
        distance = r * c
        return distance
    
    def find_nearest_aqi_station(self, shelter_lat, shelter_lon, aqi_df):
        """尋找最近的 AQI 測站"""
        min_distance = float('inf')
        nearest_station = None
        
        for idx, station in aqi_df.iterrows():
            distance = self.haversine_distance(
                shelter_lat, shelter_lon,
                station['緯度'], station['經度']
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_station = {
                    'name': station['測站名稱'],
                    'aqi': station['AQI'],
                    'distance': distance,
                    'lat': station['緯度'],
                    'lon': station['經度']
                }
        
        return nearest_station
    
    def assign_risk_labels(self, shelters_df, aqi_df):
        """進行風險標籤作業"""
        print("\n=== 風險標籤作業 ===")
        
        risk_results = []
        
        for idx, shelter in shelters_df.iterrows():
            shelter_lat = shelter['緯度']
            shelter_lon = shelter['經度']
            is_indoor = shelter['in_door']
            
            # 尋找最近的 AQI 測站
            nearest_station = self.find_nearest_aqi_station(shelter_lat, shelter_lon, aqi_df)
            
            if nearest_station:
                # 風險標籤邏輯
                risk_level = "Low Risk"
                risk_reason = ""
                
                if nearest_station['aqi'] > 100:
                    risk_level = "High Risk"
                    risk_reason = f"Nearest AQI station ({nearest_station['name']}) AQI: {nearest_station['aqi']}"
                elif nearest_station['aqi'] > 50 and not is_indoor:
                    risk_level = "Warning"
                    risk_reason = f"Nearest AQI station ({nearest_station['name']}) AQI: {nearest_station['aqi']}, Outdoor facility"
                elif nearest_station['aqi'] > 50 and is_indoor:
                    risk_level = "Medium Risk"
                    risk_reason = f"Nearest AQI station ({nearest_station['name']}) AQI: {nearest_station['aqi']}, Indoor facility"
                
                risk_results.append({
                    'shelter_name': shelter['避難收容處所名稱'],
                    'county': shelter['縣市及鄉鎮市區'],
                    'address': shelter['避難收容處所地址'],
                    'shelter_lat': shelter_lat,
                    'shelter_lon': shelter_lon,
                    'is_indoor': is_indoor,
                    'nearest_station': nearest_station['name'],
                    'nearest_aqi': nearest_station['aqi'],
                    'distance_to_station': nearest_station['distance'],
                    'risk_level': risk_level,
                    'risk_reason': risk_reason
                })
        
        print(f"完成 {len(risk_results)} 個避難所的風險標籤")
        return risk_results
    
    def analyze_risk_distribution(self, risk_results):
        """分析風險分布"""
        print("\n=== 風險分布分析 ===")
        
        risk_counts = {}
        for result in risk_results:
            risk_level = result['risk_level']
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        print("風險等級分布:")
        for risk_level, count in risk_counts.items():
            percentage = (count / len(risk_results)) * 100
            print(f"  {risk_level}: {count} 筆 ({percentage:.1f}%)")
        
        # 顯示高風險避難所
        high_risk_shelters = [r for r in risk_results if r['risk_level'] == 'High Risk']
        if high_risk_shelters:
            print(f"\n高風險避難所 ({len(high_risk_shelters)} 筆):")
            for shelter in high_risk_shelters[:5]:  # 只顯示前5筆
                print(f"  {shelter['shelter_name']} - {shelter['nearest_station']} (AQI: {shelter['nearest_aqi']})")
        
        return risk_counts
    
    def save_results(self, risk_results):
        """儲存分析結果"""
        print("\n=== 儲存分析結果 ===")
        
        # 轉換為 DataFrame
        df = pd.DataFrame(risk_results)
        
        # 重新排列欄位順序
        column_order = [
            'shelter_name', 'county', 'address', 'shelter_lat', 'shelter_lon',
            'is_indoor', 'nearest_station', 'nearest_aqi', 'distance_to_station',
            'risk_level', 'risk_reason'
        ]
        df = df[column_order]
        
        # 儲存 CSV 檔案
        output_file = os.path.join(self.output_dir, f'shelter_aqi_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"分析結果已儲存: {output_file}")
        return output_file
    
    def generate_risk_report(self, risk_results, risk_counts):
        """生成風險分析報告"""
        print("\n=== 生成風險分析報告 ===")
        
        report = f"""# 避難所 AQI 風險分析報告

## 基本資訊
- **報告生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **分析類型**: 避難所風險標籤作業
- **分析避難所數量**: {len(risk_results)} 個
- **使用 AQI 測站**: {len(set(r['nearest_station'] for r in risk_results))} 個

## 風險標籤算法

### 距離計算
- **算法**: Haversine Formula
- **用途**: 計算避難所到最近 AQI 測站的距離
- **地球半徑**: 6371 公里

### 風險標籤邏輯
1. **High Risk**: 最近 AQI 測站 > 100
2. **Warning**: 最近 AQI 測站 > 50 AND 避難所為室外設施 (is_indoor == False)
3. **Medium Risk**: 最近 AQI 測站 > 50 AND 避難所為室內設施 (is_indoor == True)
4. **Low Risk**: 其他情況

## 風險分布統計

### 風險等級分布
"""
        
        for risk_level, count in risk_counts.items():
            percentage = (count / len(risk_results)) * 100
            report += f"- **{risk_level}**: {count} 個 ({percentage:.1f}%)\n"
        
        # 高風險避難所詳情
        high_risk_shelters = [r for r in risk_results if r['risk_level'] == 'High Risk']
        if high_risk_shelters:
            report += f"""
### 高風險避難所詳情 ({len(high_risk_shelters)} 個)

| 避難所名稱 | 縣市 | 最近測站 | AQI 值 | 距離(公里) | 設施類型 |
|---|---|---|---|---|---|
"""
            for shelter in high_risk_shelters[:10]:  # 只顯示前10個
                facility_type = "室內" if shelter['is_indoor'] else "室外"
                report += f"| {shelter['shelter_name']} | {shelter['county']} | {shelter['nearest_station']} | {shelter['nearest_aqi']} | {shelter['distance_to_station']:.2f} | {facility_type} |\n"
        
        # 警告等級避難所
        warning_shelters = [r for r in risk_results if r['risk_level'] == 'Warning']
        if warning_shelters:
            report += f"""
### 警告等級避難所 ({len(warning_shelters)} 個)

這些避難所位於 AQI > 50 的區域且為室外設施，建議：
1. 考慮轉移至室內避難所
2. 加強通風設施
3. 提供空氣過濾設備

| 避難所名稱 | 縣市 | 最近測站 | AQI 值 | 距離(公里) |
|---|---|---|---|---|
"""
            for shelter in warning_shelters[:10]:  # 只顯示前10個
                report += f"| {shelter['shelter_name']} | {shelter['county']} | {shelter['nearest_station']} | {shelter['nearest_aqi']} | {shelter['distance_to_station']:.2f} |\n"
        
        report += f"""
## 分析結論

### 主要發現
1. **高風險避難所**: {len(high_risk_shelters)} 個，需要立即關注
2. **警告等級避難所**: {len(warning_shelters)} 個，需要預防措施
3. **室內設施優勢**: 室內避難所在相同 AQI 條件下風險較低

### 建議措施

#### 立即行動
- 通知高風險避難所管理單位
- 準備空氣清淨設備
- 制定應急疏散計劃

#### 預防措施
- 加強室外避難所的通風系統
- 建立即時 AQI 監測預警
- 定期檢查避難所設施狀況

#### 長期規劃
- 考慮在高風險區域增設室內避難所
- 建立避難所等級制度
- 整合氣象預報系統

---
*報告由避難所風險分析系統自動生成*
"""
        
        # 保存報告
        report_file = os.path.join(self.output_dir, f'shelter_risk_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"風險分析報告已保存: {report_file}")
        return report_file
    
    def run_analysis(self):
        """執行完整風險分析"""
        print("=" * 60)
        print("避難所 AQI 風險分析")
        print("=" * 60)
        
        # 1. 載入數據
        print("步驟 1/4: 載入數據...")
        aqi_df = self.load_aqi_data()
        shelters_df = self.load_shelter_data()
        
        if aqi_df is None or shelters_df is None:
            print("數據載入失敗，無法繼續分析")
            return
        
        # 2. 進行風險標籤
        print("步驟 2/4: 進行風險標籤...")
        risk_results = self.assign_risk_labels(shelters_df, aqi_df)
        
        # 3. 分析風險分布
        print("步驟 3/4: 分析風險分布...")
        risk_counts = self.analyze_risk_distribution(risk_results)
        
        # 4. 儲存結果
        print("步驟 4/4: 儲存結果...")
        csv_file = self.save_results(risk_results)
        report_file = self.generate_risk_report(risk_results, risk_counts)
        
        print("\n" + "=" * 60)
        print("風險分析完成！")
        print(f"AQI 測站: {len(aqi_df)} 站")
        print(f"避難所: {len(shelters_df)} 所")
        print(f"高風險: {risk_counts.get('High Risk', 0)} 所")
        print(f"警告等級: {risk_counts.get('Warning', 0)} 所")
        print(f"分析結果: {csv_file}")
        print(f"分析報告: {report_file}")
        print("=" * 60)
        
        return {
            'csv_file': csv_file,
            'report_file': report_file,
            'aqi_stations': len(aqi_df),
            'shelters': len(shelters_df),
            'high_risk': risk_counts.get('High Risk', 0),
            'warning': risk_counts.get('Warning', 0),
            'medium_risk': risk_counts.get('Medium Risk', 0),
            'low_risk': risk_counts.get('Low Risk', 0)
        }

def main():
    """主程式"""
    analyzer = ShelterRiskAnalyzer()
    results = analyzer.run_analysis()
    
    if results:
        print("\n分析結果摘要:")
        print(f"AQI 測站數據: {results['aqi_stations']} 站")
        print(f"避難所數據: {results['shelters']} 所")
        print(f"高風險避難所: {results['high_risk']} 所")
        print(f"警告等級避難所: {results['warning']} 所")
        print(f"中等風險避難所: {results['medium_risk']} 所")
        print(f"低風險避難所: {results['low_risk']} 所")
        print(f"分析結果檔案: {results['csv_file']}")
        print(f"風險分析報告: {results['report_file']}")

if __name__ == "__main__":
    main()
