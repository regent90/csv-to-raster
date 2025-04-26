import arcpy
import numpy
import pandas as pd
import os
import glob
from arcpy.sa import *

# 檢查 Spatial Analyst 授權
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
    print("已啟用 Spatial Analyst 擴充模組")
else:
    print("警告: Spatial Analyst 擴充模組不可用，無法進行柵格插值")
    exit(1)

# 獲取當前工作目錄的絕對路徑
current_dir = os.getcwd()
print(f"當前工作目錄: {current_dir}")

# 設定環境
arcpy.env.workspace = "in_memory"  # 使用記憶體工作空間
arcpy.env.overwriteOutput = True

# 定義輸入資料夾路徑 (使用絕對路徑)
input_folder = os.path.join(current_dir, "month")
if not os.path.exists(input_folder):
    print(f"錯誤: 輸入資料夾 '{input_folder}' 不存在!")
    # 嘗試列出當前目錄下的所有資料夾
    print("當前目錄下的資料夾和檔案:")
    for item in os.listdir(current_dir):
        print(f"  - {item}")
    exit(1)

# 建立輸出柵格資料夾
raster_folder = os.path.join(current_dir, "raster_IDW")
if not os.path.exists(raster_folder):
    os.makedirs(raster_folder)
    print(f"已建立柵格輸出資料夾: {raster_folder}")

# 取得所有符合格式的 CSV 檔案
csv_files = glob.glob(os.path.join(input_folder, 'rain_*.csv'))
print(f"找到 {len(csv_files)} 個 CSV 檔案需要處理")
if len(csv_files) == 0:
    print(f"警告: 在 '{input_folder}' 中找不到任何 'rain_*.csv' 檔案")
    # 列出資料夾中的所有檔案
    if os.path.exists(input_folder):
        print(f"資料夾 '{input_folder}' 中的檔案:")
        for item in os.listdir(input_folder):
            print(f"  - {item}")
    exit(1)

# 使用 WGS 1984 空間參考
spatial_ref = arcpy.SpatialReference(4326)  # WGS 1984

# 處理每個 CSV 檔案
for csv_file in csv_files:
    try:
        # 顯示完整檔案路徑
        print(f"\n處理檔案: {csv_file}")
        
        # 從檔名取得年月資訊
        file_name = os.path.basename(csv_file)
        year_month = file_name.replace("rain_", "").replace(".csv", "")
        
        # 定義輸出名稱
        point_fc = f"in_memory/rain_{year_month}_pt"
        raster_output = os.path.join(raster_folder, f"rain_{year_month}.tif")
        
        print(f"輸出點特徵類別: {point_fc}")
        print(f"輸出柵格檔案: {raster_output}")
        
        # 檢查 CSV 檔案是否存在
        if not os.path.exists(csv_file):
            print(f"錯誤: CSV 檔案 '{csv_file}' 不存在!")
            continue
        
        # 讀取 CSV 檔案
        print(f"讀取 CSV 檔案: {csv_file}")
        df = pd.read_csv(csv_file)
        print(f"資料形狀: {df.shape}")
        print("資料前 5 筆:")
        print(df.head())
        
        # 確認資料欄位
        if 'LON' not in df.columns or 'LAT' not in df.columns:
            print(f"錯誤: {file_name} 缺少 LON 或 LAT 欄位，跳過此檔案")
            continue
            
        # 確認降雨量欄位
        rainfall_field = None
        if 'RAINFALL' in df.columns:
            rainfall_field = 'RAINFALL'
        elif 'Value' in df.columns:
            rainfall_field = 'Value'
        else:
            print(f"錯誤: {file_name} 缺少降雨量欄位，跳過此檔案")
            continue
        
        print(f"使用降雨量欄位: {rainfall_field}")
        
        # 取得 LON 和 LAT 欄位的資料
        lon_values = df['LON'].tolist()
        lat_values = df['LAT'].tolist()
        rainfall_values = df[rainfall_field].tolist()
        
        # 刪除已存在的特徵類別 (如果存在)
        if arcpy.Exists(point_fc):
            print(f'刪除已存在的特徵類別: {point_fc}')
            arcpy.Delete_management(point_fc)
        
        # 創建空的點特徵類別
        print("創建點特徵類別...")
        arcpy.CreateFeatureclass_management(
            out_path="in_memory",
            out_name=f"rain_{year_month}_pt",
            geometry_type="POINT",
            spatial_reference=spatial_ref
        )
        
        # 添加降雨量欄位
        arcpy.AddField_management(point_fc, "RAINFALL", "DOUBLE")
        
        # 使用游標添加點
        print("添加點資料...")
        with arcpy.da.InsertCursor(point_fc, ["SHAPE@XY", "RAINFALL"]) as cursor:
            for i in range(len(lon_values)):
                cursor.insertRow([(lon_values[i], lat_values[i]), rainfall_values[i]])
        
        print(f'已成功建立特徵類別: {point_fc}')
        
        # 步驟 2: 將點資料插值為柵格
        print(f'開始將點資料插值為柵格...')
        
        # 定義插值參數
        z_field = "RAINFALL"  # 要插值的欄位
        cell_size = 0.0083  # 柵格大小
        
        try:
            # 使用 IDW 插值法
            idw_output = Idw(point_fc, z_field, cell_size)
            
            # 檢查輸出柵格檔案是否已存在
            if os.path.exists(raster_output):
                print(f"刪除已存在的柵格檔案: {raster_output}")
                os.remove(raster_output)
            
            # 儲存柵格結果
            idw_output.save(raster_output)
            
            print(f'已成功建立柵格資料: {raster_output}')
        except Exception as e:
            print(f"插值過程發生錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"處理檔案 {csv_file} 時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

print('\n*** 所有檔案處理完成 ***')

# 釋放 Spatial Analyst 授權
arcpy.CheckInExtension("Spatial")
print("已釋放 Spatial Analyst 擴充模組授權")
