# -*- coding:utf-8 -*-
import re, os, configparser, time, hashlib, json, requests, shutil, traceback
from PIL import Image
from tkinter import filedialog, Tk
from time import sleep


# 获取用户选取的文件夹路径，返回路径str
def get_directory():
    directory_root = Tk()
    directory_root.withdraw()
    work_path = filedialog.askdirectory()
    if work_path == '':
        print('你没有选择目录! 请重新选：')
        sleep(2)
        return get_directory()
    else:
        # askdirectory 获得是 正斜杠 路径C:/，所以下面要把 / 换成 反斜杠\
        return work_path


# 记录错误txt，无返回
def write_fail(fail_m):
    record_txt = open('【记得清理它】失败记录.txt', 'a', encoding="utf-8")
    record_txt.write(fail_m)
    record_txt.close()


# 调用百度翻译API接口，返回中文简介str
def tran(api_id, key, word, to_lang):
    # init salt and final_sign
    salt = str(time.time())[:10]
    final_sign = api_id + word + salt + key
    final_sign = hashlib.md5(final_sign.encode("utf-8")).hexdigest()
    # 表单paramas
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


# 每一部jav的“结构体”
class JavFile(object):
    def __init__(self):
        self.name = 'ABC-123.mp4'  # 文件名
        self.car = 'ABC-123'  # 车牌
        self.episodes = 0     # 第几集
        self.subt = ''        # 字幕文件名  ABC-123.srt


#  main开始
print('1、避开21:00-1:00，访问javlibrary和arzon很慢。\n'
      '2、若一直连不上javlibrary，请在ini中更新网址\n'
      '3、不要用www.javlibrary.com！用防屏蔽地址\n')
# 读取配置文件，这个ini文件用来给用户设置重命名的格式和jav网址
print('正在读取ini中的设置...', end='')
try:
    config_settings = configparser.RawConfigParser()
    config_settings.read('ini的设置会影响所有exe的操作结果.ini', encoding='utf-8-sig')
    if_nfo = config_settings.get("收集nfo", "是否收集nfo？")
    if_exnfo = config_settings.get("收集nfo", "是否跳过已存在nfo的文件夹？")
    if_review = config_settings.get("收集nfo", "是否收集javlibrary上的影评？")
    custom_title = config_settings.get("收集nfo", "nfo中title的格式")
    if_mp4 = config_settings.get("重命名影片", "是否重命名影片？")
    rename_mp4 = config_settings.get("重命名影片", "重命名影片的格式")
    if_folder = config_settings.get("修改文件夹", "是否重命名或创建独立文件夹？")
    rename_folder = config_settings.get("修改文件夹", "新文件夹的格式")
    if_rename_subt = config_settings.get("字幕文件", "是否重命名已有的字幕文件")
    if_classify_subt = config_settings.get("字幕文件", "是否使用字幕库")
    file_folder = config_settings.get("归类影片", "针对文件还是文件夹？")
    if_classify = config_settings.get("归类影片", "是否归类影片？")
    classify_root = config_settings.get("归类影片", "归类的根目录")
    classify_basis = config_settings.get("归类影片", "归类的标准")
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
    library_url = config_settings.get("其他设置", "javlibrary网址")
    bus_url = config_settings.get("其他设置", "javbus网址")
    suren_pref = config_settings.get("其他设置", "素人车牌(若有新车牌请自行添加)")
    file_type = config_settings.get("其他设置", "扫描文件类型")
    title_len = int(config_settings.get("其他设置", "重命名中的标题长度（50~150）"))
    subt_words = config_settings.get("原影片文件的性质", "是否中字即文件名包含")
    custom_subt = config_settings.get("原影片文件的性质", "是否中字的表现形式")
    xx_words = config_settings.get("原影片文件的性质", "是否xx即文件名包含")
    custom_xx = config_settings.get("原影片文件的性质", "是否xx的表现形式")
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
        print('\n    >“【缺失的女优头像统计For Kodi】.ini”文件丢失...正在重写ini...成功！')
        print('正在重新读取...', end='')
