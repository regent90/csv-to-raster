import pandas as pd
import numpy as np
import os
import glob
import re

# 設定輸入資料夾路徑
input_folder = '../ClimateData/'
output_folder = '.'  # 輸出資料夾路徑

# 取得所有符合格式的檔案
file_pattern = os.path.join(input_folder, '觀測_日資料_宜蘭縣_降雨量_*.csv')
input_files = glob.glob(file_pattern)

# 如果沒有找到檔案，直接處理指定的檔案
if len(input_files) == 0:
    input_files = ['觀測_日資料_宜蘭縣_降雨量_2020.csv']

print(f"找到 {len(input_files)} 個檔案需要處理")

# 用於儲存所有年份的月資料
all_monthly_data = []

# 用於儲存測站的經緯度資訊
station_coordinates = {}

for in_file in input_files:
    try:
        # 從檔名取得年份
        year_match = re.search(r'(\d{4})\.csv$', in_file)
        if year_match:
            year = year_match.group(1)
        else:
            # 嘗試從檔名中提取年份
            year_match = re.search(r'_(\d{4})', in_file)
            if year_match:
                year = year_match.group(1)
            else:
                year = "unknown"
        
        print(f"正在處理檔案: {os.path.basename(in_file)}")
        
        # 讀取 CSV 資料，轉換為 dataframe
        df = pd.read_csv(in_file, index_col=False)
        
        # 有些欄位名稱有空白符號，為使其一致，需修改欄位名稱
        df.columns = [s.strip() for s in df.columns]
        
        # 檢查 dataframe 的大小
        rows, cols = df.shape
        print(f'df.shape: ({rows},{cols})')
        
        # 增加 ID 欄位，紀錄點的編號
        df['ID'] = np.arange(rows)
        
        # 儲存測站的經緯度資訊
        # 先確認欄位名稱
        lon_col = 'LON' if 'LON' in df.columns else ' LON' if ' LON' in df.columns else None
        lat_col = 'LAT' if 'LAT' in df.columns else ' LAT' if ' LAT' in df.columns else None
        
        if lon_col and lat_col:
            for i, row in df.iterrows():
                station_name = row['站名'] if '站名' in df.columns else row[' 站名'] if ' 站名' in df.columns else f"Station_{i}"
                station_coordinates[station_name] = {
                    'LON': row[lon_col],
                    'LAT': row[lat_col]
                }
        
        # 轉置矩陣
        df2 = df.T
        
        # 將 -99.9 改為 numpy.NaN
        df2 = df2.replace(-99.9, np.nan)
        
        # 刪除不需要的欄位
        try:
            df2 = df2.drop(index=['LON', 'LAT', 'ID'])
        except KeyError:
            try:
                # 嘗試使用可能有空格的欄位名稱
                df2 = df2.drop(index=[' LON', ' LAT', 'ID'])
            except KeyError:
                print("警告: 無法找到 LON、LAT 或 ID 欄位，請檢查資料格式")
        
        # 檢查 dataframe 的大小
        print(f'df2.shape: {df2.shape}')
        
        # 檢查 dataframe 的 index
        print(f'df2.index 前5項: {list(df2.index)[:5]}')
        
        # 過濾掉不是日期格式的索引
        date_pattern = re.compile(r'^\d{8}$')
        valid_indices = [idx for idx in df2.index if date_pattern.match(str(idx))]
        df2 = df2.loc[valid_indices]
        
        # 將 yymmdd 格式的日期轉會成為 datetime object
        t = [f'{s[:4]}-{s[4:6]}-{s[6:]}' for s in df2.index]
        df2.index = pd.to_datetime(t)
        
        # 檢查 dataframe 的 index
        print(f'日期範圍: {df2.index.min()} 到 {df2.index.max()}')
        print(f'資料期間: {df2.index.max() - df2.index.min()}')
        
        # 由 datetime 的 index 計算欄位值的每月合計
        df3 = df2.resample('ME').sum()
        
        # 將 0 改為 -99.9
        df3 = df3.replace(0, -99.9)
        
        # 儲存此年份的月資料，用於後續合併
        all_monthly_data.append(df3)
        
        print('-' * 50)
        
    except Exception as e:
        print(f"處理檔案 {in_file} 時發生錯誤: {str(e)}")

# 合併所有年份的月資料
if all_monthly_data:
    try:
        # 合併所有年份的資料
        combined_data = pd.concat(all_monthly_data, axis=0)
        
        # 將測站經緯度資訊輸出為暫存資料
        station_coords_df = pd.DataFrame.from_dict(station_coordinates, orient='index')
        station_coords_df.reset_index(inplace=True)
        station_coords_df.rename(columns={'index': 'Station', 'LON': 'LON', 'LAT': 'LAT'}, inplace=True)
        
        # 轉置合併後的資料
        df_transposed = combined_data.T
        
        # 添加測站名稱作為欄位
        df_transposed['Station'] = df_transposed.index
        
        # 移除 "Station_" 前綴
        station_coords_df['Station'] = station_coords_df['Station'].str.replace('Station_', '', regex=True)
        
        # 將兩個資料集的 Station 欄位都轉換為字串類型
        df_transposed['Station'] = df_transposed['Station'].astype(str)
        station_coords_df['Station'] = station_coords_df['Station'].astype(str)
        
        # 合併資料
        merged_data = pd.merge(
            station_coords_df,
            df_transposed,
            on='Station',
            how='inner'  # 僅保留兩者都有的測站
        )
        
        # 從合併後的資料中刪除 Station 欄位
        merged_data = merged_data.drop(columns=['Station'])
        
        # 輸出最終合併後的資料，直接命名為 result.csv
        final_output_file = os.path.join(output_folder, 'result.csv')
        merged_data.to_csv(final_output_file, index=False)
        print(f"已將最終合併後的資料保存到 {final_output_file}")
        print(f"合併後資料形狀: {merged_data.shape}")
        
    except Exception as e:
        print(f"合併或轉置資料時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()  # 印出詳細的錯誤訊息

print("所有檔案處理完成！最終結果已保存為 result.csv")
