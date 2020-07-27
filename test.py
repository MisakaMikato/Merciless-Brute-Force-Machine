from filesio import Reader
from bruteforce import HuaweiBruteForce, H3CBruteForce, BruteForceInvoke, CiscoBruteForce
from device import Device


def huawei_brute_force_class_test():
    reader = Reader('./fileserver/20200710135334-asset.xlsx')
    obj_list = reader.goby_file_reader()
    bf = HuaweiBruteForce(obj_list)
    bf.invoke(out_file_path='./data/huawei_weak_passwd')


def huawei_function_test():
    devices = [
        Device(
            '10.99.183.30',
            'Huawei-Firewall',
            'Huawei-Firewall'
        ),
        Device(
            '10.204.62.198',
            'Huawei-Firewall',
            'Huawei-Firewall',
        )
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


if __name__ == "__main__":
    cisco_brute_force_class_test()
