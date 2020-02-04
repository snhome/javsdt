# -*- coding:utf-8 -*-
import re, os, configparser, requests, shutil, traceback, time, hashlib, json
from PIL import Image
from tkinter import filedialog, Tk
from time import sleep


# get_directory功能是 获取用户选取的文件夹路径
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


# 功能为记录错误txt
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
        rqs = requests.get(url_list[0], timeout=10, headers={'Cookie': 'existmag=all'})
    else:
        rqs = requests.get(url_list[0], proxies=url_list[1], timeout=10, headers={'Cookie': 'existmag=all'})
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
print('1、避开21:00-1:00，访问javbus和arzon很慢。\n'
      '1、如果连不上javbus，请更正防屏蔽地址\n'
      '   不要用“www.javbus.com”！\n')
# 读取配置文件，这个ini文件用来给用户设置重命名的格式和jav网址
print('正在读取ini中的设置...', end='')
try:
    config_settings = configparser.RawConfigParser()
    config_settings.read('ini的设置会影响所有exe的操作结果.ini', encoding='utf-8-sig')
    if_nfo = config_settings.get("收集nfo", "是否收集nfo？")
    if_exnfo = config_settings.get("收集nfo", "是否跳过已存在nfo的文件夹？")
    custom_title = config_settings.get("收集nfo", "nfo中title的格式")
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
        print('\n    >“【缺失的女优头像统计For Kodi】.ini”文件被你玩坏了...正在重写ini...成功！')
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
    jav_list = ['', proxies]              # 代理jav等
    arzon_list = ['', acook, proxies]     # 代理arzon
    cover_list = [0, '', '', proxies]     # 代理dmm
else:
    jav_list = ['']
    arzon_list = ['', acook]
    cover_list = [0, '', '']
# https://www.buscdn.work/
if not bus_url.endswith('/'):
    bus_url += '/'
# 归类文件夹具有最高决定权
if if_classify == '是':            # 如果需要归类
    if file_folder == '文件夹':    # 并且是针对文件夹
        if_folder = '是'           # 那么必须重命名文件夹或者创建新的文件夹
    else:
        if_folder = '否'           # 否则不会操作新文件夹
# 百度翻译是简/繁中文
if simp_trad == '简':
    t_lang = 'zh'
else:
    t_lang = 'cht'
# 初始化其他
nfo_dict = {'空格': ' ', '车牌': 'ABC-123', '标题': '未知标题', '完整标题': '完整标题', '导演': '未知导演',
            '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
            '片商': '未知片商', '首个女优': '未知演员', '全部女优': '未知演员',
            '片长': '0', '/': '/', '是否中字': '', '视频': 'ABC-123', '车牌前缀': 'ABC',
            '是否xx': '', '影片类型': movie_type, '系列': '未知系列'}         # 用于暂时存放影片信息，女优，标题等
