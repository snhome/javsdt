# -*- coding:utf-8 -*-
import re, sys, os, configparser, requests, shutil, traceback, time, hashlib, json
from PIL import Image
from time import sleep

# get_directory功能是 獲取用户選取的文件夾路徑
def get_directory():
    if os.path.exists(sys.argv[1]):
        path = os.path.abspath(sys.argv[1])
    else:
        print("Cannot find " + sys.argv[1])
        exit()
    return path

# 功能為記錄錯誤txt
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
print('1、避開21:00-1:00，訪問javbus和arzon很慢。\n'
      '1、如果連不上javbus，請更正防屏蔽地址\n'
      '   不要用“www.javbus.com”！\n')
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
    if_plot = config_settings.get("百度翻譯API", "是否需要日語簡介？")
    if_tran = config_settings.get("百度翻譯API", "是否翻譯為中文？")
    ID = config_settings.get("百度翻譯API", "APP ID")
    SK = config_settings.get("百度翻譯API", "密鑰")
    simp_trad = config_settings.get("其他設置", "簡繁中文？")
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
        print('\n    >“【缺失的女優頭像統計For Kodi】.ini”文件被你玩壞了...正在重寫ini...成功！')
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
# 歸類文件夾具有最高決定權
if if_classify == '是':            # 如果需要歸類
    if file_folder == '文件夾':    # 並且是針對文件夾
        if_folder = '是'           # 那麼必須重命名文件夾或者創建新的文件夾
    else:
        if_folder = '否'           # 否則不會操作新文件夾
# 百度翻譯是簡/繁中文
if simp_trad == '簡':
    t_lang = 'zh'
