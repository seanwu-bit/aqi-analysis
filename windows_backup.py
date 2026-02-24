#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 系統 GitHub 備份腳本
使用完整路徑執行 Git 命令
"""

import os
import subprocess
import webbrowser
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def run_git_command(command, description):
    """使用完整路徑執行 Git 命令"""
    git_path = r"C:\Program Files\Git\bin\git.exe"
    full_command = f'"{git_path}" {command}'
    
    try:
        print(f"\n[執行] {description}...")
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(f"[成功] {description}")
            if result.stdout.strip():
                print(f"   輸出: {result.stdout.strip()}")
            return True
        else:
            print(f"[失敗] {description}")
            if result.stderr.strip():
                print(f"   錯誤: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[錯誤] {description} 發生異常: {e}")
        return False

def check_git_available():
    """檢查 Git 是否可用"""
    git_path = r"C:\Program Files\Git\bin\git.exe"
    return os.path.exists(git_path)

def main():
    """主程式"""
    print("=" * 60)
    print("Windows 系統 - GitHub 雲端備份")
    print("=" * 60)
    
    # 讀取 GitHub 帳戶資訊
    github_user = os.getenv('GitHub_User')
    github_email = os.getenv('GitHub_Email')
    
    if not github_user or not github_email:
        print("[錯誤] 請在 .env 檔案中設定 GitHub_User 和 GitHub_Email")
        print("範例：")
        print("GitHub_User=你的GitHub用戶名")
        print("GitHub_Email=你的GitHub郵箱")
        return
    
    print(f"[確認] GitHub 用戶: {github_user}")
    print(f"[確認] GitHub 郵箱: {github_email}")
    
    # 檢查 Git 是否可用
    if not check_git_available():
        print("[錯誤] Git 未找到，請確認安裝路徑")
        return
    
    print("[確認] Git 已安裝在標準位置")
    
    # 執行備份步驟
    print("\n開始執行 GitHub 備份...")
    
    # 1. 初始化倉庫
    if run_git_command("init", "初始化 Git 倉庫"):
        print("Git 倉庫初始化成功")
    else:
        print("Git 倉庫可能已存在，繼續執行...")
    
    # 2. 設定用戶信息
    run_git_command(f'config user.name "{github_user}"', "設定用戶名")
    run_git_command(f'config user.email "{github_email}"', "設定郵箱")
    
    # 3. 添加檔案
    if run_git_command("add .", "添加所有檔案"):
        print("檔案添加成功")
    
    # 4. 提交變更
    commit_message = f"AQI Analysis Project - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    if run_git_command(f'commit -m "{commit_message}"', "提交變更"):
        print("變更提交成功")
    
    # 5. 連接遠端倉庫
    remote_url = f"https://github.com/{github_user}/aqi-analysis.git"
    run_git_command(f'remote add origin {remote_url}', "連接遠端倉庫")
    
    # 6. 推送到 GitHub
    print("\n[重要] 推送到 GitHub...")
    if run_git_command("push -u origin main", "推送到 GitHub"):
        print("推送成功！")
        print(f"\n您的代碼已備份到: {remote_url}")
    else:
        print("推送失敗，可能需要先在 GitHub 建立倉庫")
        print("\n請按照以下步驟：")
        print(f"1. 開啟 https://github.com/new")
        print(f"2. 倉庫名稱: aqi-analysis")
        print(f"3. 建立後重新執行此腳本")
        
        # 詢問是否開啟 GitHub
        open_github = input("是否開啟 GitHub 建立倉庫？(y/n): ").strip().lower()
        if open_github in ['y', 'yes', '是']:
            webbrowser.open('https://github.com/new')
            print("已開啟 GitHub 新倉庫頁面")
    
    print("\n" + "=" * 60)
    print("GitHub 備份流程完成！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程式中斷，再見！")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
