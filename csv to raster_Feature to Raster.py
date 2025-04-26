import arcpy
import numpy
import pandas as pd
import os
import glob
import time  # 引入時間模組用於生成唯一的臨時檔案名稱
from arcpy.sa import *

# 檢查 Spatial Analyst 授權
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
    print("已啟用 Spatial Analyst 擴充模組")
else:
    print("警告: Spatial Analyst 擴充模組不可用，無法進行柵格處理")
    exit(1)

# 獲取當前工作目錄的絕對路徑
current_dir = os.getcwd()
print(f"當前工作目錄: {current_dir}")

# 設定環境
arcpy.env.workspace = current_dir  # 使用實際目錄而非記憶體工作空間
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
raster_folder = os.path.join(current_dir, "raster_Feature_to_Raster")
if not os.path.exists(raster_folder):
    os.makedirs(raster_folder)
    print(f"已建立柵格輸出資料夾: {raster_folder}")

# 建立臨時檔案資料夾
temp_folder = os.path.join(current_dir, "temp")
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)
    print(f"已建立臨時檔案資料夾: {temp_folder}")

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
        
        # 定義輸出名稱 (使用實際檔案路徑而非記憶體)
        point_fc = os.path.join(temp_folder, f"rain_{year_month}_pt.shp")
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
            out_path=temp_folder,
            out_name=f"rain_{year_month}_pt.shp",
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
        
        # 步驟 2: 直接將點資料轉換為柵格 (使用 Feature To Raster)
        print(f'開始將點資料直接轉換為柵格...')
        
        try:
            # 定義柵格大小
            cell_size = 0.0083  # 約 1 公里
            
            # 計算研究區域範圍 (從點資料中獲取)
            extent = arcpy.Describe(point_fc).extent
            
            # 設定輸出範圍
            arcpy.env.extent = extent
            
            # 使用 Feature To Raster 工具直接將點轉換為柵格
            print("使用 Feature To Raster 工具將點資料轉換為柵格...")
            
            # 使用時間戳記建立唯一的臨時檔案名稱
            timestamp = int(time.time())
            temp_raster = os.path.join(temp_folder, f"temp_raster_{year_month}_{timestamp}.tif")
            
            # 確保臨時檔案不存在
            if arcpy.Exists(temp_raster):
                arcpy.Delete_management(temp_raster)
            
            # Feature To Raster 工具
            arcpy.conversion.FeatureToRaster(
                in_features=point_fc,
                field="RAINFALL",
                out_raster=temp_raster,
                cell_size=cell_size
            )
            
            # 檢查輸出柵格檔案是否已存在
            if os.path.exists(raster_output):
                print(f"刪除已存在的柵格檔案: {raster_output}")
                os.remove(raster_output)
            
            # 儲存柵格結果
            arcpy.management.CopyRaster(temp_raster, raster_output)
            
            # 清理臨時資料
            if arcpy.Exists(temp_raster):
                arcpy.Delete_management(temp_raster)
            
            print(f'已成功建立柵格資料: {raster_output}')
            
            # 顯示柵格資訊
            raster_desc = arcpy.Describe(raster_output)
            print(f"柵格資訊:")
            print(f"  - 寬度: {raster_desc.width} 像素")
            print(f"  - 高度: {raster_desc.height} 像素")
            print(f"  - 像素大小: {arcpy.Raster(raster_output).meanCellWidth} x {arcpy.Raster(raster_output).meanCellHeight}")
            
        except Exception as e:
            print(f"柵格轉換過程發生錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"處理檔案 {csv_file} 時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

print('\n*** 所有檔案處理完成 ***')

# 清理臨時資料夾 (可選)
# import shutil
# if os.path.exists(temp_folder):
#     shutil.rmtree(temp_folder)
#     print(f"已刪除臨時檔案資料夾: {temp_folder}")

# 釋放 Spatial Analyst 授權
arcpy.CheckInExtension("Spatial")
print("已釋放 Spatial Analyst 擴充模組授權")
