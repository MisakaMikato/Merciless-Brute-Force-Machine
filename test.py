import time
import selenium
import re

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.by import By

from filesio import Reader, Writer
from bruteforce import HuaweiBruteForce, H3CBruteForce, BruteForceInvoke, CiscoBruteForce
from device import Device


class TestPasswd:
    def __init__(self, proxy=None):
        self.proxy = Proxy({
            'proxyType': ProxyType.MANUAL,
            'httpProxy': proxy,
            'ftpProxy': proxy,
            'sslProxy': proxy,
            'noProxy': ''
        })
        self.browser = webdriver.Firefox(proxy=self.proxy)
        self.browser.set_page_load_timeout(20)

    def is_element_exist_by_id(self, element_id):
        '''判断当前页面是否存在某个元素'''
        browser = self.browser
        try:
            browser.find_element_by_id(element_id)
            return True
        except Exception:
            return False

    def test_firewall(self, ip, username, passwd):
        self.browser.get(f"http://{ip}")
        wait = WebDriverWait(self.browser, 30)
        username_input = wait.until(ec.presence_of_element_located((By.ID, 'username')))
        time.sleep(0.3)
        if self.is_element_exist_by_id('hide_pwd'):
            self.browser.find_element_by_id('hide_pwd').click()
            time.sleep(0.3)
        # 输入用户名密码
        self.browser.find_element_by_id('platcontent').send_keys(passwd)
        time.sleep(0.3)
        username_input.send_keys(username)
        time.sleep(0.3)
        # 前端不加密的防火墙
        if self.is_element_exist_by_id('btn_login-button'):
            self.browser.find_element_by_id('btn_login-button').click()
            if '登录失败' in self.browser.page_source:
                print(f"{ip}: 登录失败")
                return False
            network_menu = wait.until(ec.presence_of_element_located((By.ID, 'topMenunetwork_li')))
            network_menu.click()
            wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'x-grid3-row-table')))
        # 前端加密的防火墙
        else:
            self.browser.find_element_by_css_selector('[type="submit"]').click()
            try:
                wait.until(ec.presence_of_element_located((By.ID, 'tree')))
                self.browser.switch_to.frame('tree')
                wait.until(ec.presence_of_element_located((By.ID, 'NetWorkActuator'))).click()
                wait.until(ec.presence_of_element_located((By.ID, 'InterfaceActuator'))).click()
                time.sleep(1)
            except selenium.common.exceptions.UnexpectedAlertPresentException:
                print(f"{ip}: 登录失败")
                return False

        self.browser.get_screenshot_as_file(f'./image/{ip}.png')
        return True

    def test_secoway(self, ip, username, passwd):
        wait = WebDriverWait(self.browser, 20)
        # action_chains = ActionChains(self.browser)
        try:
            self.browser.get(f'http://{ip}')
        except selenium.common.exceptions.TimeoutException:
            print(f'{ip}: 连接超时')
            return False
        except Exception:
            self.browser.find_element_by_id('enableTls10Button').click()
        username_input = wait.until(ec.presence_of_element_located((By.ID, 'username')))
        username_input.send_keys(username)
        time.sleep(0.3)
        self.browser.find_element_by_id('platcontent').send_keys(passwd)
        time.sleep(0.3)
        # 登录按钮
        self.browser.find_element_by_id('ext-gen21').click()
        if '登录失败' in self.browser.page_source:
            print(f'{ip}: 登录失败')
            return False
        network_menu = wait.until(ec.presence_of_element_located((By.ID, 'treewoda-tree-menunetwork')))
        self.browser.find_element_by_id('ext-gen16').click()
        time.sleep(0.3)
        network_menu.click()
        wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'x-grid3-row-table')))
        self.browser.get_screenshot_as_file(f'./image/{ip}.png')
        return True


def huawei_brute_force_class_test():
    reader = Reader('./fileserver/20200710135334-asset.xlsx')
    obj_list = reader.goby_file_reader()
    bf = HuaweiBruteForce(obj_list)
    bf.invoke(out_file_path='./data/huawei_weak_passwd')


def huawei_function_test():
    devices = [
        Device('10.206.6.147', 'Huawei-Switch', 'Huawei-Switch')
    ]
    bf = HuaweiBruteForce(devices)
    bf.invoke()


def h3c_brute_force_class_test():
    reader = Reader('./fileserver/20200710135334-asset.xlsx')
    obj_list = reader.goby_file_reader()['h3c']
    bf = H3CBruteForce(obj_list)
    bf.invoke()


def cisco_brute_force_class_test():
    reader = Reader('./fileserver/20200710135334-asset.xlsx')
    obj_list = reader.goby_file_reader()['cisco']
    bf = CiscoBruteForce(obj_list)
    bf.invoke()


def brute_force_invoke_test():
    brute_force_invoke = BruteForceInvoke()
    brute_force_invoke.set_output('./data/weak_passwd')
    brute_force_invoke.do('./fileserver/20200710135334-asset.xlsx')


def create_report_test():
    writer = Writer('./data/默认口令设备清单.xlsx')
    writer.create_excel_report('./data/valid-passwd')


def passwd_valid_test(last_ip=None):
    pause = last_ip is None
    with open('./data/weak_passwd', 'r') as f:
        lines = f.readlines()
    test_obj = TestPasswd("127.0.0.1:7070")
    out_file = open('./data/valid-passwd', 'w')
    for line in lines:
        flag = False
        line = line.replace('/n', '')
        if 'unknown' in line:
            continue
        ip = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line)[0]
        hardware = re.findall(f"{ip},(.*),admin", line)[0]
        passwd = re.findall(f'{hardware},(.*)', line)[0]
        if ip == last_ip:
            pause = True
        if not pause:
            continue
        username, passwd = passwd.split(':')
        try:
            if re.findall('Secoway', hardware, re.I):
                flag = test_obj.test_secoway(ip, username, passwd)
            elif re.findall('Firewall', line, re.I):
                flag = test_obj.test_firewall(ip, username, passwd)
            if flag:
                msg = f'{ip},{hardware},{username}:{passwd}'
                out_file.write(msg + '\n')
                print(msg)
        except selenium.common.exceptions.TimeoutException:
            print(f'{ip}: 连接超时')
        except selenium.common.exceptions.WebDriverException:
            print(f'{ip}: 连接失败')


def unique(in_file_path, out_file_path):
    '''进行ip去重'''
    with open(in_file_path, 'r') as f:
        lines = f.readlines()
    vis = []
    writer = Writer(out_file_path, mode='w')
    for line in lines:
        line = line.replace('\n', '')
        ip = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line)
        if ip not in vis:
            writer.file_writer(line)
            vis.append(ip)


if __name__ == "__main__":
    # passwd_valid_test()
    # unique('./data/valid-passwd', './data/weak_passwd')
    # brute_force_invoke_test()
    create_report_test()