suren_list = suren_pref.split('、')              # 素人番号的列表
rename_mp4_list = rename_mp4.split('+')          # 重命名视频的格式
rename_folder_list = rename_folder.split('+')    # 重命名文件夹的格式
type_tuple = tuple(file_type.split('、'))        # 需要扫描的文件的类型
classify_basis_list = classify_basis.split('/')  # 归类标准，归类到哪个文件夹
title_list = custom_title.replace('标题', '完整标题', 1).split('+')  # nfo中title的写法
fanart_list = custom_fanart.split('+')  # fanart的格式
poster_list = custom_poster.split('+')  # poster的格式
word_list = subt_words.split('、')      # 包含哪些特殊含义的文字，判断是否中字
xx_list = xx_words.split('、')          # 包含哪些特殊含义的文字，判断是否xx
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
# 特点，繁转简
gen_dict = {'折磨': '折磨', '嘔吐': '呕吐', '觸手': '触手', '蠻橫嬌羞': '蛮横娇羞', '處男': '处男', '正太控': '正太控',
            '出軌': '出轨', '瘙癢': '瘙痒', '運動': '运动', '女同接吻': '女同接吻', '性感的x': '性感的', '美容院': '美容院',
            '處女': '处女', '爛醉如泥的': '烂醉如泥的', '殘忍畫面': '残忍画面', '妄想': '妄想', '惡作劇': '恶作剧', '學校作品': '学校作品',
            '粗暴': '粗暴', '通姦': '通奸', '姐妹': '姐妹', '雙性人': '双性人', '跳舞': '跳舞', '性奴': '性奴',
            '倒追': '倒追', '性騷擾': '性骚扰', '其他': '其他', '戀腿癖': '恋腿癖', '偷窥': '偷窥', '花癡': '花痴',
            '男同性恋': '男同性恋', '情侶': '情侣', '戀乳癖': '恋乳癖', '亂倫': '乱伦', '其他戀物癖': '其他恋物癖', '偶像藝人': '偶像艺人',
            '野外・露出': '野外・露出', '獵豔': '猎艳', '女同性戀': '女同性恋', '企畫': '企画', '10枚組': '10枚组', '性感的': '性感的',
            '科幻': '科幻', '女優ベスト・総集編': '女优的总编', '温泉': '温泉', 'M男': 'M男', '原作コラボ': '原作协作',
            '16時間以上作品': '16时间以上作品', 'デカチン・巨根': '巨根', 'ファン感謝・訪問': '感恩祭', '動画': '动画', '巨尻': '巨尻', 'ハーレム': '后宫',
            '日焼け': '晒黑', '早漏': '早漏', 'キス・接吻': '接吻.', '汗だく': '汗流浃背', 'スマホ専用縦動画': '智能手机的垂直视频', 'Vシネマ': '电影放映',
            'Don Cipote\'s choice': 'Don Cipote\'s choice', 'アニメ': '日本动漫', 'アクション': '动作', 'イメージビデオ（男性）': '（视频）男性', '孕ませ': '孕育', 'ボーイズラブ': '男孩恋爱',
            'ビッチ': 'bitch', '特典あり（AVベースボール）': '特典（AV棒球）', 'コミック雑誌': '漫画雑志', '時間停止': '时间停止',

            '黑幫成員': '黑帮成员', '童年朋友': '童年朋友', '公主': '公主', '亞洲女演員': '亚洲女演员', '伴侶': '伴侣', '講師': '讲师',
            '婆婆': '婆婆', '格鬥家': '格斗家', '女檢察官': '女检察官', '明星臉': '明星脸', '女主人、女老板': '女主人、女老板', '模特兒': '模特',
            '秘書': '秘书', '美少女': '美少女', '新娘、年輕妻子': '新娘、年轻妻子', '姐姐': '姐姐', '車掌小姐': '车掌小姐',
            '寡婦': '寡妇', '千金小姐': '千金小姐', '白人': '白人', '已婚婦女': '已婚妇女', '女醫生': '女医生', '各種職業': '各种职业',
            '妓女': '妓女', '賽車女郎': '赛车女郎', '女大學生': '女大学生', '展場女孩': '展场女孩', '女教師': '女教师', '母親': '母亲',
            '家教': '家教', '护士': '护士', '蕩婦': '荡妇', '黑人演員': '黑人演员', '女生': '女生', '女主播': '女主播',
            '高中女生': '高中女生', '服務生': '服务生', '魔法少女': '魔法少女', '學生（其他）': '学生（其他）', '動畫人物': '动画人物', '遊戲的真人版': '游戏真人版',
            '超級女英雄': '超级女英雄',

            '角色扮演': '角色扮演', '制服': '制服', '女戰士': '女战士', '及膝襪': '及膝袜', '娃娃': '娃娃', '女忍者': '女忍者',
            '女裝人妖': '女装人妖', '內衣': '內衣', '猥褻穿著': '猥亵穿着', '兔女郎': '兔女郎', '貓耳女': '猫耳女', '女祭司': '女祭司',
            '泡泡襪': '泡泡袜', '緊身衣': '紧身衣', '裸體圍裙': '裸体围裙', '迷你裙警察': '迷你裙警察', '空中小姐': '空中小姐',
            '連褲襪': '连裤袜', '身體意識': '身体意识', 'OL': 'OL', '和服・喪服': '和服・丧服', '體育服': '体育服', '内衣': '内衣',
            '水手服': '水手服', '學校泳裝': '学校泳装', '旗袍': '旗袍', '女傭': '女佣', '迷你裙': '迷你裙', '校服': '校服',
            '泳裝': '泳装', '眼鏡': '眼镜', '哥德蘿莉': '哥德萝莉', '和服・浴衣': '和服・浴衣',

            '超乳': '超乳', '肌肉': '肌肉', '乳房': '乳房', '嬌小的': '娇小的', '屁股': '屁股', '高': '高',
            '變性者': '变性人', '無毛': '无毛', '胖女人': '胖女人', '苗條': '苗条', '孕婦': '孕妇', '成熟的女人': '成熟的女人',
            '蘿莉塔': '萝莉塔', '貧乳・微乳': '贫乳・微乳', '巨乳': '巨乳',


            '顏面騎乘': '颜面骑乘', '食糞': '食粪', '足交': '足交', '母乳': '母乳', '手指插入': '手指插入', '按摩': '按摩',
            '女上位': '女上位', '舔陰': '舔阴', '拳交': '拳交', '深喉': '深喉', '69': '69', '淫語': '淫语',
            '潮吹': '潮吹', '乳交': '乳交', '排便': '排便', '飲尿': '饮尿', '口交': '口交', '濫交': '滥交',
            '放尿': '放尿', '打手槍': '打手枪', '吞精': '吞精', '肛交': '肛交', '顏射': '颜射', '自慰': '自慰',
            '顏射x': '颜射', '中出': '中出', '肛内中出': '肛内中出',

            '立即口交': '立即口交', '女優按摩棒': '女优按摩棒', '子宮頸': '子宫颈', '催眠': '催眠', '乳液': '乳液', '羞恥': '羞耻',
            '凌辱': '凌辱', '拘束': '拘束', '輪姦': '轮奸', '插入異物': '插入异物', '鴨嘴': '鸭嘴', '灌腸': '灌肠',
            '監禁': '监禁', '紧缚': '紧缚', '強姦': '强奸', '藥物': '药物', '汽車性愛': '汽车性爱', 'SM': 'SM',
            '糞便': '粪便', '玩具': '玩具', '跳蛋': '跳蛋', '緊縛': '紧缚', '按摩棒': '按摩棒', '多P': '多P',
            '性愛': '性爱', '假陽具': '假阳具', '逆強姦': '逆强奸',

            '合作作品': '合作作品', '恐怖': '恐怖', '給女性觀眾': '女性向', '教學': '教学', 'DMM專屬': 'DMM专属', 'R-15': 'R-15',
            'R-18': 'R-18', '戲劇': '戏剧', '3D': '3D', '特效': '特效', '故事集': '故事集', '限時降價': '限时降价',
            '複刻版': '复刻版', '戲劇x': '戏剧', '戀愛': '恋爱', '高畫質': 'xxx', '主觀視角': '主观视角', '介紹影片': '介绍影片',
            '4小時以上作品': '4小时以上作品', '薄馬賽克': '薄马赛克', '經典': '经典', '首次亮相': '首次亮相', '數位馬賽克': '数位马赛克', '投稿': '投稿',
            '纪录片': '纪录片', '國外進口': '国外进口', '第一人稱攝影': '第一人称摄影', '業餘': '业余', '局部特寫': '局部特写', '獨立製作': '独立制作',
            'DMM獨家': 'DMM独家', '單體作品': '单体作品', '合集': '合集', '高清': '高清', '字幕': '字幕', '天堂TV': '天堂TV',
            'DVD多士爐': 'DVD多士炉', 'AV OPEN 2014 スーパーヘビー': 'AV OPEN 2014 S级', 'AV OPEN 2014 ヘビー級': 'AV OPEN 2014重量级', 'AV OPEN 2014 ミドル級': 'AV OPEN 2014中量级',
            'AV OPEN 2015 マニア/フェチ部門': 'AV OPEN 2015 狂热者/恋物癖部门', 'AV OPEN 2015 熟女部門': 'AV OPEN 2015 熟女部门',
            'AV OPEN 2015 企画部門': 'AV OPEN 2015 企画部门', 'AV OPEN 2015 乙女部門': 'AV OPEN 2015 少女部',
            'AV OPEN 2015 素人部門': 'AV OPEN 2015 素人部门', 'AV OPEN 2015 SM/ハード部門': 'AV OPEN 2015 SM/硬件',
            'AV OPEN 2015 女優部門': 'AV OPEN 2015 女优部门', 'AVOPEN2016人妻・熟女部門': 'AVOPEN2016人妻・熟女部门',
            'AVOPEN2016企画部門': 'AVOPEN2016企画部', 'AVOPEN2016ハード部門': 'AVOPEN2016ハード部',
            'AVOPEN2016マニア・フェチ部門': 'AVOPEN2016疯狂恋物科', 'AVOPEN2016乙女部門': 'AVOPEN2016少女部',
            'AVOPEN2016女優部門': 'AVOPEN2016女优部', 'AVOPEN2016ドラマ・ドキュメンタリー部門': 'AVOPEN2016电视剧纪录部',
            'AVOPEN2016素人部門': 'AVOPEN2016素人部', 'AVOPEN2016バラエティ部門': 'AVOPEN2016娱乐部',
            'VR専用': 'VR専用', '堵嘴·喜劇': '堵嘴·喜剧', '幻想': '幻想', '性別轉型·女性化': '性别转型·女性化',
            '為智能手機推薦垂直視頻': '为智能手机推荐垂直视频', '設置項目': '设置项目', '迷你係列': '迷你系列',
            '體驗懺悔': '体验忏悔', '黑暗系統': '黑暗系统',

            'オナサポ': '手淫', 'アスリート': '运动员', '覆面・マスク': '蒙面具', 'ハイクオリティVR': '高品质VR', 'ヘルス・ソープ': '保健香皂', 'ホテル': '旅馆',
            'アクメ・オーガズム': '绝顶高潮', '花嫁': '花嫁', 'デート': '约会', '軟体': '软体', '娘・養女': '养女', 'スパンキング': '打屁股',
            'スワッピング・夫婦交換': '夫妇交换', '部下・同僚': '部下・同僚', '旅行': '旅行', '胸チラ': '露胸', 'バック': '后卫', 'エロス': '爱的欲望',
            '男の潮吹き': '男人高潮', '女上司': '女上司', 'セクシー': '性感美女', '受付嬢': '接待小姐', 'ノーブラ': '不穿胸罩',
            '白目・失神': '白眼失神', 'M女': 'M女', '女王様': '女王大人', 'ノーパン': '不穿内裤', 'セレブ': '名流', '病院・クリニック': '医院诊所',
            '面接': '面试', 'お風呂': '浴室', '叔母さん': '叔母阿姨', '罵倒': '骂倒', 'お爺ちゃん': '爷爷', '逆レイプ': '强奸小姨子',
            'ディルド': 'ディルド', 'ヨガ': '瑜伽', '飲み会・合コン': '酒会、联谊会', '部活・マネージャー': '社团经理', 'お婆ちゃん': '外婆', 'ビジネススーツ': '商务套装',
            'チアガール': '啦啦队女孩', 'ママ友': '妈妈的朋友', 'エマニエル': '片商Emanieru熟女塾', '妄想族': '妄想族', '蝋燭': '蜡烛', '鼻フック': '鼻钩儿',
            '放置': '放置', 'サンプル動画': '范例影片', 'サイコ・スリラー': '心理惊悚片', 'ラブコメ': '爱情喜剧', 'オタク': '御宅族',
            '中文字幕': '中文字幕'}

