import pandas as pd

# 載入原始 AQI 數據
df = pd.read_csv('outputs/aqi_data_with_distance_20260224_164419.csv', encoding='utf-8-sig')
print('原始鳳山測站:')
fengshan = df[df['測站名稱'] == '鳳山']
if not fengshan.empty:
    print(f'鳳山測站 AQI: {fengshan["AQI"].iloc[0]}')
else:
    print('未找到鳳山測站')

# 模擬
print('\n進行模擬...')
target_station = '鳳山'
station_data = df[df['測站名稱'] == target_station]
if not station_data.empty:
    original_aqi = station_data['AQI'].iloc[0]
    new_aqi = 150
    df.loc[df['測站名稱'] == target_station, 'AQI'] = new_aqi
    print(f'模擬: {target_station} AQI {original_aqi} -> {new_aqi}')
    
    # 驗證模擬結果
    updated_fengshan = df[df['測站名稱'] == target_station]
    print(f'模擬後鳳山測站 AQI: {updated_fengshan["AQI"].iloc[0]}')
else:
    print(f'未找到測站: {target_station}')

print(f'模擬後平均 AQI: {df["AQI"].mean():.1f}')
