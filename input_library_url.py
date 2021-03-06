# -*- coding:utf-8 -*-
import requests, re, os, configparser, time, hashlib, json, shutil, traceback
from PIL import Image


# 調用百度翻譯API接口
def tran(api_id, key, word, to_lang):
    # init salt and final_sign
    salt = str(time.time())[:10]
    final_sign = api_id + word + salt + key
    final_sign = hashlib.md5(final_sign.encode("utf-8")).hexdigest()
    #表單paramas
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


#  main開始
print('1、避開21:00-1:00，訪問javlibrary和arzon很慢。\n'
      '2、簡體繁體取決於複製粘貼的網址是cn還是tw！\n'
      '3、不要用www.javlibrary.com/xx/xxxx！用防屏蔽地址\n')
# 讀取配置文件，這個ini文件用來給用户設置重命名的格式和jav網址
config_settings = configparser.RawConfigParser()
print('正在讀取ini中的設置...', end='')
try:
    config_settings.read('ini的設置會影響所有exe的操作結果.ini', encoding='utf-8-sig')
    if_nfo = config_settings.get("收集nfo", "是否收集nfo？")
    if_review = config_settings.get("收集nfo", "是否收集javlibrary上的影評？")
    custom_title = config_settings.get("收集nfo", "nfo中title的格式")
    if_mp4 = config_settings.get("重命名影片", "是否重命名影片？")
    rename_mp4 = config_settings.get("重命名影片", "重命名影片的格式")
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
    bus_url = config_settings.get("其他設置", "javbus網址")
    title_len = int(config_settings.get("其他設置", "重命名中的標題長度（50~150）"))
    movie_type = config_settings.get("原影片文件的性質", "有碼")
except:
    print(traceback.format_exc())
    print('\n無法讀取ini文件，請修改它為正確格式，或者打開“【ini】重新創建ini.exe”創建全新的ini！')
    os.system('pause')
# 確認：女優頭像ini及頭像文件夾
if if_sculpture == '是':
    if not os.path.exists('女優頭像'):
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
        print('\n    >“【缺失的女優頭像統計For Kodi】.ini”文件被你玩壞了...正在重寫ini...成功！')
        print('正在重新讀取...', end='')
print('\n讀取ini文件成功! ')
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
    jav_list = ['', proxies]
    arzon_list = ['', acook, proxies]  # 代理arzon
    cover_list = [0, '', '', proxies]  # 代理dmm
else:
    jav_list = ['']
    arzon_list = ['', acook]
    cover_list = [0, '', '']\
# http://www.x39n.com/   https://www.buscdn.work/
if not bus_url.endswith('/'):
    bus_url += '/'
# 確認：百度翻譯，簡繁中文
if simp_trad == '簡':
    t_lang = 'zh'
else:
    t_lang = 'cht'
# 初始化其他
nfo_dict = {'空格': ' ', '車牌': 'ABC-123', '標題': '未知標題', '完整標題': '完整標題', '導演': '未知導演',
            '發行年月日': '1970-01-01', '發行年份': '1970', '月': '01', '日': '01', '是否中字': '', '是否xx': '',
            '片商': '未知片商', '評分': '0', '首個女優': '未知演員', '全部女優': '未知演員', '車牌前綴': 'ABC',
            '片長': '0', '/': '/', '視頻': 'ABC-123', '影片類型': movie_type, '系列': '未知系列'}  # 用於暫時存放影片信息，女優，標題等
rename_mp4_list = rename_mp4.split('+')
title_list = custom_title.replace('標題', '完整標題', 1).split('+')
fanart_list = custom_fanart.split('+')
poster_list = custom_poster.split('+')
for j in rename_mp4_list:
    if j not in nfo_dict:
        nfo_dict[j] = j
for j in title_list:
    if j not in nfo_dict:
        nfo_dict[j] = j
for j in fanart_list:
    if j not in nfo_dict:
        nfo_dict[j] = j
for j in poster_list:
    if j not in nfo_dict:
        nfo_dict[j] = j

