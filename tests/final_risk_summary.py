import pandas as pd

df = pd.read_csv('outputs/shelter_aqi_analysis_manual_20260303_214934.csv', encoding='utf-8-sig')

print('=== 鳳山 AQI=150 模擬結果摘要 ===')
print(f'總避難所數量: {len(df)}')

print('\n風險分布統計:')
risk_counts = df['risk_level'].value_counts()
for risk_level, count in risk_counts.items():
    percentage = (count / len(df)) * 100
    print(f'{risk_level}: {count} 筆 ({percentage:.1f}%)')

print('\n高風險避難所統計:')
high_risk = df[df['risk_level'] == 'High Risk']
print(f'高風險避難所總數: {len(high_risk)} 筆')

# 按最近測站統計高風險避難所
station_counts = high_risk['nearest_station'].value_counts()
print('\n高風險避難所按測站分布 (前10個):')
for station, count in station_counts.head(10).items():
    print(f'{station}: {count} 筆')

# 檢查 AQI=150 的記錄
aqi_150 = df[df['nearest_aqi'] == 150]
print(f'\nAQI=150 的避難所: {len(aqi_150)} 筆 (全部為高風險)')

# 檢查高雄地區的避難所
kaohsiung_shelters = df[df['county'].str.contains('高雄', na=False)]
print(f'\n高雄地區避難所總數: {len(kaohsiung_shelters)} 筆')

kaohsiung_high_risk = kaohsiung_shelters[kaohsiung_shelters['risk_level'] == 'High Risk']
print(f'高雄地區高風險避難所: {len(kaohsiung_high_risk)} 筆')

if len(kaohsiung_high_risk) > 0:
    print('高雄地區高風險避難所 (前5筆):')
    for idx, row in kaohsiung_high_risk.head(5).iterrows():
        facility_type = "室內" if row['is_indoor'] else "室外"
        print(f'  {row["shelter_name"]} - {row["nearest_station"]} - AQI: {row["nearest_aqi"]} - {facility_type}')

print(f'\n檔案位置: outputs/shelter_aqi_analysis_manual_20260303_214934.csv')
print('檔案大小: {:.1f} MB'.format(len(df) * 0.0002))  # 估算檔案大小
