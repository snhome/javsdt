# -*- coding:utf-8 -*-
import re, os, configparser, requests, shutil, traceback
from PIL import Image
from tkinter import filedialog, Tk
from time import sleep
from aip import AipBodyAnalysis


# get_directory功能是 獲取用户選取的文件夾路徑
def get_directory():
    directory_root = Tk()
    directory_root.withdraw()
    work_path = filedialog.askdirectory()
    if work_path == '':
        print('你沒有選擇目錄! 請重新選：')
        sleep(2)
        return get_directory()
    else:
        # askdirectory 獲得是 正斜槓 路徑C:/，所以下面要把 / 換成 反斜槓\
        return work_path


# 功能為記錄錯誤txt
def write_fail(fail_m):
    record_txt = open('【記得清理它】失敗記錄.txt', 'a', encoding="utf-8")
    record_txt.write(fail_m)
    record_txt.close()


# 人體識別，返回鼻子位置
def image_cut(file_name, cli):
    with open(file_name, 'rb') as fp:
        image = fp.read()
    try:
        result = cli.bodyAnalysis(image)
        return int(result["person_info"][0]['body_parts']['nose']['x'])
    except:
        print('    >正在嘗試重新人體檢測...')
        return image_cut(file_name, cli)


# 獲取網頁源碼，返回網頁text；假裝python的“重載”函數
def get_jav_html(url_list):
    if len(url_list) == 1:
        rqs = requests.get(url_list[0], timeout=10, headers={'Cookie': 'existmag=all'})
    else:
        rqs = requests.get(url_list[0], proxies=url_list[1], timeout=10, headers={'Cookie': 'existmag=all'})
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


# 每一部jav的“結構體”
class JavFile(object):
    def __init__(self):
        self.name = 'ABC-123.mp4'  # 文件名
        self.car = 'ABC-123'  # 車牌
        self.episodes = 0     # 第幾集
        self.subt = ''        # 字幕文件名  ABC-123.srt


#  main開始
print('1、如果連不上javbus，請更正防屏蔽地址，不要用“www.javbus.com”！\n'
      '2、無碼影片沒有簡介\n'
      '3、找不到AV信息，請在javbus上確認，再修改本地視頻文件名，如：\n'
      '   112314-742-carib-1080p.mp4 => 112314-742.mp4\n'
      '   Heyzo_HD_0733_full.mp4 => Heyzo_0733.mp4\n'
      '   Heyzo_0733_01.mp4 => Heyzo_0733啊.mp4\n'
      '   Heyzo_0733_02.mp4 => Heyzo_0733吧.mp4\n')
# 讀取配置文件，這個ini文件用來給用户設置重命名的格式和jav網址
print('正在讀取ini中的設置...', end='')
try:
    config_settings = configparser.RawConfigParser()
    config_settings.read('ini的設置會影響所有exe的操作結果.ini', encoding='utf-8-sig')
    if_nfo = config_settings.get("收集nfo", "是否收集nfo？")
    if_exnfo = config_settings.get("收集nfo", "是否跳過已存在nfo的文件夾？")
    custom_title = config_settings.get("收集nfo", "nfo中title的格式")
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
    if_jpg = config_settings.get("下載封面", "是否下載封面海報？")
    custom_fanart = config_settings.get("下載封面", "DVD封面的格式")
    custom_poster = config_settings.get("下載封面", "海報的格式")
    if_sculpture = config_settings.get("kodi專用", "是否收集女優頭像")
    if_proxy = config_settings.get("代理", "是否使用代理？")
    proxy = config_settings.get("代理", "代理IP及端口")
    if_face = config_settings.get("百度人體分析", "是否需要準確定位人臉的poster？")
    appid = config_settings.get("百度人體分析", "AppID")
    apikey = config_settings.get("百度人體分析", "API Key")
    sk = config_settings.get("百度人體分析", "Secret Key")
    simp_trad = config_settings.get("其他設置", "簡繁中文？")
    bus_url = config_settings.get("其他設置", "javbus網址")
    suren_pref = config_settings.get("其他設置", "素人車牌(若有新車牌請自行添加)")
    file_type = config_settings.get("其他設置", "掃描文件類型")
    title_len = int(config_settings.get("其他設置", "重命名中的標題長度（50~150）"))
    subt_words = config_settings.get("原影片文件的性質", "是否中字即文件名包含")
    custom_subt = config_settings.get("原影片文件的性質", "是否中字的表現形式")
    xx_words = config_settings.get("原影片文件的性質", "是否xx即文件名包含")
    custom_xx = config_settings.get("原影片文件的性質", "是否xx的表現形式")
    movie_type = config_settings.get("原影片文件的性質", "無碼")
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
print('\n讀取ini文件成功!')
# 使用人體分析
if if_face == '是':
    client = AipBodyAnalysis(appid, apikey, sk)
