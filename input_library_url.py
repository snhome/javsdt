# -*- coding:utf-8 -*-
import requests, re, os, configparser, time, hashlib, json, shutil, traceback
from PIL import Image


# 调用百度翻译API接口
def tran(api_id, key, word, to_lang):
    # init salt and final_sign
    salt = str(time.time())[:10]
    final_sign = api_id + word + salt + key
    final_sign = hashlib.md5(final_sign.encode("utf-8")).hexdigest()
    #表单paramas
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
        print('    >翻译简介失败，请截图给作者，检查是否有非法字符：', word)
        return '无法翻译该简介，请手动去arzon.jp查找简介并翻译。'
    except:
        print('    >正在尝试重新日译中...')
        return tran(api_id, key, word, to_lang)


# 获取一个arzon_cookie，返回cookie
def get_acook(prox):
    if prox:
        session = requests.Session()
        session.get('https://www.arzon.jp/index.php?action=adult_customer_agecheck&agecheck=1&redirect=https%3A%2F%2Fwww.arzon.jp%2F', proxies=prox, timeout=10)
        return session.cookies.get_dict()
    else:
        session = requests.Session()
        session.get('https://www.arzon.jp/index.php?action=adult_customer_agecheck&agecheck=1&redirect=https%3A%2F%2Fwww.arzon.jp%2F', timeout=10)
        return session.cookies.get_dict()


# 获取网页源码，返回网页text；假装python的“重载”函数
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


# 下载图片，无返回
def download_pic(cov_list):
    # 0错误次数  1图片url  2图片路径  3proxies
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
            print('    >下载失败，重新下载...')
            cov_list[0] += 1
            download_pic(cov_list)
        try:
            Image.open(cov_list[2])
        except OSError:
            print('    >下载失败，重新下载....')
            cov_list[0] += 1
            download_pic(cov_list)
    else:
        raise Exception('    >下载多次，仍然失败！')


#  main开始
print('1、避开21:00-1:00，访问javlibrary和arzon很慢。\n'
      '2、简体繁体取决于复制粘贴的网址是cn还是tw！\n'
      '3、不要用www.javlibrary.com/xx/xxxx！用防屏蔽地址\n')
# 读取配置文件，这个ini文件用来给用户设置重命名的格式和jav网址
config_settings = configparser.RawConfigParser()
print('正在读取ini中的设置...', end='')
try:
    config_settings.read('ini的设置会影响所有exe的操作结果.ini', encoding='utf-8-sig')
    if_nfo = config_settings.get("收集nfo", "是否收集nfo？")
    if_review = config_settings.get("收集nfo", "是否收集javlibrary上的影评？")
    custom_title = config_settings.get("收集nfo", "nfo中title的格式")
    if_mp4 = config_settings.get("重命名影片", "是否重命名影片？")
    rename_mp4 = config_settings.get("重命名影片", "重命名影片的格式")
    if_jpg = config_settings.get("下载封面", "是否下载封面海报？")
    custom_fanart = config_settings.get("下载封面", "DVD封面的格式")
    custom_poster = config_settings.get("下载封面", "海报的格式")
    if_sculpture = config_settings.get("kodi专用", "是否收集女优头像")
    if_proxy = config_settings.get("代理", "是否使用代理？")
    proxy = config_settings.get("代理", "代理IP及端口")
    if_plot = config_settings.get("百度翻译API", "是否需要日语简介？")
    if_tran = config_settings.get("百度翻译API", "是否翻译为中文？")
    ID = config_settings.get("百度翻译API", "APP ID")
    SK = config_settings.get("百度翻译API", "密钥")
    simp_trad = config_settings.get("其他设置", "简繁中文？")
    bus_url = config_settings.get("其他设置", "javbus网址")
    title_len = int(config_settings.get("其他设置", "重命名中的标题长度（50~150）"))
    movie_type = config_settings.get("原影片文件的性质", "有码")
except:
    print(traceback.format_exc())
    print('\n无法读取ini文件，请修改它为正确格式，或者打开“【ini】重新创建ini.exe”创建全新的ini！')
    os.system('pause')
