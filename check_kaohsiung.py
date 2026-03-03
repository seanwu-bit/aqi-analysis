import pandas as pd

df = pd.read_csv('outputs/shelter_aqi_analysis_20260303_212407.csv', encoding='utf-8-sig')
high_risk_kaohsiung = df[(df['risk_level'] == 'High Risk') & (df['county'].str.contains('高雄', na=False))]
print(f'高雄地區高風險避難所數量: {len(high_risk_kaohsiung)}')
print('前10筆:')
for idx, row in high_risk_kaohsiung.head(10).iterrows():
    print(f'{row["shelter_name"]} - {row["nearest_station"]} (AQI: {row["nearest_aqi"]})')
