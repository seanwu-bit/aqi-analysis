#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
異常點位檢測與修正腳本
檢查用戶報告的異常避難所點位
"""

import os
import pandas as pd
import requests
from dotenv import load_dotenv
from datetime import datetime

# 載入環境變數
load_dotenv()

class AnomalyDetector:
    """異常點位檢測器"""
    
    def __init__(self):
        """初始化檢測器"""
        self.output_dir = 'outputs'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 用戶報告的異常點位
        self.anomaly_shelters = [
            '霧峰國中行政大樓地下室',
            '忠孝國小',
            '松林活動中心',
            '新豐社區活動中心',
            '台東市東區樂業國小',
            '土牛活動中心',
            '同安國小',
            '追分國小多功能教室',
            '大南國民小學',
            '湖口鄉信勢國小禮堂'
        ]
        
        print(f"異常點位檢測器初始化完成，檢查 {len(self.anomaly_shelters)} 個點位")
    
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
    
    def find_anomaly_records(self, df):
        """找出異常點位的記錄"""
        print("\n=== 查找異常點位記錄 ===")
        
        anomaly_records = []
        
        for shelter_name in self.anomaly_shelters:
            # 模糊搜尋
            matches = df[df['避難收容處所名稱'].str.contains(shelter_name, na=False, case=False)]
            
            if not matches.empty:
                for idx, row in matches.iterrows():
                    anomaly_records.append({
                        'index': idx,
                        'name': row['避難收容處所名稱'],
                        'county': row['縣市及鄉鎮市區'],
                        'address': row['避難收容處所地址'],
                        'lon': row['經度'],
                        'lat': row['緯度'],
                        'in_door': row['in_door'],
                        'issue': '用戶報告海中異常'
                    })
                    print(f"找到: {row['避難收容處所名稱']} - ({row['經度']}, {row['緯度']})")
            else:
                print(f"未找到: {shelter_name}")
        
        print(f"\n共找到 {len(anomaly_records)} 筆異常記錄")
        return anomaly_records
    
    def geocode_address(self, address, county):
        """透過地址搜尋正確座標"""
        try:
            # 使用台灣開放資料平台的地址定位服務
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': f"{address}, {county}, Taiwan",
                'format': 'json',
                'limit': 1,
                'countrycodes': 'tw'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return float(data[0]['lon']), float(data[0]['lat'])
        except Exception as e:
            print(f"地址定位失敗 {address}: {e}")
        
        return None, None
    
    def analyze_coordinate_issues(self, anomaly_records):
        """分析座標問題"""
        print("\n=== 分析座標問題 ===")
        
        issues = {
            'zero_coordinates': [],
            'out_of_bounds': [],
            'swapped_coordinates': [],
            'wrong_region': []
        }
        
        for record in anomaly_records:
            lon, lat = record['lon'], record['lat']
            
            # 檢查零值座標
            if lon == 0 or lat == 0:
                issues['zero_coordinates'].append(record)
                record['issue_type'] = 'zero_coordinates'
                continue
            
            # 檢查是否在台灣合理範圍內
            if not (119.5 <= lon <= 122.5 and 21.5 <= lat <= 25.5):
                issues['out_of_bounds'].append(record)
                record['issue_type'] = 'out_of_bounds'
                continue
            
            # 檢查是否經緯度被交換
            if 21.5 <= lon <= 25.5 and 119.5 <= lat <= 122.5:
                issues['swapped_coordinates'].append(record)
                record['issue_type'] = 'swapped_coordinates'
                continue
            
            # 檢查是否在錯誤的區域
            county = record['county']
            if '新竹' in county and not (120.8 <= lon <= 121.2 and 24.5 <= lat <= 24.9):
                issues['wrong_region'].append(record)
                record['issue_type'] = 'wrong_region'
            elif '台中' in county and not (120.5 <= lon <= 121.0 and 24.0 <= lat <= 24.5):
                issues['wrong_region'].append(record)
                record['issue_type'] = 'wrong_region'
            elif '台東' in county and not (120.8 <= lon <= 121.3 and 22.5 <= lat <= 23.2):
                issues['wrong_region'].append(record)
                record['issue_type'] = 'wrong_region'
        
        # 統計問題類型
        print("問題類型統計:")
        for issue_type, records in issues.items():
            if records:
                print(f"  {issue_type}: {len(records)} 筆")
                for record in records:
                    print(f"    {record['name']} - ({record['lon']}, {record['lat']})")
        
        return issues
    
    def attempt_coordinate_correction(self, anomaly_records):
        """嘗試修正座標"""
        print("\n=== 嘗試座標修正 ===")
        
        corrected_records = []
        
        for record in anomaly_records:
            original_lon, original_lat = record['lon'], record['lat']
            county = record['county']
            address = record['address']
            
            print(f"\n處理: {record['name']}")
            print(f"原始座標: ({original_lon}, {original_lat})")
            
            # 嘗試地址定位
            if pd.notna(address) and address.strip():
                new_lon, new_lat = self.geocode_address(address, county)
                if new_lon and new_lat:
                    print(f"地址定位修正: ({new_lon}, {new_lat})")
                    record['corrected_lon'] = new_lon
                    record['corrected_lat'] = new_lat
                    record['correction_method'] = 'geocoding'
                    corrected_records.append(record)
                    continue
            
            # 嘗試交換經緯度
            if 21.5 <= original_lon <= 25.5 and 119.5 <= original_lat <= 122.5:
                swapped_lon, swapped_lat = original_lat, original_lon
                print(f"交換經緯度: ({swapped_lon}, {swapped_lat})")
                record['corrected_lon'] = swapped_lon
                record['corrected_lat'] = swapped_lat
                record['correction_method'] = 'coordinate_swap'
                corrected_records.append(record)
                continue
            
            # 無法修正
            print("無法修正，建議移除")
            record['correction_method'] = 'remove'
        
        print(f"\n成功修正: {len(corrected_records)} 筆")
        return corrected_records
    
    def generate_anomaly_report(self, anomaly_records, issues, corrected_records):
        """生成異常點位報告"""
        report = f"""# 異常點位檢測與修正報告