# 確認：代理哪些站點
proxies = {"http": "http://" + proxy, "https": "https://" + proxy}
if if_proxy == '是' and proxy != '':      # 是否需要代理，設置requests請求時的狀態
    jav_list = ['', proxies]              # 代理javbus
    cover_list = [0, '', '', proxies]        # 代理javbus上的圖片
else:
    jav_list = ['']
    cover_list = [0, '', '']
# https://www.buscdn.work/
if not bus_url.endswith('/'):
    bus_url += '/'
# 歸類文件夾具有最高決定權
if if_classify == '是':            # 如果需要歸類
    if file_folder == '文件夾':    # 並且是針對文件夾
        if_folder = '是'           # 那麼必須重命名文件夾或者創建新的文件夾
    else:
        if_folder = '否'           # 否則不會操作新文件夾
# 初始化其他
nfo_dict = {'空格': ' ', '車牌': 'ABC-123', '標題': '未知標題', '完整標題': '完整標題', '導演': '未知導演',
            '發行年月日': '1970-01-01', '發行年份': '1970', '月': '01', '日': '01',
            '片商': '未知片商', '首個女優': '未知演員', '全部女優': '未知演員',
            '片長': '0', '/': '/', '是否中字': '', '視頻': 'ABC-123', '車牌前綴': 'ABC',
            '是否xx': '', '影片類型': movie_type, '系列': '未知系列'}         # 用於暫時存放影片信息，女優，標題等
suren_list = suren_pref.split('、')              # 素人番號的列表
rename_mp4_list = rename_mp4.split('+')          # 重命名視頻的格式
rename_folder_list = rename_folder.split('+')    # 重命名文件夾的格式
type_tuple = tuple(file_type.split('、'))        # 需要掃描的文件的類型
classify_basis_list = classify_basis.split('/')  # 歸類標準，歸類到哪個文件夾
title_list = custom_title.replace('標題', '完整標題', 1).split('+')  # nfo中title的寫法
fanart_list = custom_fanart.split('+')  # fanart的格式
poster_list = custom_poster.split('+')  # poster的格式
word_list = subt_words.split('、')      # 包含哪些特殊含義的文字，判斷是否中字
xx_list = xx_words.split('、')          # 包含哪些特殊含義的文字，判斷是否xx
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
            '中文字幕': '中文字幕'}                   # 特點，繁轉簡

