'''
@Descripttion: SQL Server工具包, 集成了mssql,mysql,sqlite的操作类, 推荐使用工厂类实例化操作类
@version: 
@Author: gong
@Date: 2019-08-09 09:14:16
@LastEditors: gong
@LastEditTime: 2019-10-23 16:26:10
'''
import pymssql
import pymysql

_MSSQL = 0
_MySQL = 1
_MongoDB = 2


class ISQLServerHelper:
    '''SQL Server interface.'''
    # 联接数据库
    def ConnectDatabase(self):
        raise Exception('子类中必须实现该方法')
    # 执行SQL命令

    def ExecCommand(self, sql):
        raise Exception('子类中必须实现该方法')
    # 执行SQL查询

    def ExecQuery(self, sql):
        raise Exception('子类中必须实现该方法')
    # 更新数据库

    def Update(self, sql, param):
        raise Exception('子类中必须实现该方法')
    # 执行多个更新语句

    def UpdateMany(self, sql, paramList):
        raise Exception('子类中必须实现该方法')


class MSSQLServerHelper(ISQLServerHelper):
    def __init__(self, _host='', _database='', _user='', _passwd='', _verify=True):
        self.host = _host
        self.database = _database
        self.user = _user
        self.pwd = _passwd
        self.verify = _verify

    def ConnectDatabase(self):
        if not self.host:
            raise("没有目标数据库")
        else:
            if self.verify:
                self.connect = pymssql.connect(
                    self.host, user=self.user, password=self.pwd, database=self.database)
            else:
                self.connect = pymssql.connect(
                    self.host, database=self.database)
            cursor = self.connect.cursor()
        if not cursor:
            raise("Microsoft SQL Server访问失败")
        else:
            return cursor

    def ExecCommand(self, command):
        cursor = self.ConnectDatabase()
        cursor.execute(command)
        self.connect.commit()
        self.connect.close()

    def ExecQuery(self, command):
        cursor = self.ConnectDatabase()
        cursor.execute(command)
        resultList = cursor.fetchall()
        self.connect.close()
        return resultList

    def Update(self, command, param):
        try:
            cursor = self.ConnectDatabase()
            cursor.execute(command, param)
            self.connect.commit()
        except Exception as ex:
            print(f"[ERROR] in MSSQLServerHelper.Update, {ex}.")
        self.connect.close()


class MySQLServerHelper(ISQLServerHelper):
    def __init__(self, _host='localhost', _database='',
                 _user='', _passwd='', _verify=True):
        self.host = _host
        self.database = _database
        self.user = _user
        self.pwd = _passwd
        self.verify = _verify

    # 连接数据库
    def ConnectDatabase(self):
        if not self.host:
            raise("没有目标数据库")
        else:
            if self.verify:
                self.connect = pymysql.connect(
                    self.host,
                    user=self.user,
                    password=self.pwd,
                    database=self.database,
                    charset='utf8'
                )
            else:
                self.connect = pymssql.connect(
                    self.host, database=self.database)
            cursor = self.connect.cursor()
        if not cursor:
            raise("MySQL访问失败")
        else:
            return cursor

    def ExecCommand(self, command):
        try:
            cursor = self.ConnectDatabase()
            cursor.execute(command)
            self.connect.commit()
        except Exception:
            self.connect.rollback()
        self.connect.close()

    def ExecCommandMany(self, command, param: list):
        '''
        Execute many SQL command, such as INSERT.
        Param command: SQL command, containing placeholder, such as %s.
        Param param: the specific content of placeholder in command.
        '''
        try:
            cursor = self.ConnectDatabase()
            cursor.executemany(command, param)
            self.connect.commit()
        except Exception:
            self.connect.rollback()
        self.connect.close()

    def ExecQuery(self, command):
        cursor = self.ConnectDatabase()
        cursor.execute(command)
        resultList = cursor.fetchall()
        self.connect.close()
        return resultList

    # command中可以使用诸如%s之类的占位符, param为占位符的具体内容
    def Update(self, command, param):
        try:
            cursor = self.ConnectDatabase()
            cursor.execute(command, param)
            self.connect.commit()
        except Exception as ex:
            print("[ERROR] in MySQLServerHelper.Update: {}".format(ex))
            print("[ERROR] SQL query: {}".format(command % param))
            self.connect.rollback()
        self.connect.close()

    def UpdateMany(self, command, paramList):
        '''
        @description: do many update query.
        @param {command:string, paramList:list[tup]} 
        @return: None
        '''
        try:
            cursor = self.ConnectDatabase()
            for param in paramList:
                cursor.execute(command, param)
            self.connect.commit()
        except Exception as ex:
            print("[ERROR] in MySQLServerHelper.Update: {}".format(ex))
            self.connect.rollback()
        self.connect.close()


class MongoDBHelper(ISQLServerHelper):
    def __init__(self, _host='.', _database='', _user='', _passwd='', _verify=True):
        self.host = _host
        self.database = _database
        self.user = _user
        self.pwd = _passwd
        self.verify = _verify
    # 联接数据库

    def ConnectDatabase(self):
        raise Exception('子类中必须实现该方法')
    # 执行SQL命令

    def ExecCommand(self, sql):
        raise Exception('子类中必须实现该方法')
    # 执行SQL查询

    def ExecQuery(self, sql):
        raise Exception('子类中必须实现该方法')
    # 更新数据库

    def Update(self, sql, param):
        raise Exception('子类中必须实现该方法')


class SQLServerHelperFactory:
    '''SQLServerHelper工厂类'''
    def __init__(self, host='', database='', user='', pwd=''):
        self.__host__ = host
        self.__database__ = database
        self.__user__ = user
        self.__pwd__ = pwd

    def UseMSSQL(self):
        return MSSQLServerHelper(self.__host__, self.__database__, self.__user__, self.__pwd__)

    def UseMySQL(self):
        return MySQLServerHelper(self.__host__, self.__database__, self.__user__, self.__pwd__)

    def UseMongoDB(self):
        return MongoDBHelper(self.__host__, self.__database__, self.__user__, self.__pwd__)

    def DBChooseError(self):
        exit('[ERROR] 尚不支持此类数据库, 请使用MSSQL, MySQL或MongoDB中的一种.\n')

    def Build(self, sqlServerType):
        switchDict = {
            _MSSQL: self.UseMSSQL,
            _MySQL: self.UseMySQL,
            _MongoDB: self.UseMongoDB,
        }
        return switchDict.get(sqlServerType, self.DBChooseError)()


# example
def main():
    sqliteHelper = SQLServerHelperFactory().Build(_MSSQL)
    # resultList = sqliteHelper.ExecQuery("select * from vul")


if __name__ == "__main__":
    main()
