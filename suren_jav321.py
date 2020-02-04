# -*- coding:utf-8 -*-
import requests, re, os, shutil, configparser, time, hashlib, json, traceback
from PIL import Image
from time import sleep
from tkinter import filedialog, Tk
from shutil import copyfile


# 功能为记录错误txt
def write_fail(fail_m):
    record_txt = open('【记得清理它】失败记录.txt', 'a', encoding="utf-8")
    record_txt.write(fail_m)
    record_txt.close()


# get_directory功能为获取用户选取的文件夹路径
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
        return '无法翻译该标题作简介，请自行翻译。'
    except:
        print('    >正在尝试重新日译中...')
        return tran(api_id, key, word, to_lang)


# 获取网页源码，返回网页text；假装python的“重载”函数
def get_jav_html(url_list):
    if len(url_list) == 2:
        return requests.post(url_list[0], data=url_list[1], headers=headers, timeout=10).text
    else:
        return requests.post(url_list[0], data=url_list[1], proxies=url_list[2], headers=headers, timeout=10).text


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
        raise Exception('    >下载多次，仍然失败')


# 每一部jav的“结构体”
class JavFile(object):
    def __init__(self):
        self.name = 'ABC-123.mp4'  # 文件名
        self.car = 'ABC-123'  # 车牌
        self.episodes = 0     # 第几集
        self.subt = ''        # 字幕文件名  ABC-123.srt


# 读取配置文件
print('1、请开启代理，建议美国节点，访问“https://www.jav321.com/”\n'
      '2、影片信息没有导演，没有演员头像，可能没有演员姓名\n'
      '3、如有素人车牌识别不出，请在ini中添加该车牌\n')
print('正在读取ini中的设置...', end='')
try:
    config_settings = configparser.ConfigParser()
    config_settings.read('ini的设置会影响所有exe的操作结果.ini', encoding='utf-8-sig')
    if_nfo = config_settings.get("收集nfo", "是否收集nfo？")
    if_exnfo = config_settings.get("收集nfo", "是否跳过已存在nfo的文件夹？")
    custom_title = config_settings.get("收集nfo", "nfo中title的格式")
    if_jpg = config_settings.get("下载封面", "是否下载封面海报？")
    custom_fanart = config_settings.get("下载封面", "DVD封面的格式")
    custom_poster = config_settings.get("下载封面", "海报的格式")
    if_mp4 = config_settings.get("重命名影片", "是否重命名影片？")
    rename_mp4 = config_settings.get("重命名影片", "重命名影片的格式")
    if_folder = config_settings.get("修改文件夹", "是否重命名或创建独立文件夹？")
    rename_folder = config_settings.get("修改文件夹", "新文件夹的格式")
    if_rename_subt = config_settings.get("字幕文件", "是否重命名已有的字幕文件")
    if_classify_subt = config_settings.get("字幕文件", "是否使用字幕库")
    if_classify = config_settings.get("归类影片", "是否归类影片？")
    file_folder = config_settings.get("归类影片", "针对文件还是文件夹？")
    classify_root = config_settings.get("归类影片", "归类的根目录")
    classify_basis = config_settings.get("归类影片", "归类的标准")
    if_proxy = config_settings.get("代理", "是否使用代理？")
    proxy = config_settings.get("代理", "代理IP及端口")
    if_tran = config_settings.get("百度翻译API", "是否翻译为中文？")
    ID = config_settings.get("百度翻译API", "APP ID")
    SK = config_settings.get("百度翻译API", "密钥")
    simp_trad = config_settings.get("其他设置", "简繁中文？")
    suren_pref = config_settings.get("其他设置", "素人车牌(若有新车牌请自行添加)")
    file_type = config_settings.get("其他设置", "扫描文件类型")
    title_len = int(config_settings.get("其他设置", "重命名中的标题长度（50~150）"))
    subt_words = config_settings.get("原影片文件的性质", "是否中字即文件名包含")
    custom_subt = config_settings.get("原影片文件的性质", "是否中字的表现形式")
    xx_words = config_settings.get("原影片文件的性质", "是否xx即文件名包含")
    custom_xx = config_settings.get("原影片文件的性质", "是否xx的表现形式")
    movie_type = config_settings.get("原影片文件的性质", "素人")
