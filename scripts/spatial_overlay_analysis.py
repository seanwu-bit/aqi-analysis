#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空間疊圖分析 - AQI 測站與避難所疊加分析
Week 2 Spatial Overlay Analysis
"""

import os
import pandas as pd
import folium
from folium import plugins
import numpy as np
from dotenv import load_dotenv
import requests
import json
from datetime import datetime
import math

# 載入環境變數
load_dotenv()

class SpatialOverlayAnalyzer:
    """空間疊圖分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.output_dir = 'outputs'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 台灣中心點
        self.taiwan_center = [23.8, 120.9]
        
        # AQI 顏色對應
        self.aqi_colors = {
            (0, 50): '#00E400',      # 綠色 - 良好
            (51, 100): '#FFFF00',    # 黃色 - 普通
            (101, 500): '#FF0000'    # 紅色 - 不健康及以上
        }
        
        # 避難所圖標樣式
        self.shelter_colors = {
            True: '#FF6B6B',   # 室內 - 紅色
            False: '#4169E1'   # 室外 - 藍色
        }
        
        print("空間疊圖分析器初始化完成")
    
    def load_aqi_data(self):
        """載入 AQI 測站數據"""
        try:
            # 載入最新的 AQI 數據
            aqi_files = [f for f in os.listdir(self.output_dir) if f.startswith('aqi_data_with_distance_') and f.endswith('.csv')]
            if not aqi_files:
                print("未找到 AQI 數據檔案，使用模擬數據")
                return self.create_sample_aqi_data()
            
            latest_file = sorted(aqi_files)[-1]
            aqi_file = os.path.join(self.output_dir, latest_file)
            
            df = pd.read_csv(aqi_file, encoding='utf-8-sig')
            print(f"載入 AQI 數據: {latest_file} ({len(df)} 筆)")
            return df
        except Exception as e:
            print(f"載入 AQI 數據失敗: {e}")
            return self.create_sample_aqi_data()
    
    def create_sample_aqi_data(self):
        """創建模擬 AQI 數據"""
        print("創建模擬 AQI 數據...")
        sample_data = [
            {'測站名稱': '台北', '經度': 121.5170, '緯度': 25.0478, 'AQI': 85},
            {'測站名稱': '新竹', '經度': 120.9647, '緯度': 24.8138, 'AQI': 45},
            {'測站名稱': '台中', '經度': 120.6736, '緯度': 24.1477, 'AQI': 120},
            {'測站名稱': '台南', '經度': 120.2650, '緯度': 23.0116, 'AQI': 65},
            {'測站名稱': '高雄', '經度': 120.3014, '緯度': 22.6273, 'AQI': 95},
            {'測站名稱': '基隆', '經度': 121.7462, '緯度': 25.1276, 'AQI': 75},
            {'測站名稱': '花蓮', '經度': 121.6069, '緯度': 23.9821, 'AQI': 55},
            {'測站名稱': '宜蘭', '經度': 121.7562, '緯度': 24.7700, 'AQI': 40},
        ]
        return pd.DataFrame(sample_data)
    
    def load_shelter_data(self):
        """載入避難所數據"""
        try:
            # 載入清理後的避難所數據
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
    
    def get_aqi_color(self, aqi_value):
        """根據 AQI 數值獲取顏色"""
        try:
            aqi = int(aqi_value) if pd.notna(aqi_value) else 0
            for (min_val, max_val), color in self.aqi_colors.items():
                if min_val <= aqi <= max_val:
                    return color
            return '#FF0000'  # 超過範圍預設紅色
        except:
            return '#808080'  # 灰色表示無數據
    
    def validate_ocean_shelters(self, shelters_df):
        """驗證海洋中的避難所"""
        print("\n=== 驗證海洋中的避難所 ===")
        
        # 台灣邊界
        taiwan_bounds = {
            'min_lon': 119.5,
            'max_lon': 122.5,
            'min_lat': 21.5,
            'max_lat': 25.5
        }
        
        # 檢查在海洋中的避難所
        ocean_shelters = []
        for idx, row in shelters_df.iterrows():
            lon, lat = row['經度'], row['緯度']
            
            # 檢查是否在台灣邊界外
            if (lon < taiwan_bounds['min_lon'] or lon > taiwan_bounds['max_lon'] or
                lat < taiwan_bounds['min_lat'] or lat > taiwan_bounds['max_lat']):
                
                ocean_shelters.append({
                    'index': idx,
                    'name': row['避難收容處所名稱'],
                    'county': row['縣市及鄉鎮市區'],
                    'coordinates': (lon, lat),
                    'in_door': row['in_door']
                })
        
        print(f"發現 {len(ocean_shelters)} 筆海洋中的避難所")
        
        if ocean_shelters:
            print("海洋中的避難所列表:")
            for shelter in ocean_shelters[:5]:  # 只顯示前5筆
                print(f"  {shelter['name']} - {shelter['county']} - {shelter['coordinates']}")
        
        return ocean_shelters
    
    def create_spatial_map(self, aqi_df, shelters_df):
        """建立空間疊圖地圖"""
        print("\n=== 建立空間疊圖地圖 ===")
        
        # 計算地圖中心
        all_lats = list(aqi_df['緯度']) + list(shelters_df['緯度'])
        all_lons = list(aqi_df['經度']) + list(shelters_df['經度'])
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
        
        # 建立地圖
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # 添加 AQI 測站圖層 A
        print("添加 AQI 測站圖層...")
        for idx, row in aqi_df.iterrows():
            color = self.get_aqi_color(row['AQI'])
            
            # 根據 AQI 嚴重程度調整圓圈大小
            radius = 8 + (row['AQI'] / 20) if pd.notna(row['AQI']) else 8
            
            folium.CircleMarker(
                location=[row['緯度'], row['經度']],
                radius=radius,
                popup=folium.Popup(f"""
                <b>{row['測站名稱']} 測站</b><br>
                AQI: {row['AQI']}<br>
                狀態: {'良好' if row['AQI'] <= 50 else '普通' if row['AQI'] <= 100 else '不健康'}
                """, max_width=300),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2,
                tooltip=f"{row['測站名稱']} - AQI: {row['AQI']}"
            ).add_to(m)
        
        # 添加避難所圖層 B
        print("添加避難所圖層...")
        indoor_count = 0
        outdoor_count = 0
        
        for idx, row in shelters_df.iterrows():
            in_door = row['in_door']
            color = self.shelter_colors[in_door]
            
            if in_door:
                indoor_count += 1
                icon_symbol = '🏢'
                icon_color = 'red'
            else:
                outdoor_count += 1
                icon_symbol = '🏞'
                icon_color = 'blue'
            
            folium.Marker(
                location=[row['緯度'], row['經度']],
                popup=folium.Popup(f"""
                <b>{row['避難收容處所名稱']}</b><br>
                位置: {row['縣市及鄉鎮市區']}<br>
                類型: {'室內' if in_door else '室外'}<br>
                預計收容: {row['預計收容人數']} 人<br>
                適用災害: {row['適用災害類別']}
                """, max_width=300),
                icon=folium.Icon(
                    color=icon_color,
                    icon='info-sign',
                    prefix='fa'
                ),
                tooltip=f"{row['避難收容處所名稱']} - {'室內' if in_door else '室外'}"
            ).add_to(m)
        
        # 添加圖例
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; left: 10px; width: 300px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <h4>圖例</h4>
        
        <h5>AQI 測站 (圖層 A)</h5>
        <i style="background:#00E400; width:12px; height:12px; display:inline-block;"></i> 0-50 良好<br>
        <i style="background:#FFFF00; width:12px; height:12px; display:inline-block;"></i> 51-100 普通<br>
        <i style="background:#FF0000; width:12px; height:12px; display:inline-block;"></i> 101+ 不健康<br>
        
        <h5>避難收容所 (圖層 B)</h5>
        <i style="background:#FF6B6B; width:12px; height:12px; display:inline-block;"></i> 室內避難所<br>
        <i style="background:#4169E1; width:12px; height:12px; display:inline-block;"></i> 室外避難所<br>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 添加統計信息
        stats_html = f'''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 250px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <h4>統計信息</h4>
        <b>AQI 測站</b><br>
        總數: {len(aqi_df)} 站<br>
        平均 AQI: {aqi_df['AQI'].mean():.1f}<br>
        
        <b>避難收容所</b><br>
        總數: {len(shelters_df)} 所<br>
        室內: {indoor_count} 所<br>
        室外: {outdoor_count} 所<br>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(stats_html))
        
        # 添加圖層控制
        folium.LayerControl().add_to(m)
        
        print(f"地圖建立完成 - AQI測站: {len(aqi_df)} 站, 避難所: {len(shelters_df)} 所")
        return m
    
    def save_map(self, map_obj):
        """儲存地圖"""
        filename = f"spatial_overlay_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_path = os.path.join(self.output_dir, filename)
        
        map_obj.save(output_path)
        print(f"空間疊圖地圖已儲存: {output_path}")
        return output_path
    
    def generate_validation_report(self, ocean_shelters):
        """生成驗證報告"""
        report = f"""# 空間疊圖驗證報告

## 基本資訊
- **報告生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **分析類型**: AQI 測站與避難所空間疊圖

## 海洋中的避難所驗證

### 發現問題
- **海洋中避難所數量**: {len(ocean_shelters)} 筆
- **問題嚴重性**: 高 - 這些避難所在地圖上會顯示在海洋中

### 詳細清單
"""
        
        for i, shelter in enumerate(ocean_shelters, 1):
            report += f"""
{i}. **{shelter['name']}**
   - 位置: {shelter['county']}
   - 座標: ({shelter['coordinates'][0]:.6f}, {shelter['coordinates'][1]:.6f})
   - 類型: {'室內' if shelter['in_door'] else '室外'}
   - 狀態: 需要人工審查座標準確性
"""
        
        report += f"""
## 建議處理方式

### 1. 立即處理
- 人工驗證這 {len(ocean_shelters)} 筆避難所的實際座標
- 透過 Google Maps 或其他地圖服務確認正確位置
- 更新數據庫中的座標資訊

### 2. 預防措施
- 建立座標驗證機制，自動檢測異常座標
- 設定台灣邊界檢查，防止類似問題
- 定期進行數據品質審查

### 3. 長期改進
- 建立標準化的地址編碼流程
- 整合多個地理定位服務進行交叉驗證
- 建立異常座標警報系統

---
*報告由空間疊圖分析系統自動生成*
"""
        
        # 保存報告
        report_file = os.path.join(self.output_dir, f'spatial_validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"驗證報告已保存: {report_file}")
        return report_file
    
    def run_analysis(self):
        """執行完整空間疊圖分析"""
        print("=" * 60)
        print("空間疊圖分析 - AQI 測站與避難所")
        print("=" * 60)
        
        # 1. 載入數據
        print("步驟 1/4: 載入數據...")
        aqi_df = self.load_aqi_data()
        shelters_df = self.load_shelter_data()
        
        if aqi_df is None or shelters_df is None:
            print("數據載入失敗，無法繼續分析")
            return
        
        # 2. 驗證海洋中的避難所
        print("步驟 2/4: 驗證空間位置...")
        ocean_shelters = self.validate_ocean_shelters(shelters_df)
        
        # 3. 建立空間疊圖地圖
        print("步驟 3/4: 建立地圖...")
        map_obj = self.create_spatial_map(aqi_df, shelters_df)
        
        # 4. 生成驗證報告
        print("步驟 4/4: 生成報告...")
        validation_report = self.generate_validation_report(ocean_shelters)
        
        # 5. 儲存地圖
        map_file = self.save_map(map_obj)
        
        print("\n" + "=" * 60)
        print("空間疊圖分析完成！")
        print(f"AQI 測站: {len(aqi_df)} 站")
        print(f"避難收容所: {len(shelters_df)} 所")
        print(f"海洋異常: {len(ocean_shelters)} 所")
        print(f"疊圖地圖: {map_file}")
        print(f"驗證報告: {validation_report}")
        print("=" * 60)
        
        return {
            'map_file': map_file,
            'validation_report': validation_report,
            'aqi_stations': len(aqi_df),
            'shelters': len(shelters_df),
            'ocean_anomalies': len(ocean_shelters)
        }

def main():
    """主程式"""
    analyzer = SpatialOverlayAnalyzer()
    results = analyzer.run_analysis()
    
    if results:
        print("\n分析結果摘要:")
        print(f"AQI 測站數據: {results['aqi_stations']} 站")
        print(f"避難所數據: {results['shelters']} 所")
        print(f"海洋異常座標: {results['ocean_anomalies']} 所")
        print(f"疊圖地圖: {results['map_file']}")
        print(f"驗證報告: {results['validation_report']}")

if __name__ == "__main__":
    main()
