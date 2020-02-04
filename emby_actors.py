import requests, configparser, base64, os, urllib.parse, re, traceback

if not os.path.exists('女優頭像'):
    print('“女優頭像”文件夾丟失！請把它放進exe的文件夾中！\n')
    os.system('pause')

# 讀取配置文件，這個ini文件用來給用户設置重命名的格式和jav網址
config_settings = configparser.RawConfigParser()
print('正在讀取ini中的設置...', end='')
try:
    config_settings.read('ini的設置會影響所有exe的操作結果.ini', encoding='utf-8-sig')
    emby_url = config_settings.get("emby專用", "網址")
    api_key = config_settings.get("emby專用", "api id")
except:
    print(traceback.format_exc())
    print('\n無法讀取ini文件，請修改它為正確格式，或者打開“【ini】重新創建ini.exe”創建全新的ini！')
    os.system('pause')
print('\n讀取ini文件成功!\n')

if not emby_url.endswith('/'):
    emby_url += '/'
pics = os.listdir('女優頭像')
try:
    suc_num = 0
    num = 0
    for file in pics:
        if file.endswith('jpg') or file.endswith('png'):
            num += 1
            if num%500 == 0:
                print('已掃描', num, '個頭像')
            actor = file.split('.')[0]
            actor_urlde = urllib.parse.quote(actor)
            # ${embyServerURL}/emby/Persons/${personName}?api_key=${apiKey}
            get_url = emby_url + 'emby/Persons/' + actor_urlde + '?api_key=' + api_key
            check_res = requests.get(url=get_url)
            # print(get_url)
            actor_msg = check_res.text
            # print(actor_msg)
            if actor_msg.startswith('{"Name'):  # Object
                actor_id = re.search(r'"Id":"(\d+)"', actor_msg).group(1)  # 匹配處理“標題”
                print('>>女優：', actor, 'ID：', actor_id)
            elif actor_msg.startswith('Access'):
                print(actor_msg)
                print('請檢查API ID填寫是否正確！')
                break
            else:
                continue
            actor_path = '女優頭像/' + file
            f = open(actor_path, 'rb')            # 二進制方式打開圖文件
            b6_pic = base64.b64encode(f.read())   # 讀取文件內容，轉換為base64編碼
            f.close()
            url = emby_url + 'emby/Items/' + actor_id + '/Images/Primary?api_key=' + api_key
            if file.endswith('jpg'):
                header = {"Content-Type": 'image/png', }
            else:
                header = {"Content-Type": 'image/jpeg', }
            # print(url)
            # os.system('pause')
            respones = requests.post(url=url, data=b6_pic, headers=header)
            suc_path = '女優頭像/設置成功/' + file
            suc_num += 1
            try:
                os.rename(actor_path, suc_path)
            except:
                print('    >已經存在：', suc_path)
except requests.exceptions.ConnectionError:
    print('emby服務端無法訪問，請檢查：', emby_url, '\n')
    os.system('pause')
except:
    print(traceback.format_exc())
    print('發生未知錯誤，請截圖給作者：', emby_url, '\n')
    os.system('pause')

print('\n成功處理', suc_num, '個女優頭像！\n')
os.system('pause')

