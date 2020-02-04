# -*- coding:utf-8 -*-
import requests, re, sys, os, shutil, configparser, time, hashlib, json, traceback
from PIL import Image
from time import sleep
from tkinter import filedialog, Tk
from shutil import copyfile


# 功能為記錄錯誤txt
def write_fail(fail_m):
    record_txt = open('【記得清理它】失敗記錄.txt', 'a', encoding="utf-8")
    record_txt.write(fail_m)
    record_txt.close()


# get_directory功能為獲取用户選取的文件夾路徑
def get_directory():
    if os.path.exists(sys.argv[1]):
        path = os.path.abspath(sys.argv[1])
    else:
        print("Cannot find " + sys.argv[1])
        exit()
    return path


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
        return '無法翻譯該標題作簡介，請自行翻譯。'
    except:
        print('    >正在嘗試重新日譯中...')
        return tran(api_id, key, word, to_lang)


# 獲取網頁源碼，返回網頁text；假裝python的“重載”函數
def get_jav_html(url_list):
    if len(url_list) == 2:
        return requests.post(url_list[0], data=url_list[1], headers=headers, timeout=10).text
    else:
        return requests.post(url_list[0], data=url_list[1], proxies=url_list[2], headers=headers, timeout=10).text


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
        raise Exception('    >下載多次，仍然失敗')

def nfo_exist(files):
    return next((True for f in files if f.endswith('nfo')), False)

# 每一部jav的“結構體”
class JavFile(object):
    def __init__(self):
        self.name = 'ABC-123.mp4'  # 文件名
        self.car = 'ABC-123'  # 車牌
        self.episodes = 0     # 第幾集
        self.subt = ''        # 字幕文件名  ABC-123.srt


# 讀取配置文件
print('1、請開啟代理，建議美國節點，訪問“https://www.jav321.com/”\n'
      '2、影片信息沒有導演，沒有演員頭像，可能沒有演員姓名\n'
      '3、如有素人車牌識別不出，請在ini中添加該車牌\n')
print('正在讀取ini中的設置...', end='')
try:
    config_settings = configparser.ConfigParser()
    config_settings.read('ini的設置會影響所有exe的操作結果.ini', encoding='utf-8-sig')
    if_nfo = config_settings.get("收集nfo", "是否收集nfo？")
    if_exnfo = config_settings.get("收集nfo", "是否跳過已存在nfo的文件夾？")
    custom_title = config_settings.get("收集nfo", "nfo中title的格式")
    if_jpg = config_settings.get("下載封面", "是否下載封面海報？")
    custom_fanart = config_settings.get("下載封面", "DVD封面的格式")
    custom_poster = config_settings.get("下載封面", "海報的格式")
    if_mp4 = config_settings.get("重命名影片", "是否重命名影片？")
    rename_mp4 = config_settings.get("重命名影片", "重命名影片的格式")
    if_folder = config_settings.get("修改文件夾", "是否重命名或創建獨立文件夾？")
    rename_folder = config_settings.get("修改文件夾", "新文件夾的格式")
    if_rename_subt = config_settings.get("字幕文件", "是否重命名已有的字幕文件")
    if_classify_subt = config_settings.get("字幕文件", "是否使用字幕庫")
    if_classify = config_settings.get("歸類影片", "是否歸類影片？")
    file_folder = config_settings.get("歸類影片", "針對文件還是文件夾？")
    classify_root = config_settings.get("歸類影片", "歸類的根目錄")
    classify_basis = config_settings.get("歸類影片", "歸類的標準")
    if_proxy = config_settings.get("代理", "是否使用代理？")
    proxy = config_settings.get("代理", "代理IP及端口")
    if_tran = config_settings.get("百度翻譯API", "是否翻譯為中文？")
    ID = config_settings.get("百度翻譯API", "APP ID")
    SK = config_settings.get("百度翻譯API", "密鑰")
    simp_trad = config_settings.get("其他設置", "簡繁中文？")
    suren_pref = config_settings.get("其他設置", "素人車牌(若有新車牌請自行添加)")
    file_type = config_settings.get("其他設置", "掃描文件類型")
    title_len = int(config_settings.get("其他設置", "重命名中的標題長度（50~150）"))
    subt_words = config_settings.get("原影片文件的性質", "是否中字即文件名包含")
    custom_subt = config_settings.get("原影片文件的性質", "是否中字的表現形式")
    xx_words = config_settings.get("原影片文件的性質", "是否xx即文件名包含")
    custom_xx = config_settings.get("原影片文件的性質", "是否xx的表現形式")
    movie_type = config_settings.get("原影片文件的性質", "素人")
