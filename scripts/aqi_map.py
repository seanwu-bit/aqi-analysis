#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空氣品質指標 (AQI) 即時監測地圖
串接環境部 API 獲取全台 AQI 數據並使用 Folium 視覺化
"""

import os
import requests
import folium
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json
import math
import csv

# 載入環境變數
load_dotenv()

class AQIMapGenerator:
    """AQI 地圖生成器類別"""
    
    def __init__(self):
        """初始化 AQI 地圖生成器"""
        self.api_key = os.getenv('MOENV_API_KEY')
        if not self.api_key:
            raise ValueError("請在 .env 檔案中設定 MOENV_API_KEY")
        
        # 台北車站座標
        self.taipei_station_lat = 25.0478
        self.taipei_station_lon = 121.5170
        
        # 環境部 API 端點 (aqx_p_432: 空氣品質測站即時觀測資料)
        self.api_url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
        
        # AQI 顏色對應表 (簡化為三色)
        self.aqi_colors = {
            (0, 50): '#00E400',      # 綠色 - 良好
            (51, 100): '#FFFF00',    # 黃色 - 普通
            (101, 500): '#FF0000'    # 紅色 - 不健康及以上
        }
    
    def get_aqi_level(self, aqi_value):
        """根據 AQI 數值判斷空氣品質等級"""
        try:
            aqi = int(aqi_value)
            if 0 <= aqi <= 50:
                return '良好'
            elif 51 <= aqi <= 100:
                return '普通'
            elif aqi >= 101:
                return '不健康'
            else:
                return '未知'
        except (ValueError, TypeError):
            return '未知'
    
    def get_aqi_color(self, aqi_value):
        """根據 AQI 數值獲取對應顏色"""
        try:
            aqi = int(aqi_value)
            for (min_val, max_val), color in self.aqi_colors.items():
                if min_val <= aqi <= max_val:
                    return color
            return '#FF0000'  # 超過範圍預設紅色
        except (ValueError, TypeError):
            return '#808080'  # 灰色表示無數據
    
    def calculate_distance_to_taipei(self, lat, lon):
        """計算測站到台北車站的距離（公里）使用 Haversine 公式"""
        # 將經緯度轉換為弧度
        lat1_rad = math.radians(lat)
        lon1_rad = math.radians(lon)
        lat2_rad = math.radians(self.taipei_station_lat)
        lon2_rad = math.radians(self.taipei_station_lon)
        
        # Haversine 公式
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半徑（公里）
        r = 6371
        
        distance = r * c
        return round(distance, 2)
    
    def fetch_aqi_data(self):
        """從環境部 API 獲取 AQI 數據"""
        print("正在獲取空氣品質數據...")
        
        params = {
            'api_key': self.api_key,
            'format': 'json'
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            # 環境部 API 直接返回列表，不是包含 records 欄位的字典
            if isinstance(data, list):
                print(f"成功獲取 {len(data)} 個測站數據")
                return data
            elif isinstance(data, dict) and 'records' in data:
                # 兼容舊格式
                print(f"成功獲取 {len(data['records'])} 個測站數據")
                return data['records']
            else:
                raise ValueError("API 回應格式錯誤：找不到有效的數據欄位")
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"API 連線失敗: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失敗: {e}")
    
    def process_data(self, raw_data):
        """處理和清理 AQI 數據"""
        processed_data = []
        
        for record in raw_data:
            try:
                # 檢查必要欄位是否存在
                if not all(key in record for key in ['sitename', 'latitude', 'longitude']):
                    continue
                
                # 轉換座標為浮點數
                lat = float(record['latitude'])
                lon = float(record['longitude'])
                
                # 獲取 AQI 數值，如果為空則設為 None
                aqi = record.get('aqi')
                if aqi in ['', 'ND', None]:
                    aqi = None
                else:
                    aqi = int(aqi)
                
                # 判斷空氣品質等級
                aqi_level = self.get_aqi_level(aqi) if aqi else '無數據'
                
                # 獲取顏色
                color = self.get_aqi_color(aqi) if aqi else '#808080'  # 預設灰色
                
                # 計算到台北車站的距離
                distance_to_taipei = self.calculate_distance_to_taipei(lat, lon)
                
                processed_data.append({
                    'site_name': record['sitename'],
                    'county': record.get('county', '未知'),
                    'latitude': lat,
                    'longitude': lon,
                    'aqi': aqi,
                    'aqi_level': aqi_level,
                    'color': color,
                    'distance_to_taipei': distance_to_taipei,
                    'pm25': record.get('pm2.5'),
                    'pm10': record.get('pm10'),
                    'o3': record.get('o3'),
                    'no2': record.get('no2'),
                    'so2': record.get('so2'),
                    'co': record.get('co'),
                    'status': record.get('status', '未知')
                })
                
            except (ValueError, KeyError) as e:
                print(f"處理測站 {record.get('sitename', '未知')} 數據時發生錯誤: {e}")
                continue
        
        print(f"成功處理 {len(processed_data)} 個有效測站數據")
        return processed_data
    
    def create_map(self, aqi_data):
        """建立 Folium 地圖並標示 AQI 測站"""
        print("正在建立 AQI 地圖...")
        
        # 計算台灣中心點作為地圖初始位置
        if aqi_data:
            center_lat = sum([site['latitude'] for site in aqi_data]) / len(aqi_data)
            center_lon = sum([site['longitude'] for site in aqi_data]) / len(aqi_data)
        else:
            center_lat, center_lon = 23.8, 120.9  # 台灣中心點預設值
        
        # 建立地圖
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 添加 AQI 圖例
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>AQI 空氣品質指標</h4>
        '''
        
        # 添加簡化的圖例
        legend_html += '<i style="background:#00E400; width:12px; height:12px; display:inline-block;"></i> 0-50 良好<br>'
        legend_html += '<i style="background:#FFFF00; width:12px; height:12px; display:inline-block;"></i> 51-100 普通<br>'
        legend_html += '<i style="background:#FF0000; width:12px; height:12px; display:inline-block;"></i> 101+ 不健康<br>'
        
        legend_html += '</div>'
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 在地圖上添加測站標記
        for site in aqi_data:
            # 建立簡化的彈出視窗內容
            popup_content = f"""
            <b>{site['site_name']} 測站</b><br>
            所在地: {site['county']}<br>
            <b>AQI: {site['aqi'] if site['aqi'] else '無數據'}</b><br>
            等級: {site['aqi_level']}
            """
            
            # 建立圓形標記
            folium.CircleMarker(
                location=[site['latitude'], site['longitude']],
                radius=8,
                popup=folium.Popup(popup_content, max_width=300),
                color='black',
                weight=1,
                fillColor=site['color'],
                fillOpacity=0.8,
                tooltip=f"{site['site_name']} - AQI: {site['aqi'] if site['aqi'] else '無數據'}"
            ).add_to(m)
        
        # 添加地圖標題
        title_html = '''
        <h3 align="center" style="font-size:16px"><b>台灣空氣品質指標 (AQI) 即時監測地圖</b></h3>
        <p align="center" style="font-size:12px">更新時間: {}</p>
        '''.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        m.get_root().html.add_child(folium.Element(title_html))
        
        return m
    
    def save_map(self, map_obj, filename=None):
        """儲存地圖到 outputs 目錄"""
        if filename is None:
            filename = f"aqi_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        output_path = os.path.join('outputs', filename)
        
        # 確保 outputs 目錄存在
        os.makedirs('outputs', exist_ok=True)
        
        map_obj.save(output_path)
        print(f"地圖已儲存至: {output_path}")
        return output_path
    
    def save_to_csv(self, aqi_data, filename=None):
        """將 AQI 數據儲存為 CSV 檔案"""
        if filename is None:
            filename = f"aqi_data_with_distance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        output_path = os.path.join('outputs', filename)
        
        # 確保 outputs 目錄存在
        os.makedirs('outputs', exist_ok=True)
        
        # 建立 DataFrame
        df_data = []
        for site in aqi_data:
            df_data.append({
                '測站名稱': site['site_name'],
                '縣市': site['county'],
                '緯度': site['latitude'],
                '經度': site['longitude'],
                'AQI': site['aqi'] if site['aqi'] is not None else 'N/A',
                '空氣品質等級': site['aqi_level'],
                '距離台北車站(公里)': site['distance_to_taipei'],
                'PM2.5': site['pm25'] if site['pm25'] else 'N/A',
                'PM10': site['pm10'] if site['pm10'] else 'N/A',
                'O3': site['o3'] if site['o3'] else 'N/A',
                'NO2': site['no2'] if site['no2'] else 'N/A',
                'SO2': site['so2'] if site['so2'] else 'N/A',
                'CO': site['co'] if site['co'] else 'N/A',
                '狀態': site['status']
            })
        
        df = pd.DataFrame(df_data)
        
        # 儲存 CSV 檔案
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"AQI 數據已儲存至: {output_path}")
        return output_path
    
    def run(self):
        """執行完整的 AQI 地圖生成流程"""
        try:
            # 1. 獲取數據
            raw_data = self.fetch_aqi_data()
            
            # 2. 處理數據
            processed_data = self.process_data(raw_data)
            
            if not processed_data:
                print("沒有有效的測站數據")
                return None
            
            # 3. 建立地圖
            aqi_map = self.create_map(processed_data)
            
            # 4. 儲存地圖
            output_file = self.save_map(aqi_map)
            
            # 5. 儲存 CSV 檔案
            csv_file = self.save_to_csv(processed_data)
            
            # 6. 顯示統計資訊
            self.show_statistics(processed_data)
            
            return output_file, csv_file
            
        except Exception as e:
            print(f"執行過程中發生錯誤: {e}")
            return None
    
    def show_statistics(self, data):
        """顯示數據統計資訊"""
        print("\n=== AQI 數據統計 ===")
        print(f"總測站數量: {len(data)}")
        
        # 統計各等級數量
        level_count = {}
        valid_aqi_count = 0
        
        for site in data:
            level = site['aqi_level']
            level_count[level] = level_count.get(level, 0) + 1
            if site['aqi'] is not None:
                valid_aqi_count += 1
        
        print(f"有效 AQI 數據測站: {valid_aqi_count}")
        print("\n空氣品質等級分布:")
        for level, count in level_count.items():
            print(f"  {level}: {count} 個測站")


def main():
    """主程式入口"""
    print("=" * 50)
    print("台灣空氣品質指標 (AQI) 即時監測地圖生成器")
    print("=" * 50)
    
    try:
        # 建立 AQI 地圖生成器
        generator = AQIMapGenerator()
        
        # 執行地圖生成
        result = generator.run()
        
        if result:
            output_file, csv_file = result
            print(f"\n[成功] 地圖生成成功！")
            print(f"[檔案] 地圖檔案: {output_file}")
            print(f"[檔案] CSV 數據: {csv_file}")
            print("\n請在瀏覽器中開啟 HTML 檔案查看地圖")
            print("CSV 檔案包含距離台北車站的計算結果")
        else:
            print("\n[失敗] 地圖生成失敗")
            
    except Exception as e:
        print(f"\n[錯誤] 程式執行失敗: {e}")


if __name__ == "__main__":
    main()
