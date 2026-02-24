#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
環境安裝腳本
自動安裝 AQI 地圖專案所需的 Python 套件
"""

import subprocess
import sys
import os

def install_requirements():
    """安裝 requirements.txt 中的套件"""
    print("正在安裝專案依賴套件...")
    
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"❌ 找不到 {requirements_file} 檔案")
        return False
    
    try:
        # 使用 pip 安裝套件
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ], check=True, capture_output=True, text=True)
        
        print("✅ 套件安裝成功！")
        print("\n已安裝的套件:")
        
        # 顯示已安裝的套件
        with open(requirements_file, 'r', encoding='utf-8') as f:
            packages = f.read().strip().split('\n')
            for package in packages:
                if package.strip():
                    print(f"  • {package}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 套件安裝失敗: {e}")
        print(f"錯誤訊息: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 安裝過程發生未知錯誤: {e}")
        return False

def check_python_version():
    """檢查 Python 版本"""
    print("檢查 Python 版本...")
    
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ 需要 Python 3.7 或更高版本")
        return False
    
    print("✅ Python 版本符合要求")
    return True

def create_directories():
    """建立必要的目錄"""
    print("建立專案目錄...")
    
    directories = ['data', 'outputs', 'logs']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"  ✅ 建立目錄: {directory}")
        else:
            print(f"  ℹ️  目錄已存在: {directory}")

def main():
    """主程式"""
    print("=" * 50)
    print("AQI 地圖專案環境安裝程式")
    print("=" * 50)
    
    # 1. 檢查 Python 版本
    if not check_python_version():
        return
    
    # 2. 建立目錄
    create_directories()
    
    # 3. 安裝套件
    if install_requirements():
        print("\n" + "=" * 50)
        print("🎉 環境安裝完成！")
        print("=" * 50)
        print("\n接下來您可以：")
        print("1. 在 .env 檔案中設定您的 MOENV_API_KEY")
        print("2. 執行 python src/aqi_map.py 來生成 AQI 地圖")
        print("\n祝您使用愉快！")
    else:
        print("\n❌ 環境安裝失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main()