# 确认：女优头像ini及头像文件夹
if if_sculpture == '是':
    if not os.path.exists('女优头像'):
        print('\n“女优头像”文件夹丢失！请把它放进exe的文件夹中！\n')
        os.system('pause')
    if not os.path.exists('【缺失的女优头像统计For Kodi】.ini'):
        config_actor = configparser.ConfigParser()
        config_actor.add_section("缺失的女优头像")
        config_actor.set("缺失的女优头像", "女优姓名", "N(次数)")
        config_actor.add_section("说明")
        config_actor.set("说明", "上面的“女优姓名 = N(次数)”的表达式", "后面的N数字表示你有N部(次)影片都在找她的头像，可惜找不到")
        config_actor.set("说明", "你可以去保存一下她的头像jpg到“女优头像”文件夹", "以后就能保存她的头像到影片的文件夹了")
        config_actor.write(open('【缺失的女优头像统计For Kodi】.ini', "w", encoding='utf-8-sig'))
        print('\n    >“【缺失的女优头像统计For Kodi】.ini”文件被你玩坏了...正在重写ini...成功！')
        print('正在重新读取...', end='')
print('\n读取ini文件成功! ')
# 确认：arzon的cookie，通过成人验证
proxies = {"http": "http://" + proxy, "https": "https://" + proxy}
acook = {}
if if_plot == '是' and if_nfo == '是':
    print('正在尝试通过“https://www.arzon.jp”的成人验证...')
    try:
        if if_proxy == '是' and proxy != '':
            acook = get_acook(proxies)
        else:
            acook = get_acook({})
        print('通过arzon的成人验证！\n')
    except:
        print('连接arzon失败，请避开网络高峰期！请重启程序！\n')
        os.system('pause')
# 确认：代理哪些站点
if if_proxy == '是' and proxy != '':      # 是否需要代理，设置requests请求时的状态
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
# 确认：百度翻译，简繁中文
if simp_trad == '简':
    t_lang = 'zh'
else:
    t_lang = 'cht'
# 初始化其他
nfo_dict = {'空格': ' ', '车牌': 'ABC-123', '标题': '未知标题', '完整标题': '完整标题', '导演': '未知导演',
            '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01', '是否中字': '', '是否xx': '',
            '片商': '未知片商', '评分': '0', '首个女优': '未知演员', '全部女优': '未知演员', '车牌前缀': 'ABC',
            '片长': '0', '/': '/', '视频': 'ABC-123', '影片类型': movie_type, '系列': '未知系列'}  # 用于暂时存放影片信息，女优，标题等
