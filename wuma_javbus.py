# -*- coding:utf-8 -*-
import re, os, configparser, requests, shutil, traceback
from PIL import Image
from tkinter import filedialog, Tk
from time import sleep
from aip import AipBodyAnalysis


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


# 人体识别，返回鼻子位置
def image_cut(file_name, cli):
    with open(file_name, 'rb') as fp:
        image = fp.read()
    try:
        result = cli.bodyAnalysis(image)
        return int(result["person_info"][0]['body_parts']['nose']['x'])
    except:
        print('    >正在尝试重新人体检测...')
        return image_cut(file_name, cli)


# 获取网页源码，返回网页text；假装python的“重载”函数
def get_jav_html(url_list):
    if len(url_list) == 1:
        rqs = requests.get(url_list[0], timeout=10, headers={'Cookie': 'existmag=all'})
    else:
        rqs = requests.get(url_list[0], proxies=url_list[1], timeout=10, headers={'Cookie': 'existmag=all'})
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
print('1、如果连不上javbus，请更正防屏蔽地址，不要用“www.javbus.com”！\n'
      '2、无码影片没有简介\n'
      '3、找不到AV信息，请在javbus上确认，再修改本地视频文件名，如：\n'
      '   112314-742-carib-1080p.mp4 => 112314-742.mp4\n'
      '   Heyzo_HD_0733_full.mp4 => Heyzo_0733.mp4\n'
      '   Heyzo_0733_01.mp4 => Heyzo_0733啊.mp4\n'
      '   Heyzo_0733_02.mp4 => Heyzo_0733吧.mp4\n')
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
    if_face = config_settings.get("百度人体分析", "是否需要准确定位人脸的poster？")
    appid = config_settings.get("百度人体分析", "AppID")
    apikey = config_settings.get("百度人体分析", "API Key")
    sk = config_settings.get("百度人体分析", "Secret Key")
    simp_trad = config_settings.get("其他设置", "简繁中文？")
    bus_url = config_settings.get("其他设置", "javbus网址")
    suren_pref = config_settings.get("其他设置", "素人车牌(若有新车牌请自行添加)")
    file_type = config_settings.get("其他设置", "扫描文件类型")
    title_len = int(config_settings.get("其他设置", "重命名中的标题长度（50~150）"))
    subt_words = config_settings.get("原影片文件的性质", "是否中字即文件名包含")
    custom_subt = config_settings.get("原影片文件的性质", "是否中字的表现形式")
    xx_words = config_settings.get("原影片文件的性质", "是否xx即文件名包含")
    custom_xx = config_settings.get("原影片文件的性质", "是否xx的表现形式")
    movie_type = config_settings.get("原影片文件的性质", "无码")
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
# 使用人体分析
if if_face == '是':
    client = AipBodyAnalysis(appid, apikey, sk)
# 确认：代理哪些站点
proxies = {"http": "http://" + proxy, "https": "https://" + proxy}
if if_proxy == '是' and proxy != '':      # 是否需要代理，设置requests请求时的状态
    jav_list = ['', proxies]              # 代理javbus
    cover_list = [0, '', '', proxies]        # 代理javbus上的图片
