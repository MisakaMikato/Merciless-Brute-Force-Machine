import optparse
import json
import os

from dotenv import load_dotenv

from . import SQLHelper

load_dotenv()

__HOST = os.getenv('DATABASE_HOST')
__DATABASE = os.getenv('DATABASE_NAME')
__USER = os.getenv('DATABASE_USER')
__PASSWORD = os.getenv('DATABASE_PASSWD')


def param_input():
    usage = "[-o <output file path>][-i <input file path>]"
    parser = optparse.OptionParser(usage)
    parser.add_option(
        '-i',
        dest='in_file_path',
        type='string',
        help='eg: -i ip.txt'
    )
    parser.add_option(
        '-o',
        dest='out_file_path',
        type='string',
        help='eg: -o result.txt'
    )
    parser.add_option(
        '--host',
        dest='host',
        type='string',
        help='eg: --host 127.0.0.1'
    )
    (options, args) = parser.parse_args()

    return options


def query_ownershop(ip):
    sql_helper_factory = SQLHelper.SQLServerHelperFactory(
        host=__HOST,
        database=__DATABASE,
        user=__USER,
        pwd=__PASSWORD
    )
    sql_helper = sql_helper_factory.Build(SQLHelper._MySQL)
    sql = f'SELECT attribution FROM ip_attribution WHERE ip=INET_ATON("{ip}")'
    result = sql_helper.ExecQuery(sql)
    if len(result) == 0 or result[0][0] is None:
        return '未找到归属地'
    return result[0][0].replace('\n', '')


def format_output(ics_scan_file, out_file_path):
    protocol_mapper = {
        102: 'SIMATIC S7 PLCs',
        502: 'Modbus',
        44818: 'Rockwell Automation / Allen Bradley',
        47808: 'BACnet',
        1911: 'Niagara Fox',
        9600: 'OMRON FINS',
        1962: 'PC Worx',
        20547: 'ProConOS/MultiProg'
    }
    cnt = 1
    with open(ics_scan_file, 'r') as in_file:
        json_obj = json.load(in_file)
    with open(out_file_path, 'w') as out_file:
        for item in json_obj:
            for ip, val in item.items():
                for port, info in val.items():
                    owner_ship = query_ownershop(ip)
                    protocol = protocol_mapper[int(port)]
                    out_file.write(
                        f"{cnt},{ip},{owner_ship},{protocol},{port}\n")
                    cnt += 1


def query_by_file(in_file_path, out_file_path):
    with open(in_file_path, 'r') as in_file:
        with open(out_file_path, 'w') as out_file:
            lines = in_file.readlines()
            for ip in lines:
                ip = ip.replace('\r', '').replace('\n', '')
                result = query_ownershop(ip)
                out_file.write(f"{ip},{str(result[0][0]).replace(chr(10),'')}")
                out_file.write('\n')


def main():
    options = param_input()

    in_file_path = options.in_file_path
    out_file_path = options.out_file_path
    host = options.host

    if host:
        result = query_ownershop(host)
        print(f"the ownership of {host} is {str(result)}")

    if(in_file_path and out_file_path):
        query_by_file(in_file_path, out_file_path)


if __name__ == "__main__":
    main()
