import xlrd
import re
from loguru import logger

from device import Device

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
                self.devices_list_mapper[device_obj.format_brand].append(device_obj)
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
            # TODO here is for test
            if re.search('8443|80|443', port):
                device_obj = Device(ip, hardware, hardware)
                try:
                    self.devices_list_mapper[device_obj.format_brand].append(device_obj)
                except KeyError as ke:
                    logger.info(ke)
        return self.devices_list_mapper


class Writer:
    def __init__(self, out_file_path):
        self.out_file_path = out_file_path
    
    def file_writer(self, message, mode = 'a+'):
        with open(self.out_file_path, mode) as f:
            f.write(message+'\n')