root = os.path.join(os.path.expanduser("~"), 'Desktop')
# 獲取nfo信息的javlib搜索網頁
while 1:
    try:
        input_url = input('\n請輸入javlibrary上的某一部影片的網址：')
        print()
        jav_list[0] = input_url
        try:
            javlib_html = get_jav_html(jav_list)
        except:
            print('>>嘗試打開頁面失敗，正在嘗試第二次打開...')
            try:  #用網高峯期，經常打不開javlib，嘗試第二次
                javlib_html = get_jav_html(jav_list)
                print('    >第二次嘗試成功！')
            except:
                print('>>網址正確嗎？打不開啊！')
                continue
        # 搜索結果的網頁，大部分情況就是這個影片的網頁，也有可能是多個結果的網頁
        # 嘗試找標題，第一種情況：找得到，就是這個影片的網頁[a-zA-Z]{1,6}-\d{1,5}.+?
        titleg = re.search(r'<title>(.+?) - JAVLibrary</title>', javlib_html)  # 匹配處理“標題”
        # 搜索結果就是AV的頁面
        if str(titleg) != 'None':
            title = titleg.group(1)
        # 第二種情況：搜索結果可能是兩個以上，所以這種匹配找不到標題，None！
        else:   # 繼續找標題，但匹配形式不同，這是找“可能是多個結果的網頁”上的第一個標題
            print('>>網址正確嗎？找不到影片信息啊！')
            continue

        print('>>正在處理：', title)
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
        # 給用户用的標題是 短的title_easy
        nfo_dict['完整標題'] = car_titleg.group(2)
        # 處理影片的標題過長
        if len(nfo_dict['完整標題']) > title_len:
            nfo_dict['標題'] = nfo_dict['完整標題'][:title_len]
        else:
            nfo_dict['標題'] = nfo_dict['完整標題']
        # 處理特殊車牌 t28-573
        if nfo_dict['車牌'].startswith('T-28'):
            nfo_dict['車牌'] = nfo_dict['車牌'].replace('T-28', 'T28-', 1)
        nfo_dict['車牌前綴'] = nfo_dict['車牌'].split('-')[0]
        # 片商
        studiog = re.search(r'rel="tag">(.+?)</a> &nbsp;<span id="maker_', javlib_html)
        if str(studiog) != 'None':
            nfo_dict['片商'] = studiog.group(1)
        else:
            nfo_dict['片商'] = '未知片商'
        # 上映日
        premieredg = re.search(r'<td class="text">(\d\d\d\d-\d\d-\d\d)</td>', javlib_html)
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
        runtimeg = re.search(r'<td><span class="text">(\d+?)</span>', javlib_html)
        if str(runtimeg) != 'None':
            nfo_dict['片長'] = runtimeg.group(1)
        else:
            nfo_dict['片長'] = '0'
        # 導演
        directorg = re.search(r'rel="tag">(.+?)</a> &nbsp;<span id="director', javlib_html)
        if str(directorg) != 'None':
            nfo_dict['導演'] = directorg.group(1)
        else:
            nfo_dict['導演'] = '未知導演'
        # 演員們 和 # 第一個演員
        actors_prag = re.search(r'<span id="cast(.+?)</td>', javlib_html, re.DOTALL)
        if str(actors_prag) != 'None':
            actors = re.findall(r'rel="tag">(.+?)</a></span> <span id', actors_prag.group(1))
            if len(actors) != 0:
                if len(actors) > 7:
                    actors = actors[:7]
                nfo_dict['首個女優'] = actors[0]
                nfo_dict['全部女優'] = ' '.join(actors)
            else:
                nfo_dict['首個女優'] = nfo_dict['全部女優'] = '未知演員'
                actors = ['未知演員']
        else:
            nfo_dict['首個女優'] = nfo_dict['全部女優'] = '未知演員'
            actors = ['未知演員']
        nfo_dict['標題'] = nfo_dict['標題'].rstrip(nfo_dict['全部女優'])
        # 特點
        genres = re.findall(r'category tag">(.+?)</a>', javlib_html)
        # DVD封面cover
        coverg = re.search(r'src="(.+?)" width="600" height="403"', javlib_html)  # 封面圖片的正則對象
        if str(coverg) != 'None':
            cover_url = coverg.group(1)
        else:
            cover_url = ''
        # 評分
        scoreg = re.search(r'&nbsp;<span class="score">\((.+?)\)</span>', javlib_html)
        if str(scoreg) != 'None':
            score = float(scoreg.group(1))
            score = (score - 4) * 5 / 3     # javlib上稍微有人關注的影片評分都是6分以上（10分制），強行把它差距拉大
            if score >= 0:
                score = '%.1f' % score
                nfo_dict['評分'] = str(score)
            else:
                nfo_dict['評分'] = '0'
        else:
            nfo_dict['評分'] = '0'
        criticrating = str(float(nfo_dict['評分'])*10)
        # javlib的精彩影評   (.+?\s*.*?\s*.*?\s*.*?)  用javlib上的精彩影片，下面的匹配可能很奇怪，沒辦法，就這麼奇怪
        plot_review = ''
        if if_review == '是':
            review = re.findall(r'(hidden">.+?</textarea>)</td>\s*?<td class="scores"><table>\s*?<tr><td><span class="scoreup">\d\d+?</span>', javlib_html, re.DOTALL)
            if len(review) != 0:
                plot_review = '\n【精彩影評】：'
                for rev in review:
                    right_review = re.findall(r'hidden">(.+?)</textarea>', rev, re.DOTALL)
                    if len(right_review) != 0:
                        plot_review = plot_review + right_review[-1].replace('&', '和') + '////'
                        continue
                plot_review = plot_review.replace('\n', '').replace('&', '和').replace('/', '#') \
                    .replace(':', '：').replace('*', '#').replace('?', '？') \
                    .replace('"', '#').replace('<', '【').replace('>', '】') \
                    .replace('|', '#').replace('＜', '【').replace('＞', '】') \
                    .replace('〈', '【').replace('〉', '】').replace('＆', '和').replace('\t', '').replace('\r', '')
        #print(plot_review)
        # 企劃javlib上沒有企劃set
        #######################################################################
        # arzon的簡介
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
                        print('    >連接arzon失敗：' + arz_search_url)
                        plot = '【連接arzon失敗！看到此提示請重新整理nfo！】'
                        break
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
                                print('    >打開“', arz_url, '”第' + str(i + 1) + '個搜索結果失敗，正在嘗試第二次打開...')
                                try:
                                    jav_html = get_arzon_html(arzon_list)
                                    print('    >第二次嘗試成功！')
                                except:
                                    print('    >無法進入第' + str(i + 1) + '個搜索結果：' + arz_url)
                                    plot = '【連接arzon失敗！看到此提示請重新整理nfo！】'
                                    break
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
                                    plot = plot.replace('\n', '').replace('&', '和').replace('/', '#') \
                                        .replace('/', '#').replace(':', '：').replace('*', '#').replace('?', '？') \
                                        .replace('"', '#').replace('<', '【').replace('>', '】') \
                                        .replace('|', '#').replace('＜', '【').replace('＞', '】') \
                                        .replace('〈', '【').replace('〉', '】').replace('＆', '和').replace('\t', '').replace('\r', '')
                                    # 系列<a href="/itemlist.html?mkr=10149&series=43">麗しのノーブラ先生</a>
                                    seriesg = re.search(r'series=\d+">(.+?)</a>', jav_html)
                                    if str(seriesg) != 'None':
                                        series = nfo_dict['系列'] = seriesg.group(1)
                                    else:
                                        nfo_dict['系列'] = '未知系列'
                                    break
                        # 幾個搜索結果查找完了，也沒有找到簡介
                        if plot == '':
                            print('    >arzon有' + str(results_num) + '個搜索結果：' + arz_search_url + '，但找不到簡介！')
                            plot = '【arzon有該影片，但找不到簡介】'
                        break
                    # arzon搜索頁面實際是18歲驗證
                    else:
                        adultg = re.search(r'１８歳未満', search_html)
                        if str(adultg) != 'None':
                            print('    >成人驗證，請重啟程序！')
                            os.system('pause')
                        else:  # 不是成人驗證，也沒有簡介
                            print('    >arzon找不到該影片簡介，可能被下架!')
                            plot = '【影片下架，再無簡介】'
                            break
            if if_tran == '是':
                plot = tran(ID, SK, plot, t_lang)
        #######################################################################
        # 1重命名視頻
        new_mp4 = nfo_dict['車牌']  # 默認為車牌
        if if_mp4 == '是':
            # 新文件名new_mp4
            new_mp4 = ''
            for j in rename_mp4_list:
                new_mp4 += nfo_dict[j]
            new_mp4 = new_mp4.rstrip(' ')

        # nfo_dict['視頻']用於圖片的命名
        nfo_dict['視頻'] = new_mp4
        new_root = root  # 為了能和其他py一樣

        # 2重命名文件夾

        # 3寫入nfo開始
        if if_nfo == '是':
            cus_title = ''
            for i in title_list:
                cus_title += nfo_dict[i]
            # 寫入nfo開始
            info_path = root + '/' + new_mp4 + '.nfo'      #nfo存放的地址
            # 開始寫入nfo，這nfo格式是參考的emby的nfo
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
                    "  <set>" + series + "</set>\n")
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
                f.write("  <actor>\n    <name>" + i + "</name>\n    <type>Actor</type>\n    <thumb></thumb>\n  </actor>\n")
            f.write("</movie>\n")
            f.close()
            print('    >nfo收集完成')

        # 4需要兩張圖片
        if if_jpg == '是':
            # 下載海報的地址 cover
            cover_url = 'http:' + cover_url
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
                    print('    >連接javbus失敗，下載fanart失敗：' + bus_search_url)
                    continue
                # DVD封面cover
                coverg = re.search(r'<a class="bigImage" href="(.+?)">', bav_html)  # 封面圖片的正則對象
                if str(coverg) != 'None':
                    cover_list[0] = 0
                    cover_list[1] = cover_url
                    cover_list[2] = fanart_path
                    print('    >正在從javbus下載封面：', cover_url)
                    try:
                        download_pic(cover_list)
                        print('    >fanart.jpg下載成功')
                    except:
                        print('    >下載fanart.jpg失敗：' + cover_url)
                        continue
                else:
                    print('    >從javbus上查找封面失敗：' + bus_search_url)
                    continue
            # crop
            img = Image.open(fanart_path)
            w, h = img.size                               # fanart的寬 高
            ex = int(w * 0.52625)                         # 0.52625是根據emby的poster寬高比較出來的
            poster = img.crop((ex, 0, w, h))              # （ex，0）是左下角（x，y）座標 （w, h)是右上角（x，y）座標
            poster.save(poster_path, quality=95)          # quality=95 是無損crop，如果不設置，默認75
            print('    >poster.jpg裁剪成功')

        # 5收集女優頭像
        if if_sculpture == '是':
            if actors[0] == '未知演員':
                print('    >未知演員')
            else:
                for each_actor in actors:
                    exist_actor_path = '女優頭像/' + each_actor + '.jpg'
                    # print(exist_actor_path)
                    jpg_type = '.jpg'
                    if not os.path.exists(exist_actor_path):  # 女優jpg圖片還沒有
                        exist_actor_path = '女優頭像/' + each_actor + '.png'
                        if not os.path.exists(exist_actor_path):  # 女優png圖片還沒有
                            print('    >沒有女優頭像：' + each_actor + '\n')
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
                    actors_path = new_root + '/.actors/'
                    if not os.path.exists(actors_path):
                        os.makedirs(actors_path)
                    shutil.copyfile('女優頭像/' + each_actor + jpg_type,
                                    actors_path + each_actor + jpg_type)
                    print('    >女優頭像收集完成：', each_actor)

        print()
    except:
        print('發生錯誤，如一直在該影片報錯請截圖並聯系作者：' + relative_path + '\n' + traceback.format_exc() + '\n')
        continue
