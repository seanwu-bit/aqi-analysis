#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AQI 分析專案 - 主要運算邏輯
整合空氣品質指標 (AQI) 和氣溫監測功能
"""

import os
import sys
from datetime import datetime
from scripts.aqi_map import AQIMapGenerator
from scripts.cwa_weather_map import CWATemperatureMapGenerator

def show_menu():
    """顯示主選單"""
    print("=" * 60)
    print("AQI 分析專案 - 主要選單")
    print("=" * 60)
    print()
    print("請選擇要執行的功能：")
    print()
    print("1. 空氣品質指標 (AQI) 即時監測地圖")
    print("   - 獲取全台 AQI 數據")
    print("   - 計算各測站到台北車站的距離")
    print("   - 生成互動式地圖和 CSV 數據")
    print()
    print("2. 台灣即時氣溫監測地圖")
    print("   - 獲取全台氣象站數據")
    print("   - 生成氣溫分級視覺化地圖")
    print("   - 輸出詳細氣象數據 CSV")
    print()
    print("3. 執行完整分析（AQI + 氣溫）")
    print("   - 同時生成 AQI 和氣溫地圖")
    print("   - 產生完整的環境監測報告")
    print()
    print("4. 顯示專案資訊")
    print("5. 離開程式")
    print()
    print("=" * 60)

def get_user_choice():
    """獲取用戶選擇"""
    while True:
        try:
            choice = input("請輸入選項 (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return int(choice)
            else:
                print("無效選項，請輸入 1-5 的數字")
        except KeyboardInterrupt:
            print("\n\n程式中斷，再見！")
            sys.exit(0)
        except Exception as e:
            print(f"輸入錯誤: {e}")

def run_aqi_analysis():
    """執行 AQI 分析"""
    print("\n" + "=" * 60)
    print("執行空氣品質指標 (AQI) 分析")
    print("=" * 60)
    
    try:
        generator = AQIMapGenerator()
        result = generator.run()
        
        if result:
            output_file, csv_file = result
            print(f"\n[成功] AQI 分析完成！")
            print(f"[地圖] 地圖檔案: {output_file}")
            print(f"[數據] 數據檔案: {csv_file}")
            print(f"[說明] CSV 包含距離台北車站的計算結果")
        else:
            print("\n[失敗] AQI 分析失敗")
            
    except Exception as e:
        print(f"\n[錯誤] AQI 分析發生錯誤: {e}")

def run_temperature_analysis():
    """執行氣溫分析"""
    print("\n" + "=" * 60)
    print("執行台灣即時氣溫監測分析")
    print("=" * 60)
    
    try:
        generator = CWATemperatureMapGenerator()
        result = generator.run()
        
        if result:
            output_file, csv_files = result
            print(f"\n[成功] 氣溫分析完成！")
            print(f"[地圖] 地圖檔案: {output_file}")
            print(f"[數據] 詳細數據: {csv_files[0]}")
            print(f"[統計] 統計摘要: {csv_files[1]}")
            print(f"[縣市] 各縣市數據: {csv_files[2]}")
        else:
            print("\n[失敗] 氣溫分析失敗")
            
    except Exception as e:
        print(f"\n[錯誤] 氣溫分析發生錯誤: {e}")

def run_complete_analysis():
    """執行完整分析"""
    print("\n" + "=" * 60)
    print("執行完整環境監測分析")
    print("=" * 60)
    print("將依序執行：")
    print("   1. 空氣品質指標 (AQI) 分析")
    print("   2. 台灣即時氣溫監測分析")
    print()
    
    # 執行 AQI 分析
    print("步驟 1/2: 執行 AQI 分析...")
    run_aqi_analysis()
    
    print("\n" + "-" * 60)
    
    # 執行氣溫分析
    print("步驟 2/2: 執行氣溫分析...")
    run_temperature_analysis()
    
    print("\n" + "=" * 60)
    print("[完成] 完整環境監測分析完成！")
    print("[說明] 所有輸出檔案已儲存至 outputs/ 目錄")
    print("=" * 60)

def show_project_info():
    """顯示專案資訊"""
    print("\n" + "=" * 60)
    print("AQI 分析專案資訊")
    print("=" * 60)
    print()
    print("專案目標：")
    print("   提供台灣環境品質的即時監測與視覺化")
    print()
    print("主要功能：")
    print("   • 空氣品質指標 (AQI) 即時監測地圖")
    print("   • 台灣氣象站氣溫監測地圖")
    print("   • 空間距離計算（到台北車站）")
    print("   • CSV 數據匯出功能")
    print("   • GitHub 雲端備份支援")
    print()
    print("數據來源：")
    print("   • 環境部 API (AQI 數據)")
    print("   • 中央氣象局 API (氣象數據)")
    print()
    print("技術棧：")
    print("   • Python 3.14")
    print("   • Folium (地圖視覺化)")
    print("   • Pandas (數據處理)")
    print("   • Requests (API 串接)")
    print()
    print("輸出檔案：")
    print("   • HTML 互動式地圖")
    print("   • CSV 結構化數據")
    print("   • 統計摘要報告")
    print()
    print("GitHub 備份：")
    print("   • 請參考 GITHUB_BACKUP_INSTRUCTIONS.md")
    print("   • 倉庫名稱建議：aqi-analysis")
    print()
    print("=" * 60)

def main():
    """主程式"""
    print("啟動 AQI 分析專案...")
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    while True:
        show_menu()
        choice = get_user_choice()
        
        if choice == 1:
            run_aqi_analysis()
        elif choice == 2:
            run_temperature_analysis()
        elif choice == 3:
            run_complete_analysis()
        elif choice == 4:
            show_project_info()
        elif choice == 5:
            print("\n感謝使用 AQI 分析專案，再見！")
            break
        
        # 詢問是否繼續
        if choice != 5:
            print("\n" + "-" * 40)
            continue_choice = input("是否返回主選單？(y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes', '是']:
                print("\n感謝使用 AQI 分析專案，再見！")
                break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程式中斷，再見！")
        sys.exit(0)
    except Exception as e:
        print(f"\n[錯誤] 程式發生未預期的錯誤: {e}")
        sys.exit(1)
