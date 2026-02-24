#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣即時氣溫監測地圖
串接中央氣象局 CWA 自動氣象站觀測 API 獲取全台氣溫數據並使用 Folium 視覺化
"""

import os
import requests
import folium
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json
import csv

# 載入環境變數
load_dotenv()

class CWATemperatureMapGenerator:
    """CWA 氣溫地圖生成器類別"""
    
    def __init__(self):
        """初始化 CWA 氣溫地圖生成器"""
        self.api_key = os.getenv('CWA_API_KEY')
        if not self.api_key:
            raise ValueError("請在 .env 檔案中設定 CWA_API_KEY")
        
        # 中央氣象局 API 端點 (O-A0003-001: 自動氣象站觀測資料)
        self.api_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001"
        
        # 氣溫顏色對應表 (攝氏溫度)
        self.temp_colors = {
            (0, 10): '#0066CC',    # 深藍色 - 極冷
            (10, 15): '#0099FF',   # 藍色 - 寒冷
            (15, 20): '#00CCFF',   # 淺藍色 - 涼爽
            (20, 25): '#00FF99',   # 綠色 - 舒適
            (25, 28): '#FFFF00',   # 黃色 - 溫暖
            (28, 30): '#FF9900',   # 橙色 - 炎熱
            (30, 35): '#FF6600',   # 深橙色 - 酷熱
            (35, 50): '#FF0000'    # 紅色 - 極熱
        }
        
        # 氣溫等級對應
        self.temp_levels = {
            (0, 10): '極冷',
            (10, 15): '寒冷',
            (15, 20): '涼爽',
            (20, 25): '舒適',
            (25, 28): '溫暖',
            (28, 30): '炎熱',
            (30, 35): '酷熱',
            (35, 50): '極熱'
        }
    
    def get_temp_level(self, temp_value):
        """根據氣溫數值判斷氣溫等級"""
        try:
            temp = float(temp_value)
            for (min_val, max_val), level in self.temp_levels.items():
                if min_val <= temp < max_val:
                    return level
            return '極熱'  # 超過 35 度視為極熱
        except (ValueError, TypeError):
            return '未知'
    
    def get_temp_color(self, temp_value):
        """根據氣溫數值獲取對應顏色"""
        try:
            temp = float(temp_value)
            for (min_val, max_val), color in self.temp_colors.items():
                if min_val <= temp < max_val:
                    return color
            return '#FF0000'  # 預設紅色
        except (ValueError, TypeError):
            return '#808080'  # 灰色表示無數據
    
    def fetch_weather_data(self):
        """從中央氣象局 API 獲取氣象站數據"""
        print("正在獲取氣象站數據...")
        
        params = {
            'Authorization': self.api_key,
            'format': 'JSON'
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            # 檢查 API 回應格式
            if 'success' not in data or not data['success']:
                raise ValueError("API 回應失敗")
            
            if 'records' not in data or 'Station' not in data['records']:
                raise ValueError("API 回應格式錯誤：找不到氣象站資料")
            
            stations = data['records']['Station']
            print(f"成功獲取 {len(stations)} 個氣象站數據")
            return stations
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"API 連線失敗: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失敗: {e}")
    
    def process_data(self, raw_data):
        """處理和清理氣象站數據"""
        processed_data = []
        
        for station in raw_data:
            try:
                # 檢查必要欄位是否存在
                if not all(key in station for key in ['StationName', 'GeoInfo']):
                    continue
                
                # 獲取座標資訊
                geo_info = station['GeoInfo']['Coordinates']
                if not geo_info or len(geo_info) == 0:
                    continue
                
                # 使用 WGS84 坐標系統（第二個座標，如果有的話），否則使用第一個
                coord = geo_info[1] if len(geo_info) > 1 else geo_info[0]
                lat = float(coord['StationLatitude'])
                lon = float(coord['StationLongitude'])
                
                # 獲取氣象觀測數據
                weather_elements = station.get('WeatherElement', {})
                
                # 獲取氣溫數據
                temp = weather_elements.get('AirTemperature')
                if temp is None or temp == '':
                    temp = None
                else:
                    temp = float(temp)
                    # 過濾異常值（小於 -50°C 或大於 60°C 視為異常）
                    if temp < -50 or temp > 60:
                        temp = None
                
                # 獲取濕度
                humidity = weather_elements.get('RelativeHumidity')
                if humidity is None or humidity == '':
                    humidity = None
                else:
                    humidity = float(humidity)
                
                # 處理觀測時間
                obs_time = station.get('ObsTime', {})
                if isinstance(obs_time, dict) and 'DateTime' in obs_time:
                    observation_time = obs_time['DateTime']
                else:
                    observation_time = str(obs_time) if obs_time else '未知'
                
                # 判斷氣溫等級和顏色
                temp_level = self.get_temp_level(temp) if temp else '無數據'
                color = self.get_temp_color(temp) if temp else '#808080'
                
                # 獲取其他氣象數據
                pressure = weather_elements.get('AirPressure')
                wind_speed = weather_elements.get('WindSpeed')
                wind_direction = weather_elements.get('WindDirection')
                
                processed_data.append({
                    'station_name': station['StationName'],
                    'station_id': station.get('StationId', '未知'),
                    'county': station['GeoInfo'].get('CountyName', '未知'),
                    'latitude': lat,
                    'longitude': lon,
                    'temperature': temp,
                    'temp_level': temp_level,
                    'color': color,
                    'humidity': humidity,
                    'pressure': pressure,
                    'wind_speed': wind_speed,
                    'wind_direction': wind_direction,
                    'observation_time': observation_time
                })
                
            except (ValueError, KeyError, TypeError) as e:
                print(f"處理氣象站 {station.get('StationName', '未知')} 數據時發生錯誤: {e}")
                continue
        
        print(f"成功處理 {len(processed_data)} 個有效氣象站數據")
        return processed_data
    
    def create_map(self, weather_data):
        """建立 Folium 地圖並標示氣象站"""
        print("正在建立氣溫地圖...")
        
        # 計算台灣中心點作為地圖初始位置
        if weather_data:
            center_lat = sum([site['latitude'] for site in weather_data]) / len(weather_data)
            center_lon = sum([site['longitude'] for site in weather_data]) / len(weather_data)
        else:
            center_lat, center_lon = 23.8, 120.9  # 台灣中心點預設值
        
        # 建立地圖
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 添加氣溫圖例
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>氣溫分級圖例</h4>
        '''
        
        for (min_val, max_val), level in self.temp_levels.items():
            color = self.temp_colors[(min_val, max_val)]
            legend_html += f'<i style="background:{color}; width:12px; height:12px; display:inline-block;"></i> {min_val}-{max_val}°C {level}<br>'
        
        legend_html += '</div>'
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 在地圖上添加氣象站標記
        for site in weather_data:
            # 建立彈出視窗內容
            popup_content = f"""
            <b>{site['station_name']} 氣象站</b><br>
            測站編號: {site['station_id']}<br>
            縣市: {site['county']}<br>
            氣溫: {site['temperature']:.1f}°C ({site['temp_level']})<br>
            濕度: {site['humidity']:.1f}%<br>
            氣壓: {site['pressure']} hPa<br>
            風速: {site['wind_speed']} m/s<br>
            風向: {site['wind_direction']}°<br>
            觀測時間: {site['observation_time']}
            """ if site['temperature'] else f"""
            <b>{site['station_name']} 氣象站</b><br>
            測站編號: {site['station_id']}<br>
            縣市: {site['county']}<br>
            氣溫: 無數據<br>
            觀測時間: {site['observation_time']}
            """
            
            # 建立圓形標記，大小根據氣溫調整
            if site['temperature']:
                # 氣溫越高，圓圈越大
                radius = 5 + (site['temperature'] / 5)
            else:
                radius = 5
            
            folium.CircleMarker(
                location=[site['latitude'], site['longitude']],
                radius=radius,
                popup=folium.Popup(popup_content, max_width=300),
                color='black',
                weight=1,
                fillColor=site['color'],
                fillOpacity=0.7,
                tooltip=f"{site['station_name']} - {site['temperature']:.1f}°C" if site['temperature'] else f"{site['station_name']} - 無數據"
            ).add_to(m)
        
        # 添加地圖標題
        title_html = '''
        <h3 align="center" style="font-size:16px"><b>台灣即時氣溫監測地圖</b></h3>
        <p align="center" style="font-size:12px">更新時間: {}</p>
        '''.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        m.get_root().html.add_child(folium.Element(title_html))
        
        return m
    
    def save_map(self, map_obj, filename=None):
        """儲存地圖到 outputs 目錄"""
        if filename is None:
            filename = f"cwa_temp_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        output_path = os.path.join('outputs', filename)
        
        # 確保 outputs 目錄存在
        os.makedirs('outputs', exist_ok=True)
        
        map_obj.save(output_path)
        print(f"地圖已儲存至: {output_path}")
        return output_path
    
    def save_to_csv(self, weather_data, filename=None):
        """將氣象數據儲存為 CSV 檔案"""
        if filename is None:
            filename = f"cwa_temperature_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        output_path = os.path.join('outputs', filename)
        
        # 確保 outputs 目錄存在
        os.makedirs('outputs', exist_ok=True)
        
        # 計算統計資訊
        valid_temps = [site['temperature'] for site in weather_data if site['temperature'] is not None]
        max_temp = max(valid_temps) if valid_temps else None
        min_temp = min(valid_temps) if valid_temps else None
        avg_temp = sum(valid_temps) / len(valid_temps) if valid_temps else None
        
        # 建立 DataFrame
        df_data = []
        for site in weather_data:
            df_data.append({
                '測站名稱': site['station_name'],
                '測站編號': site['station_id'],
                '縣市': site['county'],
                '緯度': site['latitude'],
                '經度': site['longitude'],
                '氣溫(°C)': site['temperature'] if site['temperature'] is not None else 'N/A',
                '氣溫等級': site['temp_level'],
                '相對濕度(%)': site['humidity'] if site['humidity'] is not None else 'N/A',
                '氣壓(hPa)': site['pressure'] if site['pressure'] else 'N/A',
                '風速(m/s)': site['wind_speed'] if site['wind_speed'] else 'N/A',
                '風向(度)': site['wind_direction'] if site['wind_direction'] else 'N/A',
                '觀測時間': site['observation_time']
            })
        
        df = pd.DataFrame(df_data)
        
        # 儲存主要數據
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        # 建立統計摘要檔案
        summary_filename = f"cwa_temperature_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        summary_path = os.path.join('outputs', summary_filename)
        
        # 統計各等級數量
        level_count = {}
        for site in weather_data:
            level = site['temp_level']
            level_count[level] = level_count.get(level, 0) + 1
        
        # 統計各縣市平均氣溫
        city_temps = {}
        city_count = {}
        for site in weather_data:
            if site['temperature'] is not None:
                city = site['county']
                city_temps[city] = city_temps.get(city, 0) + site['temperature']
                city_count[city] = city_count.get(city, 0) + 1
        
        city_avg_temps = {city: city_temps[city] / city_count[city] for city in city_temps}
        
        # 建立統計摘要
        summary_data = {
            '統計項目': [
                '總測站數量',
                '有效氣溫數據測站數量',
                '平均氣溫(°C)',
                '最高氣溫(°C)',
                '最低氣溫(°C)',
                '資料擷取時間'
            ],
            '數值': [
                len(weather_data),
                len(valid_temps),
                f"{avg_temp:.1f}" if avg_temp else 'N/A',
                f"{max_temp:.1f}" if max_temp else 'N/A',
                f"{min_temp:.1f}" if min_temp else 'N/A',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')
        
        # 建立各縣市平均氣溫檔案
        city_filename = f"cwa_temperature_by_city_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        city_path = os.path.join('outputs', city_filename)
        
        city_data = []
        for city in sorted(city_avg_temps.keys()):
            city_data.append({
                '縣市': city,
                '平均氣溫(°C)': f"{city_avg_temps[city]:.1f}",
                '測站數量': city_count[city]
            })
        
        city_df = pd.DataFrame(city_data)
        city_df.to_csv(city_path, index=False, encoding='utf-8-sig')
        
        print(f"詳細數據已儲存至: {output_path}")
        print(f"統計摘要已儲存至: {summary_path}")
        print(f"各縣市數據已儲存至: {city_path}")
        
        return output_path, summary_path, city_path
    
    def run(self):
        """執行完整的氣溫地圖生成流程"""
        try:
            # 1. 獲取數據
            raw_data = self.fetch_weather_data()
            
            # 2. 處理數據
            processed_data = self.process_data(raw_data)
            
            if not processed_data:
                print("沒有有效的氣象站數據")
                return None
            
            # 3. 建立地圖
            weather_map = self.create_map(processed_data)
            
            # 4. 儲存地圖
            output_file = self.save_map(weather_map)
            
            # 5. 儲存 CSV 檔案
            csv_files = self.save_to_csv(processed_data)
            
            # 6. 顯示統計資訊
            self.show_statistics(processed_data)
            
            return output_file, csv_files
            
        except Exception as e:
            print(f"執行過程中發生錯誤: {e}")
            return None
    
    def show_statistics(self, data):
        """顯示數據統計資訊"""
        print("\n=== 氣溫數據統計 ===")
        print(f"總氣象站數量: {len(data)}")
        
        # 統計各等級數量
        level_count = {}
        valid_temp_count = 0
        temps = []
        
        for site in data:
            level = site['temp_level']
            level_count[level] = level_count.get(level, 0) + 1
            if site['temperature'] is not None:
                valid_temp_count += 1
                temps.append(site['temperature'])
        
        print(f"有效氣溫數據測站: {valid_temp_count}")
        
        if temps:
            print(f"平均氣溫: {sum(temps)/len(temps):.1f}°C")
            print(f"最高氣溫: {max(temps):.1f}°C")
            print(f"最低氣溫: {min(temps):.1f}°C")
        
        print("\n氣溫等級分布:")
        for level in sorted(level_count.keys()):
            count = level_count[level]
            print(f"  {level}: {count} 個測站")


def main():
    """主程式入口"""
    print("=" * 50)
    print("台灣即時氣溫監測地圖生成器")
    print("=" * 50)
    
    try:
        # 建立 CWA 氣溫地圖生成器
        generator = CWATemperatureMapGenerator()
        
        # 執行地圖生成
        result = generator.run()
        
        if result:
            output_file, csv_files = result
            print(f"\n[成功] 地圖生成成功！")
            print(f"[檔案] 地圖檔案: {output_file}")
            print(f"[檔案] 詳細數據: {csv_files[0]}")
            print(f"[檔案] 統計摘要: {csv_files[1]}")
            print(f"[檔案] 各縣市數據: {csv_files[2]}")
            print("\n請在瀏覽器中開啟 HTML 檔案查看地圖")
            print("CSV 檔案可用於數據分析")
        else:
            print("\n[失敗] 地圖生成失敗")
            
    except Exception as e:
        print(f"\n[錯誤] 程式執行失敗: {e}")


if __name__ == "__main__":
    main()
