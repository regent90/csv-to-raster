import pandas as pd
import os
import re
from datetime import datetime

# 設定輸入檔案和輸出資料夾
input_file = 'result.csv'
output_folder = 'month'

# 確保輸出資料夾存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"已建立資料夾: {output_folder}")

# 讀取 result.csv 檔案
try:
    print(f"正在讀取檔案: {input_file}")
    df = pd.read_csv(input_file)
    
    # 顯示資料基本資訊
    print(f"資料形狀: {df.shape}")
    print(f"資料欄位: {df.columns.tolist()}")
    
    # 確認資料中有 LON 和 LAT 欄位
    if 'LON' not in df.columns or 'LAT' not in df.columns:
        print("錯誤: 資料中缺少 LON 或 LAT 欄位")
        exit(1)
    
    # 篩選出日期欄位 (假設日期欄位的格式為 YYYY-MM-DD)
    date_columns = []
    for col in df.columns:
        if col not in ['LON', 'LAT']:  # 排除經緯度欄位
            date_columns.append(col)
    
    print(f"找到 {len(date_columns)} 個日期欄位")
    
    # 處理每個日期欄位
    for date_col in date_columns:
        try:
            # 嘗試解析日期格式
            date_obj = datetime.strptime(date_col, '%Y-%m-%d')
            year = date_obj.year
            month = date_obj.month
            
            # 建立新的 DataFrame，只包含經緯度和當前日期的降雨量
            month_df = df[['LON', 'LAT', date_col]].copy()
            
            # 重新命名欄位，將日期欄位改名為 "RAINFALL"
            month_df.rename(columns={date_col: 'RAINFALL'}, inplace=True)
            
            # 輸出檔案名稱格式: rain_YYYY_MM.csv
            output_file = os.path.join(output_folder, f'rain_{year}_{month:02d}.csv')
            
            # 將資料寫入 CSV 檔案
            month_df.to_csv(output_file, index=False)
            print(f"已輸出檔案: {output_file}")
            
        except ValueError as e:
            # 如果無法解析日期格式，嘗試其他可能的格式
            try:
                # 嘗試從欄位名稱中提取年月
                match = re.search(r'(\d{4})-(\d{2})', date_col)
                if match:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    
                    # 建立新的 DataFrame，只包含經緯度和當前日期的降雨量
                    month_df = df[['LON', 'LAT', date_col]].copy()
                    
                    # 重新命名欄位，將日期欄位改名為 "RAINFALL"
                    month_df.rename(columns={date_col: 'RAINFALL'}, inplace=True)
                    
                    # 輸出檔案名稱格式: rain_YYYY_MM.csv
                    output_file = os.path.join(output_folder, f'rain_{year}_{month:02d}.csv')
                    
                    # 將資料寫入 CSV 檔案
                    month_df.to_csv(output_file, index=False)
                    print(f"已輸出檔案: {output_file}")
                else:
                    print(f"無法從欄位名稱 '{date_col}' 中提取年月資訊，跳過此欄位")
            except Exception as inner_e:
                print(f"處理欄位 '{date_col}' 時發生錯誤: {str(inner_e)}")
    
    print("所有月份資料拆分完成！")
    
except Exception as e:
    print(f"讀取或處理檔案時發生錯誤: {str(e)}")
    import traceback
    traceback.print_exc()