except:
    print(traceback.format_exc())
    print('\n无法读取ini文件，请修改它为正确格式，或者打开“【ini】重新创建ini.exe”创建全新的ini！')
    os.system('pause')
print('\n读取ini文件成功! ')

# 归类文件夹具有最高决定权
if if_classify == '是':            # 如果需要归类
    if file_folder == '文件夹':    # 并且是针对文件夹
        if_folder = '是'           # 那么必须重命名文件夹或者创建新的文件夹
    else:
        if_folder = '否'           # 否则不会操作新文件夹
# 简繁
if simp_trad == '简':  # https://tw.jav321.com/video/ssni00643
    url = 'https://www.jav321.com/search'
    t_lang = 'zh'          # 百度翻译，日译简中
else:
    url = 'https://tw.jav321.com/search'
    t_lang = 'cht'
# 确认：代理哪些站点
proxies = {"http": "http://" + proxy, "https": "https://" + proxy}
if if_proxy == '是' and proxy != '':      # 是否需要代理，设置requests请求时的状态
    jav_list = [url, {}, proxies]              # 代理javbus
    cover_list = [0, '', '', proxies]        # 代理javbus上的图片  0错误次数  1图片url  2图片路径  3proxies
else:
    jav_list = [url, {}]
    cover_list = [0, '', '']
# 初始化其他
nfo_dict = {'空格': ' ', '车牌': 'ABC-123', '标题': '未知标题', '完整标题': '完整标题',
            '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
            '片商': '未知片商', '评分': '0', '首个女优': '未知演员', '全部女优': '未知演员',
            '片长': '0', '/': '/', '是否中字': custom_subt, '视频': 'ABC-123', '车牌前缀': 'ABC',
            '是否xx': custom_xx, '影片类型': movie_type, '系列': '未知系列'}  # 用于暂时存放影片信息，女优，标题等
suren_list = suren_pref.split('、')
rename_mp4_list = rename_mp4.split('+')
rename_folder_list = rename_folder.split('+')
type_tuple = tuple(file_type.split('、'))
classify_basis_list = classify_basis.split('/')
title_list = custom_title.replace('标题', '完整标题', 1).split('+')
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}  # 伪装成浏览器浏览网页

