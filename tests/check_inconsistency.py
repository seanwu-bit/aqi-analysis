import pandas as pd

df = pd.read_csv('outputs/shelter_data_cleaned_20260303_210104.csv', encoding='utf-8-sig')
print('檢查室內欄位與in_door的一致性:')
inconsistent = df[(df['室內'] == '是') & (df['in_door'] == False)]
print(f'不一致的記錄數量: {len(inconsistent)}')
if len(inconsistent) > 0:
    print('前5筆不一致的記錄:')
    for idx, row in inconsistent.head(5).iterrows():
        print(f'  {row["避難收容處所名稱"]} - 室內: {row["室內"]} - in_door: {row["in_door"]}')

print('\n檢查整體統計:')
print(f'室內為"是"的總數: {len(df[df["室內"] == "是"])}')
print(f'in_door為True的總數: {len(df[df["in_door"] == True])}')
print(f'室內為"否"的總數: {len(df[df["室內"] == "否"])}')
print(f'in_door為False的總數: {len(df[df["in_door"] == False])}')