else:
    t_lang = 'cht'
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
# 特點，繁轉簡
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
        if if_exnfo == '是' and files and nfo_exist(files):
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
        # print('>>掃描字幕文件完畢！')
        for raw_file in files:
            # 判斷是不是視頻，得到車牌號
            if raw_file.endswith(type_tuple) and not raw_file.startswith('.'):
                videos_num += 1
                video_num_g = re.search(r'(\d?\d?[a-zA-Z]{1,7}\d?\d?)-? ?_?(\d{2,6})', raw_file)  # 這個正則表達式匹配“車牌號”可能有點奇怪，
                if str(video_num_g) != 'None':  # 如果你下過上千部片，各種參差不齊的命名，你就會理解我了。
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
                    if car_num not in cars_dic:  # cars_dic中沒有這個車牌，表示這一層文件夾下新發現一個車牌
                        cars_dic[car_num] = 1  # 這個新車牌有了第一集
                    else:
                        cars_dic[car_num] += 1  # 已經有這個車牌了，加一集cd
                    jav_file = JavFile()
                    jav_file.car = car_num  # 車牌
                    jav_file.name = raw_file  # 原文件名
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
                # 獲取nfo信息的javbus搜索網頁  https://www.cdnbus.work/search/avop&type=&parent=ce
                bus_bu_url = bus_url + 'search/' + car_num + '&type=1&parent=ce'
                jav_list[0] = bus_bu_url
                try:
                    jav_html = get_jav_html(jav_list)
                except:
                    print('>>嘗試打開javbus有碼頁面失敗，正在嘗試第二次打開...')
                    try:
                        jav_html = get_jav_html(jav_list)
                        print('    >第二次嘗試成功！')
                    except:
                        fail_times += 1
                        fail_message = '第' + str(fail_times) + '個失敗！連接javbus有碼失敗：' + bus_bu_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                # 搜索結果的網頁，大部分情況一個結果，也有可能是多個結果的網頁
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
                    # 有碼搜索的結果一個都匹配不上
                    if bav_url == '':
                        fail_times += 1
                        print(jav_html)
                        fail_message = '第' + str(fail_times) + '個失敗！多個搜索結果也找不到AV信息：' + bus_bu_url + '，' + relative_path + '\n'
                        print('>>' + fail_message, end='')
                        fail_list.append('    >' + fail_message)
                        write_fail('    >' + fail_message)
                        continue
                else:  # 找不到box
                    # 嘗試在無碼區搜索該車牌
                    bus_qi_url = bus_url + 'uncensored/search/' + car_num + '&type=&parent=uc'  # 有碼搜索url
                    jav_list[0] = bus_qi_url
                    try:
                        jav_html = get_jav_html(jav_list)
                    except:
                        print('>>嘗試打開javbus無碼頁面失敗，正在嘗試第二次打開...')
                        try:
                            jav_html = get_jav_html(jav_list)
                            print('    >第二次嘗試成功！')
                        except:
                            fail_times += 1
                            fail_message = '第' + str(fail_times) + '個失敗！連接javbus無碼失敗：' + bus_qi_url + '，' + relative_path + '\n'
                            print('>>' + fail_message, end='')
                            fail_list.append('    >' + fail_message)
                            write_fail('    >' + fail_message)
                            continue
                    bav_urls = re.findall(r'<a class="movie-box" href="(.+?)">', jav_html)  # 在“有碼”中匹配處理“標題”
                    if len(bav_urls) > 0:
                        print('>>跳過無碼影片：', file)
                        continue
                    # # 上面只能搜索
                    # bus_bu_url = bus_url + 'search/' + car_num + '&type=1'
                    # jav_list[0] = bus_bu_url
                    # try:
                    #     jav_html = get_jav_html(jav_list)
                    # except:
                    fail_times += 1
                    fail_message = '第' + str(fail_times) + '個失敗！有碼無碼都找不到AV信息：' + bus_bu_url + '，' + relative_path + '\n'
                    print('>>' + fail_message, end='')
                    fail_list.append('    >' + fail_message)
                    write_fail('    >' + fail_message)
                    continue
                # 經過上面的三種情況，可能找到了jav在bus上的網頁鏈接bav_url
                jav_list[0] = bav_url
                try:
                    bav_html = get_jav_html(jav_list)
                except:
                    print('>>嘗試打開javbus上的jav網頁失敗，正在嘗試第二次打開...')
                    try:
                        bav_html = get_jav_html(jav_list)
                        print('    >第二次嘗試成功！')
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
                # 導演  >導演:</span> <a href="https://www.cdnbus.work/director/1q9">宮藤春男<
                directorg = re.search(r'導演:</span> <a href=".+?">(.+?)<', bav_html)
                if str(directorg) != 'None':
                    nfo_dict['導演'] = directorg.group(1)
                else:
                    nfo_dict['導演'] = '未知導演'
                # 演員們 和 # 第一個演員
                # <a href="https://www.cdnbus.work/star/v0o" title="琴音芽衣">
                # <img src="https://images.javcdn.pw/actress/q7u.jpg" title="神田るな">
                # actors = re.findall(r'<img src="https://images.javcdn.pw/actress/q7u.jpg" title="神田るな">', bav_html)
                actors = re.findall(r'/star/.+?"><img src=.+?" title="(.+?)">', bav_html)
                # print(actors)
                if len(actors) != 0:
                    if len(actors) > 7:
                        actors = actors[:7]
                    nfo_dict['首個女優'] = actors[0]
                    nfo_dict['userrating'] = rating_settings.get('actor', actors[0], fallback= '0')
                    nfo_dict['全部女優'] = ' '.join(actors)
                else:
                    nfo_dict['userrating'] = '0'
                    nfo_dict['首個女優'] = nfo_dict['全部女優'] = '未知演員'
                    actors = ['未知演員']
                nfo_dict['標題'] = nfo_dict['標題'].rstrip(nfo_dict['全部女優'])
                # 特點 <span class="genre"><a href="https://www.cdnbus.work/uncensored/genre/gre085">自慰</a></span>
                genres = re.findall(r'<span class="genre"><a href=".+?">(.+?)</a></span>', bav_html)
                genres = [i for i in genres if i != '字幕' and i != '高清' and i != '高畫質']
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
                # arzon的簡介 #########################################################
                plot = ''
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
                            # arzon搜索頁面實際是18歲驗證
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
                                        fail_times) + '個失敗！arzon找不到該影片，可能被下架：' + arz_search_url + '，' + relative_path + '\n'
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
                if if_mp4 == '是':  # 新文件名
                    new_mp4 = ''
                    for j in rename_mp4_list:
                        new_mp4 += nfo_dict[j]
                    new_mp4 = new_mp4.rstrip(' ')
                    cd_msg = ''
                    if cars_dic[car_num] > 1:    # 是CD1還是CDn？
                        cd_msg = part_prefix + str(srt.episodes)
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
                            "  <plot>" + plot + "</plot>\n"
                            "  <title>" + cus_title + "</title>\n"
                            "  <director>" + nfo_dict['導演'] + "</director>\n"
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
                    w, h = img.size  # fanart的寬 高
                    ex = int(w * 0.52625)  # 0.52625是根據emby的poster寬高比較出來的
                    poster = img.crop((ex, 0, w, h))  # （ex，0）是左下角（x，y）座標 （w, h)是右上角（x，y）座標
                    poster.save(poster_path, quality=95)  # quality=95 是無損crop，如果不設置，默認75
                    print('    >poster.jpg裁剪成功')

                # 5收集女優頭像
                if if_sculpture == '是':
                    if actors[0] == '未知演員':
                        print('    >未知演員')
                    else:
                        for each_actor in actors:
                            exist_actor_path = actors_source + '/' + each_actor + '.jpg'
                            jpg_type = '.jpg'
                            if not os.path.exists(exist_actor_path):  # 女優jpg圖片還沒有
                                exist_actor_path = actors_source + '/' + each_actor + '.png'
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
                            shutil.copyfile(actors_source + '/' + each_actor + jpg_type,
                                            actors_path + each_actor + jpg_type)
                            print('    >女優頭像收集完成：', each_actor)

                # 6歸類影片，針對文件夾
                if if_classify == '是'  and file_folder == '文件夾' and (
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

    start_key = 'skip'