else:
    jav_list = ['']
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
gen_dict = {'高清': 'XXXX', '字幕': 'XXXX', '推薦作品': '推荐作品', '通姦': '通奸', '淋浴': '淋浴', '舌頭': '舌头',
            '下流': '下流', '敏感': '敏感', '變態': '变态', '願望': '愿望', '慾求不滿': '慾求不满', '服侍': '服侍',
            '外遇': '外遇', '訪問': '访问', '性伴侶': '性伴侣', '保守': '保守', '購物': '购物', '誘惑': '诱惑',
            '出差': '出差', '煩惱': '烦恼', '主動': '主动', '再會': '再会', '戀物癖': '恋物癖', '問題': '问题',
            '騙奸': '骗奸', '鬼混': '鬼混', '高手': '高手', '順從': '顺从', '密會': '密会', '做家務': '做家务',
            '秘密': '秘密', '送貨上門': '送货上门', '壓力': '压力', '處女作': '处女作', '淫語': '淫语', '問卷': '问卷',
            '住一宿': '住一宿', '眼淚': '眼泪', '跪求': '跪求', '求職': '求职', '婚禮': '婚礼', '第一視角': '第一视角',
            '洗澡': '洗澡', '首次': '首次', '劇情': '剧情', '約會': '约会', '實拍': '实拍', '同性戀': '同性恋',
            '幻想': '幻想', '淫蕩': '淫荡', '旅行': '旅行', '面試': '面试', '喝酒': '喝酒', '尖叫': '尖叫',
            '新年': '新年', '借款': '借款', '不忠': '不忠', '檢查': '检查', '羞恥': '羞耻', '勾引': '勾引',
            '新人': '新人', '推銷': '推销', 'ブルマ': '运动短裤',

            'AV女優': 'XXXX', '情人': '情人', '丈夫': '丈夫', '辣妹': '辣妹', 'S級女優': 'S级女优', '白領': '白领',
            '偶像': '偶像', '兒子': '儿子', '女僕': '女仆', '老師': '老师', '夫婦': '夫妇', '保健室': '保健室',
            '朋友': '朋友', '工作人員': '工作人员', '明星': '明星', '同事': '同事', '面具男': '面具男', '上司': '上司',
            '睡眠系': '睡眠系', '奶奶': '奶奶', '播音員': '播音员', '鄰居': '邻居', '親人': '亲人', '店員': '店员',
            '魔女': '魔女', '視訊小姐': '视讯小姐', '大學生': '大学生', '寡婦': '寡妇', '小姐': '小姐', '秘書': '秘书',
            '人妖': '人妖', '啦啦隊': '啦啦队', '美容師': '美容师', '岳母': '岳母', '警察': '警察', '熟女': '熟女',
            '素人': '素人', '人妻': '人妻', '痴女': '痴女', '角色扮演': '角色扮演', '蘿莉': '萝莉', '姐姐': '姐姐',
            '模特': '模特', '教師': '教师', '學生': '学生', '少女': '少女', '新手': '新手', '男友': '男友',
            '護士': '护士', '媽媽': '妈妈', '主婦': '主妇', '孕婦': '孕妇', '女教師': '女教师', '年輕人妻': '年轻人妻',
            '職員': '职员', '看護': '看护', '外觀相似': '外观相似', '色狼': '色狼', '醫生': '医生', '新婚': '新婚',
            '黑人': '黑人', '空姐': '空中小姐', '運動系': '运动系', '女王': '女王', '西裝': '西装', '旗袍': '旗袍',
            '兔女郎': '兔女郎', '白人': '白人',

            '制服': '制服', '內衣': '内衣', '休閒裝': '休閒装', '水手服': '水手服', '全裸': '全裸', '不穿內褲': '不穿内裤',
            '和服': '和服', '不戴胸罩': '不戴胸罩', '連衣裙': '连衣裙', '打底褲': '打底裤', '緊身衣': '紧身衣', '客人': '客人',
            '晚禮服': '晚礼服', '治癒系': '治癒系', '大衣': '大衣', '裸體襪子': '裸体袜子', '絲帶': '丝带', '睡衣': '睡衣',
            '面具': '面具', '牛仔褲': '牛仔裤', '喪服': '丧服', '極小比基尼': '极小比基尼', '混血': '混血', '毛衣': '毛衣',
            '頸鏈': '颈链', '短褲': '短裤', '美人': '美人', '連褲襪': '连裤袜', '裙子': '裙子', '浴衣和服': '浴衣和服',
            '泳衣': '泳衣', '網襪': '网袜', '眼罩': '眼罩', '圍裙': '围裙', '比基尼': '比基尼', '情趣內衣': '情趣内衣',
            '迷你裙': '迷你裙', '套裝': '套装', '眼鏡': '眼镜', '丁字褲': '丁字裤', '陽具腰帶': '阳具腰带', '男装': '男装',
            '襪': '袜',

            '美肌': '美肌', '屁股': '屁股', '美穴': '美穴', '黑髮': '黑发', '嬌小': '娇小', '曬痕': '晒痕',
            'F罩杯': 'F罩杯', 'E罩杯': 'E罩杯', 'D罩杯': 'D罩杯', '素顏': '素颜', '貓眼': '猫眼', '捲髮': '捲发',
            '虎牙': '虎牙', 'C罩杯': 'C罩杯', 'I罩杯': 'I罩杯', '小麥色': '小麦色', '大陰蒂': '大阴蒂', '美乳': '美乳',
            '巨乳': '巨乳', '豐滿': '丰满', '苗條': '苗条', '美臀': '美臀', '美腿': '美腿', '無毛': '无毛',
            '美白': '美白', '微乳': '微乳', '性感': '性感', '高個子': '高个子', '爆乳': '爆乳', 'G罩杯': 'G罩杯',
            '多毛': '多毛', '巨臀': '巨臀', '軟體': '软体', '巨大陽具': '巨大阳具', '長發': '长发', 'H罩杯': 'H罩杯',


            '舔陰': '舔阴', '電動陽具': '电动阳具', '淫亂': '淫乱', '射在外陰': '射在外阴', '猛烈': '猛烈', '後入內射': '后入内射',
            '足交': '足交', '射在胸部': '射在胸部', '側位內射': '侧位内射', '射在腹部': '射在腹部', '騎乘內射': '骑乘内射', '射在頭髮': '射在头发',
            '母乳': '母乳', '站立姿勢': '站立姿势', '肛射': '肛射', '陰道擴張': '阴道扩张', '內射觀察': '内射观察', '射在大腿': '射在大腿',
            '精液流出': '精液流出', '射在屁股': '射在屁股', '內射潮吹': '内射潮吹', '首次肛交': '首次肛交', '射在衣服上': '射在衣服上', '首次內射': '首次内射',
            '早洩': '早洩', '翻白眼': '翻白眼', '舔腳': '舔脚', '喝尿': '喝尿', '口交': '口交', '內射': '内射',
            '自慰': '自慰', '後入': '后入', '騎乘位': '骑乘位', '顏射': '颜射', '口內射精': '口内射精', '手淫': '手淫',
            '潮吹': '潮吹', '輪姦': '轮奸', '亂交': '乱交', '乳交': '乳交', '小便': '小便', '吸精': '吸精',
            '深膚色': '深肤色', '指法': '指法', '騎在臉上': '骑在脸上', '連續內射': '连续内射', '打樁機': '打桩机', '肛交': '肛交',
            '吞精': '吞精', '鴨嘴': '鸭嘴', '打飛機': '打飞机', '剃毛': '剃毛', '站立位': '站立位', '高潮': '高潮',
            '二穴同入': '二穴同入', '舔肛': '舔肛', '多人口交': '多人口交', '痙攣': '痉挛', '玩弄肛門': '玩弄肛门', '立即口交': '立即口交',
            '舔蛋蛋': '舔蛋蛋', '口射': '口射', '陰屁': '阴屁', '失禁': '失禁', '大量潮吹': '大量潮吹', '69': '69',

            '振動': '振动', '搭訕': '搭讪', '奴役': '奴役', '打屁股': '打屁股', '潤滑油': '润滑油',
            '按摩': '按摩', '散步': '散步', '扯破連褲襪': '扯破连裤袜', '手銬': '手铐', '束縛': '束缚', '調教': '调教',
            '假陽具': '假阳具', '變態遊戲': '变态游戏', '注視': '注视', '蠟燭': '蜡烛', '電鑽': '电钻', '亂搞': '乱搞',
            '摩擦': '摩擦', '項圈': '项圈', '繩子': '绳子', '灌腸': '灌肠', '監禁': '监禁', '車震': '车震',
            '鞭打': '鞭打', '懸掛': '悬挂', '喝口水': '喝口水', '精液塗抹': '精液涂抹', '舔耳朵': '舔耳朵', '女體盛': '女体盛',
            '便利店': '便利店', '插兩根': '插两根', '開口器': '开口器', '暴露': '暴露', '陰道放入食物': '阴道放入食物', '大便': '大便',
            '經期': '经期', '惡作劇': '恶作剧', '電動按摩器': '电动按摩器', '凌辱': '凌辱', '玩具': '玩具', '露出': '露出',
            '肛門': '肛门', '拘束': '拘束', '多P': '多P', '潤滑劑': '润滑剂', '攝影': '摄影', '野外': '野外',
            '陰道觀察': '阴道观察', 'SM': 'SM', '灌入精液': '灌入精液', '受虐': '受虐', '綁縛': '绑缚', '偷拍': '偷拍',
            '異物插入': '异物插入', '電話': '电话', '公寓': '公寓', '遠程操作': '远程操作', '偷窺': '偷窥', '踩踏': '踩踏',
            '無套': '无套',

            '企劃物': '企划物', '獨佔動畫': '独佔动画', '10代': '10代', '1080p': 'XXXX', '人氣系列': '人气系列', '60fps': 'XXXX',
            '超VIP': '超VIP', '投稿': '投稿', 'VIP': 'VIP', '椅子': '椅子', '風格出眾': '风格出众', '首次作品': '首次作品',
            '更衣室': '更衣室', '下午': '下午', 'KTV': 'KTV', '白天': '白天', '最佳合集': '最佳合集', 'VR': 'VR',
            '動漫': '动漫',

            '酒店': '酒店', '密室': '密室', '車': '车', '床': '床', '陽台': '阳台', '公園': '公园',
            '家中': '家中', '公交車': '公交车', '公司': '公司', '門口': '门口', '附近': '附近', '學校': '学校',
            '辦公室': '办公室', '樓梯': '楼梯', '住宅': '住宅', '公共廁所': '公共厕所', '旅館': '旅馆', '教室': '教室',
            '廚房': '厨房', '桌子': '桌子', '大街': '大街', '農村': '农村', '和室': '和室', '地下室': '地下室',
            '牢籠': '牢笼', '屋頂': '屋顶', '游泳池': '游泳池', '電梯': '电梯', '拍攝現場': '拍摄现场', '別墅': '别墅',
            '房間': '房间', '愛情旅館': '爱情旅馆', '車內': '车内', '沙發': '沙发', '浴室': '浴室', '廁所': '厕所',
            '溫泉': '温泉', '醫院': '医院', '榻榻米': '榻榻米',
            '中文字幕': '中文字幕'}                   # 特点，繁转简

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
                srt_g = re.search(r'([a-zA-Z0-9]+-?_?[a-zA-Z0-9]+-?_?\d*)', raw_file)  # 这个正则表达式匹配“车牌号”可能有点奇怪，
                if str(srt_g) != 'None':  # 如果你下过上千部片，各种参差不齐的命名，你就会理解我了。
                    car_num = srt_g.group(1)
                    subts_dict[raw_file] = car_num
                continue
        # print(subts_dict)
        # print('>>扫描字幕文件完毕！')
        for raw_file in files:
            # 判断是不是视频，得到车牌号
            if raw_file.endswith(type_tuple) and not raw_file.startswith('.'):  # ([a-zA-Z]*\d*-?)+
                videos_num += 1
                video_num_g = re.search(r'([a-zA-Z0-9]+-?_?[a-zA-Z0-9]+-?_?\d*)', raw_file)
                if str(video_num_g) != 'None':  # 如果你下过上千部片，各种参差不齐的命名，你就会理解我了。
                    car_num = video_num_g.group(1)
                    alpg = re.search(r'([a-zA-Z]+)', car_num)
                    if str(alpg) != 'None':
                        if alpg.group(1).upper() in suren_list:  # 如果这是素人影片，告诉一下用户，它们需要另外处理
                            fail_times += 1
                            fail_message = '第' + str(fail_times) + '个警告！素人影片：' + root.lstrip(path) + '/' + raw_file + '\n'
                            print('>>' + fail_message, end='')
                            fail_list.append('    >' + fail_message)
                            write_fail('    >' + fail_message)
                            continue
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
                # 获取nfo信息的javbus搜索网页
                bus_bu_url = bus_url + 'uncensored/search/' + car_num + '&type=&parent=uc'
                jav_list[0] = bus_bu_url
                try:
                    jav_html = get_jav_html(jav_list)
                except:
                    print(traceback.format_exc())
                    fail_times += 1
                    fail_message = '第' + str(fail_times) + '个失败！连接javbus无码失败：' + bus_bu_url + '，' + relative_path + '\n'
                    print('>>' + fail_message, end='')
                    fail_list.append('    >' + fail_message)
                    write_fail('    >' + fail_message)
                    continue
                # 搜索结果的网页，大部分情况一个结果，也有可能是多个结果的网页 <a class="movie-box" href="https://www.cdnbus.work/030619-872">
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
                    # 无码搜索的结果一个都匹配不上
                    if bav_url == '':
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '个失败！多个搜索结果也找不到AV信息：' + bus_bu_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                else:  # 找不到box
                    # 尝试在有码区搜索该车牌
                    bus_qi_url = bus_url + 'search/' + car_num + '&type=1'  # 有码搜索url
                    jav_list[0] = bus_qi_url
                    try:
                        jav_html = get_jav_html(jav_list)
                    except:
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '个失败！连接javbus有码失败：' + bus_qi_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                    bav_urls = re.findall(r'<a class="movie-box" href="(.+?)">', jav_html)  # 在“有码”中匹配处理“标题”
                    if len(bav_urls) > 0:
                        print('>>跳过有码影片：', file)
                        continue
                    fail_times += 1
                    fail_message = '第' + str(fail_times) + '个失败！无码有码都找不到AV信息：' + bus_bu_url + '，' + relative_path + '\n'
                    print('>>' + fail_message, end='')
                    fail_list.append('    >' + fail_message)
                    write_fail('    >' + fail_message)
                    continue
                # 经过上面的三种情况，可能找到了jav在bus上的网页链接bav_url
                jav_list[0] = bav_url
                try:
                    bav_html = get_jav_html(jav_list)
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
                # 導演:</span> <a href="https://www.cdnbus.work/director/3hy">うさぴょん。</a></p>
                directorg = re.search(r'導演:</span> <a href=".+?">(.+?)</a>', jav_html)
                if str(directorg) != 'None':
                    nfo_dict['导演'] = directorg.group(1)
                else:
                    nfo_dict['导演'] = '未知导演'
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
                # 演员们 和 # 第一个演员
                # <img src="https://images.javcdn.pw/actress/q7u.jpg" title="神田るな">
                # actors = re.findall(r'<img src="https://images.javcdn.pw/actress/q7u.jpg" title="神田るな">', bav_html)
                actors = re.findall(r'<img src="https://images.javcdn.pw/actress/.+?" title="(.+?)"></a>', bav_html)
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
                genres = [i for i in genres if i != '字幕' and i != '高清' and i != '1080p' and i != '60fps' and i != 'AV女優']
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
                            "  <plot></plot>\n"
                            "  <title>" + cus_title + "</title>\n"
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
                    w = img.width  # fanart的宽
                    h = img.height  # fanart的高
                    ew = int(0.653 * h)  # poster的宽
                    ex = w - ew  # x坐标
                    if if_face == '是':
                        ex = image_cut(fanart_path, client)  # 鼻子的x坐标  0.704 0.653
                        if ex + ew/2 > w:     # 鼻子 + 一半poster宽超出poster右边
                            ex = w - ew       # 以右边为poster
                        elif ex - ew/2 < 0:   # 鼻子 - 一半poster宽超出poster左边
                            ex = 0            # 以左边为poster
                        else:                 # 不会超出poster
                            ex = ex-ew/2       # 以鼻子为中心向两边扩展
                    # crop
                    poster = img.crop((ex, 0, ex + ew, h))
                    poster.save(poster_path, quality=95)
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
                if if_classify == '是' and file_folder == '文件夹' and (
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
