# -*- coding:utf-8 -*-
import re, sys, os, configparser, time, hashlib, json, requests, shutil, traceback
from PIL import Image
from time import sleep


# 獲取用户選取的文件夾路徑，返回路徑str
def get_directory():
    if os.path.exists(sys.argv[1]):
        path = os.path.abspath(sys.argv[1])
    else:
        print("Cannot find " + sys.argv[1])
        exit()
    return path


# 記錄錯誤txt，無返回
def write_fail(fail_m):
    record_txt = open('【記得清理它】失敗記錄.txt', 'a', encoding="utf-8")
    record_txt.write(fail_m)
    record_txt.close()


# 調用百度翻譯API接口，返回中文簡介str
def tran(api_id, key, word, to_lang):
    # init salt and final_sign
    salt = str(time.time())[:10]
    final_sign = api_id + word + salt + key
    final_sign = hashlib.md5(final_sign.encode("utf-8")).hexdigest()
    # 表單paramas
    paramas = {
        'q': word,
        'from': 'jp',
        'to': to_lang,
        'appid': '%s' % api_id,
        'salt': '%s' % salt,
        'sign': '%s' % final_sign
    }
    response = requests.get('http://api.fanyi.baidu.com/api/trans/vip/translate', params=paramas, timeout=10).content
    content = str(response, encoding="utf-8")
    try:
        json_reads = json.loads(content)
        return json_reads['trans_result'][0]['dst']
    except json.decoder.JSONDecodeError:
        print('    >翻譯簡介失敗，請截圖給作者，檢查是否有非法字符：', word)
        return '無法翻譯該簡介，請手動去arzon.jp查找簡介並翻譯。'
    except:
        print('    >正在嘗試重新日譯中...')
        return tran(api_id, key, word, to_lang)


# 獲取一個arzon_cookie，返回cookie
def get_acook(prox):
    if prox:
        session = requests.Session()
        session.get('https://www.arzon.jp/index.php?action=adult_customer_agecheck&agecheck=1&redirect=https%3A%2F%2Fwww.arzon.jp%2F', proxies=prox, timeout=10)
        return session.cookies.get_dict()
    else:
        session = requests.Session()
        session.get('https://www.arzon.jp/index.php?action=adult_customer_agecheck&agecheck=1&redirect=https%3A%2F%2Fwww.arzon.jp%2F', timeout=10)
        return session.cookies.get_dict()


# 獲取網頁源碼，返回網頁text；假裝python的“重載”函數
def get_jav_html(url_list):
    if len(url_list) == 1:
        rqs = requests.get(url_list[0], timeout=10)
    else:
        rqs = requests.get(url_list[0], proxies=url_list[1], timeout=10)
    rqs.encoding = 'utf-8'
    return rqs.text


def get_arzon_html(url_list):
    if len(url_list) == 2:
        rqs = requests.get(url_list[0], cookies=url_list[1], timeout=10)
    else:
        rqs = requests.get(url_list[0], cookies=url_list[1], proxies=url_list[2], timeout=10)
    rqs.encoding = 'utf-8'
    return rqs.text


# 下載圖片，無返回
def download_pic(cov_list):
    # 0錯誤次數  1圖片url  2圖片路徑  3proxies
    if cov_list[0] < 5:
        try:
            if len(cov_list) == 3:
                r = requests.get(cov_list[1], stream=True, timeout=(3, 7))
                with open(cov_list[2], 'wb') as pic:
                    for chunk in r:
                        pic.write(chunk)
            else:
                r = requests.get(cov_list[1], proxies=cov_list[3], stream=True, timeout=(3, 7))
                with open(cov_list[2], 'wb') as pic:
                    for chunk in r:
                        pic.write(chunk)
        except:
            print('    >下載失敗，重新下載...')
            cov_list[0] += 1
            download_pic(cov_list)
        try:
            Image.open(cov_list[2])
        except OSError:
            print('    >下載失敗，重新下載....')
            cov_list[0] += 1
            download_pic(cov_list)
    else:
        raise Exception('    >下載多次，仍然失敗！')

def nfo_exist(files):
    return next((True for f in files if f.endswith('nfo')), False)

# 每一部jav的“結構體”
class JavFile(object):
    def __init__(self):
        self.name = 'ABC-123.mp4'  # 文件名
        self.car = 'ABC-123'  # 車牌
        self.episodes = 0     # 第幾集
        self.subt = ''        # 字幕文件名  ABC-123.srt


#  main開始
print('1、避開21:00-1:00，訪問javlibrary和arzon很慢。\n'
      '2、若一直連不上javlibrary，請在ini中更新網址\n'
      '3、不要用www.javlibrary.com！用防屏蔽地址\n')
