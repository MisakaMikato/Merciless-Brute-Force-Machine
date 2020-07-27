import re


class Device:
    def __init__(self, ip, brand, device_type=None):
        self.brand_pattern = [
            'cisco|:cisco', 'huawei|hua|华为|:huawei', 'engeniux|:engeniux', 'h3c|华三|:h3c',
            'hirschmann|赫斯曼|:hirschmann', 'leadsec|:leadsec', 'nsfocus|绿盟|:nsfocus',
            'sangfor|深信服|:sangfor', 'secworld|网神|:secworld', 'topsec|天融信|:topsec',
            'venustech|启明星辰|:venustech', 'zte|中兴|:zte', 'zzhr|鸿瑞|:zzhr'
        ]
        self.type_pattern = [
            # TODO 根据具体的型号(而不是模糊的)返回设备类型
            'secoway', 'firewall', 'switch', 'gateway', 'router'
        ]
        self.ip = ip
        self.brand = brand
        self.type = self.get_format_type(device_type)
        self.default_brand = 'default'
        self.format_brand = self.get_format_brand(self.brand)

    def __str__(self):
        return f"{self.ip},{self.brand},{self.format_brand},{self.type}"

    def __repr__(self):
        return f"{self.ip},{self.brand}"

    def get_format_brand(self, brand):
        for pattern in self.brand_pattern:
            if re.search(pattern, brand, re.I):
                return re.findall(':(.*)', pattern)[0]
        return self.default_brand

    def get_format_type(self, device_type):
        if not device_type:
            return None
        for pattern in self.type_pattern:
            if re.search(pattern, device_type, re.I):
                return pattern
        return None
