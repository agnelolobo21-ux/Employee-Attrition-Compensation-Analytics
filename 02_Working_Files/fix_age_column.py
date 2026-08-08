import pandas as pd

df = pd.read_csv(r"C:\Users\ACER\OneDrive\Desktop\Data Analytics Projects\Claude Employee Attrition  and Compensation Analytics\01_Raw_Data\attrition_events_raw.csv")

print("Total rows in attrition_events_raw.csv:", len(df))
print("\nColumn info:")
print(df.info())
print("\nAny missing values per column:")
print(df.isna().sum())