## 基本資訊
- **報告生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **檢測類型**: 用戶報告海中異常點位
- **檢測點位數量**: {len(self.anomaly_shelters)} 個
- **實際找到記錄**: {len(anomaly_records)} 筆

## 異常點位詳細分析

### 1. 問題類型統計
"""
        
        for issue_type, records in issues.items():
            if records:
                report += f"- **{issue_type}**: {len(records)} 筆\n"
        
        report += f"""
### 2. 異常點位清單
"""
        
        for i, record in enumerate(anomaly_records, 1):
            issue_type = record.get('issue_type', 'unknown')
            report += f"""
{i}. **{record['name']}**
   - 位置: {record['county']}
   - 地址: {record['address']}
   - 原始座標: ({record['lon']}, {record['lat']})
   - 問題類型: {issue_type}
   - 室內/室外: {'室內' if record['in_door'] else '室外'}
"""
        
        report += f"""
### 3. 修正結果
"""
        
        if corrected_records:
            report += f"成功修正 {len(corrected_records)} 筆記錄:\n\n"
            for record in corrected_records:
                report += f"- **{record['name']}**: "
                if record['correction_method'] == 'geocoding':
                    report += f"地址定位修正 ({record['corrected_lon']}, {record['corrected_lat']})\n"
                elif record['correction_method'] == 'coordinate_swap':
                    report += f"交換經緯度修正 ({record['corrected_lon']}, {record['corrected_lat']})\n"
        else:
            report += "無法修正任何記錄，建議全部移除\n"
        
        report += f"""
### 4. 修正建議

#### 立即處理
- 將無法修正的記錄從數據庫中移除
- 更新可修正記錄的座標資訊
- 重新執行空間疊圖分析

#### 預防措施
- 加強座標驗證機制
- 增加經緯度合理性檢查
- 建立異常座標自動警報

#### 數據品質改進
- 定期進行地址編碼驗證
- 建立座標交叉驗證流程
- 增加人工審查環節

---
*報告由異常點位檢測系統自動生成*
"""
        
        # 保存報告
        report_file = os.path.join(self.output_dir, f'anomaly_detection_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"異常檢測報告已保存: {report_file}")
        return report_file
    
    def run_detection(self):
        """執行異常檢測"""
        print("=" * 60)
        print("異常點位檢測與修正")
        print("=" * 60)
        
        # 1. 載入數據
        df = self.load_shelter_data()
        if df is None:
            return
        
        # 2. 找出異常記錄
        anomaly_records = self.find_anomaly_records(df)
        
        if not anomaly_records:
            print("未找到任何異常記錄")
            return
        
        # 3. 分析座標問題
        issues = self.analyze_coordinate_issues(anomaly_records)
        
        # 4. 嘗試修正座標
        corrected_records = self.attempt_coordinate_correction(anomaly_records)
        
        # 5. 生成報告
        report_file = self.generate_anomaly_report(anomaly_records, issues, corrected_records)
        
        print("\n" + "=" * 60)
        print("異常檢測完成！")
        print(f"檢測點位: {len(self.anomaly_shelters)} 個")
        print(f"異常記錄: {len(anomaly_records)} 筆")
        print(f"修正記錄: {len(corrected_records)} 筆")
        print(f"檢測報告: {report_file}")
        print("=" * 60)
        
        return {
            'anomaly_records': anomaly_records,
            'issues': issues,
            'corrected_records': corrected_records,
            'report_file': report_file
        }

def main():
    """主程式"""
    detector = AnomalyDetector()
    results = detector.run_detection()
    
    if results:
        print("\n檢測結果摘要:")
        print(f"異常記錄: {len(results['anomaly_records'])} 筆")
        print(f"可修正: {len(results['corrected_records'])} 筆")
        print(f"需移除: {len(results['anomaly_records']) - len(results['corrected_records'])} 筆")

if __name__ == "__main__":
    main()
