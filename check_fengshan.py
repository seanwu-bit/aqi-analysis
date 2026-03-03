import pandas as pd

df = pd.read_csv('outputs/shelter_aqi_analysis_20260303_214009.csv', encoding='utf-8-sig')
print('風險分布統計:')
risk_counts = df['risk_level'].value_counts()
for risk_level, count in risk_counts.items():
    percentage = (count / len(df)) * 100
    print(f'{risk_level}: {count} 筆 ({percentage:.1f}%)')

print('\n檢查鳳山測站影響的避難所:')
fengshan_stations = df[df['nearest_station'].str.contains('鳳山', na=False)]
print(f'鳳山測站影響的避難所數量: {len(fengshan_stations)}')
print('鳳山測站 AQI 值:')
print(fengshan_stations['nearest_aqi'].unique())

print('\n檢查是否有 AQI=150 的記錄:')
aqi_150 = df[df['nearest_aqi'] == 150]
print(f'AQI=150 的避難所數量: {len(aqi_150)}')
if len(aqi_150) > 0:
    print('前5筆 AQI=150 的避難所:')
    for idx, row in aqi_150.head(5).iterrows():
        print(f'{row["shelter_name"]} - {row["nearest_station"]} (AQI: {row["nearest_aqi"]}) - {row["risk_level"]}')

print('\n高風險避難所中最近測站統計:')
high_risk = df[df['risk_level'] == 'High Risk']
station_counts = high_risk['nearest_station'].value_counts()
print(station_counts.head(10))
