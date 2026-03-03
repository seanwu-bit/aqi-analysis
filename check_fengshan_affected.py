import pandas as pd

df = pd.read_csv('outputs/shelter_aqi_analysis_manual_20260303_214934.csv', encoding='utf-8-sig')
fengshan_affected = df[df['nearest_station'] == '鳳山']

print(f'鳳山測站影響的避難所數量: {len(fengshan_affected)}')
print('前10筆鳳山測站影響的避難所:')
for idx, row in fengshan_affected.head(10).iterrows():
    facility_type = "室內" if row['is_indoor'] else "室外"
    print(f'{row["shelter_name"]} - {row["county"]} - {facility_type} - AQI: {row["nearest_aqi"]} - {row["risk_level"]}')

print('\n風險等級統計:')
risk_counts = fengshan_affected['risk_level'].value_counts()
for risk_level, count in risk_counts.items():
    percentage = (count / len(fengshan_affected)) * 100
    print(f'{risk_level}: {count} 筆 ({percentage:.1f}%)')