start_key = ''
while start_key == '':
    # 用户選擇文件夾
    print('請選擇要整理的文件夾：', end='')
    path = get_directory()
    print(path)
    write_fail('已選擇文件夾：' + path+'\n')
    print('...文件掃描開始...如果時間過長...請避開中午夜晚高峯期...\n')
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
    # 初始化“失敗信息”
    fail_times = 0                             # 處理過程中錯失敗的個數
    fail_list = []                             # 用於存放處理失敗的信息
    # os.system('pause')
    # root【當前根目錄】 dirs【子目錄】 files【文件】，root是字符串，後兩個是列表
    for root, dirs, files in os.walk(path):
        if if_classify == '是' and root.startswith(classify_root):
            # print('>>該文件夾在歸類的根目錄中，跳過處理...', root)
            continue
        if if_exnfo == '是' and files and (files[-1].endswith('nfo') or (len(files) > 1 and files[-2].endswith('nfo'))):
            continue
        # 對這一層文件夾進行評估,有多少視頻，有多少同車牌視頻，是不是獨立文件夾
        jav_videos = []  # 存放：需要整理的jav的結構體
        cars_dic = {}
        videos_num = 0  # 當前文件夾中視頻的數量，可能有視頻不是jav
        subtitles = False      # 有沒有字幕
        subts_dict = {}          # 存放：jav的字幕文件
        for raw_file in files:
            # 判斷文件是不是字幕文件
            if raw_file.endswith(('.srt', '.vtt', '.ass', '.ssa',)):
                srt_g = re.search(r'([a-zA-Z0-9]+-?_?[a-zA-Z0-9]+-?_?\d*)', raw_file)  # 這個正則表達式匹配“車牌號”可能有點奇怪，
                if str(srt_g) != 'None':  # 如果你下過上千部片，各種參差不齊的命名，你就會理解我了。
                    car_num = srt_g.group(1)
                    subts_dict[raw_file] = car_num
                continue
        # print(subts_dict)
        # print('>>掃描字幕文件完畢！')
        for raw_file in files:
            # 判斷是不是視頻，得到車牌號
            if raw_file.endswith(type_tuple) and not raw_file.startswith('.'):  # ([a-zA-Z]*\d*-?)+
                videos_num += 1
                video_num_g = re.search(r'([a-zA-Z0-9]+-?_?[a-zA-Z0-9]+-?_?\d*)', raw_file)
                if str(video_num_g) != 'None':  # 如果你下過上千部片，各種參差不齊的命名，你就會理解我了。
                    car_num = video_num_g.group(1)
                    alpg = re.search(r'([a-zA-Z]+)', car_num)
                    if str(alpg) != 'None':
                        if alpg.group(1).upper() in suren_list:  # 如果這是素人影片，告訴一下用户，它們需要另外處理
                            fail_times += 1
                            fail_message = '第' + str(fail_times) + '個警告！素人影片：' + root.lstrip(path) + '/' + raw_file + '\n'
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
        # 判定影片所在文件夾是否是獨立文件夾
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
        # print(jav_videos)
        for srt in jav_videos:
            car_num = srt.car
            file = srt.name
            relative_path = '/' + root.lstrip(path) + '/' + file  # 影片的相對於所選文件夾的路徑，用於報錯
            try:
                # 獲取nfo信息的javbus搜索網頁
                bus_bu_url = bus_url + 'uncensored/search/' + car_num + '&type=&parent=uc'
                jav_list[0] = bus_bu_url
                try:
                    jav_html = get_jav_html(jav_list)
                except:
                    print(traceback.format_exc())
                    fail_times += 1
                    fail_message = '第' + str(fail_times) + '個失敗！連接javbus無碼失敗：' + bus_bu_url + '，' + relative_path + '\n'
                    print('>>' + fail_message, end='')
                    fail_list.append('    >' + fail_message)
                    write_fail('    >' + fail_message)
                    continue
                # 搜索結果的網頁，大部分情況一個結果，也有可能是多個結果的網頁 <a class="movie-box" href="https://www.cdnbus.work/030619-872">
                # 嘗試找movie-box
                bav_urls = re.findall(r'<a class="movie-box" href="(.+?)">', jav_html)  # 匹配處理“標題”
                if len(bav_urls) == 1:  # 搜索結果頁面只有一個box
                    bav_url = bav_urls[0]
                elif len(bav_urls) > 1:  # 找到不止一個box
                    print('>>該車牌：' + car_num + ' 搜索到多個結果，正在嘗試精確定位...')
                    car_suf = re.findall(r'\d+', car_num)[-1]  # 當前車牌的後綴數字
                    car_suf = car_suf.lstrip('0')              # 去除-0001中的000
                    car_prefs = re.findall(r'[a-zA-Z]+', car_num)  # 匹配車牌的前綴字母
                    if car_prefs:
                        car_pref = car_prefs[-1].upper()
                    else:
                        car_pref = ''   # 也可能沒字母，全是數字12345_678.mp4
                    bav_url = ''
                    for i in bav_urls:
                        # print(re.findall(r'\d+', i.split('/')[-1]))
                        url_suf = re.findall(r'\d+', i.split('/')[-1])[-1]  # 匹配處理“01”，box上影片車牌的後綴數字
                        url_suf = url_suf.lstrip('0')  # 去除-0001中的000
                        if car_suf == url_suf:         # 數字相同
                            url_prefs = re.findall(r'[a-zA-Z]+', i.split('/')[-1])  # 匹配處理“n”
                            if url_prefs:   # box的前綴字母
                                url_pref = url_prefs[-1].upper()
                            else:
                                url_pref = ''
                            if car_pref == url_pref:  # 數字相同的基礎下，字母也相同，即可能車牌相同
                                bav_url = i
                                fail_times += 1
                                fail_message = '第' + str(fail_times) + '個警告！從“' + file + '”的多個搜索結果中確定為：' + bav_url + '\n'
                                print('>>' + fail_message, end='')
                                fail_list.append('    >' + fail_message)
                                write_fail('    >' + fail_message)
                                break
                        else:
                            continue
                    # 無碼搜索的結果一個都匹配不上
                    if bav_url == '':
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '個失敗！多個搜索結果也找不到AV信息：' + bus_bu_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                else:  # 找不到box
                    # 嘗試在有碼區搜索該車牌
                    bus_qi_url = bus_url + 'search/' + car_num + '&type=1'  # 有碼搜索url
                    jav_list[0] = bus_qi_url
                    try:
                        jav_html = get_jav_html(jav_list)
                    except:
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '個失敗！連接javbus有碼失敗：' + bus_qi_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                    bav_urls = re.findall(r'<a class="movie-box" href="(.+?)">', jav_html)  # 在“有碼”中匹配處理“標題”
                    if len(bav_urls) > 0:
                        print('>>跳過有碼影片：', file)
                        continue
                    fail_times += 1
                    fail_message = '第' + str(fail_times) + '個失敗！無碼有碼都找不到AV信息：' + bus_bu_url + '，' + relative_path + '\n'
                    print('>>' + fail_message, end='')
                    fail_list.append('    >' + fail_message)
                    write_fail('    >' + fail_message)
                    continue
                # 經過上面的三種情況，可能找到了jav在bus上的網頁鏈接bav_url
                jav_list[0] = bav_url
                try:
                    bav_html = get_jav_html(jav_list)
                except:
                    fail_times += 1
                    fail_message = '第' + str(fail_times) + '個失敗！打開javbus上的jav網頁失敗：' + bav_url + '，' + relative_path + '\n'
                    print('>>' + fail_message, end='')
                    fail_list.append('    >' + fail_message)
                    write_fail('    >' + fail_message)
                    continue

                # 正則匹配 影片信息 開始！
                # title的開頭是車牌號，而我想要後面的純標題
                try:  # 標題 <title>030619-872 スーパーボディと最強の美貌の悶える女 - JavBus</title>
                    title = re.search(r'<title>(.+?) - JavBus</title>', bav_html, re.DOTALL).group(1)   # 這邊匹配番號
                except:
                    fail_times += 1
                    fail_message = '第' + str(fail_times) + '個失敗！頁面上找不到AV信息：' + bav_url + '，' + relative_path + '\n'
                    print('>>' + fail_message, end='')
                    fail_list.append('    >' + fail_message)
                    write_fail('    >' + fail_message)
                    continue

                print('>>正在處理：', title)
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
                # 去除title中的特殊字符
                title = title.replace('\n', '').replace('&', '和').replace('/', '#') \
                    .replace('/', '#').replace(':', '：').replace('*', '#').replace('?', '？') \
                    .replace('"', '#').replace('<', '【').replace('>', '】') \
                    .replace('|', '#').replace('＜', '【').replace('＞', '】') \
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
                # 導演:</span> <a href="https://www.cdnbus.work/director/3hy">うさぴょん。</a></p>
                directorg = re.search(r'導演:</span> <a href=".+?">(.+?)</a>', jav_html)
                if str(directorg) != 'None':
                    nfo_dict['導演'] = directorg.group(1)
                else:
                    nfo_dict['導演'] = '未知導演'
                # 片商 製作商:</span> <a href="https://www.cdnbus.work/uncensored/studio/3n">カリビアンコム</a>
                studiog = re.search(r'製作商:</span> <a href=".+?">(.+?)</a>', bav_html)
                if str(studiog) != 'None':
                    nfo_dict['片商'] = studiog.group(1)
                else:
                    nfo_dict['片商'] = '未知片商'
                # 發行日期:</span> 2019-03-06</p>
                premieredg = re.search(r'發行日期:</span> (.+?)</p>', bav_html)
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
                runtimeg = re.search(r'長度:</span> (.+?)分鐘</p>', bav_html)
                if str(runtimeg) != 'None':
                    nfo_dict['片長'] = runtimeg.group(1)
                else:
                    nfo_dict['片長'] = '0'
                # 演員們 和 # 第一個演員
                # <img src="https://images.javcdn.pw/actress/q7u.jpg" title="神田るな">
                # actors = re.findall(r'<img src="https://images.javcdn.pw/actress/q7u.jpg" title="神田るな">', bav_html)
                actors = re.findall(r'<img src="https://images.javcdn.pw/actress/.+?" title="(.+?)"></a>', bav_html)
                # print(actors)
                if len(actors) != 0:
                    if len(actors) > 7:
                        actors = actors[:7]
                    nfo_dict['首個女優'] = actors[0]
                    nfo_dict['全部女優'] = ' '.join(actors)
                else:
                    nfo_dict['首個女優'] = nfo_dict['全部女優'] = '未知演員'
                    actors = ['未知演員']
                nfo_dict['標題'] = nfo_dict['標題'].rstrip(nfo_dict['全部女優'])
                # 特點 <span class="genre"><a href="https://www.cdnbus.work/uncensored/genre/gre085">自慰</a></span>
                genres = re.findall(r'<span class="genre"><a href=".+?">(.+?)</a></span>', bav_html)
                genres = [i for i in genres if i != '字幕' and i != '高清' and i != '1080p' and i != '60fps' and i != 'AV女優']
                if nfo_dict['是否中字']:
                    genres.append('中文字幕')
                # DVD封面cover
                cover_url = ''
                coverg = re.search(r'<a class="bigImage" href="(.+?)">', bav_html)  # 封面圖片的正則對象
                if str(coverg) != 'None':
                    cover_url = coverg.group(1)
                # 系列:</span> <a href="https://www.cdnbus.work/series/kpl">悪質シロウトナンパ</a>
                seriesg = re.search(r'系列:</span> <a href=".+?">(.+?)</a>', bav_html)  # 封面圖片的正則對象
                if str(seriesg) != 'None':
                    series = nfo_dict['系列'] = seriesg.group(1)
                else:
                    series = ''
                    nfo_dict['系列'] = '未知系列'
                    #######################################################################

                # 1重命名視頻
                new_mp4 = file[:-len(video_type)].rstrip(' ')
                if if_mp4 == '是':  # 新文件名
                    new_mp4 = ''
                    for j in rename_mp4_list:
                        new_mp4 += nfo_dict[j]
                    new_mp4 = new_mp4.rstrip(' ')
                    cd_msg = ''
                    if cars_dic[car_num] > 1:    # 是CD1還是CDn？
                        cd_msg = '-cd' + str(srt.episodes)
                        new_mp4 += cd_msg
                    # rename mp4
                    os.rename(root + '/' + file, root + '/' + new_mp4 + video_type)
                    # file發生了變化
                    file = new_mp4 + video_type
                    print('    >修改文件名' + cd_msg + '完成')
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
                    new_root = class_root  # 新的影片的目錄路徑，C:/Users/JuneRain/Desktop/測試文件夾/1/葵司/
                    new_folder = new_root.split('/')[-1]  # 新的影片的目錄名稱，變成了目標目錄“葵司”
                    if not os.path.exists(new_root):  # 不存在目標文件夾
                        os.makedirs(new_root)
                    jav_new_path = new_root + '/' + file  # 新的影片路徑
                    if not os.path.exists(jav_new_path):  # 目標文件夾沒有相同的影片
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
                        # 放進獨立文件夾
                        os.rename(root + '/' + file, root + '/' + new_folder + '/' + file)  # 就把影片放進去
                        new_root = root + '/' + new_folder  # 在當前文件夾下再創建新文件夾
                        print('    >創建獨立的文件夾完成')
                        if subt_name:
                            os.rename(root + '/' + subt_name, root + '/' + new_folder + '/' + subt_name)  # 就把字幕放進去
                            print('    >移動字幕到獨立文件夾')

                # 更新一下relative_path
                relative_path = '/' + new_root.lstrip(path) + '/' + file  # 影片的相對於所選文件夾的路徑，用於報錯
                # 3寫入nfo開始
                if if_nfo == '是':
                    cus_title = ''
                    for i in title_list:
                        cus_title += nfo_dict[i]
                    # 開始寫入nfo，這nfo格式是參考的emby的nfo
                    info_path = new_root + '/' + new_mp4 + '.nfo'      #nfo存放的地址
                    f = open(info_path, 'w', encoding="utf-8")
                    f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>\n"
                            "<movie>\n"
                            "  <plot></plot>\n"
                            "  <title>" + cus_title + "</title>\n"
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
                    if simp_trad == '簡':
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

                # 4需要下載三張圖片
                if if_jpg == '是':
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
                        print('    >嘗試下載fanart失敗，正在嘗試第二次下載...')
                        try:
                            download_pic(cover_list)
                            print('    >第二次下載成功')
                        except:
                            fail_times += 1
                            fail_message = '    >第' + str(fail_times) + '個失敗！下載fanart.jpg失敗：' + cover_url + '，' + relative_path + '\n'
                            print(fail_message, end='')
                            fail_list.append(fail_message)
                            write_fail(fail_message)
                            continue
                    # 下載 poster
                    # 默認的 全標題.jpg封面
                    # 裁剪 海報
                    img = Image.open(fanart_path)
                    w = img.width  # fanart的寬
                    h = img.height  # fanart的高
                    ew = int(0.653 * h)  # poster的寬
                    ex = w - ew  # x座標
                    if if_face == '是':
                        ex = image_cut(fanart_path, client)  # 鼻子的x座標  0.704 0.653
                        if ex + ew/2 > w:     # 鼻子 + 一半poster寬超出poster右邊
                            ex = w - ew       # 以右邊為poster
                        elif ex - ew/2 < 0:   # 鼻子 - 一半poster寬超出poster左邊
                            ex = 0            # 以左邊為poster
                        else:                 # 不會超出poster
                            ex = ex-ew/2       # 以鼻子為中心向兩邊擴展
                    # crop
                    poster = img.crop((ex, 0, ex + ew, h))
                    poster.save(poster_path, quality=95)
                    print('    >poster.jpg裁剪成功')

                # 5收集女優頭像
                if if_sculpture == '是':
                    if actors[0] == '未知演員':
                        print('    >未知演員')
                    else:
                        for each_actor in actors:
                            exist_actor_path = '女優頭像/' + each_actor + '.jpg'
                            jpg_type = '.jpg'
                            if not os.path.exists(exist_actor_path):  # 女優jpg圖片還沒有
                                exist_actor_path = '女優頭像/' + each_actor + '.png'
                                if not os.path.exists(exist_actor_path):  # 女優png圖片還沒有
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
                            actors_path = new_root + '/.actors/'
                            if not os.path.exists(actors_path):
                                os.makedirs(actors_path)
                            shutil.copyfile('女優頭像/' + each_actor + jpg_type,
                                            actors_path + each_actor + jpg_type)
                            print('    >女優頭像收集完成：', each_actor)

                # 6歸類影片，針對文件夾
                if if_classify == '是' and file_folder == '文件夾' and (
                        cars_dic[car_num] == 1 or (cars_dic[car_num] > 1 and cars_dic[car_num] == srt.episodes)):
                    # 需要移動文件夾，且，是該影片的最後一集
                    if separate_folder and classify_root.startswith(root):
                        print('    >無法歸類，請選擇該文件夾的上級目錄作它的歸類根目錄', root.lstrip(path))
                        continue
                    class_root = classify_root + '/'
                    # 移動的目標文件夾
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
                        # print(traceback.format_exc())
                        fail_times += 1
                        fail_message = '    >第' + str(fail_times) + '個失敗！歸類失敗，重複的影片，歸類的根目錄已存在相同文件夾：' + new_new_root + '\n'
                        print(fail_message, end='')
                        fail_list.append(fail_message)
                        write_fail(fail_message)
                        continue

            except:
                fail_times += 1
                fail_message = '    >第' + str(fail_times) + '個失敗！發生錯誤，如一直在該影片報錯請截圖並聯系作者：' + relative_path + '\n' + traceback.format_exc() + '\n'
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

    start_key = input('回車繼續選擇文件夾整理：')
