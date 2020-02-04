# jav-standard-tool 簡稱javsdt
簡介：收集jav元數據，並規範本地文件（夾）的格式，收集女優頭像，為emby、kodi、jellyfin、極影派等影片管理軟件鋪路。  
python3.7  使用pyinstaller打包成發行版exe。  

1、運行源代碼：  
    如果要運行py文件，PIL即pillow不要用新版，新版僅支持“png”，我是“pip install pillow==6.0.0”  
    百度人體分析的“from aip import AipBodyAnalysis”，aip是“pip install baidu-aip”  
    另外需要mac、linux系統下的同志幫忙發佈各系統的發行版，要改代碼，windows的路徑是反斜槓“\”。  
  
2、下載及羣鏈接：  
    目前20-01-22更新1.0.3版本  
    [前往下載exe](https://github.com/junerain123/javsdt/releases/tag/V1.0.3)或者[從藍奏雲下載](https://www.lanzous.com/i8tkzjg)  
  
[前往下載女優頭像](https://github.com/junerain123/JAV-Scraper-and-Rename-local-files/releases/tag/女優頭像)   
  
[電報羣](https://t.me/javsdtool)  
[企鵝羣](https://jq.qq.com/?_wv=1027&k=5CbWOpV)  
  
3、工作流程：  
    （1）用户選擇文件夾，遍歷路徑下的所有文件。  
    （2）文件是jav，取車牌號，到javXXX網站搜索影片找到對應網頁。  
    （3）獲取網頁源碼找出“標題”“導演”“發行日期”等信息和DVD封面url。  
    （4）重命名影片文件。  
    （5）重命名文件夾或建立獨立文件夾。  
    （6）保存信息寫入nfo。   
    （7）下載封面url作fanart.jpg，裁剪右半邊作poster.jpg。   
    （8）移動文件夾，完成歸類。  
  
4、目標效果：  
![image](https://github.com/junerain123/Collect-Info-and-Fanart-for-JAV-/blob/master/images/1.png)  
![image](https://github.com/junerain123/Collect-Info-and-Fanart-for-JAV-/blob/master/images/2.png)  
![image](https://github.com/junerain123/Collect-Info-and-Fanart-for-JAV-/blob/master/images/3.jpg)  
  
5、ini中的用户設置：  
![image](https://github.com/junerain123/Collect-Info-and-Fanart-for-JAV-/blob/master/images/4.PNG)  
  
6、其他説明：  
（1）不需要贊助；  
（2）允許對軟件進行任何形式的轉載；  
（3）代碼及軟件使用“MIT許可證”，他人可以修改代碼、發佈分支，允許閉源、商業化，但造成後果與本作者無關。  
