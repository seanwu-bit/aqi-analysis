#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品質檢查腳本 - 評估各項評分標準的完成度
"""

import pandas as pd
import numpy as np
import math
import os
from datetime import datetime

class QualityChecker:
    """品質檢查器"""
    
    def __init__(self):
        self.output_dir = 'outputs'
        self.results = {}
    
    def check_spatial_audit(self):
        """檢查 Spatial Audit (25%)"""
        print("=== Spatial Audit 檢查 ===")
        
        # 載入清理後的避難所數據
        try:
            df = pd.read_csv('outputs/shelter_data_cleaned_20260303_210104.csv', encoding='utf-8-sig')
            
            # 檢查座標問題識別品質
            coordinate_issues = 0
            
            # 1. 檢查零值座標
            zero_coords = (df['經度'] == 0) | (df['緯度'] == 0)
            coordinate_issues += zero_coords.sum()
            
            # 2. 檢查超出台灣範圍的座標
            out_of_bounds = (
                (df['經度'] < 119.5) | (df['經度'] > 122.5) |
                (df['緯度'] < 21.5) | (df['緯度'] > 25.5)
            )
            coordinate_issues += out_of_bounds.sum()
            
            # 3. 檢查 is_indoor 推斷品質
            indoor_stats = df['in_door'].value_counts()
            indoor_coverage = (indoor_stats.sum() / len(df)) * 100
            
            # 4. 檢查區域座標合理性
            region_issues = 0
            county_bounds = {
                '新竹縣': {'lon': (120.8, 121.2), 'lat': (24.5, 24.9)},
                '高雄市': {'lon': (120.2, 120.6), 'lat': (22.4, 23.0)},
                '臺北市': {'lon': (121.4, 121.7), 'lat': (24.9, 25.2)},
            }
            
            for county, bounds in county_bounds.items():
                county_data = df[df['縣市及鄉鎮市區'].str.contains(county, na=False)]
                if not county_data.empty:
                    invalid_coords = (
                        (county_data['經度'] < bounds['lon'][0]) | 
                        (county_data['經度'] > bounds['lon'][1]) |
                        (county_data['緯度'] < bounds['lat'][0]) | 
                        (county_data['緯度'] > bounds['lat'][1])
                    )
                    region_issues += invalid_coords.sum()
            
            self.results['spatial_audit'] = {
                'total_shelters': len(df),
                'coordinate_issues': coordinate_issues,
                'region_issues': region_issues,
                'indoor_coverage': indoor_coverage,
                'indoor_true': indoor_stats.get(True, 0),
                'indoor_false': indoor_stats.get(False, 0),
                'quality_score': max(0, 100 - (coordinate_issues + region_issues) / len(df) * 100)
            }
            
            print(f"總避難所數量: {len(df)}")
            print(f"座標問題數量: {coordinate_issues}")
            print(f"區域問題數量: {region_issues}")
            print(f"室內外屬性覆蓋率: {indoor_coverage:.1f}%")
            print(f"品質評分: {self.results['spatial_audit']['quality_score']:.1f}/100")
            
        except Exception as e:
            print(f"Spatial Audit 檢查失敗: {e}")
            self.results['spatial_audit'] = {'quality_score': 0}
    
    def check_overlay_accuracy(self):
        """檢查 Overlay Accuracy (20%)"""
        print("\n=== Overlay Accuracy 檢查 ===")
        
        try:
            # 檢查是否有地圖檔案
            map_files = [f for f in os.listdir('outputs') if f.endswith('.html') and 'map' in f]
            
            # 檢查 CRS 轉換
            aqi_files = [f for f in os.listdir('outputs') if f.startswith('aqi_data_with_distance_')]
            
            # 檢查空間疊圖檔案
            overlay_files = [f for f in os.listdir('outputs') if 'spatial_overlay' in f]
            
            # 檢查驗證報告
            validation_files = [f for f in os.listdir('outputs') if 'spatial_validation' in f]
            
            # 載入 AQI 數據檢查座標格式
            if aqi_files:
                aqi_df = pd.read_csv(f'outputs/{aqi_files[0]}', encoding='utf-8-sig')
                crs_check = (
                    aqi_df['經度'].between(119, 123).all() and 
                    aqi_df['緯度'].between(21, 26).all()
                )
            else:
                crs_check = False
            
            self.results['overlay_accuracy'] = {
                'map_files': len(map_files),
                'aqi_files': len(aqi_files),
                'overlay_files': len(overlay_files),
                'validation_files': len(validation_files),
                'crs_check': crs_check,
                'quality_score': (
                    len(map_files) * 25 + 
                    len(overlay_files) * 25 + 
                    len(validation_files) * 25 + 
                    (100 if crs_check else 0) * 25
                )
            }
            
            print(f"地圖檔案數量: {len(map_files)}")
            print(f"空間疊圖檔案數量: {len(overlay_files)}")
            print(f"驗證報告數量: {len(validation_files)}")
            print(f"CRS 檢查: {'通過' if crs_check else '失敗'}")
            print(f"品質評分: {self.results['overlay_accuracy']['quality_score']:.1f}/100")
            
        except Exception as e:
            print(f"Overlay Accuracy 檢查失敗: {e}")
            self.results['overlay_accuracy'] = {'quality_score': 0}
    
    def check_analysis_logic(self):
        """檢查 Analysis Logic (25%)"""
        print("\n=== Analysis Logic 檢查 ===")
        
        try:
            # 載入風險分析結果
            df = pd.read_csv('outputs/shelter_aqi_analysis_manual_20260303_214934.csv', encoding='utf-8-sig')
            
            # 檢查 Haversine 實現
            # 驗證距離計算的合理性
            distance_stats = df['distance_to_station'].describe()
            reasonable_distances = (
                distance_stats['min'] >= 0 and 
                distance_stats['max'] <= 100  # 最大距離應該在合理範圍內
            )
            
            # 檢查風險標籤邏輯
            risk_labels = df['risk_level'].value_counts()
            expected_labels = ['High Risk', 'Medium Risk', 'Warning', 'Low Risk']
            label_coverage = all(label in risk_labels.index for label in expected_labels)
            
            # 檢查風險標籤一致性
            high_risk = df[df['risk_level'] == 'High Risk']
            logic_consistency = (high_risk['nearest_aqi'] > 100).all()
            
            # 檢查室內外邏輯
            warning_outdoor = df[df['risk_level'] == 'Warning']
            outdoor_logic = (warning_outdoor['is_indoor'] == False).all()
            
            # 檢查距離計算精度
            sample_distance = df.iloc[0]['distance_to_station']
            distance_precision = not pd.isna(sample_distance) and sample_distance > 0
            
            self.results['analysis_logic'] = {
                'total_analyzed': len(df),
                'reasonable_distances': reasonable_distances,
                'label_coverage': label_coverage,
                'logic_consistency': logic_consistency,
                'outdoor_logic': outdoor_logic,
                'distance_precision': distance_precision,
                'risk_distribution': risk_labels.to_dict(),
                'quality_score': (
                    (100 if reasonable_distances else 0) * 20 +
                    (100 if label_coverage else 0) * 20 +
                    (100 if logic_consistency else 0) * 20 +
                    (100 if outdoor_logic else 0) * 20 +
                    (100 if distance_precision else 0) * 20
                )
            }
            
            print(f"分析避難所數量: {len(df)}")
            print(f"距離計算合理性: {'通過' if reasonable_distances else '失敗'}")
            print(f"風險標籤覆蓋: {'通過' if label_coverage else '失敗'}")
            print(f"邏輯一致性: {'通過' if logic_consistency else '失敗'}")
            print(f"室外邏輯: {'通過' if outdoor_logic else '失敗'}")
            print(f"距離精度: {'通過' if distance_precision else '失敗'}")
            print(f"品質評分: {self.results['analysis_logic']['quality_score']:.1f}/100")
            
        except Exception as e:
            print(f"Analysis Logic 檢查失敗: {e}")
            self.results['analysis_logic'] = {'quality_score': 0}
    
    def check_reflection(self):
        """檢查 Reflection (20%)"""
        print("\n=== Reflection 檢查 ===")
        
        try:
            # 檢查反思文件是否存在
            reflection_file = 'outputs/reflection.md'
            reflection_exists = os.path.exists(reflection_file)
            
            if reflection_exists:
                with open(reflection_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查反思內容完整性
                sections = [
                    'Data Integrity',
                    'AI Collaboration', 
                    'Spatial Reasoning',
                    '技術架構反思'
                ]
                
                section_coverage = sum(1 for section in sections if section in content)
                content_depth = len(content)  # 內容深度以字數衡量
                
                # 檢查關鍵概念
                key_concepts = [
                    '座標系統問題',
                    '室內室外屬性',
                    'CRS幻覺',
                    '最近測站',
                    '風向',
                    '地形高程'
                ]
                
                concept_coverage = sum(1 for concept in key_concepts if concept in content)
                
                self.results['reflection'] = {
                    'file_exists': reflection_exists,
                    'section_coverage': section_coverage,
                    'content_depth': content_depth,
                    'concept_coverage': concept_coverage,
                    'quality_score': (
                        (100 if reflection_exists else 0) * 25 +
                        (section_coverage / len(sections)) * 100 * 25 +
                        min(content_depth / 5000, 1) * 100 * 25 +
                        (concept_coverage / len(key_concepts)) * 100 * 25
                    )
                }
                
                print(f"反思文件存在: {'是' if reflection_exists else '否'}")
                print(f"章節覆蓋: {section_coverage}/{len(sections)}")
                print(f"內容深度: {content_depth} 字元")
                print(f"概念覆蓋: {concept_coverage}/{len(key_concepts)}")
                print(f"品質評分: {self.results['reflection']['quality_score']:.1f}/100")
            else:
                self.results['reflection'] = {'quality_score': 0}
                print("反思文件不存在")
                
        except Exception as e:
            print(f"Reflection 檢查失敗: {e}")
            self.results['reflection'] = {'quality_score': 0}
    
    def check_git_workflow(self):
        """檢查 Git Workflow (10%)"""
        print("\n=== Git Workflow 檢查 ===")
        
        try:
            # 檢查是否為 Git 倉庫
            is_git_repo = os.path.exists('.git')
            
            # 檢查分支狀態
            current_branch = "main"  # 假設在 main 分支
            
            # 檢查檔案結構
            required_files = [
                'aqi-analysis/data/shelters_cleaned.csv',
                'aqi-analysis/outputs/audit_report.md',
                'aqi-analysis/outputs/shelter_aqi_analysis.csv',
                'aqi-analysis/outputs/reflection.md',
                'aqi-analysis/scripts/shelter_aqi_analysis.py',
                'aqi-analysis/README.md'
            ]
            
            files_exist = sum(1 for file in required_files if os.path.exists(file))
            file_structure_score = (files_exist / len(required_files)) * 100
            
            # 檢查文檔完整性
            doc_files = [
                'aqi-analysis/README.md',
                'aqi-analysis/outputs/reflection.md'
            ]
            
            docs_exist = sum(1 for file in doc_files if os.path.exists(file))
            doc_score = (docs_exist / len(doc_files)) * 100
            
            self.results['git_workflow'] = {
                'is_git_repo': is_git_repo,
                'current_branch': current_branch,
                'files_exist': files_exist,
                'total_files': len(required_files),
                'file_structure_score': file_structure_score,
                'doc_score': doc_score,
                'quality_score': (
                    (100 if is_git_repo else 0) * 30 +
                    file_structure_score * 40 +
                    doc_score * 30
                )
            }
            
            print(f"Git 倉庫: {'是' if is_git_repo else '否'}")
            print(f"檔案結構: {files_exist}/{len(required_files)} ({file_structure_score:.1f}%)")
            print(f"文檔完整性: {docs_exist}/{len(doc_files)} ({doc_score:.1f}%)")
            print(f"品質評分: {self.results['git_workflow']['quality_score']:.1f}/100")
            
        except Exception as e:
            print(f"Git Workflow 檢查失敗: {e}")
            self.results['git_workflow'] = {'quality_score': 0}
    
    def generate_quality_report(self):
        """生成品質報告"""
        print("\n" + "="*60)
        print("品質檢查報告")
        print("="*60)
        
        # 計算加權總分
        weights = {
            'spatial_audit': 0.25,
            'overlay_accuracy': 0.20,
            'analysis_logic': 0.25,
            'reflection': 0.20,
            'git_workflow': 0.10
        }
        
        total_score = 0
        for category, weight in weights.items():
            if category in self.results:
                score = self.results[category]['quality_score']
                weighted_score = score * weight
                total_score += weighted_score
                
                print(f"{category.upper()}: {score:.1f}/100 (權重: {weight*100:.0f}%) = {weighted_score:.1f}")
        
        print(f"\n總分: {total_score:.1f}/100")
        
        # 優化建議
        print("\n優化建議:")
        if self.results.get('spatial_audit', {}).get('quality_score', 0) < 90:
            print("- Spatial Audit: 進一步檢查座標異常和區域合理性")
        
        if self.results.get('overlay_accuracy', {}).get('quality_score', 0) < 90:
            print("- Overlay Accuracy: 確保 CRS 轉換和地圖可視化品質")
        
        if self.results.get('analysis_logic', {}).get('quality_score', 0) < 90:
            print("- Analysis Logic: 驗證 Haversine 實現和風險標籤邏輯")
        
        if self.results.get('reflection', {}).get('quality_score', 0) < 90:
            print("- Reflection: 深化批判性思考和 AI 互動反思")
        
        if self.results.get('git_workflow', {}).get('quality_score', 0) < 90:
            print("- Git Workflow: 完善分支管理和提交歷史")
        
        return total_score

def main():
    """主程式"""
    checker = QualityChecker()
    
    # 執行所有檢查
    checker.check_spatial_audit()
    checker.check_overlay_accuracy()
    checker.check_analysis_logic()
    checker.check_reflection()
    checker.check_git_workflow()
    
    # 生成品質報告
    total_score = checker.generate_quality_report()
    
    # 決定是否需要優化
    if total_score >= 90:
        print(f"\n🎉 品質評分優秀 ({total_score:.1f}/100)，可以推送到 GitHub！")
        return True
    else:
        print(f"\n⚠️  品質評分需要改進 ({total_score:.1f}/100)")
        return False

if __name__ == "__main__":
    main()
