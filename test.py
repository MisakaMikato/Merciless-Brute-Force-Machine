from filesio import Reader, Writer
from bruteforce import HuaweiBruteForce, H3CBruteForce, BruteForceInvoke, CiscoBruteForce
from device import Device


def huawei_brute_force_class_test():
    reader = Reader('./fileserver/20200710135334-asset.xlsx')
    obj_list = reader.goby_file_reader()
    bf = HuaweiBruteForce(obj_list)
    bf.invoke(out_file_path='./data/huawei_weak_passwd')


def huawei_function_test():
    devices = []
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
    writer.create_excel_report('./data/weak_passwd.bak')


if __name__ == "__main__":
    create_report_test()
