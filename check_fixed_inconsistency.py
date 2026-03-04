import pandas as pd
import os

# 找到最新的清理檔案
output_files = [f for f in os.listdir('outputs') if f.startswith('shelter_data_cleaned_') and f.endswith('.csv')]
if output_files:
    latest_file = sorted(output_files)[-1]
    df = pd.read_csv(f'outputs/{latest_file}', encoding='utf-8-sig')
    print(f'檢查檔案: {latest_file}')
    
    print('檢查室內欄位與in_door的一致性:')
    inconsistent = df[(df['室內'] == '是') & (df['in_door'] == False)]
    print(f'不一致的記錄數量: {len(inconsistent)}')
    if len(inconsistent) > 0:
        print('前5筆不一致的記錄:')
        for idx, row in inconsistent.head(5).iterrows():
            print(f'  {row["避難收容處所名稱"]} - 室內: {row["室內"]} - in_door: {row["in_door"]}')
    else:
        print('✅ 無不一致記錄！')
    
    print('\n檢查整體統計:')
    print(f'室內為"是"的總數: {len(df[df["室內"] == "是"])}')
    print(f'in_door為True的總數: {len(df[df["in_door"] == True])}')
    print(f'室內為"否"的總數: {len(df[df["室內"] == "否"])}')
    print(f'in_door為False的總數: {len(df[df["in_door"] == False])}')
    
    print('\n驗證修正效果:')
    consistent_indoor = df[(df['室內'] == '是') & (df['in_door'] == True)]
    consistent_outdoor = df[(df['室內'] == '否') & (df['in_door'] == False)]
    print(f'一致的室內記錄: {len(consistent_indoor)}')
    print(f'一致的室外記錄: {len(consistent_outdoor)}')
    print(f'總一致性: {(len(consistent_indoor) + len(consistent_outdoor)) / len(df) * 100:.1f}%')
else:
    print('未找到清理後的檔案')
