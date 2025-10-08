##
# @Author: SocialSisterYi
# @Edit: Samueli924
# @Reference: https://github.com/SocialSisterYi/xuexiaoyi-to-xuexitong-tampermonkey-proxy
#

import base64
import hashlib
import json
import os
import sys
from io import BytesIO
from pathlib import Path
from typing import Dict, IO, Optional, Union

from fontTools.ttLib.tables._g_l_y_f import Glyph, table__g_l_y_f
from fontTools.ttLib.ttFont import TTFont
from api.exceptions import FontDecodeError
from api.logger import logger


# 康熙部首替换表
KX_RADICALS_TAB = str.maketrans(
    # 康熙部首
    "⼀⼄⼆⼈⼉⼊⼋⼏⼑⼒⼔⼗⼘⼚⼜⼝⼞⼟⼠⼤⼥⼦⼨⼩⼫⼭⼯⼰⼲⼴⼸⼼⼽⼿⽀⽂⽃⽄⽅⽆⽇⽈⽉⽊⽋⽌⽍⽏⽐⽑⽒⽓⽔⽕⽖⽗⽚⽛⽜⽝⽞⽟⽠⽡⽢⽣⽤⽥⽩⽪⽫⽬⽭⽮⽯⽰⽲⽳⽴⽵⽶⽸⽹⽺⽻⽼⽽⽿⾁⾂⾃⾄⾆⾈⾉⾊⾍⾎⾏⾐⾒⾓⾔⾕⾖⾚⾛⾜⾝⾞⾟⾠⾢⾣⾤⾥⾦⾧⾨⾩⾪⾬⾭⾮⾯⾰⾲⾳⾴⾵⾶⾷⾸⾹⾺⾻⾼⿁⿂⿃⿄⿅⿇⿉⿊⿍⿎⿏⿐⿒⿓⼣⺁⺇⺌⺎⺏⺐⺑⺒⺓⺛⺝⺟⺠⺱⺸⻁⻄⻅⻆⻇⻉⻋⻒⻓⻔⻗⻘⻙⻚⻛⻜⻝⻡⻢⻣⻤⻥⻦⻧⻨⻩⻬⻮⻯⻰⻳⾅⼾⼱⼁⼂⼃⼅⼇⼌⼍⼎⼐⼓⼕⼖⼙⼛⼡⼢⼧⼪⼬⼮⼳⼵⼶⼷⼹⼺⼻⽁⽎⽘⽙⽦⽧⽨⽱⽷⽾⾀⾇⾋⾌⾑⾗⾘⾙⾡⾫⾱髙⾽⾾⾿⿀⿆⿈⿋⿌⿑⿔⿕",
    # 对应汉字
    "一乙二人儿入八几刀力匕十卜厂又口囗土士大女子寸小尸山工己干广弓心戈手支文斗斤方无日曰月木欠止歹毋比毛氏气水火爪父片牙牛犬玄玉瓜瓦甘生用田白皮皿目矛矢石示禾穴立竹米缶网羊羽老而耳肉臣自至舌舟艮色虫血行衣見角言谷豆赤走足身車辛辰邑酉采里金長門阜隶雨青非面革韭音頁風飛食首香馬骨高鬼魚鳥鹵鹿麻黍黑鼎鼓鼠鼻齒龍夕厂几小兀尣尢𡯂巳幺旡月母民冈芈虎西见角𧢲贝车镸长门雨青韦页风飞食𩠐马骨鬼鱼鸟卤麦黄齐齿竜龙龟臼戶巾丨丶丿亅亠冂冖冫凵勹匚匸卩厶夂夊宀尢屮巛幺廴廾弋彐彡彳攴殳爻爿疋疒癶禸糸耒聿舛艸虍襾豕豸貝辵隹韋高髟鬥鬯鬲麥黃黹黽齊龜龠",
)


def resource_path(relative_path: str) -> str:
    """
    获取资源文件的路径，兼容PyInstaller打包后的环境

    Args:
        relative_path: 相对路径

    Returns:
        资源文件的绝对路径
    """
    try:
        # PyInstaller创建临时文件夹，定位路径
        base_path = sys._MEIPASS
    except Exception:
        # 非打包环境，使用当前目录
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