# 讀取配置文件，這個ini文件用來給用户設置重命名的格式和jav網址
print('正在讀取ini中的設置...', end='')
try:
    config_settings = configparser.RawConfigParser()
    config_settings.read('ini的設置會影響所有exe的操作結果.ini', encoding='utf-8-sig')
    rating_settings = configparser.RawConfigParser(strict=False)
    if os.path.isfile('rating.ini'):
        rating_settings.read('rating.ini', encoding='utf-8-sig')

    if_nfo = config_settings.get("收集nfo", "是否收集nfo？")
    if_exnfo = config_settings.get("收集nfo", "是否跳過已存在nfo的文件夾？")
    if_review = config_settings.get("收集nfo", "是否收集javlibrary上的影評？")
    custom_title = config_settings.get("收集nfo", "nfo中title的格式")
    if_mp4 = config_settings.get("重命名影片", "是否重命名影片？")
    rename_mp4 = config_settings.get("重命名影片", "重命名影片的格式")
    if_folder = config_settings.get("修改文件夾", "是否重命名或創建獨立文件夾？")
    rename_folder = config_settings.get("修改文件夾", "新文件夾的格式")
    if_rename_subt = config_settings.get("字幕文件", "是否重命名已有的字幕文件")
    if_classify_subt = config_settings.get("字幕文件", "是否使用字幕庫")
    file_folder = config_settings.get("歸類影片", "針對文件還是文件夾？")
    if_classify = config_settings.get("歸類影片", "是否歸類影片？")
    classify_root = config_settings.get("歸類影片", "歸類的根目錄")
    classify_basis = config_settings.get("歸類影片", "歸類的標準")
    if_jpg = config_settings.get("下載封面", "是否下載封面海報？")
    custom_fanart = config_settings.get("下載封面", "DVD封面的格式")
    custom_poster = config_settings.get("下載封面", "海報的格式")
    if_sculpture = config_settings.get("kodi專用", "是否收集女優頭像")
    if_proxy = config_settings.get("代理", "是否使用代理？")
    proxy = config_settings.get("代理", "代理IP及端口")
    if_plot = config_settings.get("百度翻譯API", "是否需要日語簡介？")
    if_tran = config_settings.get("百度翻譯API", "是否翻譯為中文？")
    ID = config_settings.get("百度翻譯API", "APP ID")
    SK = config_settings.get("百度翻譯API", "密鑰")
    simp_trad = config_settings.get("其他設置", "簡繁中文？")
    library_url = config_settings.get("其他設置", "javlibrary網址")
    bus_url = config_settings.get("其他設置", "javbus網址")
    suren_pref = config_settings.get("其他設置", "素人車牌(若有新車牌請自行添加)")
    file_type = config_settings.get("其他設置", "掃描文件類型")
    title_len = int(config_settings.get("其他設置", "重命名中的標題長度（50~150）"))
    subt_words = config_settings.get("原影片文件的性質", "是否中字即文件名包含")
    custom_subt = config_settings.get("原影片文件的性質", "是否中字的表現形式")
    xx_words = config_settings.get("原影片文件的性質", "是否xx即文件名包含")
    custom_xx = config_settings.get("原影片文件的性質", "是否xx的表現形式")
    movie_type = config_settings.get("原影片文件的性質", "有碼")
    part_prefix = config_settings.get("分段文件", "分段前序")
    actors_source = config_settings.get("kodi專用", "女優頭像位置")

except:
    print(traceback.format_exc())
    print('\n無法讀取ini文件，請修改它為正確格式，或者打開“【ini】重新創建ini.exe”創建全新的ini！')
    os.system('pause')

# 確認：女優頭像ini及頭像文件夾
if if_sculpture == '是':
    if not os.path.exists(actors_source):
        print('\n“女優頭像”文件夾丟失！請把它放進exe的文件夾中！\n')
        os.system('pause')
    if not os.path.exists('【缺失的女優頭像統計For Kodi】.ini'):
        config_actor = configparser.ConfigParser()
        config_actor.add_section("缺失的女優頭像")
        config_actor.set("缺失的女優頭像", "女優姓名", "N(次數)")
        config_actor.add_section("説明")
        config_actor.set("説明", "上面的“女優姓名 = N(次數)”的表達式", "後面的N數字表示你有N部(次)影片都在找她的頭像，可惜找不到")
        config_actor.set("説明", "你可以去保存一下她的頭像jpg到“女優頭像”文件夾", "以後就能保存她的頭像到影片的文件夾了")
        config_actor.write(open('【缺失的女優頭像統計For Kodi】.ini', "w", encoding='utf-8-sig'))
        print('\n    >“【缺失的女優頭像統計For Kodi】.ini”文件丟失...正在重寫ini...成功！')
        print('正在重新讀取...', end='')
print('\n讀取ini文件成功!')
# 確認：arzon的cookie，通過成人驗證
proxies = {"http": "http://" + proxy, "https": "https://" + proxy}
acook = {}
if if_plot == '是' and if_nfo == '是':
    print('正在嘗試通過“https://www.arzon.jp”的成人驗證...')
    try:
        if if_proxy == '是' and proxy != '':
            acook = get_acook(proxies)
        else:
            acook = get_acook({})
        print('通過arzon的成人驗證！\n')
    except:
        print('連接arzon失敗，請避開網絡高峯期！請重啟程序！\n')
        os.system('pause')
# 確認：代理哪些站點
if if_proxy == '是' and proxy != '':      # 是否需要代理，設置requests請求時的狀態
    jav_list = ['', proxies]              # 代理jav等網站
    arzon_list = ['', acook, proxies]     # 代理arzon
    cover_list = [0, '', '', proxies]     # 代理dmm圖片原
else:
    jav_list = ['']
    arzon_list = ['', acook]
    cover_list = [0, '', '']
# 歸類文件夾具有最高決定權
if if_classify == '是':            # 如果需要歸類
    if file_folder == '文件夾':    # 並且是針對文件夾
        if_folder = '是'           # 那麼必須重命名文件夾或者創建新的文件夾
    else:
        if_folder = '否'           # 否則不會操作新文件夾
# http://www.x39n.com/   https://www.buscdn.work/ 無論用户輸不輸人後面的斜槓
if not library_url.endswith('/'):
    library_url += '/'
if not bus_url.endswith('/'):
    bus_url += '/'
# 確認網站、百度翻譯是簡/繁中文
if simp_trad == '簡':
    library_url += 'cn/'
    t_lang = 'zh'
else:
    library_url += 'tw/'
    t_lang = 'cht'
# 初始化其他
nfo_dict = {'空格': ' ', '車牌': 'ABC-123', '標題': '未知標題', '完整標題': '完整標題', '導演': '未知導演',
            '發行年月日': '1970-01-01', '發行年份': '1970', '月': '01', '日': '01',
            '片商': '未知片商', '評分': '0', '首個女優': '未知演員', '全部女優': '未知演員',
            '片長': '0', '/': '/', '是否中字': '', '視頻': 'ABC-123', '車牌前綴': 'ABC',
            '是否xx': '', '影片類型': movie_type, '系列': '未知系列'}         # 存放影片信息，女優，標題等
suren_list = suren_pref.split('、')               # 素人番號的列表
rename_mp4_list = rename_mp4.split('+')           # 重命名視頻的格式
rename_folder_list = rename_folder.split('+')     # 重命名文件夾的格式
type_tuple = tuple(file_type.split('、'))         # 需要掃描的文件的類型
classify_basis_list = classify_basis.split('/')  # 歸類標準，歸類到哪個文件夾
title_list = custom_title.replace('標題', '完整標題', 1).split('+')  # nfo中title的寫法
fanart_list = custom_fanart.split('+')            # fanart的格式
poster_list = custom_poster.split('+')            # poster的格式
word_list = subt_words.split('、')                # 包含哪些特殊含義的文字，判斷是否中字
xx_list = xx_words.split('、')                    # 包含哪些特殊含義的文字，判斷是否xx
for j in rename_mp4_list:
    if j not in nfo_dict:
        nfo_dict[j] = j