except:
    print(traceback.format_exc())
    print('\n無法讀取ini文件，請修改它為正確格式，或者打開“【ini】重新創建ini.exe”創建全新的ini！')
    os.system('pause')
print('\n讀取ini文件成功! ')

# 歸類文件夾具有最高決定權
if if_classify == '是':            # 如果需要歸類
    if file_folder == '文件夾':    # 並且是針對文件夾
        if_folder = '是'           # 那麼必須重命名文件夾或者創建新的文件夾
    else:
        if_folder = '否'           # 否則不會操作新文件夾
# 簡繁
if simp_trad == '簡':  # https://tw.jav321.com/video/ssni00643
    url = 'https://www.jav321.com/search'
    t_lang = 'zh'          # 百度翻譯，日譯簡中
else:
    url = 'https://tw.jav321.com/search'
    t_lang = 'cht'
# 確認：代理哪些站點
proxies = {"http": "http://" + proxy, "https": "https://" + proxy}
if if_proxy == '是' and proxy != '':      # 是否需要代理，設置requests請求時的狀態
    jav_list = [url, {}, proxies]              # 代理javbus
    cover_list = [0, '', '', proxies]        # 代理javbus上的圖片  0錯誤次數  1圖片url  2圖片路徑  3proxies
else:
    jav_list = [url, {}]
    cover_list = [0, '', '']
# 初始化其他
nfo_dict = {'空格': ' ', '車牌': 'ABC-123', '標題': '未知標題', '完整標題': '完整標題',
            '發行年月日': '1970-01-01', '發行年份': '1970', '月': '01', '日': '01',
            '片商': '未知片商', '評分': '0', '首個女優': '未知演員', '全部女優': '未知演員',
            '片長': '0', '/': '/', '是否中字': custom_subt, '視頻': 'ABC-123', '車牌前綴': 'ABC',
            '是否xx': custom_xx, '影片類型': movie_type, '系列': '未知系列'}  # 用於暫時存放影片信息，女優，標題等
suren_list = suren_pref.split('、')
rename_mp4_list = rename_mp4.split('+')
rename_folder_list = rename_folder.split('+')
type_tuple = tuple(file_type.split('、'))
classify_basis_list = classify_basis.split('/')
title_list = custom_title.replace('標題', '完整標題', 1).split('+')
fanart_list = custom_fanart.split('+')
poster_list = custom_poster.split('+')
word_list = subt_words.split('、')
xx_list = xx_words.split('、')
for j in rename_mp4_list and rename_folder_list:
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
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}  # 偽裝成瀏覽器瀏覽網頁

