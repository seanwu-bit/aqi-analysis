import pandas as pd
import numpy as np
import math
from datetime import datetime
import os

class ManualRiskAnalyzer:
    def __init__(self):
        self.output_dir = 'outputs'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """計算兩點間的距離（Haversine 公式）"""
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        r = 6371  # 地球半徑（公里）
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
    
    def run_manual_simulation(self):
        """執行手動模擬"""
        print("=" * 60)
        print("手動模擬 - 鳳山 AQI=150")
        print("=" * 60)
        
        # 載入數據
        aqi_df = pd.read_csv('outputs/aqi_data_with_distance_20260224_164419.csv', encoding='utf-8-sig')
        
        # 找到最新的清理檔案
        shelter_files = [f for f in os.listdir('outputs') if f.startswith('shelter_data_cleaned_') and f.endswith('.csv')]
        if shelter_files:
            latest_shelter_file = sorted(shelter_files)[-1]
            shelters_df = pd.read_csv(f'outputs/{latest_shelter_file}', encoding='utf-8-sig')
        else:
            print("未找到清理後的避難所數據")
            return
        
        print(f"載入 AQI 數據: {len(aqi_df)} 筆")
        print(f"載入避難所數據: {len(shelters_df)} 筆")
        
        # 手動模擬鳳山 AQI=150
        print("\n=== 手動模擬 ===")
        fengshan_idx = aqi_df[aqi_df['測站名稱'] == '鳳山'].index
        if len(fengshan_idx) > 0:
            idx = fengshan_idx[0]
            original_aqi = aqi_df.loc[idx, 'AQI']
            aqi_df.loc[idx, 'AQI'] = 150
            print(f"模擬: 鳳山 AQI {original_aqi} -> 150")
        else:
            print("未找到鳳山測站")
            return
        
        print(f"模擬後平均 AQI: {aqi_df['AQI'].mean():.1f}")
        
        # 進行風險標籤
        risk_results = self.assign_risk_labels(shelters_df, aqi_df)
        
        # 分析風險分布
        risk_counts = {}
        for result in risk_results:
            risk_level = result['risk_level']
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        print("\n=== 風險分布分析 ===")
        print("風險等級分布:")
        for risk_level, count in risk_counts.items():
            percentage = (count / len(risk_results)) * 100
            print(f"  {risk_level}: {count} 筆 ({percentage:.1f}%)")
        
        # 檢查鳳山影響的避難所
        fengshan_affected = [r for r in risk_results if r['nearest_station'] == '鳳山']
        print(f"\n鳳山測站影響的避難所: {len(fengshan_affected)} 筆")
        
        # 檢查 AQI=150 的記錄
        aqi_150 = [r for r in risk_results if r['nearest_aqi'] == 150]
        print(f"AQI=150 的避難所: {len(aqi_150)} 筆")
        
        if aqi_150:
            print("前5筆 AQI=150 的避難所:")
            for shelter in aqi_150[:5]:
                print(f"  {shelter['shelter_name']} - {shelter['nearest_station']} (AQI: {shelter['nearest_aqi']}) - {shelter['risk_level']}")
        
        # 保存結果
        df = pd.DataFrame(risk_results)
        column_order = [
            'shelter_name', 'county', 'address', 'shelter_lat', 'shelter_lon',
            'is_indoor', 'nearest_station', 'nearest_aqi', 'distance_to_station',
            'risk_level', 'risk_reason'
        ]
        df = df[column_order]
        
        output_file = os.path.join(self.output_dir, f'shelter_aqi_analysis_manual_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n手動模擬結果已保存: {output_file}")
        return output_file

def main():
    analyzer = ManualRiskAnalyzer()
    result = analyzer.run_manual_simulation()
    print(f"\n生成的檔案: {result}")

if __name__ == "__main__":
    main()