for j in rename_folder_list:
    if j not in nfo_dict:
        nfo_dict[j] = j
classify_list = []
for i in classify_basis_list:
    for j in i.split('+'):
        if j not in nfo_dict:
            nfo_dict[j] = j
        classify_list.append(j)
    classify_list.append('/')
for j in title_list:
    if j not in nfo_dict:
        nfo_dict[j] = j
for j in fanart_list:
    if j not in nfo_dict:
        nfo_dict[j] = j
for j in poster_list:
    if j not in nfo_dict:
        nfo_dict[j] = j


start_key = ''
while start_key == '':
    # 用户選擇文件夾
    print('請選擇要整理的文件夾：', end='')
    path = get_directory()
    print(path)
    write_fail('已選擇文件夾：' + path + '\n')
    print('...文件掃描開始...如果時間過長...請避開中午夜晚高峯期...\n')
    # 確定歸類根目錄
    if if_classify == '是':
        classify_root = classify_root.rstrip('/')
        if classify_root != '所選文件夾':
            if classify_root != path:  # 歸類根目錄和所選不一樣，繼續核實歸類根目錄的合法性
                if classify_root[:2] != path[:2]:
                    print('歸類的根目錄“', classify_root, '”和所選文件夾不在同一磁盤無法歸類！請修正！')
                    os.system('pause')
                if not os.path.exists(classify_root):
                    print('歸類的根目錄“', classify_root, '”不存在！無法歸類！請修正！')
                    os.system('pause')
            else:  # 一樣
                classify_root = path + '/歸類完成'
        else:
            classify_root = path + '/歸類完成'
    # 初始化“失敗信息”
    fail_times = 0                             # 處理過程中失敗的個數
    fail_list = []                             # 用於存放處理失敗的信息
    # root【當前根目錄】 dirs【子目錄】 files【文件】，root是字符串，後兩個是列表
    for root, dirs, files in os.walk(path):
        if if_classify == '是' and root.startswith(classify_root):  # “當前目錄”在“目標歸類目錄”中
            # print('>>該文件夾在歸類的根目錄中，跳過處理...', root)
            continue
        if if_exnfo == '是' and files and nfo_exist(files):
            print(root+'/'+files[-1])
            continue
        # 對這一層文件夾進行評估,有多少視頻，有多少同車牌視頻，是不是獨立文件夾
        jav_videos = []        # 存放：需要整理的jav的結構體
        cars_dic = {}          # 存放：這一層目錄下的幾個車牌
        videos_num = 0         # 當前文件夾中視頻的數量，可能有視頻不是jav
        subtitles = False      # 有沒有字幕
        subts_dict = {}        # 存放：jav的字幕文件 {'c:/a/abc_123.srt': 'abc-123'}
        for raw_file in files:
            # 判斷文件是不是字幕文件
            if raw_file.endswith(('.srt', '.vtt', '.ass', '.ssa',)):
                srt_g = re.search(r'([a-zA-Z]{2,7})-? ?_?(\d{2,6})', raw_file)
                if str(srt_g) != 'None':
                    num_pref = srt_g.group(1).upper()
                    if num_pref in suren_list:
                        continue
                    num_suf = srt_g.group(2)
                    car_num = num_pref + '-' + num_suf
                    subts_dict[raw_file] = car_num
                continue
        # print(subts_dict)
        # print('>>掃描字幕文件完畢！')
        for raw_file in files:
            # 判斷是不是視頻，得到車牌號
            if raw_file.endswith(type_tuple) and not raw_file.startswith('.'):
                videos_num += 1
                video_num_g = re.search(r'([a-zA-Z]{2,7})-? ?_?(\d{2,6})', raw_file)    # 這個正則表達式匹配“車牌號”可能有點奇怪，
                if str(video_num_g) != 'None':                               # 如果你下過上千部片，各種參差不齊的命名，你就會理解我了。
                    num_pref = video_num_g.group(1).upper()
                    num_suf = video_num_g.group(2)
                    car_num = num_pref + '-' + num_suf
                    if num_pref in suren_list:  # 如果這是素人影片，告訴一下用户，它們需要另外處理
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '個警告！素人影片：' + root.lstrip(path) + '/' + raw_file + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue  # 素人影片不參與下面的整理
                    if car_num not in cars_dic:      # cars_dic中沒有這個車牌，表示這一層文件夾下新發現一個車牌
                        cars_dic[car_num] = 1        # 這個新車牌有了第一集
                    else:
                        cars_dic[car_num] += 1       # 已經有這個車牌了，加一集cd
                    jav_file = JavFile()
                    jav_file.car = car_num           # 車牌
                    jav_file.name = raw_file         # 原文件名
                    jav_file.episodes = cars_dic[car_num]  # 這個jav視頻，是第幾集
                    if car_num in subts_dict.values():
                        jav_file.subt = list(subts_dict.keys())[list(subts_dict.values()).index(car_num)]
                        del subts_dict[jav_file.subt]
                    jav_videos.append(jav_file)
                else:
                    continue
            else:
                continue
        # 判定影片所在文件夾是否是獨立文件夾
        if cars_dic:  # 這一層文件夾下有jav
            if len(cars_dic) > 1 or videos_num > len(jav_videos) or len(dirs) > 1 or (len(dirs) == 1 and dirs[0] != '.actors'):
                # 當前文件夾下，車牌不止一個，還有其他非jav視頻，            有其他文件夾，除了女優頭像文件夾“.actors”
                separate_folder = False   # 不是獨立的文件夾
            else:
                separate_folder = True    # 這一層文件夾是這部jav的獨立文件夾
        else:
            continue

        # 正式開始
        # print(jav_videos)
        # os.system('pasue')
        for srt in jav_videos:
            car_num = srt.car
            file = srt.name
            relative_path = '/' + root.lstrip(path) + '/' + file  # 影片的相對於所選文件夾的路徑，用於報錯
            try:
                # 獲取nfo信息的javlibrary搜索網頁
                lib_search_url = library_url + 'vl_searchbyid.php?keyword=' + car_num
                jav_list[0] = lib_search_url
                try:
                    jav_html = get_jav_html(jav_list)
                except:
                    print('>>嘗試打開javlibrary搜索頁面失敗，正在嘗試第二次打開...')
                    try:  # 用網高峯期，經常打不開javlibrary，嘗試第二次
                        jav_html = get_jav_html(jav_list)
                        print('    >第二次嘗試成功！')
                    except:
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '個失敗！打開javlibrary搜索頁面失敗：' + lib_search_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                # 搜索結果的網頁，大部分情況就是這個影片的網頁，也有可能是多個結果的網頁
                # 嘗試找標題，第一種情況：找得到，就是這個影片的網頁
                titleg = re.search(r'<title>([A-Z].+?) - JAVLibrary</title>', jav_html)  # 匹配處理“標題”
                # 搜索結果就是AV的頁面
                if str(titleg) != 'None':
                    title = titleg.group(1)
                # 第二種情況：搜索結果可能是兩個以上，所以這種匹配找不到標題，None！
                else:   # 繼續找標題，但匹配形式不同，這是找“可能是多個結果的網頁”上的第一個標題
                    search_results = re.findall(r'v=javli(.+?)" title="(.+?-\d+?[a-z]? .+?)"', jav_html)
                    # os.system('pause')
                    # 搜索有幾個結果，用第一個AV的網頁，打開它
                    if search_results:
                        result_first_url = library_url + '?v=javli' + search_results[0][0]
                        if len(search_results) > 1:   # 只有一個結果，其實有的結果被忽略了，比如avop-00127bod，它是近幾年重置的，信息宂餘
                            if search_results[0][1].endswith('ク）'):   # 排在第一個的是藍光重置版，比如SSNI-589（ブルーレイディスク），它的封面不正常，跳過它
                                result_first_url = library_url + '?v=javli' + search_results[1][0]
                            elif search_results[1][1].startswith(car_num):  # 不同的片，但車牌完全相同，比如id-020。警告用户，但默認用第一個結果。
                                fail_times += 1
                                fail_message = '第' + str(fail_times) + '個警告！搜索頁面上的有多個結果：' + lib_search_url + '\n'
                                print('>>' + fail_message, end='')
                                fail_list.append('    >' + fail_message)
                                write_fail('    >' + fail_message)
                            # else: 還有一種情況，不同片，車牌也不同，但搜索到一堆，比如搜“AVOP-039”，還會得到“AVOP-390”，正確的肯定是第一個。
                        jav_list[0] = result_first_url
                        try:
                            jav_html = get_jav_html(jav_list)
                        except:
                            fail_times += 1
                            fail_message = '>第' + str(fail_times) + '個失敗！打開javlibrary搜索頁面上的第一個AV失敗：' + result_first_url + '，' + relative_path + '\n'
                            print('>>' + fail_message, end='')
                            fail_list.append('    >' + fail_message)
                            write_fail('    >' + fail_message)
                            continue
                        # 找到標題，留着馬上整理信息用
                        title = re.search(r'<title>([A-Z].+?) - JAVLibrary</title>', jav_html).group(1)
                    # 第三種情況：搜索不到這部影片，搜索結果頁面什麼都沒有
                    else:
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '個失敗！javlibrary找不到AV信息，無碼？新系列素人？年代久遠？：' + lib_search_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('>>' + fail_message)
                        continue

                print('>>正在處理：', title)
                # 影片文件本身的一些屬性
                video_type = '.' + file.split('.')[-1]         # 文件類型，如：.mp4
                subt_name = srt.subt
                if subt_name:
                    subtitles = True
                    subt_type = '.' + subt_name.split('.')[-1]  # 字幕類型，如：.srt
                else:
                    subtitles = False
                    subt_type = ''
                nfo_dict['是否中字'] = ''
                if not subtitles:             # 沒有外掛字幕
                    for i in word_list:       # 但是原文件名包含“-c、-C、中字”這些字符
                        if i in file:
                            nfo_dict['是否中字'] = custom_subt
                            break
                else:
                    nfo_dict['是否中字'] = custom_subt
                nfo_dict['是否xx'] = ''
                for i in xx_list:
                    if i in file:
                        nfo_dict['是否xx'] = custom_xx
                        break
                # 去除title中的特殊字符
                title = title.replace('\n', '').replace('&', '和').replace('/', '#')\
                    .replace('/', '#').replace(':', '：').replace('*', '#').replace('?', '？')\
                    .replace('"', '#').replace('<', '【').replace('>', '】')\
                    .replace('|', '#').replace('＜', '【').replace('＞', '】')\
                    .replace('〈', '【').replace('〉', '】').replace('＆', '和').replace('\t', '').replace('\r', '')
                # 正則匹配 影片信息 開始！
                # title的開頭是車牌號，想要後面的純標題
                car_titleg = re.search(r'(.+?) (.+)', title)  # 這邊匹配番號，[a-z]可能很奇怪，
                # 車牌號
                nfo_dict['車牌'] = car_titleg.group(1)
                nfo_dict['車牌前綴'] = nfo_dict['車牌'].split('-')[0]
                # 給用户用的標題是 短的title_easy
                nfo_dict['完整標題'] = car_titleg.group(2)
                # 處理影片的標題過長
                if len(nfo_dict['完整標題']) > title_len:
                    nfo_dict['標題'] = nfo_dict['完整標題'][:title_len]
                else:
                    nfo_dict['標題'] = nfo_dict['完整標題']
                # 片商
                studiog = re.search(r'rel="tag">(.+?)</a> &nbsp;<span id="maker_', jav_html)
                if str(studiog) != 'None':
                    nfo_dict['片商'] = studiog.group(1)
                else:
                    nfo_dict['片商'] = '未知片商'
                # 上映日
                premieredg = re.search(r'<td class="text">(\d\d\d\d-\d\d-\d\d)</td>', jav_html)
                if str(premieredg) != 'None':
                    nfo_dict['發行年月日'] = premieredg.group(1)
                    nfo_dict['發行年份'] = nfo_dict['發行年月日'][0:4]
                    nfo_dict['月'] = nfo_dict['發行年月日'][5:7]
                    nfo_dict['日'] = nfo_dict['發行年月日'][8:10]
                else:
                    nfo_dict['發行年月日'] = '1970-01-01'
                    nfo_dict['發行年份'] = '1970'
                    nfo_dict['月'] = '01'
                    nfo_dict['日'] = '01'
                # 片長 <td><span class="text">150</span> 分鐘</td>
                runtimeg = re.search(r'<td><span class="text">(\d+?)</span>', jav_html)
                if str(runtimeg) != 'None':
                    nfo_dict['片長'] = runtimeg.group(1)
                else:
                    nfo_dict['片長'] = '0'
                # 導演
                directorg = re.search(r'rel="tag">(.+?)</a> &nbsp;<span id="director', jav_html)
                if str(directorg) != 'None':
                    nfo_dict['導演'] = directorg.group(1)
                else:
                    nfo_dict['導演'] = '未知導演'
                # 演員們 和 # 第一個演員
                actors_prag = re.search(r'<span id="cast(.+?)</td>', jav_html, re.DOTALL)
                if str(actors_prag) != 'None':
                    actors = re.findall(r'rel="tag">(.+?)</a></span> <span id', actors_prag.group(1))
                    if len(actors) != 0:
                        if len(actors) > 7:
                            actors = actors[:7]
                        nfo_dict['首個女優'] = actors[0]
                        nfo_dict['userrating'] = rating_settings.get('actor', actors[0], fallback= '0')
                        nfo_dict['全部女優'] = ' '.join(actors)
                    else:
                        nfo_dict['首個女優'] = nfo_dict['全部女優'] = '未知演員'
                        nfo_dict['userrating'] = '0'
                        actors = ['未知演員']
                else:
                    nfo_dict['首個女優'] = nfo_dict['全部女優'] = '未知演員'
                    actors = ['未知演員']
                nfo_dict['標題'] = nfo_dict['標題'].rstrip(nfo_dict['全部女優'])
                # 特點
                genres = re.findall(r'category tag">(.+?)</a>', jav_html)
                if nfo_dict['是否中字']:
                    genres.append('中文字幕')
                if nfo_dict['是否xx']:
                    genres.append('無碼流出')
                # print(genres)
                # DVD封面cover
                coverg = re.search(r'src="(.+?)" width="600" height="403"', jav_html)  # 封面圖片的正則對象
                if str(coverg) != 'None':
                    cover_url = coverg.group(1)
                else:
                    cover_url = ''
                # 評分
                scoreg = re.search(r'&nbsp;<span class="score">\((.+?)\)</span>', jav_html)
                if str(scoreg) != 'None':
                    score = float(scoreg.group(1))
                    score = (score - 4) * 5 / 3     # javlibrary上稍微有人關注的影片評分都是6分以上（10分制），強行把它差距拉大
                    if score >= 0:
                        score = '%.1f' % score
                        nfo_dict['評分'] = str(score)
                    else:
                        nfo_dict['評分'] = '0'
                else:
                    nfo_dict['評分'] = '0'
                criticrating = str(float(nfo_dict['評分'])*10)
                # javlibrary的精彩影評   (.+?\s*.*?\s*.*?\s*.*?) 下面的匹配可能很奇怪，沒辦法，就這麼奇怪
                plot_review = ''
                if if_review == '是':
                    review = re.findall(r'(hidden">.+?</textarea>)</td>\s*?<td class="scores"><table>\s*?<tr><td><span class="scoreup">\d\d+?</span>', jav_html, re.DOTALL)
                    if len(review) != 0:
                        plot_review = '\n【精彩影評】：'
                        for rev in review:
                            right_review = re.findall(r'hidden">(.+?)</textarea>', rev, re.DOTALL)
                            if len(right_review) != 0:
                                plot_review = plot_review + right_review[-1] + '////'
                                continue
                        plot_review = plot_review.replace('\n', '').replace('&', '和').replace('/', '#') \
                            .replace(':', '：').replace('*', '#').replace('?', '？') \
                            .replace('"', '#').replace('<', '【').replace('>', '】') \
                            .replace('|', '#').replace('＜', '【').replace('＞', '】') \
                            .replace('〈', '【').replace('〉', '】').replace('＆', '和').replace('\t', '').replace('\r', '')
                # arzon的簡介 #########################################################
                plot = series = ''
                if if_nfo == '是' and if_plot == '是':
                    while 1:
                        arz_search_url = 'https://www.arzon.jp/itemlist.html?t=&m=all&s=&q=' + nfo_dict['車牌']
                        print('    >正在查找簡介：', arz_search_url)
                        arzon_list[0] = arz_search_url
                        try:
                            search_html = get_arzon_html(arzon_list)
                        except:
                            print('    >嘗試打開“', arz_search_url, '”搜索頁面失敗，正在嘗試第二次打開...')
                            try:
                                search_html = get_arzon_html(arzon_list)
                                print('    >第二次嘗試成功！')
                            except:
                                fail_times += 1
                                fail_message = '    >第' + str(
                                    fail_times) + '個失敗！連接arzon失敗：' + arz_search_url + '，' + relative_path + '\n'
                                print(fail_message, end='')
                                fail_list.append(fail_message)
                                write_fail(fail_message)
                                plot = '【連接arzon失敗！看到此提示請重新整理nfo！】'
                                break  # 跳出while
                        if plot == '':
                            # <dt><a href="https://www.arzon.jp/item_1376110.html" title="限界集落に越してきた人妻 ～村民"><img src=
                            AVs = re.findall(r'<h2><a href="(/item.+?)" title=', search_html)  # 所有搜索結果鏈接
                            # 搜索結果為N個AV的界面
                            if AVs:  # arzon有搜索結果
                                results_num = len(AVs)
                                for i in range(results_num):
                                    arz_url = 'https://www.arzon.jp' + AVs[i]  # 第i+1個鏈接
                                    arzon_list[0] = arz_url
                                    try:
                                        jav_html = get_arzon_html(arzon_list)
                                    except:
                                        print('    >打開“', arz_url, '”第' + str(i+1) + '個搜索結果失敗，正在嘗試第二次打開...')
                                        try:
                                            jav_html = get_arzon_html(arzon_list)
                                            print('    >第二次嘗試成功！')
                                        except:
                                            fail_times += 1
                                            fail_message = '    >第' + str(
                                                fail_times) + '個失敗！無法進入第' + str(i+1) + '個搜索結果：' + arz_url + '，' + relative_path + '\n'
                                            print(fail_message, end='')
                                            fail_list.append(fail_message)
                                            write_fail(fail_message)
                                            plot = '【連接arzon失敗！看到此提示請重新整理nfo！】'
                                            break  # 跳出for AVs
                                    if plot == '':
                                        # 在該arz_url網頁上查找簡介
                                        plotg = re.search(r'<h2>作品紹介</h2>([\s\S]*?)</div>', jav_html)
                                        # 成功找到plot
                                        if str(plotg) != 'None':
                                            plot_br = plotg.group(1)
                                            plot = ''
                                            for line in plot_br.split('<br />'):
                                                line = line.strip()
                                                plot += line
                                            plot = plot.replace('\n', '').replace('&', '和').replace('/', '#')\
                                                .replace('/', '#').replace(':', '：').replace('*', '#').replace('?', '？')\
                                                .replace('"', '#').replace('<', '【').replace('>', '】')\
                                                .replace('|', '#').replace('＜', '【').replace('＞', '】')\
                                                .replace('〈', '【').replace('〉', '】').replace('＆', '和').replace('\t', '').replace('\r', '')
                                            # 系列<a href="/itemlist.html?mkr=10149&series=43">麗しのノーブラ先生</a>
                                            seriesg = re.search(r'series=\d+">(.+?)</a>', jav_html)
                                            if str(seriesg) != 'None':
                                                series = nfo_dict['系列'] = seriesg.group(1)
                                            else:
                                                nfo_dict['系列'] = '未知系列'
                                            break  # 跳出for AVs
                                # 幾個搜索結果查找完了，也沒有找到簡介
                                if plot == '':
                                    plot = '【arzon有該影片，但找不到簡介】'
                                    fail_times += 1
                                    fail_message = '    >arzon有' + str(results_num) + '個搜索結果：' + arz_search_url + '，但找不到簡介！：' + relative_path + '\n'
                                    print(fail_message, end='')
                                    fail_list.append(fail_message)
                                    write_fail(fail_message)
                                break  # 跳出while
                            # arzon返回的頁面實際是18歲驗證
                            else:
                                adultg = re.search(r'１８歳未満', search_html)
                                if str(adultg) != 'None':
                                    fail_times += 1
                                    fail_message = '    >第' + str(
                                        fail_times) + '個失敗！arzon成人驗證，請重啟程序：' + relative_path + '\n'
                                    print(fail_message, end='')
                                    fail_list.append(fail_message)
                                    write_fail(fail_message)
                                    os.system('pause')
                                else:  # 不是成人驗證，也沒有簡介
                                    fail_times += 1
                                    fail_message = '    >第' + str(
                                        fail_times) + '個失敗！arzon找不到該影片簡介，可能被下架：' + arz_search_url + '，' + relative_path + '\n'
                                    print(fail_message, end='')
                                    fail_list.append(fail_message)
                                    write_fail(fail_message)
                                    plot = '【影片下架，再無簡介】'
                                    break  # 跳出while
                    if if_tran == '是':
                        plot = tran(ID, SK, plot, t_lang)
                #######################################################################

                # 1重命名視頻
                new_mp4 = file[:-len(video_type)].rstrip(' ')
                if if_mp4 == '是':
                    new_mp4 = ''                   # 新文件名
                    for j in rename_mp4_list:
                        new_mp4 += nfo_dict[j]
                    new_mp4 = new_mp4.rstrip(' ')  # 去除末尾空格，否則windows會自動刪除空格，導致程序仍以為帶空格
                    cd_msg = ''
                    if cars_dic[car_num] > 1:      # 是CD1還是CDn？
                        cd_msg = part_prefix + str(srt.episodes)
                        new_mp4 += cd_msg
                    # rename mp4
                    os.rename(root + '/' + file, root + '/' + new_mp4 + video_type)
                    # file發生了變化
                    file = new_mp4 + video_type
                    print('    >修改文件名' + cd_msg + '完成')
                    # 重命名字幕
                    if subt_name and if_rename_subt == '是':
                        os.rename(root + '/' + subt_name, root + '/' + new_mp4 + subt_type)
                        subt_name = new_mp4 + subt_type
                        print('    >修改字幕名完成')

                # nfo_dict['視頻']用於圖片的命名
                nfo_dict['視頻'] = new_mp4

                # 1.5 歸類影片，只針對影片
                if if_classify == '是' and file_folder != '文件夾':
                    # 需要歸類影片，針對這個影片
                    class_root = classify_root + '/'
                    # 移動的目標文件夾
                    for j in classify_list:
                        class_root += nfo_dict[j].rstrip(' .')  # C:/Users/JuneRain/Desktop/測試文件夾/1/葵司/
                    new_root = class_root                    # 新的影片的目錄路徑，C:/Users/JuneRain/Desktop/測試文件夾/1/葵司/
                    new_folder = new_root.split('/')[-1]    # 新的影片的目錄名稱，變成了目標目錄“葵司”
                    if not os.path.exists(new_root):
                        os.makedirs(new_root)
                    jav_new_path = new_root + '/' + file   # 新的影片路徑
                    if not os.path.exists(jav_new_path):    # 目標文件夾沒有相同的影片
                        os.rename(root + '/' + file, jav_new_path)
                        print('    >歸類影片文件完成')
                        if subt_name:
                            os.rename(root + '/' + subt_name, new_root + '/' + subt_name)
                            print('    >歸類字幕文件完成')
                    else:
                        fail_times += 1
                        fail_message = '    >第' + str(
                            fail_times) + '個失敗！歸類失敗，重複的影片，歸類的目標文件夾已經存在相同的影片：' + jav_new_path + '\n'
                        print(fail_message, end='')
                        fail_list.append(fail_message)
                        write_fail(fail_message)
                        continue
                else:
                    new_root = root                    # 當前影片的目錄路徑，在下面的重命名操作中將發生變化
                    new_folder = root.split('/')[-1]  # 當前影片的目錄名稱，在下面的重命名操作中即將發生變化

                # 2重命名文件夾
                if if_folder == '是':                   # 如果是針對“文件”歸類，這一步會被跳過
                    # 新文件夾名new_folder
                    new_folder = ''
                    for j in rename_folder_list:
                        new_folder += (nfo_dict[j])
                    new_folder = new_folder.rstrip(' .')  # 去除末尾空格和“.”，否則windows會自動刪除它們，導致程序仍以為帶空格和“.”
                    if separate_folder:                  # 是獨立文件夾，才會重命名文件夾
                        if cars_dic[car_num] == 1 or (cars_dic[car_num] > 1 and cars_dic[car_num] == srt.episodes):
                            # 同一車牌有多部，且這是最後一部，才會重命名
                            newroot_list = root.split('/')
                            del newroot_list[-1]
                            upper2_root = '/'.join(newroot_list)         # 當前文件夾的上級目錄
                            new_root = upper2_root + '/' + new_folder    # 上級目錄+新目錄名稱=新目錄路徑
                            if not os.path.exists(new_root) or new_root == root:              # 目標影片文件夾不存在，或者目標影片文件夾存在，但就是現在的文件夾，即新舊相同
                                # 修改文件夾
                                os.rename(root, new_root)
                                print('    >重命名文件夾完成')
                            else:                             # 已經有一個那樣的文件夾了
                                fail_times += 1
                                fail_message = '    >第' + str(
                                    fail_times) + '個失敗！重命名文件夾失敗，重複的影片，已存在相同文件夾：' + relative_path + file + '\n'
                                print(fail_message, end='')
                                fail_list.append(fail_message)
                                write_fail(fail_message)
                                continue
                    else:        # 不是獨立，還有其他影片
                        if not os.path.exists(root + '/' + new_folder):   # 準備建個新的文件夾，確認沒有同名文件夾
                            os.makedirs(root + '/' + new_folder)
                        # 放進獨立文件夾
                        os.rename(root + '/' + file, root + '/' + new_folder + '/' + file)
                        new_root = root + '/' + new_folder                # 更新new_root 當前非獨立的目錄+新目錄名稱=新獨立的文件夾
                        print('    >創建獨立的文件夾完成')
                        # 移動字幕
                        if subt_name:
                            os.rename(root + '/' + subt_name, root + '/' + new_folder + '/' + subt_name)
                            print('    >移動字幕到獨立文件夾')

                # 更新一下relative_path
                relative_path = '/' + new_root.lstrip(path) + '/' + file  # 影片的相對於所選文件夾的路徑，用於報錯

                # 3寫入nfo開始
                if if_nfo == '是':
                    cus_title = ''
                    for i in title_list:
                        cus_title += nfo_dict[i]
                    # 開始寫入nfo，這nfo格式是參考的kodi的nfo
                    info_path = new_root + '/' + new_mp4 + '.nfo'      #nfo存放的地址
                    f = open(info_path, 'w', encoding="utf-8")
                    f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>\n"
                            "<movie>\n"
                            "  <plot>" + plot + plot_review + "</plot>\n"
                            "  <title>" + cus_title + "</title>\n"
                            "  <director>" + nfo_dict['導演'] + "</director>\n"
                            "  <rating>" + nfo_dict['評分'] + "</rating>\n"
                            "  <criticrating>" + criticrating + "</criticrating>\n"
                            "  <year>" + nfo_dict['發行年份'] + "</year>\n"
                            "  <mpaa>NC-17</mpaa>\n"                            
                            "  <customrating>NC-17</customrating>\n"
                            "  <countrycode>JP</countrycode>\n"
                            "  <premiered>" + nfo_dict['發行年月日'] + "</premiered>\n"
                            "  <release>" + nfo_dict['發行年月日'] + "</release>\n"
                            "  <runtime>" + nfo_dict['片長'] + "</runtime>\n"
                            "  <country>日本</country>\n"
                            "  <studio>" + nfo_dict['片商'] + "</studio>\n"
                            "  <id>" + nfo_dict['車牌'] + "</id>\n"
                            "  <num>" + nfo_dict['車牌'] + "</num>\n"
                            "  <set>" + series + "</set>\n"
                            "  <userrating>" + nfo_dict['userrating'] + "</userrating>\n")
                    for i in genres:
                        f.write("  <genre>" + i + "</genre>\n")
                    if series:
                        f.write("  <genre>系列:" + series + "</genre>\n")
                    f.write("  <genre>片商:" + nfo_dict['片商'] + "</genre>\n")
                    for i in genres:
                        f.write("  <tag>" + i + "</tag>\n")
                    if series:
                        f.write("  <tag>系列:" + series + "</tag>\n")
                    f.write("  <tag>片商:" + nfo_dict['片商'] + "</tag>\n")
                    for i in actors:
                        f.write("  <actor>\n    <name>" + i + "</name>\n    <type>Actor</type>\n  </actor>\n")
                    f.write("</movie>\n")
                    f.close()
                    print('    >nfo收集完成')

                # 4需要兩張圖片
                if if_jpg == '是':
                    # 下載海報的地址 cover
                    cover_url = 'http:' + cover_url
                    # print(cover_url.replace('pics.dmm.co.jp', 'jp.netcdn.space'))   有人向我建議用avmoo的圖片地址代替dmm
                    # fanart和poster路徑
                    fanart_path = new_root + '/'
                    poster_path = new_root + '/'
                    for i in fanart_list:
                        fanart_path += nfo_dict[i]
                    for i in poster_list:
                        poster_path += nfo_dict[i]
                    # 下載 海報
                    print('    >正在下載封面：', cover_url)
                    cover_list[0] = 0
                    cover_list[1] = cover_url
                    cover_list[2] = fanart_path
                    try:
                        download_pic(cover_list)
                        print('    >fanart.jpg下載成功')
                    except:
                        print('    >從javlibrary下載fanart.jpg失敗，正在前往javbus...')
                        # 在javbus上找圖片url
                        bus_search_url = bus_url + nfo_dict['車牌']
                        jav_list[0] = bus_search_url
                        try:
                            bav_html = get_jav_html(jav_list)
                        except:
                            fail_times += 1
                            fail_message = '    >第' + str(
                                fail_times) + '個失敗！連接javbus失敗，下載fanart失敗：' + bus_search_url + '，' + relative_path + '\n'
                            print(fail_message, end='')
                            fail_list.append(fail_message)
                            write_fail(fail_message)
                            continue
                        # DVD封面cover
                        coverg = re.search(r'<a class="bigImage" href="(.+?)">', bav_html)
                        if str(coverg) != 'None':
                            cover_url = coverg.group(1)
                            cover_list[0] = 0
                            cover_list[1] = cover_url
                            cover_list[2] = fanart_path
                            print('    >正在從javbus下載封面：', cover_url)
                            try:
                                download_pic(cover_list)
                                print('    >fanart.jpg下載成功')
                            except:
                                fail_times += 1
                                fail_message = '    >第' + str(fail_times) + '個失敗！下載fanart.jpg失敗：' + cover_url + '，' + relative_path + '\n'
                                print(fail_message, end='')
                                fail_list.append(fail_message)
                                write_fail(fail_message)
                                continue
                        else:
                            fail_times += 1
                            fail_message = '    >第' + str(
                                fail_times) + '個失敗！從javbus上查找封面失敗：' + bus_search_url + '，' + relative_path + '\n'
                            print(fail_message, end='')
                            fail_list.append(fail_message)
                            write_fail(fail_message)
                            continue
                    # 裁剪生成 poster
                    img = Image.open(fanart_path)
                    w, h = img.size                        # fanart的寬 高
                    ex = int(w*0.52625)                    # 0.525是海報寬（800-379）/800原長
                    poster = img.crop((ex, 0, w, h))       # （ex，0）是左下角（x，y）座標 （w, h)是右上角（x，y）座標
                    poster.save(poster_path, quality=95)   # quality=95 是無損crop，如果不設置，默認75
                    print('    >poster.jpg裁剪成功')

                # 5收集女優頭像
                if if_sculpture == '是':
                    if actors[0] == '未知演員':
                        print('    >未知演員')
                    else:
                        for each_actor in actors:
                            exist_actor_path = actors_source + '/' + each_actor + '.jpg'  # 事先準備好的女優頭像路徑
                            # print(exist_actor_path)
                            jpg_type = '.jpg'
                            if not os.path.exists(exist_actor_path):                # 女優jpg圖片還沒有
                                exist_actor_path = actors_source + '/' + each_actor + '.png'
                                if not os.path.exists(exist_actor_path):            # 女優png圖片還沒有
                                    fail_times += 1
                                    fail_message = '    >第' + str(
                                        fail_times) + '個失敗！沒有女優頭像：' + each_actor + '，' + relative_path + '\n'
                                    print(fail_message, end='')
                                    fail_list.append(fail_message)
                                    write_fail(fail_message)
                                    config_actor = configparser.ConfigParser()
                                    config_actor.read('【缺失的女優頭像統計For Kodi】.ini', encoding='utf-8-sig')
                                    try:
                                        each_actor_times = config_actor.get('缺失的女優頭像', each_actor)
                                        config_actor.set("缺失的女優頭像", each_actor, str(int(each_actor_times) + 1))
                                    except:
                                        config_actor.set("缺失的女優頭像", each_actor, '1')
                                    config_actor.write(open('【缺失的女優頭像統計For Kodi】.ini', "w", encoding='utf-8-sig'))
                                    continue
                                else:
                                    jpg_type = '.png'
                            actors_path = new_root + '/.actors/'                    # 已經收錄了這個女優頭像
                            if not os.path.exists(actors_path):
                                os.makedirs(actors_path)
                            shutil.copyfile(actors_source + '/' + each_actor + jpg_type,
                                            actors_path + each_actor + jpg_type)       # 複製一份到“.actors”
                            print('    >女優頭像收集完成：', each_actor)

                # 6歸類影片，針對文件夾
                if if_classify == '是' and file_folder == '文件夾' and (
                        cars_dic[car_num] == 1 or (cars_dic[car_num] > 1 and cars_dic[car_num] == srt.episodes)):
                    # 需要移動文件夾，且，是該影片的最後一集
                    if separate_folder and classify_root.startswith(root):      # 用户選擇的文件夾是一部影片的獨立文件夾，為了避免在這個文件夾裏又建立新的獨立文件夾
                        print('    >無法歸類，請選擇該文件夾的上級目錄作它的歸類根目錄', root.lstrip(path))
                        continue
                    class_root = classify_root + '/'
                    # 移動的目標文件夾
                    for j in classify_list:
                        class_root += nfo_dict[j].rstrip(' .')  # C:/Users/JuneRain/Desktop/測試文件夾/1/葵司/
                    new_new_root = class_root + new_folder  # 移動的目標文件夾 C:/Users/JuneRain/Desktop/測試文件夾/1/葵司/【葵司】AVOP-127
                    if not os.path.exists(new_new_root):
                        os.makedirs(new_new_root)
                        jav_files = os.listdir(new_root)
                        for i in jav_files:
                            os.rename(new_root + '/' + i, new_new_root + '/' + i)
                        os.rmdir(new_root)
                        print('    >歸類文件夾完成')
                    else:
                        fail_times += 1
                        fail_message = '    >第' + str(fail_times) + '個失敗！歸類失敗，重複的影片，歸類的目標目錄已存在相同文件夾：' + new_new_root + '\n'
                        print(fail_message, end='')
                        fail_list.append(fail_message)
                        write_fail(fail_message)
                        continue

            except:
                fail_times += 1
                fail_message = '    >第' + str(fail_times) + '個失敗！發生錯誤，如一直在該影片報錯請截圖並聯系作者：' + relative_path + '\n'\
                               + traceback.format_exc() + '\n'
                print(fail_message, end='')
                fail_list.append(fail_message)
                write_fail(fail_message)
                continue
    # 完結撒花
    print('\n當前文件夾完成，', end='')
    if fail_times > 0:
        print('失敗', fail_times, '個!  ', path, '\n')
        if len(fail_list) > 0:
            for fail in fail_list:
                print(fail, end='')
        print('\n“【記得清理它】失敗記錄.txt”已記錄錯誤\n')
    else:
        print('沒有處理失敗的AV，幹得漂亮！  ', path, '\n')
    # os.system('pause')
    start_key = 'skip'
