# 降雨資料處理與視覺化工具集

這個專案提供了一系列 Python 腳本，用於處理降雨資料、轉換為柵格檔案並套用視覺化符號。這些工具可以協助氣象資料分析人員和 GIS 專家快速處理大量降雨觀測資料，並產生高品質的視覺化成果。

## 檔案說明

### 資料前處理

#### `result.py`
根據各年觀測資料生成總觀測資料。[1]
- 功能：整合各年份的觀測資料，生成總觀測資料
- 使用時機：需要對多年降雨資料進行整合時
- 輸出：包含整合觀測資料的 CSV 檔案

#### `month split.py`
將總觀測資料按月份分割，方便後續處理和分析。[2]
- 功能：讀取降雨資料並按月份分割成多個檔案
- 使用時機：當您有跨越多個月份的大型降雨資料集時
- 輸出：按月份命名的 CSV 檔案

#### `csv to dataframe.py`
將 CSV 格式的降雨資料轉換為 Pandas DataFrame，便於資料操作和分析。[3]
- 功能：讀取 CSV 檔案並轉換為結構化的 DataFrame
- 使用時機：需要在進行空間轉換前對資料進行清理或分析時
- 輸出：處理過的 DataFrame 物件

### 空間內插與柵格轉換

#### `csv to raster_Feature to Raster.py`
將點位降雨資料轉換為特徵圖層，再轉換為柵格檔案。[4]
- 功能：將 CSV 降雨資料轉換為點位特徵圖層，再轉換為柵格
- 使用時機：當您需要直接從觀測站點資料生成柵格而不進行內插時
- 輸出：TIF 格式的柵格檔案

#### `csv to raster_IDW.py`
使用反距離權重法 (IDW) 對降雨資料進行內插，生成連續的降雨分布柵格。[5]
- 功能：利用 IDW 內插法將點位降雨資料轉換為連續表面
- 使用時機：需要根據有限的觀測站點估計整個區域的降雨分布時
- 輸出：TIF 格式的柵格檔案，表示內插後的降雨分布

#### `csv to raster_PointToRaster.py`
直接將點位資料轉換為柵格，適用於高密度觀測網絡的資料。[6]
- 功能：使用 ArcGIS 的 PointToRaster 工具將點位資料轉換為柵格
- 使用時機：觀測站點密度高且分布均勻時
- 輸出：TIF 格式的柵格檔案

### 視覺化與符號設定

#### `Raster Symbology_equal interval.py`
使用等間隔分類方法為降雨柵格資料套用符號設定。[7]
- 功能：為柵格檔案套用等間隔分類的降雨符號
- 使用時機：需要以相等的數值間隔顯示降雨量分布時
- 輸出：套用符號設定的 LYRX 檔案和處理後的 TIF 檔案

#### `Raster Symbology_manual interval.py`
使用手動設定的分類間隔為降雨柵格資料套用符號設定。[8]
- 功能：為柵格檔案套用自定義分類間隔的降雨符號
- 使用時機：需要根據特定標準或閾值顯示降雨量分布時
- 輸出：套用符號設定的 LYRX 檔案和處理後的 TIF 檔案

## 使用流程

一般的資料處理流程如下：

1. 使用 `result.py` 整合多年資料並生成總觀測資料
2. 使用 `month split.py` 將總觀測資料按月份分割
3. 使用 `csv to dataframe.py` 進行資料清理和預處理
4. 選擇以下其中一種方法將資料轉換為柵格：
  - `csv to raster_Feature to Raster.py`
  - `csv to raster_IDW.py`
  - `csv to raster_PointToRaster.py`
5. 使用以下其中一種方法套用符號設定：
   - `Raster Symbology_equal interval.py`
   - `Raster Symbology_manual interval.py`

## 系統需求

- ArcGIS Pro 2.5 或更新版本
- Python 3.6 或更新版本
- 必要的 Python 套件：
  - arcpy (隨 ArcGIS Pro 安裝)
  - pandas
  - numpy
  - glob
  - os

## 注意事項

- 執行腳本前請確保已安裝 Spatial Analyst 擴充模組並擁有有效授權
- 部分腳本需要大量記憶體，處理大型資料集時請確保系統資源充足
- 建議在執行前備份原始資料，特別是使用會直接修改原始檔案的腳本時

## 貢獻與問題回報

如發現任何問題或有改進建議，請透過 GitHub Issues 回報。歡迎提交 Pull Request 協助改進這些工具。

## 資料來源

資料來源：[臺灣氣候變遷推估資訊與調適知識平台](https://tccip.ncdr.nat.gov.tw/)
