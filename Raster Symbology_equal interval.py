import arcpy
import os
import glob
from arcpy.sa import *  # 引入 Spatial Analyst 模組

def apply_rainfall_symbology_batch(raster_folder):
    """批次對資料夾中的所有 TIF 檔案套用降雨量符號設定"""
    
    print(f"正在處理資料夾: {raster_folder}")
    
    # 檢查 Spatial Analyst 授權
    arcpy.CheckOutExtension("Spatial")
    
    # 創建輸出資料夾
    output_folder = os.path.join(raster_folder, "Raster Symbology")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"已創建輸出資料夾: {output_folder}")
    
    # 取得所有 TIF 檔案
    raster_files = glob.glob(os.path.join(raster_folder, "*.tif"))
    print(f"找到 {len(raster_files)} 個柵格檔案")
    
    # 建立 ArcGIS Pro 專案
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    
    # 取得第一個地圖或建立新地圖
    if len(aprx.listMaps()) == 0:
        m = aprx.createMap("Map")
    else:
        m = aprx.listMaps()[0]
    
    # 取得色彩方案
    color_ramp = None
    color_ramps = aprx.listColorRamps("Yellow-Orange-Brown (Continuous)")
    if color_ramps:
        color_ramp = color_ramps[0]
        print(f"找到色彩方案: {color_ramp.name}")
    else:
        print("找不到 Yellow-Orange-Brown 色彩方案，將使用預設色彩方案")
    
    # 處理每個柵格檔案
    for raster_path in raster_files:
        try:
            base_filename = os.path.basename(raster_path)
            print(f"\n處理柵格: {base_filename}")
            
            # 設定輸出檔案路徑
            output_raster = os.path.join(output_folder, base_filename)
            
            # 使用 SetNull 將小於 0 的值設為 NoData，並儲存到輸出資料夾
            outSetNull = SetNull(raster_path, raster_path, "VALUE = -99.9")
            outSetNull.save(output_raster)
            print(f"已將小於 0 的值設為 NoData 並儲存至: {output_raster}")
            
            # 添加處理後的柵格到地圖
            lyr = m.addDataFromPath(output_raster)
            
            # 設定符號
            sym = lyr.symbology
            
            # 檢查是否為柵格符號
            if hasattr(sym, 'updateColorizer'):
                # 設定為分類符號
                sym.updateColorizer('RasterClassifyColorizer')
                
                # 取得色彩設定器
                colorizer = sym.colorizer
                
                # 設定分類方法為等間隔
                colorizer.classificationMethod = "EqualInterval"
                
                # 取得柵格的最大值以便進行分組
                raster = arcpy.Raster(output_raster)
                max_value = raster.maximum
                min_value = raster.minimum
                
                print(f"柵格最小值: {min_value}, 最大值: {max_value}")
                
                # 設定分界點數量
                colorizer.breakCount = 9
                
                # 設定色彩方案
                if color_ramp:
                    colorizer.colorRamp = color_ramp
                
                # 套用符號設定
                lyr.symbology = sym
                
                # 儲存圖層檔案到輸出資料夾
                lyr_path = os.path.join(output_folder, base_filename.replace(".tif", ".lyrx"))
                lyr.saveACopy(lyr_path)
                print(f"已儲存符號設定至: {lyr_path}")
            else:
                print("無法設定符號：不是有效的柵格圖層")
            
            # 移除圖層
            m.removeLayer(lyr)
            
        except Exception as e:
            print(f"處理柵格 {raster_path} 時發生錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 釋放 Spatial Analyst 授權
    arcpy.CheckInExtension("Spatial")
    
    print("\n所有柵格符號設定完成")

# 使用方式
raster_folder = r"C:\Users\regent\OneDrive - National ChengChi University\113-2\地理資訊系統特論\HW2\raster_Feature_to_Raster"
apply_rainfall_symbology_batch(raster_folder)
