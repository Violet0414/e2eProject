"""测试数据生成工具"""
import random
import string
from datetime import datetime, timedelta


class DataGenerator:
    """数据生成工具类"""

    @staticmethod
    def random_4bit_str():
        """生成4位随机字符串"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

    @staticmethod
    def random_phone():
        """生成随机手机号"""
        prefixes = ['130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
                   '150', '151', '152', '153', '155', '156', '157', '158', '159',
                   '180', '181', '182', '183', '184', '185', '186', '187', '188', '189']
        return random.choice(prefixes) + ''.join(random.choices(string.digits, k=8))

    @staticmethod
    def random_name():
        """生成随机姓名"""
        surnames = ['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '周', '吴',
                   '徐', '孙', '马', '朱', '胡', '郭', '林', '何', '高', '梁']
        given = ['伟', '芳', '娜', '敏', '静', '丽', '强', '磊', '军', '洋',
                '勇', '艳', '杰', '涛', '明', '超', '秀英', '桂英', '建华', '志强']
        return random.choice(surnames) + random.choice(given)

    @staticmethod
    def random_company():
        """生成随机公司名称"""
        prefixes = ['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉', '南京', '西安', '重庆']
        names = ['科技', '实业', '贸易', '信息', '网络', '传媒', '咨询', '服务', '电子', '智能']
        types = ['有限公司', '股份有限公司', '集团有限公司']
        return (random.choice(prefixes) + random.choice(names) +
                random.choice(names) + random.choice(types))

    @staticmethod
    def random_address():
        """生成随机地址"""
        streets = ['人民路', '建设路', '解放路', '文化路', '和平路', '光明路', '复兴路', '友谊路']
        return (f"{random.choice(['成都市', '北京市', '上海市', '广州市', '深圳市'])}"
                f"{random.choice(streets)}{random.randint(1, 999)}号")

    @staticmethod
    def random_email():
        """生成随机邮箱"""
        username = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 10)))
        domains = ['qq.com', '163.com', '126.com', 'gmail.com', 'hotmail.com']
        return f"{username}@{random.choice(domains)}"

    @staticmethod
    def random_id_card():
        """生成随机身份证号（模拟格式）"""
        area_codes = ['110101', '310101', '440103', '510104', '320105']
        area_code = random.choice(area_codes)
        birth_date = (datetime.now() - timedelta(days=random.randint(365*18, 365*60))).strftime('%Y%m%d')
        seq = ''.join(random.choices(string.digits, k=3))
        check_code = random.choice(string.digits + 'Xx')
        return f"{area_code}{birth_date}{seq}{check_code}"

    @staticmethod
    def random_int(min_val: int = 0, max_val: int = 100):
        """生成随机整数"""
        return random.randint(min_val, max_val)

    @staticmethod
    def random_float(min_val: float = 0, max_val: float = 1000, decimals: int = 2):
        """生成随机浮点数"""
        value = random.uniform(min_val, max_val)
        return round(value, decimals)


fake_data = DataGenerator()