class FontHashDAO:
    """
    字体哈希数据访问对象，负责管理字体哈希映射表
    """

    def __init__(self, file_path: str = "resource/font_map_table.json"):
        """
        初始化字体哈希数据访问对象

        Args:
            file_path: 字体映射表JSON文件路径，相对于资源目录
        
        Raises:
            FileNotFoundError: 当字体映射表文件不存在时
            json.JSONDecodeError: 当字体映射表JSON格式错误时
        """
        self.char_map: Dict[str, str] = {}  # unicode -> hash
        self.hash_map: Dict[str, str] = {}  # hash -> unicode
        
        full_path = resource_path(file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as fp:
                self.char_map = json.load(fp)
                self.hash_map = {hash_val: char for char, hash_val in self.char_map.items()}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise FontDecodeError(f"加载字体映射表失败: {full_path} - {e}") from e

    def find_char(self, font_hash: str) -> Optional[str]:
        """
        通过字体哈希值查找对应的Unicode字符编码

        Args:
            font_hash: 字体哈希值

        Returns:
            对应的Unicode字符编码，如果未找到则返回None
        """
        return self.hash_map.get(font_hash)

    def find_hash(self, char: str) -> Optional[str]:
        """
        通过Unicode字符编码查找对应的字体哈希值

        Args:
            char: Unicode字符编码 (如 "uni4E00")

        Returns:
            对应的字体哈希值，如果未找到则返回None
        """
        return self.char_map.get(char)


# 初始化字体哈希DAO单例
try:
    fonthash_dao = FontHashDAO()
except Exception as e:
    logger.warning(f"初始化字体哈希数据失败 - {e}")
    fonthash_dao = FontHashDAO.__new__(FontHashDAO)
    fonthash_dao.char_map = {}
    fonthash_dao.hash_map = {}


def hash_glyph(glyph: Glyph) -> str:
    """
    计算TTF字体字形的哈希值
    
    Args:
        glyph: TTF字体字形对象
    
    Returns:
        字形的MD5哈希值
    """
    if glyph.numberOfContours <= 0:
        return ""
    
    pos_data = []
    last_index = 0
    
    for i in range(glyph.numberOfContours):
        end_point = glyph.endPtsOfContours[i]
        for j in range(last_index, end_point + 1):
            x, y = glyph.coordinates[j]
            flag = glyph.flags[j] & 0x01
            pos_data.append(f"{x}{y}{flag}")
        last_index = end_point + 1
    
    pos_bin = "".join(pos_data)
    return hashlib.md5(pos_bin.encode()).hexdigest()


def font2map(font_data: Union[IO, Path, str]) -> Dict[str, str]:
    """
    从字体文件或Base64编码的字体数据中提取字形哈希映射表
    
    Args:
        font_data: 字体文件路径、文件对象或Base64编码的字体数据
    
    Returns:
        字形名称到哈希值的映射字典 ({"uni4E00": "hash值", ...})
    
    Raises:
        ValueError: 当无法解析字体数据时
    """
    font_hashmap = {}
    
    # 处理Base64编码的字体数据
    if isinstance(font_data, str) and font_data.startswith("data:application/font-ttf;charset=utf-8;base64,"):
        try:
            font_data = BytesIO(base64.b64decode(font_data[47:]))
        except Exception as e:
            raise FontDecodeError(f"无法解码Base64字体数据: {e}") from e

    try:
        with TTFont(font_data, lazy=False) as font_file:
            table: table__g_l_y_f = font_file["glyf"]
            for name in table.glyphOrder:
                if name.startswith("uni"):
                    glyph_hash = hash_glyph(table.glyphs[name])
                    if glyph_hash:
                        font_hashmap[name] = glyph_hash
    except Exception as e:
        raise FontDecodeError(f"无法解析字体文件: {e}") from e

    return font_hashmap


def decrypt(dst_fontmap: Dict[str, str], encrypted_text: str) -> str:
    """
    解密超星学习通加密字体的文本
    
    Args:
        dst_fontmap: 目标字体的字形哈希映射表
        encrypted_text: 加密的文本
    
    Returns:
        解密后的文本
    """
    result = []
    
    for char in encrypted_text:
        # 构造Unicode字符名称 (如 "uni4E00")
        char_code = f"uni{ord(char):X}"
        
        # 查找字符在目标字体中的哈希值
        if char_code in dst_fontmap:
            dst_hash = dst_fontmap[char_code]
            # 通过哈希值找回原始字符
            original_char_code = fonthash_dao.find_char(dst_hash)
            if original_char_code:
                # 将Unicode编码转换为字符
                try:
                    original_char = chr(int(original_char_code[3:], 16))
                    result.append(original_char)
                    continue
                except (ValueError, IndexError):
                    pass
        
        # 如果无法解密，则保留原字符
        result.append(char)
    
    # 替换解密后的康熙部首
    decrypted_text = "".join(result).translate(KX_RADICALS_TAB)
    return decrypted_text
