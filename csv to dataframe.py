import arcpy
import numpy
import pandas as pd
import os
import glob

# 設定環境
arcpy.env.workspace = "./grid/grid.gdb"
arcpy.env.overwriteOutput = True

# 定義輸入資料夾路徑
input_folder = './month'

# 取得所有符合格式的 CSV 檔案
csv_files = glob.glob(os.path.join(input_folder, 'rain_*.csv'))
print(f"找到 {len(csv_files)} 個 CSV 檔案需要處理")

# 定義空間參考（假設所有檔案使用相同的空間參考）
spatial_ref = arcpy.Describe("rain_1960_01").spatialReference

# 處理每個 CSV 檔案
for csv_file in csv_files:
    try:
        # 從檔名取得年月資訊
        file_name = os.path.basename(csv_file)
        base_name = os.path.splitext(file_name)[0]  # 移除副檔名
        
        print(f"\n正在處理: {file_name}")
        
        # 簡化特徵類別名稱
        year_month = file_name.replace("rain_", "").replace(".csv", "")
        feature_name = f"rain_{year_month}_pt"
        
        # 確保使用完整路徑
        gdb_path = arcpy.env.workspace
        outFC = os.path.join(gdb_path, feature_name)
        
        print(f"輸出特徵類別路徑: {outFC}")
        
        # 讀取 CSV 檔案
        df = pd.read_csv(csv_file)
        print(f"資料形狀: {df.shape}")
        
        # 確認資料欄位
        required_fields = ['LON', 'LAT', 'Value']
        missing_fields = [field for field in required_fields if field not in df.columns]
        
        if missing_fields:
            print(f"錯誤: {file_name} 缺少以下欄位: {missing_fields}")
            # 檢查是否有替代欄位
            if 'RAINFALL' in df.columns and 'Value' in missing_fields:
                print("找到替代欄位 'RAINFALL'，將使用此欄位")
                df['Value'] = df['RAINFALL']
            else:
                print("跳過此檔案")
                continue
        
        # 取得 LON 和 LAT 欄位的資料，轉換成 list of tuples
        xy = list(df[['LON', 'LAT']].itertuples(index=False, name=None))
        
        # 取得 Value 欄位的資料，轉換成 list
        v = list(df['Value'])
        
        # 組合座標和降雨量資料
        data_list = list(zip(xy, v))
        
        # 建立 numpy 陣列
        array = numpy.array(
            data_list,
            numpy.dtype([("XY", "<f8", 2), ("Value", "<f8")]),
        )
        
        # 檢查輸出特徵類別是否存在，如果存在則刪除
        if arcpy.Exists(outFC):
            print(f'刪除已存在的特徵類別: {outFC}')
            arcpy.Delete_management(outFC)
        
        # 將 numpy 陣列轉換為特徵類別
        arcpy.da.NumPyArrayToFeatureClass(array, outFC, ["XY"], spatial_ref)
        
        print(f'已成功建立特徵類別: {outFC}')
        
    except Exception as e:
        print(f"處理檔案 {csv_file} 時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

print('\n*** 所有檔案處理完成 ***')