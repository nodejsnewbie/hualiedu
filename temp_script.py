import pandas as pd
from pathlib import Path

# 读取 Excel 文件
excel_path = Path("/Users/linyuan/jobs/22g-class-java-homework/平时成绩登记表-22计算机G1班.xlsx")
df = pd.read_excel(excel_path, header=None)

print("First few rows:")
print(df.head())

print("\nLooking for 朱俏任:")
for idx, row in df.iterrows():
    print(f"Row {idx}: '{str(row[0]).strip()}'") 