start_key = ''
while start_key == '':
    # 用户選擇文件夾
    print('請選擇要整理的文件夾：', end='')
    path = get_directory()
    print(path)
    write_fail('已選擇文件夾：' + path + '\n')
    print('...文件掃描開始...如果時間過長...請避開中午夜晚高峯期...\n')
    #
    if if_classify == '是':
        classify_root = classify_root.rstrip('/')
        if classify_root != '所選文件夾':
            if classify_root != path:  # 歸類根目錄和所選不一樣，繼續核實歸類根目錄和所選不一樣的合法性
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
    #
    fail_times = 0  # 處理過程中錯失敗的個數
    fail_list = []  # 用於存放處理失敗的信息
    # 【當前路徑】 【子目錄】 【文件】
    for root, dirs, files in os.walk(path):
        if if_classify == '是' and root.startswith(classify_root):
            # print('>>該文件夾在歸類的根目錄中，跳過處理...', root)
            continue
        if if_exnfo == '是' and files and nfo_exist(files):
            continue
        # 對這一層文件夾進行評估,有多少視頻，有多少同車牌視頻，是不是獨立文件夾
        jav_videos = []        # 存放：需要整理的jav的結構體
        cars_dic = {}          # car 車牌
        videos_num = 0        # 當前文件夾中視頻的數量，可能有視頻不是jav
        subtitles = False      # 有沒有字幕
        subts_dict = {}          # 存放：jav的字幕文件{'路徑': '文件中的車牌'}
        for raw_file in files:
            # 判斷文件是不是字幕文件
            if raw_file.endswith(('.srt', '.vtt', '.ass', '.ssa',)):
                srt_g = re.search(r'([a-zA-Z]{2,7})-? ?_?(\d{2,6})', raw_file)  # 這個正則表達式匹配“車牌號”可能有點奇怪，
                if str(srt_g) != 'None':  # 如果你下過上千部片，各種參差不齊的命名，你就會理解我了。
                    num_pref = srt_g.group(1).upper()
                    if num_pref in suren_list:
                        num_suf = srt_g.group(2)
                        car_num = num_pref + '-' + num_suf
                        subts_dict[raw_file] = car_num
                continue
        # print(subts_dict)
        # print('>>掃描字幕文件完畢！')
        for raw_file in files:
            # 判斷是不是視頻，得到車牌號
            if raw_file.endswith(type_tuple) and not raw_file.startswith('.'):
                video_num_g = re.search(r'([a-zA-Z]{2,7})-? ?_?(\d{2,6})', raw_file)
                if str(video_num_g) != 'None':
                    num_pref = video_num_g.group(1)
                    num_pref = num_pref.upper()
                    if num_pref in suren_list:
                        num_suf = video_num_g.group(2)
                        car_num = num_pref + '-' + num_suf
                        if car_num not in cars_dic:
                            cars_dic[car_num] = 1
                        else:
                            cars_dic[car_num] += 1
                        jav_file = JavFile()
                        jav_file.car = car_num
                        jav_file.name = raw_file
                        jav_file.episodes = cars_dic[car_num]
                        if car_num in subts_dict.values():
                            jav_file.subt = list(subts_dict.keys())[list(subts_dict.values()).index(car_num)]
                            del subts_dict[jav_file.subt]
                        jav_videos.append(jav_file)
                    else:
                        continue
                else:
                    continue
            else:
                continue
        if cars_dic:
            if len(cars_dic) > 1 or videos_num > len(jav_videos) or len(dirs) > 1 or (
                    len(dirs) == 1 and dirs[0] != '.actors'):
                # 當前文件夾下， 車牌不止一個，還有其他非jav視頻，有其他文件夾
                separate_folder = False
            else:
                separate_folder = True
        else:
            continue

        # 正式開始
        for srt in jav_videos:
            car_num = srt.car
            file = srt.name
            relative_path = '/' + root.lstrip(path) + '/' + file  # 影片的相對於所選文件夾的路徑，用於報錯
            try:
                # 獲取nfo信息的jav321搜索網頁
                jav_list[1] = {'sn': car_num}
                try:
                    jav_html = get_jav_html(jav_list)
                except:
                    print('>>嘗試打開jav321搜索頁面失敗，正在嘗試第二次打開...')
                    try:
                        jav_html = get_jav_html(jav_list)
                        print('    >第二次嘗試成功！')
                    except:
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '個失敗！連接jav321失敗，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                # 嘗試找標題
                titleg = re.search(r'<h3>(.+?) <small>', jav_html)  # 匹配處理“標題”
                # 搜索結果就是AV的頁面
                if str(titleg) != 'None':
                    only_title = titleg.group(1)
                    # print(only_title)
                # 找不到標題，jav321找不到影片
                else:
                    fail_times += 1
                    fail_message = '第' + str(fail_times) + '個失敗！找不到該車牌的影片：' + relative_path + '\n'
                    print('>>' + fail_message, end='')
                    fail_list.append('    >' + fail_message)
                    write_fail('    >' + fail_message)
                    continue

                # 影片的一些屬性
                video_type = '.' + file.split('.')[-1]  # 文件類型，如：.mp4
                subt_name = srt.subt
                if subt_name:
                    subtitles = True
                    subt_type = '.' + subt_name.split('.')[-1]  # 文件類型，如：.srt
                else:
                    subtitles = False
                    subt_type = ''
                nfo_dict['是否中字'] = ''
                if not subtitles:  # 沒有外掛字幕
                    for i in word_list:
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
                # 正則匹配 影片信息 開始
                # 車牌號
                nfo_dict['車牌'] = re.search(r'番.</b>: (.+?)<br>', jav_html).group(1).upper()
                nfo_dict['車牌前綴'] = nfo_dict['車牌'].split('-')[0]
                # 去除title中的特殊字符
                only_title = only_title.replace('\n', '').replace('&', '和').replace('/', '#') \
                    .replace('/', '#').replace(':', '：').replace('*', '#').replace('?', '？') \
                    .replace('"', '#').replace('<', '【').replace('>', '】') \
                    .replace('|', '#').replace('＜', '【').replace('＞', '】') \
                    .replace('〈', '【').replace('〉', '】').replace('＆', '和').replace('\t', '').replace('\r', '')
                # 素人的title開頭不是車牌
                title = nfo_dict['車牌'] + ' ' + only_title
                print('>>正在處理：', title)
                # 處理標題過長
                nfo_dict['完整標題'] = only_title
                if len(only_title) > title_len:
                    nfo_dict['標題'] = only_title[:title_len]
                else:
                    nfo_dict['標題'] = only_title
                # 片商</b>: <a href="/company/%E83%A0%28PRESTIGE+PREMIUM%29/1">プレステージプレミアム(PRESTIGE PREMIUM)</a>
                studiog = re.search(r'<a href="/company.+?">(.+?)</a>', jav_html)
                if str(studiog) != 'None':
                    nfo_dict['片商'] = studiog.group(1)
                else:
                    nfo_dict['片商'] = '未知片商'
                # 上映日 (\d\d\d\d-\d\d-\d\d)</td>
                premieredg = re.search(r'日期</b>: (\d\d\d\d-\d\d-\d\d)<br>', jav_html)
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
                runtimeg = re.search(r'播放..</b>: (\d+)', jav_html)
                if str(runtimeg) != 'None':
                    nfo_dict['片長'] = runtimeg.group(1)
                else:
                    nfo_dict['片長'] = '0'
                # 沒有導演
                # 演員們 和 # 第一個演員   女優</b>: 花音さん 21歳 牀屋さん(家族経営) &nbsp
                actorg = re.search(r'<small>(.+?)</small>', jav_html)
                if str(actorg) != 'None':
                    actor_str = actorg.group(1)
                    actor_list = actor_str.replace('/', ' ').split(' ')  # <small>luxu-071 鬆波優 29歳 システムエンジニア</small>
                    actor_list = [i for i in actor_list if i != '']
                    if len(actor_list) > 3:
                        nfo_dict['首個女優'] = actor_list[1] + ' ' + actor_list[2] + ' ' + actor_list[3]
                    elif len(actor_list) > 1:
                        del actor_list[0]
                        nfo_dict['首個女優'] = ' '.join(actor_list)
                    else:
                        nfo_dict['首個女優'] = '素人'
                    nfo_dict['全部女優'] = nfo_dict['首個女優']
                else:
                    nfo_dict['首個女優'] = nfo_dict['全部女優'] = '素人'
                # print(nfo_dict['全部女優'])
                # 特點
                genres = re.findall(r'genre.+?">(.+?)</a>', jav_html)
                genres = [i for i in genres if i != '標籤' and i != '標籤']
                if nfo_dict['是否中字']:
                    genres.append('中文字幕')
                if nfo_dict['是否xx']:
                    genres.append('無碼流出')
                # 下載封面 cover fanart
                coverg = re.search(r'poster="(.+?)"><source', jav_html)  # 封面圖片的正則對象
                if str(coverg) != 'None':
                    cover_url = coverg.group(1)
                else:  # src="http://pics.dmm.co.jp/digital/amateur/scute530/scute530jp-001.jpg"
                    coverg = re.search(r'img-responsive" src="(.+?)"', jav_html)  # 封面圖片的正則對象
                    if str(coverg) != 'None':
                        cover_url = coverg.group(1)
                    else:  # src="http://pics.dmm.co.jp/digital/amateur/scute530/scute530jp-001.jpg"
                        coverg = re.search(r'src="(.+?)"', jav_html)  # 封面圖片的正則對象
                        if str(coverg) != 'None':
                            cover_url = coverg.group(1)
                        else:
                            cover_url = ''
                # 下載海報 poster
                posterg = re.search(r'img-responsive" src="(.+?)"', jav_html)  # 封面圖片的正則對象
                if str(posterg) != 'None':
                    poster_url = posterg.group(1)
                else:
                    poster_url = ''
                # 評分
                scoreg = re.search(r'評分</b>: (\d\.\d)<br>', jav_html)
                if str(scoreg) != 'None':
                    score = float(scoreg.group(1))
                    score = (score - 2) * 10 / 3
                    if score >= 0:
                        score = '%.1f' % score
                        nfo_dict['評分'] = str(score)
                    else:
                        nfo_dict['評分'] = '0'
                else:
                    scoreg = re.search(r'"/img/(\d\d)\.gif', jav_html)
                    if str(scoreg) != 'None':
                        score = float(scoreg.group(1))/10
                        score = (score - 2) * 10 / 3
                        if score >= 0:
                            score = '%.1f' % score
                            nfo_dict['評分'] = str(score)
                        else:
                            nfo_dict['評分'] = '0'
                    else:
                        nfo_dict['評分'] = '0'
                criticrating = str(float(nfo_dict['評分'])*10)
                # 素人上沒有企劃set
                # 把標題當做plot
                plot = only_title
                if if_nfo == '是' and if_tran == '是':
                    print('    >正在日譯中...')
                    plot = tran(ID, SK, title, t_lang)

                # 1重命名視頻
                new_mp4 = file[:-len(video_type)].rstrip(' ')
                if if_mp4 == '是':
                    # 新文件名new_mp4
                    new_mp4 = ''
                    # print(nfo_dict['完整標題'])
                    for j in rename_mp4_list:
                        new_mp4 += nfo_dict[j]
                    new_mp4 = new_mp4.rstrip(' ')
                    cd_msg = ''
                    if cars_dic[car_num] > 1:  # 是CD1還是CDn？
                        cd_msg = '-cd' + str(srt.episodes)
                        new_mp4 += cd_msg
                    # rename 文件名
                    os.rename(root + '/' + file, root + '/' + new_mp4 + video_type)
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
                        class_root += nfo_dict[j].rstrip(' .')      # C:/Users/JuneRain/Desktop/測試文件夾/1/葵司/
                    new_root = class_root              # 新的影片的目錄路徑，C:/Users/JuneRain/Desktop/測試文件夾/1/葵司/
                    new_folder = new_root.split('/')[-1]  # 新的影片的目錄名稱，變成了目標目錄“葵司”
                    if not os.path.exists(new_root):   # 不存在目標文件夾
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
                    new_root = root  # 當前影片的目錄路徑，在下面的重命名操作中將發生變化
                    new_folder = root.split('/')[-1]  # 當前影片的目錄名稱，在下面的重命名操作中即將發生變化

                # 2重命名文件夾
                if if_folder == '是':
                    # 新文件夾名rename_folder
                    new_folder = ''
                    for j in rename_folder_list:
                        new_folder += (nfo_dict[j])
                    new_folder = new_folder.rstrip(' .')
                    if separate_folder:
                        if cars_dic[car_num] == 1 or (
                                cars_dic[car_num] > 1 and cars_dic[car_num] == srt.episodes):  # 同一車牌有多部，且這是最後一部，才會重命名
                            newroot_list = root.split('/')
                            del newroot_list[-1]
                            upper2_root = '/'.join(newroot_list)
                            new_root = upper2_root + '/' + new_folder  # 當前文件夾就會被重命名
                            if not os.path.exists(
                                    new_root) or new_root == root:  # 目標影片文件夾不存在，或者目標影片文件夾存在，但就是現在的文件夾，即新舊相同
                                # 修改文件夾
                                os.rename(root, new_root)
                                print('    >重命名文件夾完成')
                            else:  # 已經有一個那樣的文件夾了
                                fail_times += 1
                                fail_message = '    >第' + str(
                                    fail_times) + '個失敗！重命名文件夾失敗，重複的影片，已存在相同文件夾：' + relative_path + file + '\n'
                                print(fail_message, end='')
                                fail_list.append(fail_message)
                                write_fail(fail_message)
                                continue
                    else:
                        if not os.path.exists(root + '/' + new_folder):  # 已經存在目標文件夾
                            os.makedirs(root + '/' + new_folder)
                        # 創建獨立的文件夾完成
                        os.rename(root + '/' + file, root + '/' + new_folder + '/' + file)  # 就把影片放進去
                        new_root = root + '/' + new_folder  # 在當前文件夾下再創建新文件夾
                        print('    >創建獨立的文件夾完成')
                        if subt_name:
                            os.rename(root + '/' + subt_name, root + '/' + new_folder + '/' + subt_name)  # 就把字幕放進去
                            print('    >移動字幕到獨立文件夾')

                # 更新一下relative_path
                relative_path = '/' + new_root.lstrip(path) + '/' + file  # 影片的相對於所選文件夾的路徑，用於報錯

                # 3寫入nfo
                if if_nfo:
                    cus_title = ''
                    for i in title_list:
                        cus_title += nfo_dict[i]
                    # 寫入nfo開始
                    info_path = new_root + '/' + new_mp4 + '.nfo'
                    # 開始寫入nfo
                    f = open(info_path, 'w', encoding="utf-8")
                    f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>\n"
                            "<movie>\n"
                            "  <plot>" + plot + "</plot>\n"
                            "  <title>" + cus_title + "</title>\n"
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
                            "  <num>" + nfo_dict['車牌'] + "</num>\n")
                    for i in genres:
                        f.write("  <genre>" + i + "</genre>\n")
                    f.write("  <genre>片商:" + nfo_dict['片商'] + "</genre>\n")
                    for i in genres:
                        f.write("  <tag>" + i + "</tag>\n")
                    f.write("  <tag>片商:" + nfo_dict['片商'] + "</tag>\n")
                    f.write("  <actor>\n    <name>" + nfo_dict['首個女優'] + "</name>\n    <type>Actor</type>\n  </actor>\n")
                    f.write("</movie>\n")
                    f.close()
                    print("    >nfo收集完成")

                # 4需要兩張圖片
                if if_jpg == '是':
                    # fanart和poster路徑
                    fanart_path = new_root + '/'
                    poster_path = new_root + '/'
                    for i in fanart_list:
                        fanart_path += nfo_dict[i]
                    for i in poster_list:
                        poster_path += nfo_dict[i]
                    # 下載海報的地址 cover
                    print('    >fanart.jpg的鏈接：', cover_url)
                    # 下載 海報
                    cover_list[0] = 0
                    cover_list[1] = cover_url
                    cover_list[2] = fanart_path
                    try:
                        download_pic(cover_list)
                        print('    >fanart.jpg下載成功')
                    except:
                        fail_times += 1
                        fail_message = '    >第' + str(
                            fail_times) + '個失敗！fanart下載失敗：' + cover_url + '，網絡不佳，下載失敗：' + relative_path + '\n'
                        print(fail_message, end='')
                        fail_list.append(fail_message)
                        write_fail(fail_message)
                        continue
                    # 下載poster.jpg   img-responsive" src="https://www.jav321.com/images/prestigepremium/300mium/034/pf_o1_300mium-034.jpg">
                    print('    >poster.jpg的鏈接：', poster_url)
                    cover_list[0] = 0
                    cover_list[1] = poster_url
                    cover_list[2] = poster_path
                    try:
                        download_pic(cover_list)
                        print('    >poster.jpg下載成功')
                    except:
                        fail_times += 1
                        fail_message = '    >第' + str(
                            fail_times) + '個失敗！poster下載失敗：' + relative_path + '\n'
                        print(fail_message, end='')
                        fail_list.append(fail_message)
                        write_fail(fail_message)
                        continue

                # 5收集女優頭像

                # 6歸類影片，針對文件夾
                if if_classify == '是' and file_folder == '文件夾' and (
                        cars_dic[car_num] == 1 or (cars_dic[car_num] > 1 and cars_dic[car_num] == srt.episodes)):
                    # 需要移動文件夾，且，是該影片的最後一集
                    if separate_folder and classify_root.startswith(root):
                        print('    >無法歸類，請選擇該文件夾的上級目錄作它的歸類根目錄', root.lstrip(path))
                        continue
                    class_root = classify_root + '/'
                    # 對歸類標準再細化
                    for j in classify_list:
                        class_root += nfo_dict[j].rstrip(' .')  # C:/Users/JuneRain/Desktop/測試文件夾/1/葵司/
                    new_new_root = class_root + new_folder  # 移動的目標文件夾 C:/Users/JuneRain/Desktop/測試文件夾/1/葵司/【葵司】AVOP-127
                    if not os.path.exists(new_new_root):    # 不存在目標目錄
                        os.makedirs(new_new_root)
                        jav_files = os.listdir(new_root)
                        for i in jav_files:
                            os.rename(new_root + '/' + i, new_new_root + '/' + i)
                        os.rmdir(new_root)
                        print('    >歸類文件夾完成')
                    else:
                        fail_times += 1
                        fail_message = '    >第' + str(fail_times) + '個失敗！歸類失敗，重複的影片，歸類的根目錄已存在相同文件夾：' + new_new_root + '\n'
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

    print('\n當前文件夾完成，', end='')
    if fail_times > 0:
        print('失敗', fail_times, '個!  ', path, '\n')
        if len(fail_list) > 0:
            for fail in fail_list:
                print(fail, end='')
        print('\n“【記得清理它】失敗記錄.txt”已記錄錯誤\n')
    else:
        print('沒有處理失敗的AV，幹得漂亮！  ', path, '\n')

    start_key = 'skip'