start_key = ''
while start_key == '':
    # 用户选择文件夹
    print('请选择要整理的文件夹：', end='')
    path = get_directory()
    print(path)
    write_fail('已选择文件夹：' + path+'\n')
    print('...文件扫描开始...如果时间过长...请避开中午夜晚高峰期...\n')
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
    # 初始化“失败信息”
    fail_times = 0                             # 处理过程中错失败的个数
    fail_list = []                             # 用于存放处理失败的信息
    # os.system('pause')
    # root【当前根目录】 dirs【子目录】 files【文件】，root是字符串，后两个是列表
    for root, dirs, files in os.walk(path):
        if if_classify == '是' and root.startswith(classify_root):
            # print('>>该文件夹在归类的根目录中，跳过处理...', root)
            continue
        if if_exnfo == '是' and files and (files[-1].endswith('nfo') or (len(files) > 1 and files[-2].endswith('nfo'))):
            continue
        # 对这一层文件夹进行评估,有多少视频，有多少同车牌视频，是不是独立文件夹
        jav_videos = []  # 存放：需要整理的jav的结构体
        cars_dic = {}
        videos_num = 0  # 当前文件夹中视频的数量，可能有视频不是jav
        subtitles = False      # 有没有字幕
        subts_dict = {}          # 存放：jav的字幕文件
        for raw_file in files:
            # 判断文件是不是字幕文件
            if raw_file.endswith(('.srt', '.vtt', '.ass', '.ssa',)):
                srt_g = re.search(r'(\d?\d?[a-zA-Z]{1,7}\d?\d?)-? ?_?(\d{2,6})', raw_file)
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
                video_num_g = re.search(r'(\d?\d?[a-zA-Z]{1,7}\d?\d?)-? ?_?(\d{2,6})', raw_file)  # 这个正则表达式匹配“车牌号”可能有点奇怪，
                if str(video_num_g) != 'None':  # 如果你下过上千部片，各种参差不齐的命名，你就会理解我了。
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
                    if car_num not in cars_dic:  # cars_dic中没有这个车牌，表示这一层文件夹下新发现一个车牌
                        cars_dic[car_num] = 1  # 这个新车牌有了第一集
                    else:
                        cars_dic[car_num] += 1  # 已经有这个车牌了，加一集cd
                    jav_file = JavFile()
                    jav_file.car = car_num  # 车牌
                    jav_file.name = raw_file  # 原文件名
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
        # print(jav_videos)
        for srt in jav_videos:
            car_num = srt.car
            file = srt.name
            relative_path = '/' + root.lstrip(path) + '/' + file  # 影片的相对于所选文件夹的路径，用于报错
            try:
                # 获取nfo信息的javbus搜索网页  https://www.cdnbus.work/search/avop&type=&parent=ce
                bus_bu_url = bus_url + 'search/' + car_num + '&type=1&parent=ce'
                jav_list[0] = bus_bu_url
                try:
                    jav_html = get_jav_html(jav_list)
                except:
                    print('>>尝试打开javbus有码页面失败，正在尝试第二次打开...')
                    try:
                        jav_html = get_jav_html(jav_list)
                        print('    >第二次尝试成功！')
                    except:
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '个失败！连接javbus有码失败：' + bus_bu_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                # 搜索结果的网页，大部分情况一个结果，也有可能是多个结果的网页
                # 尝试找movie-box
                bav_urls = re.findall(r'<a class="movie-box" href="(.+?)">', jav_html)  # 匹配处理“标题”
                if len(bav_urls) == 1:  # 搜索结果页面只有一个box
                    bav_url = bav_urls[0]
                elif len(bav_urls) > 1:  # 找到不止一个box
                    print('>>该车牌：' + car_num + ' 搜索到多个结果，正在尝试精确定位...')
                    car_suf = re.findall(r'\d+', car_num)[-1]  # 当前车牌的后缀数字
                    car_suf = car_suf.lstrip('0')              # 去除-0001中的000
                    car_prefs = re.findall(r'[a-zA-Z]+', car_num)  # 匹配车牌的前缀字母
                    if car_prefs:
                        car_pref = car_prefs[-1].upper()
                    else:
                        car_pref = ''   # 也可能没字母，全是数字12345_678.mp4
                    bav_url = ''
                    for i in bav_urls:
                        # print(re.findall(r'\d+', i.split('/')[-1]))
                        url_suf = re.findall(r'\d+', i.split('/')[-1])[-1]  # 匹配处理“01”，box上影片车牌的后缀数字
                        url_suf = url_suf.lstrip('0')  # 去除-0001中的000
                        if car_suf == url_suf:         # 数字相同
                            url_prefs = re.findall(r'[a-zA-Z]+', i.split('/')[-1])  # 匹配处理“n”
                            if url_prefs:   # box的前缀字母
                                url_pref = url_prefs[-1].upper()
                            else:
                                url_pref = ''
                            if car_pref == url_pref:  # 数字相同的基础下，字母也相同，即可能车牌相同
                                bav_url = i
                                fail_times += 1
                                fail_message = '第' + str(fail_times) + '个警告！从“' + file + '”的多个搜索结果中确定为：' + bav_url + '\n'
                                print('>>' + fail_message, end='')
                                fail_list.append('    >' + fail_message)
                                write_fail('    >' + fail_message)
                                break
                        else:
                            continue
                    # 有码搜索的结果一个都匹配不上
                    if bav_url == '':
                        fail_times += 1
                        print(jav_html)
                        fail_message = '第' + str(fail_times) + '个失败！多个搜索结果也找不到AV信息：' + bus_bu_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                else:  # 找不到box
                    # 尝试在无码区搜索该车牌
                    bus_qi_url = bus_url + 'uncensored/search/' + car_num + '&type=&parent=uc'  # 有码搜索url
                    jav_list[0] = bus_qi_url
                    try:
                        jav_html = get_jav_html(jav_list)
                    except:
                        print('>>尝试打开javbus无码页面失败，正在尝试第二次打开...')
                        try:
                            jav_html = get_jav_html(jav_list)
                            print('    >第二次尝试成功！')
                        except:
                            fail_times += 1
                            fail_message = '第' + str(fail_times) + '个失败！连接javbus无码失败：' + bus_qi_url + '，' + relative_path + '\n'
                            print('>>' + fail_message, end='')
                            fail_list.append('    >' + fail_message)
                            write_fail('    >' + fail_message)
                            continue
                    bav_urls = re.findall(r'<a class="movie-box" href="(.+?)">', jav_html)  # 在“有码”中匹配处理“标题”
                    if len(bav_urls) > 0:
                        print('>>跳过无码影片：', file)
                        continue
                    # # 上面只能搜索
                    # bus_bu_url = bus_url + 'search/' + car_num + '&type=1'
                    # jav_list[0] = bus_bu_url
                    # try:
                    #     jav_html = get_jav_html(jav_list)
                    # except:
                    fail_times += 1
                    fail_message = '第' + str(fail_times) + '个失败！有码无码都找不到AV信息：' + bus_bu_url + '，' + relative_path + '\n'
                    print('>>' + fail_message, end='')
                    fail_list.append('    >' + fail_message)
                    write_fail('    >' + fail_message)
                    continue
                # 经过上面的三种情况，可能找到了jav在bus上的网页链接bav_url
                jav_list[0] = bav_url
                try:
                    bav_html = get_jav_html(jav_list)
                except:
                    print('>>尝试打开javbus上的jav网页失败，正在尝试第二次打开...')
                    try:
                        bav_html = get_jav_html(jav_list)
                        print('    >第二次尝试成功！')
                    except:
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '个失败！打开javbus上的jav网页失败：' + bav_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue

                # 正则匹配 影片信息 开始！
                # title的开头是车牌号，而我想要后面的纯标题
                try:  # 标题 <title>030619-872 スーパーボディと最強の美貌の悶える女 - JavBus</title>
                    title = re.search(r'<title>(.+?) - JavBus</title>', bav_html, re.DOTALL).group(1)   # 这边匹配番号
                except:
                    fail_times += 1
                    fail_message = '第' + str(fail_times) + '个失败！页面上找不到AV信息：' + bav_url + '，' + relative_path + '\n'
                    print('>>' + fail_message, end='')
                    fail_list.append('    >' + fail_message)
                    write_fail('    >' + fail_message)
                    continue

                print('>>正在处理：', title)
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
                # 去除title中的特殊字符
                title = title.replace('\n', '').replace('&', '和').replace('/', '#') \
                    .replace('/', '#').replace(':', '：').replace('*', '#').replace('?', '？') \
                    .replace('"', '#').replace('<', '【').replace('>', '】') \
                    .replace('|', '#').replace('＜', '【').replace('＞', '】') \
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
                # 片商 製作商:</span> <a href="https://www.cdnbus.work/uncensored/studio/3n">カリビアンコム</a>
                studiog = re.search(r'製作商:</span> <a href=".+?">(.+?)</a>', bav_html)
                if str(studiog) != 'None':
                    nfo_dict['片商'] = studiog.group(1)
                else:
                    nfo_dict['片商'] = '未知片商'
                # 發行日期:</span> 2019-03-06</p>
                premieredg = re.search(r'發行日期:</span> (.+?)</p>', bav_html)
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
                runtimeg = re.search(r'長度:</span> (.+?)分鐘</p>', bav_html)
                if str(runtimeg) != 'None':
                    nfo_dict['片长'] = runtimeg.group(1)
                else:
                    nfo_dict['片长'] = '0'
                # 导演  >導演:</span> <a href="https://www.cdnbus.work/director/1q9">宮藤春男<
                directorg = re.search(r'導演:</span> <a href=".+?">(.+?)<', bav_html)
                if str(directorg) != 'None':
                    nfo_dict['导演'] = directorg.group(1)
                else:
                    nfo_dict['导演'] = '未知导演'
                # 演员们 和 # 第一个演员
                # <a href="https://www.cdnbus.work/star/v0o" title="琴音芽衣">
                # <img src="https://images.javcdn.pw/actress/q7u.jpg" title="神田るな">
                # actors = re.findall(r'<img src="https://images.javcdn.pw/actress/q7u.jpg" title="神田るな">', bav_html)
                actors = re.findall(r'/star/.+?"><img src=.+?" title="(.+?)">', bav_html)
                # print(actors)
                if len(actors) != 0:
                    if len(actors) > 7:
                        actors = actors[:7]
                    nfo_dict['首个女优'] = actors[0]
                    nfo_dict['全部女优'] = ' '.join(actors)
                else:
                    nfo_dict['首个女优'] = nfo_dict['全部女优'] = '未知演员'
                    actors = ['未知演员']
                nfo_dict['标题'] = nfo_dict['标题'].rstrip(nfo_dict['全部女优'])
                # 特点 <span class="genre"><a href="https://www.cdnbus.work/uncensored/genre/gre085">自慰</a></span>
                genres = re.findall(r'<span class="genre"><a href=".+?">(.+?)</a></span>', bav_html)
                genres = [i for i in genres if i != '字幕' and i != '高清' and i != '高畫質']
                if nfo_dict['是否中字']:
                    genres.append('中文字幕')
                # DVD封面cover
                cover_url = ''
                coverg = re.search(r'<a class="bigImage" href="(.+?)">', bav_html)  # 封面图片的正则对象
                if str(coverg) != 'None':
                    cover_url = coverg.group(1)
                # 系列:</span> <a href="https://www.cdnbus.work/series/kpl">悪質シロウトナンパ</a>
                seriesg = re.search(r'系列:</span> <a href=".+?">(.+?)</a>', bav_html)  # 封面图片的正则对象
                if str(seriesg) != 'None':
                    series = nfo_dict['系列'] = seriesg.group(1)
                else:
                    series = ''
                    nfo_dict['系列'] = '未知系列'
                # arzon的简介 #########################################################
                plot = ''
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
                            # arzon搜索页面实际是18岁验证
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
                                        fail_times) + '个失败！arzon找不到该影片，可能被下架：' + arz_search_url + '，' + relative_path + '\n'
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
                if if_mp4 == '是':  # 新文件名
                    new_mp4 = ''
                    for j in rename_mp4_list:
                        new_mp4 += nfo_dict[j]
                    new_mp4 = new_mp4.rstrip(' ')
                    cd_msg = ''
                    if cars_dic[car_num] > 1:    # 是CD1还是CDn？
                        cd_msg = '-cd' + str(srt.episodes)
                        new_mp4 += cd_msg
                    # rename mp4
                    os.rename(root + '/' + file, root + '/' + new_mp4 + video_type)
                    # file发生了变化
                    file = new_mp4 + video_type
                    print('    >修改文件名' + cd_msg + '完成')
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
                    new_root = class_root  # 新的影片的目录路径，C:/Users/JuneRain/Desktop/测试文件夹/1/葵司/
                    new_folder = new_root.split('/')[-1]  # 新的影片的目录名称，变成了目标目录“葵司”
                    if not os.path.exists(new_root):  # 不存在目标文件夹
                        os.makedirs(new_root)
                    jav_new_path = new_root + '/' + file  # 新的影片路径
                    if not os.path.exists(jav_new_path):  # 目标文件夹没有相同的影片
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
                    else:
                        if not os.path.exists(root + '/' + new_folder):  # 已经存在目标文件夹
                            os.makedirs(root + '/' + new_folder)
                        # 放进独立文件夹
                        os.rename(root + '/' + file, root + '/' + new_folder + '/' + file)  # 就把影片放进去
                        new_root = root + '/' + new_folder  # 在当前文件夹下再创建新文件夹
                        print('    >创建独立的文件夹完成')
                        if subt_name:
                            os.rename(root + '/' + subt_name, root + '/' + new_folder + '/' + subt_name)  # 就把字幕放进去
                            print('    >移动字幕到独立文件夹')

                # 更新一下relative_path
                relative_path = '/' + new_root.lstrip(path) + '/' + file  # 影片的相对于所选文件夹的路径，用于报错
                # 3写入nfo开始
                if if_nfo == '是':
                    cus_title = ''
                    for i in title_list:
                        cus_title += nfo_dict[i]
                    # 开始写入nfo，这nfo格式是参考的emby的nfo
                    info_path = new_root + '/' + new_mp4 + '.nfo'      #nfo存放的地址
                    f = open(info_path, 'w', encoding="utf-8")
                    f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>\n"
                            "<movie>\n"
                            "  <plot>" + plot + "</plot>\n"
                            "  <title>" + cus_title + "</title>\n"
                            "  <director>" + nfo_dict['导演'] + "</director>\n"
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
                    if simp_trad == '简':
                        for i in genres:
                            f.write("  <genre>" + gen_dict[i] + "</genre>\n")
                        if series:
                            f.write("  <genre>系列:" + series + "</genre>\n")
                        f.write("  <genre>片商:" + nfo_dict['片商'] + "</genre>\n")
                        for i in genres:
                            f.write("  <tag>" + gen_dict[i] + "</tag>\n")
                        if series:
                            f.write("  <tag>系列:" + series + "</tag>\n")
                        f.write("  <tag>片商:" + nfo_dict['片商'] + "</tag>\n")
                    else:
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

                # 4需要下载三张图片
                if if_jpg == '是':
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
                        print('    >尝试下载fanart失败，正在尝试第二次下载...')
                        try:
                            download_pic(cover_list)
                            print('    >第二次下载成功')
                        except:
                            fail_times += 1
                            fail_message = '    >第' + str(fail_times) + '个失败！下载fanart.jpg失败：' + cover_url + '，' + relative_path + '\n'
                            print(fail_message, end='')
                            fail_list.append(fail_message)
                            write_fail(fail_message)
                            continue
                    # 下载 poster
                    # 默认的 全标题.jpg封面
                    # 裁剪 海报
                    img = Image.open(fanart_path)
                    w, h = img.size  # fanart的宽 高
                    ex = int(w * 0.52625)  # 0.52625是根据emby的poster宽高比较出来的
                    poster = img.crop((ex, 0, w, h))  # （ex，0）是左下角（x，y）坐标 （w, h)是右上角（x，y）坐标
                    poster.save(poster_path, quality=95)  # quality=95 是无损crop，如果不设置，默认75
                    print('    >poster.jpg裁剪成功')

                # 5收集女优头像
                if if_sculpture == '是':
                    if actors[0] == '未知演员':
                        print('    >未知演员')
                    else:
                        for each_actor in actors:
                            exist_actor_path = '女优头像/' + each_actor + '.jpg'
                            jpg_type = '.jpg'
                            if not os.path.exists(exist_actor_path):  # 女优jpg图片还没有
                                exist_actor_path = '女优头像/' + each_actor + '.png'
                                if not os.path.exists(exist_actor_path):  # 女优png图片还没有
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
                            actors_path = new_root + '/.actors/'
                            if not os.path.exists(actors_path):
                                os.makedirs(actors_path)
                            shutil.copyfile('女优头像/' + each_actor + jpg_type,
                                            actors_path + each_actor + jpg_type)
                            print('    >女优头像收集完成：', each_actor)

                # 6归类影片，针对文件夹
                if if_classify == '是'  and file_folder == '文件夹' and (
                        cars_dic[car_num] == 1 or (cars_dic[car_num] > 1 and cars_dic[car_num] == srt.episodes)):
                    # 需要移动文件夹，且，是该影片的最后一集
                    if separate_folder and classify_root.startswith(root):
                        print('    >无法归类，请选择该文件夹的上级目录作它的归类根目录', root.lstrip(path))
                        continue
                    class_root = classify_root + '/'
                    # 移动的目标文件夹
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
                        # print(traceback.format_exc())
                        fail_times += 1
                        fail_message = '    >第' + str(fail_times) + '个失败！归类失败，重复的影片，归类的根目录已存在相同文件夹：' + new_new_root + '\n'
                        print(fail_message, end='')
                        fail_list.append(fail_message)
                        write_fail(fail_message)
                        continue

            except:
                fail_times += 1
                fail_message = '    >第' + str(fail_times) + '个失败！发生错误，如一直在该影片报错请截图并联系作者：' + relative_path + '\n' + traceback.format_exc() + '\n'
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

    start_key = input('回车继续选择文件夹整理：')
