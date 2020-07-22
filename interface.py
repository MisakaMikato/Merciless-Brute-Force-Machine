from typing import List
from abc import abstractmethod, ABCMeta
from filesio import Writer
from loguru import logger

from device import Device


class IBruteForce(metaclass=ABCMeta):
    def __init__(
        self,
        device_obj_list: List[Device]
    ):
        self.passwd_dict_mapper = {
            "huawei": "./dict/huawei_default",
            "cisco": "./dict/cisco_default",
            "engeniux": "./dict/engenius_default",
            "h3c": "./dict/h3c_default",
            "hirschmann": "./dict/hirschmann_default",
            "leadsec": "./dict/leadsec_default",
            "nsfocus": "./dict/nsfocus_default",
            "sangfor": "./dict/sangfor_default",
            "secworld": "./dict/secworld_default",
            "topsec": "./dict/topsec_default",
            "venustech": "./dict/venustech_default",
            "zte": "./dict/zte_deafult",
            "zzhr": "./dict/zzhr_default",
            "default": "./dict/common_passwd"
        }
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4086.0 Safari/537.36',
            'Connection': 'close'
        }
        self.device_obj_list: List[Device] = device_obj_list
        self.method_mapper = self.set_method_mapper()

    @abstractmethod
    def set_method_mapper(self):
        pass

    def unknown_device(self, *args):
        return 'unknown device.'

    def invoke(self, out_file_path=None):
        '''在外部调用该方法以进行弱口令爆破

        Keyword arguments:
        out_file_path -> output path of weak passwd, default path(None) is sys.stdout.
        '''
        writer = Writer(out_file_path)
        for device in self.device_obj_list:
            print(device.ip)
            try:
                result = self.method_mapper.get(
                    device.type,
                    self.unknown_device
                )(device)
            except Exception as e:
                logger.add('./log/error.log')
                logger.error(
                    f"device {device.ip}, {device.type} connect error, see error.log for more information."
                )
                logger.error(e)
                continue
            if result is not None:
                msg = f"{device.ip},{device.brand},{result}"
                print(msg)
                if out_file_path:
                    writer.file_writer(msg)