rename_mp4_list = rename_mp4.split('+')
title_list = custom_title.replace('标题', '完整标题', 1).split('+')
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
# 获取nfo信息的javlib搜索网页
while 1:
    try:
        input_url = input('\n请输入javlibrary上的某一部影片的网址：')
        print()
        jav_list[0] = input_url
        try:
            javlib_html = get_jav_html(jav_list)
        except:
            print('>>尝试打开页面失败，正在尝试第二次打开...')
            try:  #用网高峰期，经常打不开javlib，尝试第二次
                javlib_html = get_jav_html(jav_list)
                print('    >第二次尝试成功！')
            except:
                print('>>网址正确吗？打不开啊！')
                continue
        # 搜索结果的网页，大部分情况就是这个影片的网页，也有可能是多个结果的网页
        # 尝试找标题，第一种情况：找得到，就是这个影片的网页[a-zA-Z]{1,6}-\d{1,5}.+?
        titleg = re.search(r'<title>(.+?) - JAVLibrary</title>', javlib_html)  # 匹配处理“标题”
        # 搜索结果就是AV的页面
        if str(titleg) != 'None':
            title = titleg.group(1)
        # 第二种情况：搜索结果可能是两个以上，所以这种匹配找不到标题，None！
        else:   # 继续找标题，但匹配形式不同，这是找“可能是多个结果的网页”上的第一个标题
            print('>>网址正确吗？找不到影片信息啊！')
            continue

        print('>>正在处理：', title)
        # 去除title中的特殊字符
        title = title.replace('\n', '').replace('&', '和').replace('/', '#')\
               .replace('/', '#').replace(':', '：').replace('*', '#').replace('?', '？')\
               .replace('"', '#').replace('<', '【').replace('>', '】')\
               .replace('|', '#').replace('＜', '【').replace('＞', '】')\
               .replace('〈', '【').replace('〉', '】').replace('＆', '和').replace('\t', '').replace('\r', '')
        # 正则匹配 影片信息 开始！
        # title的开头是车牌号，想要后面的纯标题
        car_titleg = re.search(r'(.+?) (.+)', title)  # 这边匹配番号，[a-z]可能很奇怪，
        # 车牌号
        nfo_dict['车牌'] = car_titleg.group(1)
        # 给用户用的标题是 短的title_easy
        nfo_dict['完整标题'] = car_titleg.group(2)
        # 处理影片的标题过长
        if len(nfo_dict['完整标题']) > title_len:
            nfo_dict['标题'] = nfo_dict['完整标题'][:title_len]
        else:
            nfo_dict['标题'] = nfo_dict['完整标题']
        # 处理特殊车牌 t28-573
        if nfo_dict['车牌'].startswith('T-28'):
            nfo_dict['车牌'] = nfo_dict['车牌'].replace('T-28', 'T28-', 1)
        nfo_dict['车牌前缀'] = nfo_dict['车牌'].split('-')[0]
        # 片商
        studiog = re.search(r'rel="tag">(.+?)</a> &nbsp;<span id="maker_', javlib_html)
        if str(studiog) != 'None':
            nfo_dict['片商'] = studiog.group(1)
        else:
            nfo_dict['片商'] = '未知片商'
        # 上映日
        premieredg = re.search(r'<td class="text">(\d\d\d\d-\d\d-\d\d)</td>', javlib_html)
        if str(premieredg) != 'None':
            nfo_dict['发行年月日'] = premieredg.group(1)
            nfo_dict['发行年份'] = nfo_dict['发行年月日'][0:4]
            nfo_dict['月'] = nfo_dict['发行年月日'][5:7]
            nfo_dict['日'] = nfo_dict['发行年月日'][8:10]
        else:
            nfo_dict['发行年月日'] = '1970-01-01'
            nfo_dict['发行年份'] = '1970'
            nfo_dict['月'] = '01'
            nfo_dict['日'] = '01'
        # 片长 <td><span class="text">150</span> 分钟</td>
        runtimeg = re.search(r'<td><span class="text">(\d+?)</span>', javlib_html)
        if str(runtimeg) != 'None':
            nfo_dict['片长'] = runtimeg.group(1)
        else:
            nfo_dict['片长'] = '0'
        # 导演
        directorg = re.search(r'rel="tag">(.+?)</a> &nbsp;<span id="director', javlib_html)
        if str(directorg) != 'None':
            nfo_dict['导演'] = directorg.group(1)
        else:
            nfo_dict['导演'] = '未知导演'
        # 演员们 和 # 第一个演员
        actors_prag = re.search(r'<span id="cast(.+?)</td>', javlib_html, re.DOTALL)
        if str(actors_prag) != 'None':
            actors = re.findall(r'rel="tag">(.+?)</a></span> <span id', actors_prag.group(1))
            if len(actors) != 0:
                if len(actors) > 7:
                    actors = actors[:7]
                nfo_dict['首个女优'] = actors[0]
                nfo_dict['全部女优'] = ' '.join(actors)
            else:
                nfo_dict['首个女优'] = nfo_dict['全部女优'] = '未知演员'
                actors = ['未知演员']
        else:
            nfo_dict['首个女优'] = nfo_dict['全部女优'] = '未知演员'
            actors = ['未知演员']
        nfo_dict['标题'] = nfo_dict['标题'].rstrip(nfo_dict['全部女优'])
        # 特点
        genres = re.findall(r'category tag">(.+?)</a>', javlib_html)
        # DVD封面cover
        coverg = re.search(r'src="(.+?)" width="600" height="403"', javlib_html)  # 封面图片的正则对象
        if str(coverg) != 'None':
            cover_url = coverg.group(1)
        else:
            cover_url = ''
        # 评分
        scoreg = re.search(r'&nbsp;<span class="score">\((.+?)\)</span>', javlib_html)
        if str(scoreg) != 'None':
            score = float(scoreg.group(1))
            score = (score - 4) * 5 / 3     # javlib上稍微有人关注的影片评分都是6分以上（10分制），强行把它差距拉大
            if score >= 0:
                score = '%.1f' % score
                nfo_dict['评分'] = str(score)
            else:
                nfo_dict['评分'] = '0'
        else:
            nfo_dict['评分'] = '0'
        criticrating = str(float(nfo_dict['评分'])*10)
        # javlib的精彩影评   (.+?\s*.*?\s*.*?\s*.*?)  用javlib上的精彩影片，下面的匹配可能很奇怪，没办法，就这么奇怪
        plot_review = ''
        if if_review == '是':
            review = re.findall(r'(hidden">.+?</textarea>)</td>\s*?<td class="scores"><table>\s*?<tr><td><span class="scoreup">\d\d+?</span>', javlib_html, re.DOTALL)
            if len(review) != 0:
                plot_review = '\n【精彩影评】：'
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
        # 企划javlib上没有企划set
        #######################################################################
        # arzon的简介
        plot = series = ''
        if if_nfo == '是' and if_plot == '是':
            while 1:
                arz_search_url = 'https://www.arzon.jp/itemlist.html?t=&m=all&s=&q=' + nfo_dict['车牌']
                print('    >正在查找简介：', arz_search_url)
                arzon_list[0] = arz_search_url
                try:
                    search_html = get_arzon_html(arzon_list)
                except:
                    print('    >尝试打开“', arz_search_url, '”搜索页面失败，正在尝试第二次打开...')
                    try:
                        search_html = get_arzon_html(arzon_list)
                        print('    >第二次尝试成功！')
                    except:
                        print('    >连接arzon失败：' + arz_search_url)
                        plot = '【连接arzon失败！看到此提示请重新整理nfo！】'
                        break
                if plot == '':
                    # <dt><a href="https://www.arzon.jp/item_1376110.html" title="限界集落に越してきた人妻 ～村民"><img src=
                    AVs = re.findall(r'<h2><a href="(/item.+?)" title=', search_html)  # 所有搜索结果链接
                    # 搜索结果为N个AV的界面
                    if AVs:  # arzon有搜索结果
                        results_num = len(AVs)
                        for i in range(results_num):
                            arz_url = 'https://www.arzon.jp' + AVs[i]  # 第i+1个链接
                            arzon_list[0] = arz_url
                            try:
                                jav_html = get_arzon_html(arzon_list)
                            except:
                                print('    >打开“', arz_url, '”第' + str(i + 1) + '个搜索结果失败，正在尝试第二次打开...')
                                try:
                                    jav_html = get_arzon_html(arzon_list)
                                    print('    >第二次尝试成功！')
                                except:
                                    print('    >无法进入第' + str(i + 1) + '个搜索结果：' + arz_url)
                                    plot = '【连接arzon失败！看到此提示请重新整理nfo！】'
                                    break
                            if plot == '':
                                # 在该arz_url网页上查找简介
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
                        # 几个搜索结果查找完了，也没有找到简介
                        if plot == '':
                            print('    >arzon有' + str(results_num) + '个搜索结果：' + arz_search_url + '，但找不到简介！')
                            plot = '【arzon有该影片，但找不到简介】'
                        break
                    # arzon搜索页面实际是18岁验证
                    else:
                        adultg = re.search(r'１８歳未満', search_html)
                        if str(adultg) != 'None':
                            print('    >成人验证，请重启程序！')
                            os.system('pause')
                        else:  # 不是成人验证，也没有简介
                            print('    >arzon找不到该影片简介，可能被下架!')
                            plot = '【影片下架，再无简介】'
                            break
            if if_tran == '是':
                plot = tran(ID, SK, plot, t_lang)
        #######################################################################
        # 1重命名视频
        new_mp4 = nfo_dict['车牌']  # 默认为车牌
        if if_mp4 == '是':
            # 新文件名new_mp4
            new_mp4 = ''
            for j in rename_mp4_list:
                new_mp4 += nfo_dict[j]
            new_mp4 = new_mp4.rstrip(' ')

        # nfo_dict['视频']用于图片的命名
        nfo_dict['视频'] = new_mp4
        new_root = root  # 为了能和其他py一样

        # 2重命名文件夹

        # 3写入nfo开始
        if if_nfo == '是':
            cus_title = ''
            for i in title_list:
                cus_title += nfo_dict[i]
            # 写入nfo开始
            info_path = root + '/' + new_mp4 + '.nfo'      #nfo存放的地址
            # 开始写入nfo，这nfo格式是参考的emby的nfo
            f = open(info_path, 'w', encoding="utf-8")
            f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>\n"
                    "<movie>\n"
                    "  <plot>" + plot + plot_review + "</plot>\n"
                    "  <title>" + cus_title + "</title>\n"
                    "  <director>" + nfo_dict['导演'] + "</director>\n"
                    "  <rating>" + nfo_dict['评分'] + "</rating>\n"
                    "  <criticrating>" + criticrating + "</criticrating>\n"
                    "  <year>" + nfo_dict['发行年份'] + "</year>\n"
                    "  <mpaa>NC-17</mpaa>\n"                            
                    "  <customrating>NC-17</customrating>\n"
                    "  <countrycode>JP</countrycode>\n"
                    "  <premiered>" + nfo_dict['发行年月日'] + "</premiered>\n"
                    "  <release>" + nfo_dict['发行年月日'] + "</release>\n"
                    "  <runtime>" + nfo_dict['片长'] + "</runtime>\n"
                    "  <country>日本</country>\n"
                    "  <studio>" + nfo_dict['片商'] + "</studio>\n"
                    "  <id>" + nfo_dict['车牌'] + "</id>\n"
                    "  <num>" + nfo_dict['车牌'] + "</num>\n"
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

        # 4需要两张图片
        if if_jpg == '是':
            # 下载海报的地址 cover
            cover_url = 'http:' + cover_url
            # fanart和poster路径
            fanart_path = new_root + '/'
            poster_path = new_root + '/'
            for i in fanart_list:
                fanart_path += nfo_dict[i]
            for i in poster_list:
                poster_path += nfo_dict[i]
            # 下载 海报
            print('    >正在下载封面：', cover_url)
            cover_list[0] = 0
            cover_list[1] = cover_url
            cover_list[2] = fanart_path
            try:
                download_pic(cover_list)
                print('    >fanart.jpg下载成功')
            except:
                print('    >从javlibrary下载fanart.jpg失败，正在前往javbus...')
                # 在javbus上找图片url
                bus_search_url = bus_url + nfo_dict['车牌']
                jav_list[0] = bus_search_url
                try:
                    bav_html = get_jav_html(jav_list)
                except:
                    print('    >连接javbus失败，下载fanart失败：' + bus_search_url)
                    continue
                # DVD封面cover
                coverg = re.search(r'<a class="bigImage" href="(.+?)">', bav_html)  # 封面图片的正则对象
                if str(coverg) != 'None':
                    cover_list[0] = 0
                    cover_list[1] = cover_url
                    cover_list[2] = fanart_path
                    print('    >正在从javbus下载封面：', cover_url)
                    try:
                        download_pic(cover_list)
                        print('    >fanart.jpg下载成功')
                    except:
                        print('    >下载fanart.jpg失败：' + cover_url)
                        continue
                else:
                    print('    >从javbus上查找封面失败：' + bus_search_url)
                    continue
            # crop
            img = Image.open(fanart_path)
            w, h = img.size                               # fanart的宽 高
            ex = int(w * 0.52625)                         # 0.52625是根据emby的poster宽高比较出来的
            poster = img.crop((ex, 0, w, h))              # （ex，0）是左下角（x，y）坐标 （w, h)是右上角（x，y）坐标
            poster.save(poster_path, quality=95)          # quality=95 是无损crop，如果不设置，默认75
            print('    >poster.jpg裁剪成功')

        # 5收集女优头像
        if if_sculpture == '是':
            if actors[0] == '未知演员':
                print('    >未知演员')
            else:
                for each_actor in actors:
                    exist_actor_path = '女优头像/' + each_actor + '.jpg'
                    # print(exist_actor_path)
                    jpg_type = '.jpg'
                    if not os.path.exists(exist_actor_path):  # 女优jpg图片还没有
                        exist_actor_path = '女优头像/' + each_actor + '.png'
                        if not os.path.exists(exist_actor_path):  # 女优png图片还没有
                            print('    >没有女优头像：' + each_actor + '\n')
                            config_actor = configparser.ConfigParser()
                            config_actor.read('【缺失的女优头像统计For Kodi】.ini', encoding='utf-8-sig')
                            try:
                                each_actor_times = config_actor.get('缺失的女优头像', each_actor)
                                config_actor.set("缺失的女优头像", each_actor, str(int(each_actor_times) + 1))
                            except:
                                config_actor.set("缺失的女优头像", each_actor, '1')
                            config_actor.write(open('【缺失的女优头像统计For Kodi】.ini', "w", encoding='utf-8-sig'))
                            continue
                        else:
                            jpg_type = '.png'
                    actors_path = new_root + '/.actors/'
                    if not os.path.exists(actors_path):
                        os.makedirs(actors_path)
                    shutil.copyfile('女优头像/' + each_actor + jpg_type,
                                    actors_path + each_actor + jpg_type)
                    print('    >女优头像收集完成：', each_actor)

        print()
    except:
        print('发生错误，如一直在该影片报错请截图并联系作者：' + relative_path + '\n' + traceback.format_exc() + '\n')
        continue