print('\n读取ini文件成功!')
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
    jav_list = ['', proxies]              # 代理jav等网站
    arzon_list = ['', acook, proxies]     # 代理arzon
    cover_list = [0, '', '', proxies]     # 代理dmm图片原
else:
    jav_list = ['']
    arzon_list = ['', acook]
    cover_list = [0, '', '']
# 归类文件夹具有最高决定权
if if_classify == '是':            # 如果需要归类
    if file_folder == '文件夹':    # 并且是针对文件夹
        if_folder = '是'           # 那么必须重命名文件夹或者创建新的文件夹
    else:
        if_folder = '否'           # 否则不会操作新文件夹
# http://www.x39n.com/   https://www.buscdn.work/ 无论用户输不输人后面的斜杠
if not library_url.endswith('/'):
    library_url += '/'
if not bus_url.endswith('/'):
    bus_url += '/'
# 确认网站、百度翻译是简/繁中文
if simp_trad == '简':
    library_url += 'cn/'
    t_lang = 'zh'
else:
    library_url += 'tw/'
    t_lang = 'cht'
# 初始化其他
nfo_dict = {'空格': ' ', '车牌': 'ABC-123', '标题': '未知标题', '完整标题': '完整标题', '导演': '未知导演',
            '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
            '片商': '未知片商', '评分': '0', '首个女优': '未知演员', '全部女优': '未知演员',
            '片长': '0', '/': '/', '是否中字': '', '视频': 'ABC-123', '车牌前缀': 'ABC',
            '是否xx': '', '影片类型': movie_type, '系列': '未知系列'}         # 存放影片信息，女优，标题等
