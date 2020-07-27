import xlrd
import xlwt
import re
from loguru import logger

from device import Device
from query.query_ip_ownership import query_ownershop


class Reader:
    '''从文件中读取信息'''

    def __init__(self, in_file_path):
        self.devices_list_mapper = {
            "huawei": [],
            "cisco": [],
            "engeniux": [],
            "h3c": [],
            "hirschmann": [],
            "leadsec": [],
            "nsfocus": [],
            "sangfor": [],
            "secworld": [],
            "topsec": [],
            "venustech": [],
            "zte": [],
            "zzhr": [],
            "default": []
        }
        self.in_file_path = in_file_path

    def xls_file_reader(self):
        '''读入xls模板文件, 生成标准的device列表映射器'''
        IP_COL = 3
        BRAND_COL = 4
        OTHER_COL = 6
        xls = xlrd.open_workbook(self.in_file_path)
        sheet = xls.sheets()[0]
        len_rows = sheet.nrows
        for i in range(1, len_rows):
            ip = sheet.cell_value(i, IP_COL)
            brand = sheet.cell_value(i, BRAND_COL)
            if brand.strip() == '其它':
                brand = sheet.cell_value(i, OTHER_COL)
            device_obj = Device(ip, brand)
            try:
                self.devices_list_mapper[device_obj.format_brand].append(
                    device_obj)
            except KeyError as ke:
                logger.info(ke)
        return self.devices_list_mapper

    def goby_file_reader(self):
        '''根据goby的扫描xls文件, 生成标准的device列表映射器'''
        IP_COL = 0
        PORT_COL = 1
        HARDWARE_COL = 9
        xls = xlrd.open_workbook(self.in_file_path)
        sheet = xls.sheets()[0]
        len_rows = sheet.nrows
        for i in range(1, len_rows):
            ip = sheet.cell_value(i, IP_COL)
            port = sheet.cell_value(i, PORT_COL)
            hardware = sheet.cell_value(i, HARDWARE_COL)
            if re.search('8443|80|443', port):
                device_obj = Device(ip, hardware, hardware)
                try:
                    self.devices_list_mapper[device_obj.format_brand].append(
                        device_obj)
                except KeyError as ke:
                    logger.info(ke)
        return self.devices_list_mapper


class Writer:
    def __init__(self, out_file_path):
        self.out_file_path = out_file_path

    def file_writer(self, message, mode='a+'):
        with open(self.out_file_path, mode) as f:
            f.write(message+'\n')

    def create_excel_report(self, brute_force_result_path):
        '''根据爆破的结果生成excel报告

        Keyword arguments:
        brute_force_result_path -> 爆破结果的路径
        out_file_path -> 报告输出路径
        '''
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Sheet1')
        i = 0
        with open(brute_force_result_path, 'r') as f:
            lines = f.readlines()

        for line in lines:
            line = line.replace('\n', '')
            if 'unknown' in line:
                continue
            ip = re.findall(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', line)[0]
            hardware = re.findall(r'[0-9]{1,3},(.*),admin', line)[0]
            passwd = re.findall(hardware + ',(.*)', line)
            ownershop = query_ownershop(ip)
            worksheet.write(i, 0, label=(i + 1))
            worksheet.write(i, 1, label=ip)
            worksheet.write(i, 2, label=hardware)
            worksheet.write(i, 3, label=passwd)
            worksheet.write(i, 4, label=ownershop)
            i += 1
        workbook.save(self.out_file_path)
