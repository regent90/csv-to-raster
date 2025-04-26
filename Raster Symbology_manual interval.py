import arcpy
import os
import glob

def apply_rainfall_symbology_batch(raster_folder):
    """批次對資料夾中的所有 TIF 檔案套用降雨量符號設定"""
    
    print(f"正在處理資料夾: {raster_folder}")
    
    # 取得所有 TIF 檔案
    raster_files = glob.glob(os.path.join(raster_folder, "rain_1960_01.tif"))
    print(f"找到 {len(raster_files)} 個柵格檔案")
    
    # 建立 ArcGIS Pro 專案
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    
    # 取得第一個地圖或建立新地圖
    if len(aprx.listMaps()) == 0:
        m = aprx.createMap("Map")
    else:
        m = aprx.listMaps()[0]
    
    # 取得 Yellow-Orange-Brown (Continuous) 色彩方案
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
            print(f"\n處理柵格: {os.path.basename(raster_path)}")
            
            # 先建立屬性表
            try:
                arcpy.management.BuildRasterAttributeTable(raster_path, "Overwrite")
                print("已建立柵格屬性表")
            except:
                print("無法建立柵格屬性表，繼續處理...")
            
            # 添加柵格到地圖
            lyr = m.addDataFromPath(raster_path)
            
            # 設定符號
            sym = lyr.symbology
            
            # 檢查是否為柵格符號
            if hasattr(sym, 'updateColorizer'):
                # 設定為分類符號
                sym.updateColorizer('RasterClassifyColorizer')
                
                # 取得色彩設定器
                colorizer = sym.colorizer

                # 設定分類方法為手動
                colorizer.classificationMethod = "ManualInterval"
                
                # 取得柵格的最大值以便進行分組
                raster = arcpy.Raster(raster_path)
                max_value = raster.maximum
                min_value = raster.minimum
                
                print(f"柵格最小值: {min_value}, 最大值: {max_value}")
                
                # 設定手動分界點
                breaks = [-99.9, 0]  # 首先加入無資料值和 0 作為分界點
                if max_value > 0:
                    interval = max_value / 8
                    for i in range(1, 8):  # 只需要 7 個分界點，因為已經有 0 了
                        breaks.append(i * interval)
                
                # 設定分界點
                colorizer.breakCount = len(breaks)
                colorizer.breakValues = breaks
                
                # 設定色彩方案
                if color_ramp:
                    colorizer.colorRamp = color_ramp
                
                # 套用符號設定
                lyr.symbology = sym
                
                # 儲存圖層檔案
                lyr_path = raster_path.replace(".tif", ".lyrx")
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
    
    print("\n所有柵格符號設定完成")

# 使用方式
raster_folder = r"C:\Users\regent\OneDrive - National ChengChi University\113-2\地理資訊系統特論\HW2\raster_Feature_to_Raster"
apply_rainfall_symbology_batch(raster_folder)