suren_list = suren_pref.split('、')               # 素人番号的列表
rename_mp4_list = rename_mp4.split('+')           # 重命名视频的格式
rename_folder_list = rename_folder.split('+')     # 重命名文件夹的格式
type_tuple = tuple(file_type.split('、'))         # 需要扫描的文件的类型
classify_basis_list = classify_basis.split('/')  # 归类标准，归类到哪个文件夹
title_list = custom_title.replace('标题', '完整标题', 1).split('+')  # nfo中title的写法
fanart_list = custom_fanart.split('+')            # fanart的格式
poster_list = custom_poster.split('+')            # poster的格式
word_list = subt_words.split('、')                # 包含哪些特殊含义的文字，判断是否中字
xx_list = xx_words.split('、')                    # 包含哪些特殊含义的文字，判断是否xx
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
    # 用户选择文件夹
    print('请选择要整理的文件夹：', end='')
    path = get_directory()
    print(path)
    write_fail('已选择文件夹：' + path + '\n')
    print('...文件扫描开始...如果时间过长...请避开中午夜晚高峰期...\n')
    # 确定归类根目录
    if if_classify == '是':
        classify_root = classify_root.rstrip('/')
        if classify_root != '所选文件夹':
            if classify_root != path:  # 归类根目录和所选不一样，继续核实归类根目录的合法性
                if classify_root[:2] != path[:2]:
                    print('归类的根目录“', classify_root, '”和所选文件夹不在同一磁盘无法归类！请修正！')
                    os.system('pause')
                if not os.path.exists(classify_root):
                    print('归类的根目录“', classify_root, '”不存在！无法归类！请修正！')
                    os.system('pause')
            else:  # 一样
                classify_root = path + '/归类完成'
        else:
            classify_root = path + '/归类完成'
    # 初始化“失败信息”
    fail_times = 0                             # 处理过程中失败的个数
    fail_list = []                             # 用于存放处理失败的信息
    # root【当前根目录】 dirs【子目录】 files【文件】，root是字符串，后两个是列表
    for root, dirs, files in os.walk(path):
        if if_classify == '是' and root.startswith(classify_root):  # “当前目录”在“目标归类目录”中
            # print('>>该文件夹在归类的根目录中，跳过处理...', root)
            continue
        if if_exnfo == '是' and files and (files[-1].endswith('nfo') or (len(files) > 1 and files[-2].endswith('nfo'))):
            print(root+'/'+files[-1])
            continue
        # 对这一层文件夹进行评估,有多少视频，有多少同车牌视频，是不是独立文件夹
        jav_videos = []        # 存放：需要整理的jav的结构体
        cars_dic = {}          # 存放：这一层目录下的几个车牌
        videos_num = 0         # 当前文件夹中视频的数量，可能有视频不是jav
        subtitles = False      # 有没有字幕
        subts_dict = {}        # 存放：jav的字幕文件 {'c:/a/abc_123.srt': 'abc-123'}
        for raw_file in files:
            # 判断文件是不是字幕文件
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
        # print('>>扫描字幕文件完毕！')
        for raw_file in files:
            # 判断是不是视频，得到车牌号
            if raw_file.endswith(type_tuple) and not raw_file.startswith('.'):
                videos_num += 1
                video_num_g = re.search(r'([a-zA-Z]{2,7})-? ?_?(\d{2,6})', raw_file)    # 这个正则表达式匹配“车牌号”可能有点奇怪，
                if str(video_num_g) != 'None':                               # 如果你下过上千部片，各种参差不齐的命名，你就会理解我了。
                    num_pref = video_num_g.group(1).upper()
                    num_suf = video_num_g.group(2)
                    car_num = num_pref + '-' + num_suf
                    if num_pref in suren_list:  # 如果这是素人影片，告诉一下用户，它们需要另外处理
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '个警告！素人影片：' + root.lstrip(path) + '/' + raw_file + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue  # 素人影片不参与下面的整理
                    if car_num not in cars_dic:      # cars_dic中没有这个车牌，表示这一层文件夹下新发现一个车牌
                        cars_dic[car_num] = 1        # 这个新车牌有了第一集
                    else:
                        cars_dic[car_num] += 1       # 已经有这个车牌了，加一集cd
                    jav_file = JavFile()
                    jav_file.car = car_num           # 车牌
                    jav_file.name = raw_file         # 原文件名
                    jav_file.episodes = cars_dic[car_num]  # 这个jav视频，是第几集
                    if car_num in subts_dict.values():
                        jav_file.subt = list(subts_dict.keys())[list(subts_dict.values()).index(car_num)]
                        del subts_dict[jav_file.subt]
                    jav_videos.append(jav_file)
                else:
                    continue
            else:
                continue
        # 判定影片所在文件夹是否是独立文件夹
        if cars_dic:  # 这一层文件夹下有jav
            if len(cars_dic) > 1 or videos_num > len(jav_videos) or len(dirs) > 1 or (len(dirs) == 1 and dirs[0] != '.actors'):
                # 当前文件夹下，车牌不止一个，还有其他非jav视频，            有其他文件夹，除了女优头像文件夹“.actors”
                separate_folder = False   # 不是独立的文件夹
            else:
                separate_folder = True    # 这一层文件夹是这部jav的独立文件夹
        else:
            continue

        # 正式开始
        # print(jav_videos)
        # os.system('pasue')
        for srt in jav_videos:
            car_num = srt.car
            file = srt.name
            relative_path = '/' + root.lstrip(path) + '/' + file  # 影片的相对于所选文件夹的路径，用于报错
            try:
                # 获取nfo信息的javlibrary搜索网页
                lib_search_url = library_url + 'vl_searchbyid.php?keyword=' + car_num
                jav_list[0] = lib_search_url
                try:
                    jav_html = get_jav_html(jav_list)
                except:
                    print('>>尝试打开javlibrary搜索页面失败，正在尝试第二次打开...')
                    try:  # 用网高峰期，经常打不开javlibrary，尝试第二次
                        jav_html = get_jav_html(jav_list)
                        print('    >第二次尝试成功！')
                    except:
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '个失败！打开javlibrary搜索页面失败：' + lib_search_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                # 搜索结果的网页，大部分情况就是这个影片的网页，也有可能是多个结果的网页
                # 尝试找标题，第一种情况：找得到，就是这个影片的网页
                titleg = re.search(r'<title>([A-Z].+?) - JAVLibrary</title>', jav_html)  # 匹配处理“标题”
                # 搜索结果就是AV的页面
                if str(titleg) != 'None':
                    title = titleg.group(1)
                # 第二种情况：搜索结果可能是两个以上，所以这种匹配找不到标题，None！
                else:   # 继续找标题，但匹配形式不同，这是找“可能是多个结果的网页”上的第一个标题
                    search_results = re.findall(r'v=javli(.+?)" title="(.+?-\d+?[a-z]? .+?)"', jav_html)
                    # os.system('pause')
                    # 搜索有几个结果，用第一个AV的网页，打开它
                    if search_results:
                        result_first_url = library_url + '?v=javli' + search_results[0][0]
                        if len(search_results) > 1:   # 只有一个结果，其实有的结果被忽略了，比如avop-00127bod，它是近几年重置的，信息冗余
                            if search_results[0][1].endswith('ク）'):   # 排在第一个的是蓝光重置版，比如SSNI-589（ブルーレイディスク），它的封面不正常，跳过它
                                result_first_url = library_url + '?v=javli' + search_results[1][0]
                            elif search_results[1][1].startswith(car_num):  # 不同的片，但车牌完全相同，比如id-020。警告用户，但默认用第一个结果。
                                fail_times += 1
                                fail_message = '第' + str(fail_times) + '个警告！搜索页面上的有多个结果：' + lib_search_url + '\n'
                                print('>>' + fail_message, end='')
                                fail_list.append('    >' + fail_message)
                                write_fail('    >' + fail_message)
                            # else: 还有一种情况，不同片，车牌也不同，但搜索到一堆，比如搜“AVOP-039”，还会得到“AVOP-390”，正确的肯定是第一个。
                        jav_list[0] = result_first_url
                        try:
                            jav_html = get_jav_html(jav_list)
                        except:
                            fail_times += 1
                            fail_message = '>第' + str(fail_times) + '个失败！打开javlibrary搜索页面上的第一个AV失败：' + result_first_url + '，' + relative_path + '\n'
                            print('>>' + fail_message, end='')
                            fail_list.append('    >' + fail_message)
                            write_fail('    >' + fail_message)
                            continue
                        # 找到标题，留着马上整理信息用
                        title = re.search(r'<title>([A-Z].+?) - JAVLibrary</title>', jav_html).group(1)
                    # 第三种情况：搜索不到这部影片，搜索结果页面什么都没有
                    else:
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '个失败！javlibrary找不到AV信息，无码？新系列素人？年代久远？：' + lib_search_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('>>' + fail_message)
                        continue

                print('>>正在处理：', title)
                # 影片文件本身的一些属性
                video_type = '.' + file.split('.')[-1]         # 文件类型，如：.mp4
                subt_name = srt.subt
                if subt_name:
                    subtitles = True
                    subt_type = '.' + subt_name.split('.')[-1]  # 字幕类型，如：.srt
                else:
                    subtitles = False
                    subt_type = ''
                nfo_dict['是否中字'] = ''
                if not subtitles:             # 没有外挂字幕
                    for i in word_list:       # 但是原文件名包含“-c、-C、中字”这些字符
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
                # 正则匹配 影片信息 开始！
                # title的开头是车牌号，想要后面的纯标题
                car_titleg = re.search(r'(.+?) (.+)', title)  # 这边匹配番号，[a-z]可能很奇怪，
                # 车牌号
                nfo_dict['车牌'] = car_titleg.group(1)
                nfo_dict['车牌前缀'] = nfo_dict['车牌'].split('-')[0]
                # 给用户用的标题是 短的title_easy
                nfo_dict['完整标题'] = car_titleg.group(2)
                # 处理影片的标题过长
                if len(nfo_dict['完整标题']) > title_len:
                    nfo_dict['标题'] = nfo_dict['完整标题'][:title_len]
                else:
                    nfo_dict['标题'] = nfo_dict['完整标题']
                # 片商
                studiog = re.search(r'rel="tag">(.+?)</a> &nbsp;<span id="maker_', jav_html)
                if str(studiog) != 'None':
                    nfo_dict['片商'] = studiog.group(1)
                else:
                    nfo_dict['片商'] = '未知片商'
                # 上映日
                premieredg = re.search(r'<td class="text">(\d\d\d\d-\d\d-\d\d)</td>', jav_html)
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
                runtimeg = re.search(r'<td><span class="text">(\d+?)</span>', jav_html)
                if str(runtimeg) != 'None':
                    nfo_dict['片长'] = runtimeg.group(1)
                else:
                    nfo_dict['片长'] = '0'
                # 导演
                directorg = re.search(r'rel="tag">(.+?)</a> &nbsp;<span id="director', jav_html)
                if str(directorg) != 'None':
                    nfo_dict['导演'] = directorg.group(1)
                else:
                    nfo_dict['导演'] = '未知导演'
                # 演员们 和 # 第一个演员
                actors_prag = re.search(r'<span id="cast(.+?)</td>', jav_html, re.DOTALL)
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
                genres = re.findall(r'category tag">(.+?)</a>', jav_html)
                if nfo_dict['是否中字']:
                    genres.append('中文字幕')
                if nfo_dict['是否xx']:
                    genres.append('无码流出')
                # print(genres)
                # DVD封面cover
                coverg = re.search(r'src="(.+?)" width="600" height="403"', jav_html)  # 封面图片的正则对象
                if str(coverg) != 'None':
                    cover_url = coverg.group(1)
                else:
                    cover_url = ''
                # 评分
                scoreg = re.search(r'&nbsp;<span class="score">\((.+?)\)</span>', jav_html)
                if str(scoreg) != 'None':
                    score = float(scoreg.group(1))
                    score = (score - 4) * 5 / 3     # javlibrary上稍微有人关注的影片评分都是6分以上（10分制），强行把它差距拉大
                    if score >= 0:
                        score = '%.1f' % score
                        nfo_dict['评分'] = str(score)
                    else:
                        nfo_dict['评分'] = '0'
                else:
                    nfo_dict['评分'] = '0'
                criticrating = str(float(nfo_dict['评分'])*10)
                # javlibrary的精彩影评   (.+?\s*.*?\s*.*?\s*.*?) 下面的匹配可能很奇怪，没办法，就这么奇怪
                plot_review = ''
                if if_review == '是':
                    review = re.findall(r'(hidden">.+?</textarea>)</td>\s*?<td class="scores"><table>\s*?<tr><td><span class="scoreup">\d\d+?</span>', jav_html, re.DOTALL)
                    if len(review) != 0:
                        plot_review = '\n【精彩影评】：'
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
                # arzon的简介 #########################################################
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
                                fail_times += 1
                                fail_message = '    >第' + str(
                                    fail_times) + '个失败！连接arzon失败：' + arz_search_url + '，' + relative_path + '\n'
                                print(fail_message, end='')
                                fail_list.append(fail_message)
                                write_fail(fail_message)
                                plot = '【连接arzon失败！看到此提示请重新整理nfo！】'
                                break  # 跳出while
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
                                        print('    >打开“', arz_url, '”第' + str(i+1) + '个搜索结果失败，正在尝试第二次打开...')
                                        try:
                                            jav_html = get_arzon_html(arzon_list)
                                            print('    >第二次尝试成功！')
                                        except:
                                            fail_times += 1
                                            fail_message = '    >第' + str(
                                                fail_times) + '个失败！无法进入第' + str(i+1) + '个搜索结果：' + arz_url + '，' + relative_path + '\n'
                                            print(fail_message, end='')
                                            fail_list.append(fail_message)
                                            write_fail(fail_message)
                                            plot = '【连接arzon失败！看到此提示请重新整理nfo！】'
                                            break  # 跳出for AVs
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
                                # 几个搜索结果查找完了，也没有找到简介
                                if plot == '':
                                    plot = '【arzon有该影片，但找不到简介】'
                                    fail_times += 1
                                    fail_message = '    >arzon有' + str(results_num) + '个搜索结果：' + arz_search_url + '，但找不到简介！：' + relative_path + '\n'
                                    print(fail_message, end='')
                                    fail_list.append(fail_message)
                                    write_fail(fail_message)
                                break  # 跳出while
                            # arzon返回的页面实际是18岁验证
                            else:
                                adultg = re.search(r'１８歳未満', search_html)
                                if str(adultg) != 'None':
                                    fail_times += 1
                                    fail_message = '    >第' + str(
                                        fail_times) + '个失败！arzon成人验证，请重启程序：' + relative_path + '\n'
                                    print(fail_message, end='')
                                    fail_list.append(fail_message)
                                    write_fail(fail_message)
                                    os.system('pause')
                                else:  # 不是成人验证，也没有简介
                                    fail_times += 1
                                    fail_message = '    >第' + str(
                                        fail_times) + '个失败！arzon找不到该影片简介，可能被下架：' + arz_search_url + '，' + relative_path + '\n'
                                    print(fail_message, end='')
                                    fail_list.append(fail_message)
                                    write_fail(fail_message)
                                    plot = '【影片下架，再无简介】'
                                    break  # 跳出while
                    if if_tran == '是':
                        plot = tran(ID, SK, plot, t_lang)
                #######################################################################

                # 1重命名视频
                new_mp4 = file[:-len(video_type)].rstrip(' ')
                if if_mp4 == '是':
                    new_mp4 = ''                   # 新文件名
                    for j in rename_mp4_list:
                        new_mp4 += nfo_dict[j]
                    new_mp4 = new_mp4.rstrip(' ')  # 去除末尾空格，否则windows会自动删除空格，导致程序仍以为带空格
                    cd_msg = ''
                    if cars_dic[car_num] > 1:      # 是CD1还是CDn？
                        cd_msg = '-cd' + str(srt.episodes)
                        new_mp4 += cd_msg
                    # rename mp4
                    os.rename(root + '/' + file, root + '/' + new_mp4 + video_type)
                    # file发生了变化
                    file = new_mp4 + video_type
                    print('    >修改文件名' + cd_msg + '完成')
                    # 重命名字幕
                    if subt_name and if_rename_subt == '是':
                        os.rename(root + '/' + subt_name, root + '/' + new_mp4 + subt_type)
                        subt_name = new_mp4 + subt_type
                        print('    >修改字幕名完成')

                # nfo_dict['视频']用于图片的命名
                nfo_dict['视频'] = new_mp4

                # 1.5 归类影片，只针对影片
                if if_classify == '是' and file_folder != '文件夹':
                    # 需要归类影片，针对这个影片
                    class_root = classify_root + '/'
                    # 移动的目标文件夹
                    for j in classify_list:
                        class_root += nfo_dict[j].rstrip(' .')  # C:/Users/JuneRain/Desktop/测试文件夹/1/葵司/
                    new_root = class_root                    # 新的影片的目录路径，C:/Users/JuneRain/Desktop/测试文件夹/1/葵司/
                    new_folder = new_root.split('/')[-1]    # 新的影片的目录名称，变成了目标目录“葵司”
                    if not os.path.exists(new_root):
                        os.makedirs(new_root)
                    jav_new_path = new_root + '/' + file   # 新的影片路径
                    if not os.path.exists(jav_new_path):    # 目标文件夹没有相同的影片
                        os.rename(root + '/' + file, jav_new_path)
                        print('    >归类影片文件完成')
                        if subt_name:
                            os.rename(root + '/' + subt_name, new_root + '/' + subt_name)
                            print('    >归类字幕文件完成')
                    else:
                        fail_times += 1
                        fail_message = '    >第' + str(
                            fail_times) + '个失败！归类失败，重复的影片，归类的目标文件夹已经存在相同的影片：' + jav_new_path + '\n'
                        print(fail_message, end='')
                        fail_list.append(fail_message)
                        write_fail(fail_message)
                        continue
                else:
                    new_root = root                    # 当前影片的目录路径，在下面的重命名操作中将发生变化
                    new_folder = root.split('/')[-1]  # 当前影片的目录名称，在下面的重命名操作中即将发生变化

                # 2重命名文件夹
                if if_folder == '是':                   # 如果是针对“文件”归类，这一步会被跳过
                    # 新文件夹名new_folder
                    new_folder = ''
                    for j in rename_folder_list:
                        new_folder += (nfo_dict[j])
                    new_folder = new_folder.rstrip(' .')  # 去除末尾空格和“.”，否则windows会自动删除它们，导致程序仍以为带空格和“.”
                    if separate_folder:                  # 是独立文件夹，才会重命名文件夹
                        if cars_dic[car_num] == 1 or (cars_dic[car_num] > 1 and cars_dic[car_num] == srt.episodes):
                            # 同一车牌有多部，且这是最后一部，才会重命名
                            newroot_list = root.split('/')
                            del newroot_list[-1]
                            upper2_root = '/'.join(newroot_list)         # 当前文件夹的上级目录
                            new_root = upper2_root + '/' + new_folder    # 上级目录+新目录名称=新目录路径
                            if not os.path.exists(new_root) or new_root == root:              # 目标影片文件夹不存在，或者目标影片文件夹存在，但就是现在的文件夹，即新旧相同
                                # 修改文件夹
                                os.rename(root, new_root)
                                print('    >重命名文件夹完成')
                            else:                             # 已经有一个那样的文件夹了
                                fail_times += 1
                                fail_message = '    >第' + str(
                                    fail_times) + '个失败！重命名文件夹失败，重复的影片，已存在相同文件夹：' + relative_path + file + '\n'
                                print(fail_message, end='')
                                fail_list.append(fail_message)
                                write_fail(fail_message)
                                continue
                    else:        # 不是独立，还有其他影片
                        if not os.path.exists(root + '/' + new_folder):   # 准备建个新的文件夹，确认没有同名文件夹
                            os.makedirs(root + '/' + new_folder)
                        # 放进独立文件夹
                        os.rename(root + '/' + file, root + '/' + new_folder + '/' + file)
                        new_root = root + '/' + new_folder                # 更新new_root 当前非独立的目录+新目录名称=新独立的文件夹
                        print('    >创建独立的文件夹完成')
                        # 移动字幕
                        if subt_name:
                            os.rename(root + '/' + subt_name, root + '/' + new_folder + '/' + subt_name)
                            print('    >移动字幕到独立文件夹')

                # 更新一下relative_path
                relative_path = '/' + new_root.lstrip(path) + '/' + file  # 影片的相对于所选文件夹的路径，用于报错

                # 3写入nfo开始
                if if_nfo == '是':
                    cus_title = ''
                    for i in title_list:
                        cus_title += nfo_dict[i]
                    # 开始写入nfo，这nfo格式是参考的kodi的nfo
                    info_path = new_root + '/' + new_mp4 + '.nfo'      #nfo存放的地址
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
                        f.write("  <actor>\n    <name>" + i + "</name>\n    <type>Actor</type>\n  </actor>\n")
                    f.write("</movie>\n")
                    f.close()
                    print('    >nfo收集完成')

                # 4需要两张图片
                if if_jpg == '是':
                    # 下载海报的地址 cover
                    cover_url = 'http:' + cover_url
                    # print(cover_url.replace('pics.dmm.co.jp', 'jp.netcdn.space'))   有人向我建议用avmoo的图片地址代替dmm
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
                            fail_times += 1
                            fail_message = '    >第' + str(
                                fail_times) + '个失败！连接javbus失败，下载fanart失败：' + bus_search_url + '，' + relative_path + '\n'
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
                            print('    >正在从javbus下载封面：', cover_url)
                            try:
                                download_pic(cover_list)
                                print('    >fanart.jpg下载成功')
                            except:
                                fail_times += 1
                                fail_message = '    >第' + str(fail_times) + '个失败！下载fanart.jpg失败：' + cover_url + '，' + relative_path + '\n'
                                print(fail_message, end='')
                                fail_list.append(fail_message)
                                write_fail(fail_message)
                                continue
                        else:
                            fail_times += 1
                            fail_message = '    >第' + str(
                                fail_times) + '个失败！从javbus上查找封面失败：' + bus_search_url + '，' + relative_path + '\n'
                            print(fail_message, end='')
                            fail_list.append(fail_message)
                            write_fail(fail_message)
                            continue
                    # 裁剪生成 poster
                    img = Image.open(fanart_path)
                    w, h = img.size                        # fanart的宽 高
                    ex = int(w*0.52625)                    # 0.525是海报宽（800-379）/800原长
                    poster = img.crop((ex, 0, w, h))       # （ex，0）是左下角（x，y）坐标 （w, h)是右上角（x，y）坐标
                    poster.save(poster_path, quality=95)   # quality=95 是无损crop，如果不设置，默认75
                    print('    >poster.jpg裁剪成功')

                # 5收集女优头像
                if if_sculpture == '是':
                    if actors[0] == '未知演员':
                        print('    >未知演员')
                    else:
                        for each_actor in actors:
                            exist_actor_path = '女优头像/' + each_actor + '.jpg'  # 事先准备好的女优头像路径
                            # print(exist_actor_path)
                            jpg_type = '.jpg'
                            if not os.path.exists(exist_actor_path):                # 女优jpg图片还没有
                                exist_actor_path = '女优头像/' + each_actor + '.png'
                                if not os.path.exists(exist_actor_path):            # 女优png图片还没有
                                    fail_times += 1
                                    fail_message = '    >第' + str(
                                        fail_times) + '个失败！没有女优头像：' + each_actor + '，' + relative_path + '\n'
                                    print(fail_message, end='')
                                    fail_list.append(fail_message)
                                    write_fail(fail_message)
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
                            actors_path = new_root + '/.actors/'                    # 已经收录了这个女优头像
                            if not os.path.exists(actors_path):
                                os.makedirs(actors_path)
                            shutil.copyfile('女优头像/' + each_actor + jpg_type,
                                            actors_path + each_actor + jpg_type)       # 复制一份到“.actors”
                            print('    >女优头像收集完成：', each_actor)

                # 6归类影片，针对文件夹
                if if_classify == '是' and file_folder == '文件夹' and (
                        cars_dic[car_num] == 1 or (cars_dic[car_num] > 1 and cars_dic[car_num] == srt.episodes)):
                    # 需要移动文件夹，且，是该影片的最后一集
                    if separate_folder and classify_root.startswith(root):      # 用户选择的文件夹是一部影片的独立文件夹，为了避免在这个文件夹里又建立新的独立文件夹
                        print('    >无法归类，请选择该文件夹的上级目录作它的归类根目录', root.lstrip(path))
                        continue
                    class_root = classify_root + '/'
                    # 移动的目标文件夹
                    for j in classify_list:
                        class_root += nfo_dict[j].rstrip(' .')  # C:/Users/JuneRain/Desktop/测试文件夹/1/葵司/
                    new_new_root = class_root + new_folder  # 移动的目标文件夹 C:/Users/JuneRain/Desktop/测试文件夹/1/葵司/【葵司】AVOP-127
                    if not os.path.exists(new_new_root):
                        os.makedirs(new_new_root)
                        jav_files = os.listdir(new_root)
                        for i in jav_files:
                            os.rename(new_root + '/' + i, new_new_root + '/' + i)
                        os.rmdir(new_root)
                        print('    >归类文件夹完成')
                    else:
                        fail_times += 1
                        fail_message = '    >第' + str(fail_times) + '个失败！归类失败，重复的影片，归类的目标目录已存在相同文件夹：' + new_new_root + '\n'
                        print(fail_message, end='')
                        fail_list.append(fail_message)
                        write_fail(fail_message)
                        continue

            except:
                fail_times += 1
                fail_message = '    >第' + str(fail_times) + '个失败！发生错误，如一直在该影片报错请截图并联系作者：' + relative_path + '\n'\
                               + traceback.format_exc() + '\n'
                print(fail_message, end='')
                fail_list.append(fail_message)
                write_fail(fail_message)
                continue
    # 完结撒花
    print('\n当前文件夹完成，', end='')
    if fail_times > 0:
        print('失败', fail_times, '个!  ', path, '\n')
        if len(fail_list) > 0:
            for fail in fail_list:
                print(fail, end='')
        print('\n“【记得清理它】失败记录.txt”已记录错误\n')
    else:
        print('没有处理失败的AV，干得漂亮！  ', path, '\n')
    # os.system('pause')
    start_key = input('回车继续选择文件夹整理：')
