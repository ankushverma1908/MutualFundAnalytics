import pandas as pd

files = [
    'data/raw/nav_125497_hdfc_top_100_direct.csv',
    'data/raw/nav_119551_sbi_bluechip.csv',
    'data/raw/nav_120503_icici_bluechip.csv',
    'data/raw/nav_118632_nippon_large_cap.csv',
    'data/raw/nav_119092_axis_bluechip.csv',
    'data/raw/nav_120841_kotak_bluechip.csv',
]

dfs = []
for f in files:
    df = pd.read_csv(f)
    dfs.append(df)

master = pd.concat(dfs, ignore_index=True)
master.to_csv('data/raw/fund_master.csv', index=False)
print(f'fund_master.csv created with {len(master)} rows!')
print(master.head())