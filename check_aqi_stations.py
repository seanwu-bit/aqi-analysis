import pandas as pd

# 檢查原始 AQI 數據
df = pd.read_csv('outputs/aqi_data_with_distance_20260224_164419.csv', encoding='utf-8-sig')
print('原始 AQI 測站:')
for idx, row in df.iterrows():
    print(f'{row["測站名稱"]}: {row["AQI"]}')

print('\n檢查是否有高雄測站:')
kaohsiung = df[df['測站名稱'].str.contains('高雄', na=False)]
print(f'高雄測站數量: {len(kaohsiung)}')
if len(kaohsiung) > 0:
    for idx, row in kaohsiung.iterrows():
        print(f'{row["測站名稱"]}: {row["AQI"]}')