start_key = ''
while start_key == '':
    # 用户选择文件夹
    print('请选择要整理的文件夹：', end='')
    path = get_directory()
    print(path)
    write_fail('已选择文件夹：' + path + '\n')
    print('...文件扫描开始...如果时间过长...请避开中午夜晚高峰期...\n')
    #
    if if_classify == '是':
        classify_root = classify_root.rstrip('/')
        if classify_root != '所选文件夹':
            if classify_root != path:  # 归类根目录和所选不一样，继续核实归类根目录和所选不一样的合法性
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
    #
    fail_times = 0  # 处理过程中错失败的个数
    fail_list = []  # 用于存放处理失败的信息
    # 【当前路径】 【子目录】 【文件】
    for root, dirs, files in os.walk(path):
        if if_classify == '是' and root.startswith(classify_root):
            # print('>>该文件夹在归类的根目录中，跳过处理...', root)
            continue
        if if_exnfo == '是' and files and (files[-1].endswith('nfo') or (len(files) > 1 and files[-2].endswith('nfo'))):
            continue
        # 对这一层文件夹进行评估,有多少视频，有多少同车牌视频，是不是独立文件夹
        jav_videos = []        # 存放：需要整理的jav的结构体
        cars_dic = {}          # car 车牌
        videos_num = 0        # 当前文件夹中视频的数量，可能有视频不是jav
        subtitles = False      # 有没有字幕
        subts_dict = {}          # 存放：jav的字幕文件{'路径': '文件中的车牌'}
        for raw_file in files:
            # 判断文件是不是字幕文件
            if raw_file.endswith(('.srt', '.vtt', '.ass', '.ssa',)):
                srt_g = re.search(r'([a-zA-Z]{2,7})-? ?_?(\d{2,6})', raw_file)  # 这个正则表达式匹配“车牌号”可能有点奇怪，
                if str(srt_g) != 'None':  # 如果你下过上千部片，各种参差不齐的命名，你就会理解我了。
                    num_pref = srt_g.group(1).upper()
                    if num_pref in suren_list:
                        num_suf = srt_g.group(2)
                        car_num = num_pref + '-' + num_suf
                        subts_dict[raw_file] = car_num
                continue
        # print(subts_dict)
        # print('>>扫描字幕文件完毕！')
        for raw_file in files:
            # 判断是不是视频，得到车牌号
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
                # 当前文件夹下， 车牌不止一个，还有其他非jav视频，有其他文件夹
                separate_folder = False
            else:
                separate_folder = True
        else:
            continue

        # 正式开始
        for srt in jav_videos:
            car_num = srt.car
            file = srt.name
            relative_path = '/' + root.lstrip(path) + '/' + file  # 影片的相对于所选文件夹的路径，用于报错
            try:
                # 获取nfo信息的jav321搜索网页
                jav_list[1] = {'sn': car_num}
                try:
                    jav_html = get_jav_html(jav_list)
                except:
                    print('>>尝试打开jav321搜索页面失败，正在尝试第二次打开...')
                    try:
                        jav_html = get_jav_html(jav_list)
                        print('    >第二次尝试成功！')
                    except:
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '个失败！连接jav321失败，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                # 尝试找标题
                titleg = re.search(r'<h3>(.+?) <small>', jav_html)  # 匹配处理“标题”
                # 搜索结果就是AV的页面
                if str(titleg) != 'None':
                    only_title = titleg.group(1)
                    # print(only_title)
                # 找不到标题，jav321找不到影片
                else:
                    fail_times += 1
                    fail_message = '第' + str(fail_times) + '个失败！找不到该车牌的影片：' + relative_path + '\n'
                    print('>>' + fail_message, end='')
                    fail_list.append('    >' + fail_message)
                    write_fail('    >' + fail_message)
                    continue

                # 影片的一些属性
                video_type = '.' + file.split('.')[-1]  # 文件类型，如：.mp4
                subt_name = srt.subt
                if subt_name:
                    subtitles = True
                    subt_type = '.' + subt_name.split('.')[-1]  # 文件类型，如：.srt
                else:
                    subtitles = False
                    subt_type = ''
                nfo_dict['是否中字'] = ''
                if not subtitles:  # 没有外挂字幕
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
                # 正则匹配 影片信息 开始
                # 车牌号
                nfo_dict['车牌'] = re.search(r'番.</b>: (.+?)<br>', jav_html).group(1).upper()
                nfo_dict['车牌前缀'] = nfo_dict['车牌'].split('-')[0]
                # 去除title中的特殊字符
                only_title = only_title.replace('\n', '').replace('&', '和').replace('/', '#') \
                    .replace('/', '#').replace(':', '：').replace('*', '#').replace('?', '？') \
                    .replace('"', '#').replace('<', '【').replace('>', '】') \
                    .replace('|', '#').replace('＜', '【').replace('＞', '】') \
                    .replace('〈', '【').replace('〉', '】').replace('＆', '和').replace('\t', '').replace('\r', '')
                # 素人的title开头不是车牌
                title = nfo_dict['车牌'] + ' ' + only_title
                print('>>正在处理：', title)
                # 处理标题过长
                nfo_dict['完整标题'] = only_title
                if len(only_title) > title_len:
                    nfo_dict['标题'] = only_title[:title_len]
                else:
                    nfo_dict['标题'] = only_title
                # 片商</b>: <a href="/company/%E83%A0%28PRESTIGE+PREMIUM%29/1">プレステージプレミアム(PRESTIGE PREMIUM)</a>
                studiog = re.search(r'<a href="/company.+?">(.+?)</a>', jav_html)
                if str(studiog) != 'None':
                    nfo_dict['片商'] = studiog.group(1)
                else:
                    nfo_dict['片商'] = '未知片商'
                # 上映日 (\d\d\d\d-\d\d-\d\d)</td>
                premieredg = re.search(r'日期</b>: (\d\d\d\d-\d\d-\d\d)<br>', jav_html)
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
                runtimeg = re.search(r'播放..</b>: (\d+)', jav_html)
                if str(runtimeg) != 'None':
                    nfo_dict['片长'] = runtimeg.group(1)
                else:
                    nfo_dict['片长'] = '0'
                # 没有导演
                # 演员们 和 # 第一个演员   女优</b>: 花音さん 21歳 床屋さん(家族経営) &nbsp
                actorg = re.search(r'<small>(.+?)</small>', jav_html)
                if str(actorg) != 'None':
                    actor_str = actorg.group(1)
                    actor_list = actor_str.replace('/', ' ').split(' ')  # <small>luxu-071 松波優 29歳 システムエンジニア</small>
                    actor_list = [i for i in actor_list if i != '']
                    if len(actor_list) > 3:
                        nfo_dict['首个女优'] = actor_list[1] + ' ' + actor_list[2] + ' ' + actor_list[3]
                    elif len(actor_list) > 1:
                        del actor_list[0]
                        nfo_dict['首个女优'] = ' '.join(actor_list)
                    else:
                        nfo_dict['首个女优'] = '素人'
                    nfo_dict['全部女优'] = nfo_dict['首个女优']
                else:
                    nfo_dict['首个女优'] = nfo_dict['全部女优'] = '素人'
                # print(nfo_dict['全部女优'])
                # 特点
                genres = re.findall(r'genre.+?">(.+?)</a>', jav_html)
                genres = [i for i in genres if i != '标签' and i != '標籤']
                if nfo_dict['是否中字']:
                    genres.append('中文字幕')
                if nfo_dict['是否xx']:
                    genres.append('无码流出')
                # 下载封面 cover fanart
                coverg = re.search(r'poster="(.+?)"><source', jav_html)  # 封面图片的正则对象
                if str(coverg) != 'None':
                    cover_url = coverg.group(1)
                else:  # src="http://pics.dmm.co.jp/digital/amateur/scute530/scute530jp-001.jpg"
                    coverg = re.search(r'img-responsive" src="(.+?)"', jav_html)  # 封面图片的正则对象
                    if str(coverg) != 'None':
                        cover_url = coverg.group(1)
                    else:  # src="http://pics.dmm.co.jp/digital/amateur/scute530/scute530jp-001.jpg"
                        coverg = re.search(r'src="(.+?)"', jav_html)  # 封面图片的正则对象
                        if str(coverg) != 'None':
                            cover_url = coverg.group(1)
                        else:
                            cover_url = ''
                # 下载海报 poster
                posterg = re.search(r'img-responsive" src="(.+?)"', jav_html)  # 封面图片的正则对象
                if str(posterg) != 'None':
                    poster_url = posterg.group(1)
                else:
                    poster_url = ''
                # 评分
                scoreg = re.search(r'评分</b>: (\d\.\d)<br>', jav_html)
                if str(scoreg) != 'None':
                    score = float(scoreg.group(1))
                    score = (score - 2) * 10 / 3
                    if score >= 0:
                        score = '%.1f' % score
                        nfo_dict['评分'] = str(score)
                    else:
                        nfo_dict['评分'] = '0'
                else:
                    scoreg = re.search(r'"/img/(\d\d)\.gif', jav_html)
                    if str(scoreg) != 'None':
                        score = float(scoreg.group(1))/10
                        score = (score - 2) * 10 / 3
                        if score >= 0:
                            score = '%.1f' % score
                            nfo_dict['评分'] = str(score)
                        else:
                            nfo_dict['评分'] = '0'
                    else:
                        nfo_dict['评分'] = '0'
                criticrating = str(float(nfo_dict['评分'])*10)
                # 素人上没有企划set
                # 把标题当做plot
                plot = only_title
                if if_nfo == '是' and if_tran == '是':
                    print('    >正在日译中...')
                    plot = tran(ID, SK, title, t_lang)

                # 1重命名视频
                new_mp4 = file[:-len(video_type)].rstrip(' ')
                if if_mp4 == '是':
                    # 新文件名new_mp4
                    new_mp4 = ''
                    # print(nfo_dict['完整标题'])
                    for j in rename_mp4_list:
                        new_mp4 += nfo_dict[j]
                    new_mp4 = new_mp4.rstrip(' ')
                    cd_msg = ''
                    if cars_dic[car_num] > 1:  # 是CD1还是CDn？
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

                # nfo_dict['视频']用于图片的命名
                nfo_dict['视频'] = new_mp4

                # 1.5 归类影片，只针对影片
                if if_classify == '是' and file_folder != '文件夹':
                    # 需要归类影片，针对这个影片
                    class_root = classify_root + '/'
                    # 移动的目标文件夹
                    for j in classify_list:
                        class_root += nfo_dict[j].rstrip(' .')      # C:/Users/JuneRain/Desktop/测试文件夹/1/葵司/
                    new_root = class_root              # 新的影片的目录路径，C:/Users/JuneRain/Desktop/测试文件夹/1/葵司/
                    new_folder = new_root.split('/')[-1]  # 新的影片的目录名称，变成了目标目录“葵司”
                    if not os.path.exists(new_root):   # 不存在目标文件夹
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
                    new_root = root  # 当前影片的目录路径，在下面的重命名操作中将发生变化
                    new_folder = root.split('/')[-1]  # 当前影片的目录名称，在下面的重命名操作中即将发生变化

                # 2重命名文件夹
                if if_folder == '是':
                    # 新文件夹名rename_folder
                    new_folder = ''
                    for j in rename_folder_list:
                        new_folder += (nfo_dict[j])
                    new_folder = new_folder.rstrip(' .')
                    if separate_folder:
                        if cars_dic[car_num] == 1 or (
                                cars_dic[car_num] > 1 and cars_dic[car_num] == srt.episodes):  # 同一车牌有多部，且这是最后一部，才会重命名
                            newroot_list = root.split('/')
                            del newroot_list[-1]
                            upper2_root = '/'.join(newroot_list)
                            new_root = upper2_root + '/' + new_folder  # 当前文件夹就会被重命名
                            if not os.path.exists(
                                    new_root) or new_root == root:  # 目标影片文件夹不存在，或者目标影片文件夹存在，但就是现在的文件夹，即新旧相同
                                # 修改文件夹
                                os.rename(root, new_root)
                                print('    >重命名文件夹完成')
                            else:  # 已经有一个那样的文件夹了
                                fail_times += 1
                                fail_message = '    >第' + str(
                                    fail_times) + '个失败！重命名文件夹失败，重复的影片，已存在相同文件夹：' + relative_path + file + '\n'
                                print(fail_message, end='')
                                fail_list.append(fail_message)
                                write_fail(fail_message)
                                continue
                    else:
                        if not os.path.exists(root + '/' + new_folder):  # 已经存在目标文件夹
                            os.makedirs(root + '/' + new_folder)
                        # 创建独立的文件夹完成
                        os.rename(root + '/' + file, root + '/' + new_folder + '/' + file)  # 就把影片放进去
                        new_root = root + '/' + new_folder  # 在当前文件夹下再创建新文件夹
                        print('    >创建独立的文件夹完成')
                        if subt_name:
                            os.rename(root + '/' + subt_name, root + '/' + new_folder + '/' + subt_name)  # 就把字幕放进去
                            print('    >移动字幕到独立文件夹')

                # 更新一下relative_path
                relative_path = '/' + new_root.lstrip(path) + '/' + file  # 影片的相对于所选文件夹的路径，用于报错

                # 3写入nfo
                if if_nfo:
                    cus_title = ''
                    for i in title_list:
                        cus_title += nfo_dict[i]
                    # 写入nfo开始
                    info_path = new_root + '/' + new_mp4 + '.nfo'
                    # 开始写入nfo
                    f = open(info_path, 'w', encoding="utf-8")
                    f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>\n"
                            "<movie>\n"
                            "  <plot>" + plot + "</plot>\n"
                            "  <title>" + cus_title + "</title>\n"
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
                            "  <num>" + nfo_dict['车牌'] + "</num>\n")
                    for i in genres:
                        f.write("  <genre>" + i + "</genre>\n")
                    f.write("  <genre>片商:" + nfo_dict['片商'] + "</genre>\n")
                    for i in genres:
                        f.write("  <tag>" + i + "</tag>\n")
                    f.write("  <tag>片商:" + nfo_dict['片商'] + "</tag>\n")
                    f.write("  <actor>\n    <name>" + nfo_dict['首个女优'] + "</name>\n    <type>Actor</type>\n  </actor>\n")
                    f.write("</movie>\n")
                    f.close()
                    print("    >nfo收集完成")

                # 4需要两张图片
                if if_jpg == '是':
                    # fanart和poster路径
                    fanart_path = new_root + '/'
                    poster_path = new_root + '/'
                    for i in fanart_list:
                        fanart_path += nfo_dict[i]
                    for i in poster_list:
                        poster_path += nfo_dict[i]
                    # 下载海报的地址 cover
                    print('    >fanart.jpg的链接：', cover_url)
                    # 下载 海报
                    cover_list[0] = 0
                    cover_list[1] = cover_url
                    cover_list[2] = fanart_path
                    try:
                        download_pic(cover_list)
                        print('    >fanart.jpg下载成功')
                    except:
                        fail_times += 1
                        fail_message = '    >第' + str(
                            fail_times) + '个失败！fanart下载失败：' + cover_url + '，网络不佳，下载失败：' + relative_path + '\n'
                        print(fail_message, end='')
                        fail_list.append(fail_message)
                        write_fail(fail_message)
                        continue
                    # 下载poster.jpg   img-responsive" src="https://www.jav321.com/images/prestigepremium/300mium/034/pf_o1_300mium-034.jpg">
                    print('    >poster.jpg的链接：', poster_url)
                    cover_list[0] = 0
                    cover_list[1] = poster_url
                    cover_list[2] = poster_path
                    try:
                        download_pic(cover_list)
                        print('    >poster.jpg下载成功')
                    except:
                        fail_times += 1
                        fail_message = '    >第' + str(
                            fail_times) + '个失败！poster下载失败：' + relative_path + '\n'
                        print(fail_message, end='')
                        fail_list.append(fail_message)
                        write_fail(fail_message)
                        continue

                # 5收集女优头像

                # 6归类影片，针对文件夹
                if if_classify == '是' and file_folder == '文件夹' and (
                        cars_dic[car_num] == 1 or (cars_dic[car_num] > 1 and cars_dic[car_num] == srt.episodes)):
                    # 需要移动文件夹，且，是该影片的最后一集
                    if separate_folder and classify_root.startswith(root):
                        print('    >无法归类，请选择该文件夹的上级目录作它的归类根目录', root.lstrip(path))
                        continue
                    class_root = classify_root + '/'
                    # 对归类标准再细化
                    for j in classify_list:
                        class_root += nfo_dict[j].rstrip(' .')  # C:/Users/JuneRain/Desktop/测试文件夹/1/葵司/
                    new_new_root = class_root + new_folder  # 移动的目标文件夹 C:/Users/JuneRain/Desktop/测试文件夹/1/葵司/【葵司】AVOP-127
                    if not os.path.exists(new_new_root):    # 不存在目标目录
                        os.makedirs(new_new_root)
                        jav_files = os.listdir(new_root)
                        for i in jav_files:
                            os.rename(new_root + '/' + i, new_new_root + '/' + i)
                        os.rmdir(new_root)
                        print('    >归类文件夹完成')
                    else:
                        fail_times += 1
                        fail_message = '    >第' + str(fail_times) + '个失败！归类失败，重复的影片，归类的根目录已存在相同文件夹：' + new_new_root + '\n'
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

    print('\n当前文件夹完成，', end='')
    if fail_times > 0:
        print('失败', fail_times, '个!  ', path, '\n')
        if len(fail_list) > 0:
            for fail in fail_list:
                print(fail, end='')
        print('\n“【记得清理它】失败记录.txt”已记录错误\n')
    else:
        print('没有处理失败的AV，干得漂亮！  ', path, '\n')

    start_key = input('回车继续选择文件夹整理：')
