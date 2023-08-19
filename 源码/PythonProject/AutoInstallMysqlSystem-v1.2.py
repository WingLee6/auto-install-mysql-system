# -*- coding: utf-8 -*-
# @Time    : 2020/1/27 
# @Author  : lee
# @FileName: 
# @Desc    :
#


import sys
import re
import os
import xlrd, xlwt
from decimal import Decimal
from tkinter import *
from tkinter import ttk
import tkinter.messagebox  # 弹窗库
import tkinter.filedialog  # 弹窗文件对话框
import time
import paramiko


class LinkServer():
    def __init__(self, ip, sPwd, mysqlPwd, version):
        self.ip = ip
        self.sPwd = sPwd
        self.mysqlPwd = mysqlPwd
        self.version = version
        self.port = 22
        self.user = 'root'

        self.install_command = 'sh InstallMysql.sh ' + self.mysqlPwd + ' ' + str(self.version)
        self.uninstall_command = 'sh ClearMysql.sh'

        self.rm_install_command = 'rm -rf InstallMysql.sh'
        self.rm_uninstall_command = 'rm -rf ClearMysql.sh'

        self.install_server_path = '/root/InstallMysql.sh'
        self.install_local_path = 'InstallMysql.sh'
        self.uninstall_server_path = '/root/ClearMysql.sh'
        self.uninstall_local_path = 'ClearMysql.sh'

    def mkdir_shell_file(self, shellName, context):
        self.send_command('echo \'#!/bin/bash\' > ' + shellName)
        for i in range(len(context)):
            print(' >> '+context[i])
            self.send_command('echo \'' + context[i] + '\' >> ' + shellName)
            # 检测语句是否写入服务器上shell文件成功
            while self.check_mkdir_shell_file(shellName, context[i]):
                self.send_command('echo \'' + context[i] + '\' >> ' + shellName)
                print(context[i])

    def check_mkdir_shell_file(self, shellName, contextLine):
        '''
        在服务器运行 command 命令，并返回运行结果（没有交互）
        :param command: Linux命令行
        :return:
        '''
        # 检测是否追加写入成功，失败为 False
        writeOK = False
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(self.ip, 22, self.user, self.sPwd, timeout=10)
            std_in, std_out, std_err = ssh_client.exec_command('tail -n 1' + shellName)

            for line in std_out:
                if line.strip("\n") == contextLine:
                    writeOK = True
            ssh_client.close()
        except Exception as e:
            print(e)
        return writeOK

    def check_mysql(self):
        # 检测服务器是否已经安装mysql
        # 未安装为0 安装输出版本号
        checkMysql = '0'

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(self.ip, 22, self.user, self.sPwd, timeout=10)
        std_in, std_out, std_err = ssh_client.exec_command(
            'mysql -uroot -p"' + self.mysqlPwd + '" -e"select version()";')
        # mysql -uroot -p"Mysql345@" -e"select version()";

        for line in std_out:
            # return:
            # version()
            # 5.7.29
            # print(line.strip("\n"))
            checkMysql = line.strip("\n")
        ssh_client.close()

        return checkMysql

    def uninstall_mysql(self):
        # 写入本地卸载脚本ClearMysql.sh准备传到服务器，卸载后删除
        uninstallContext = [
                            '# step1 检测系统是否自带安装 MySQL',
                            'mysql=`rpm -qa | grep mysql`',
                            'mysqlResidualFile=`find / -name mysql`',
                            '# 判断mysql和mysqlResidualFile都不为空（-a)',
                            'if [ -z "$mysql" ] ',
                            'then',
                            '    echo "没有安装MySQL"',
                            'else',
                            '    # step2 若安装mysql，卸载',
                            '    echo "监测到mysql 安装包:"',
                            '    for line in ${mysql}',
                            '    do',
                            '        echo $line',
                            '    done',
                            '    echo "监测到mysql残留文件："',
                            '    for line in ${mysqlResidualFile}',
                            '    do',
                            '        echo $line',
                            '    done',
                            '    # 准备卸载MySQL',
                            '    # read -p "是否立即卸载MySQL(y or n)" yesorno',
                            '    yesorno="y"',
                            '    if [[ $yesorno = "y" || $yesorno = "Y" ]];',
                            '    then',
                            '        # 卸载mysql安装包',
                            '        for line in ${mysql}',
                            '        do',
                            '             echo "正在卸载安装包：$line"',
                            '             rpm -e --nodeps $line',
                            '        done',
                            '        # 删除残留的mysql目录或文件',
                            '        for line in ${mysqlResidualFile}',
                            '        do',
                            '            echo "正在删除残留文件：$line"',
                            '            rm -rf $line',
                            '        done',
                            '        echo "已彻底卸载MySQL";',
                            '    else',
                            '        echo "MySQL未卸载"',
                            '    fi',
                            'fi']
        self.mkdir_shell_file(self.uninstall_local_path, uninstallContext)

        # 上传本地脚本，然后运行该脚本
        # self.sftp_upload_installFile(self.uninstall_server_path, self.uninstall_local_path)
        self.send_command(self.uninstall_command)
        # 检查/等待是否【卸载】完成
        while self.check_mysql() != '0':
            time.sleep(5)

        # 清除服务器的shell脚本文件
        self.send_command(self.rm_uninstall_command)
        self.send_command('ls -l')
        # 清除本地shell文件
        # os.remove(self.uninstall_local_path)

    def install_mysql(self):
        # 写入本地卸载脚本ClearMysql.sh准备传到服务器，卸载后删除
        uninstallContext = [
                            '# step1 检测系统是否自带安装 MySQL',
                            'mysql=`rpm -qa | grep mysql`',
                            'mysqlResidualFile=`find / -name mysql`',
                            '# 判断mysql和mysqlResidualFile都不为空（-a)',
                            'if [ -z "$mysql" ] ',
                            'then',
                            '    echo "没有安装MySQL"',
                            'else',
                            '    # step2 若安装mysql，卸载',
                            '    echo "监测到mysql 安装包:"',
                            '    for line in ${mysql}',
                            '    do',
                            '        echo $line',
                            '    done',
                            '    echo "监测到mysql残留文件："',
                            '    for line in ${mysqlResidualFile}',
                            '    do',
                            '        echo $line',
                            '    done',
                            '    # 准备卸载MySQL',
                            '    # read -p "是否立即卸载MySQL(y or n)" yesorno',
                            '    yesorno="y"',
                            '    if [[ $yesorno = "y" || $yesorno = "Y" ]];',
                            '    then',
                            '        # 卸载mysql安装包',
                            '        for line in ${mysql}',
                            '        do',
                            '             echo "正在卸载安装包：$line"',
                            '             rpm -e --nodeps $line',
                            '        done',
                            '        # 删除残留的mysql目录或文件',
                            '        for line in ${mysqlResidualFile}',
                            '        do',
                            '            echo "正在删除残留文件：$line"',
                            '            rm -rf $line',
                            '        done',
                            '        echo "已彻底卸载MySQL";',
                            '    else',
                            '        echo "MySQL未卸载"',
                            '    fi',
                            'fi']
        self.mkdir_shell_file(self.uninstall_local_path, uninstallContext)
        # 写入本地安装脚本InstallMysql.sh准备传到服务器，卸载后删除
        installContext = [
            'pw=$1',
            'version=$2',
            'echo $pw',
            'echo $version',
            'V=$version',
            '',
            '# 更改安装MySQL版本号',
            '# 参数：$1来自inputVersion()函数，为mysql版本代号',
            'changeVersion(){',
            '    version="mysql"$1',
            '    addr="/etc/yum.repos.d/mysql-community.repo"',
            '',
            '    # line = enabled=0所在行 = [mysql56-community]所在行 + 3',
            '    line=`sed -n  "/${version}/=" $addr`',
            '    line=`expr $line + 3`',
            '     ',
            '    # 将第$line行enabled=0改为=1',
            '    sed -i "${line}s/0/1/" $addr',
            '    # sed  "${line}cenabled=1" $addr',
            '    ',
            '    # 将默认的[mysql80-community]下的enabled=1改为=0',
            '    version80="mysql80"',
            '    line80=`sed -n  "/${version80}/=" $addr`',
            '    line80=`expr $line80 + 3`',
            '    sed -i "${line80}s/1/0/" $addr',
            '}',
            '',
            '# 输入版本号，并验证输入合法性',
            '# 若输入版本号合法，则修改相应配置',
            '# 若输入版本号不合法，再次调用该函数',
            'inputVersion(){',
            '    # 输入您想安装的MySQL版本号',
            '    echo "目前可安装版本为:"',
            '    echo "       mysql55-community ==> 输入55"',
            '    echo "       mysql56-community ==> 输入56"',
            '    echo "       mysql57-community ==> 输入57"',
            '    echo "       mysql80-community ==> 输入80"',
            '    ',
            '    # 测试样例：version=57',
            '    version=$1',
            '    # read -p "输入您想安装的MySQL版本号" version',
            '',
            '    if [ $version == 55 ]',
            '    then',
            '        changeVersion $version',
            '        echo "55"',
            '    elif [ $version == 56 ]',
            '    then',
            '        changeVersion $version',
            '        echo "56"',
            '    elif [ $version == 57 ]',
            '    then',
            '        changeVersion $version',
            '        echo "57"',
            '    elif [ $version == 80 ]',
            '    then',
            '         echo "将安装mysql80-community"',
            '    else',
            '        echo "没有符合的版本号"',
            '        inputVersion',
            '    fi',
            '    return $version',
            '}',
            '',
            'wgetMysql(){',
            '    # 检测安装包是否存在',
            '    mysqlRpm="mysql80-community-release-el7-3.noarch.rpm"',
            '    if [ -e $mysqlRpm ]',
            '    then',
            '        echo "文件 mysql80-community-release-el7-3.noarch.rpm 存>在"',
            '    else',
            '       wget wget https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm',
            '    fi',
            '}',
            '',
            'rpmMysql(){',
            '    rpm -ivh mysql80-community-release-el7-3.noarch.rpm',
            '}',
            '',
            'yumMysql(){',
            '    yum -y update',
            '    yum -y install mysql-server',
            '}',
            '',
            'settingPermissions(){',
            '    echo "权限设置"',
            '    chown mysql:mysql -R /var/lib/mysql',
            '}',
            '',
            'initMysql(){',
            '    # 初始化 MySQL',
            '    echo "初始化 MySQL"',
            '    mysqld --initialize',
            '}',
            '',
            'startMysql(){',
            '    # 启动 MySQL',
            '    echo "启动 MySQL"',
            '    error=`systemctl start mysqld`',
            '',
            '    # 检测报错：Job for mysqld.service failed because the control process exited with error code. See “systemctl status mysqld.service” and “journalctl -xe” for details.',
            '    if [ -n !"$a" ]',
            '    then',
            '        rm -rf /var/lib/mysql',
            '        service mysqld restart',
            '    fi',
            '}',
            '',
            'statusMysql(){',
            '    # 查看 MySQL 运行状态',
            '    echo "查看 MySQL 运行状态"',
            '    systemctl status mysqld',
            '}',
            '',
            'changePassword(){',
            '    version=$1',
            '    pw=$2',
            '',
            '    echo $pw',
            '    echo $version',
            '',
            '    if [ $version -eq 57 -o $version -eq 80 ]',
            '    then',
            '        # 查看mysql尝试随机密码',
            "        a=`cat /var/log/mysqld.log | grep \"temporary password\"`",
            '        echo ${a##*root@localhost: }',
            '        initpw=${a##*root@localhost: }',
            '        # 修改密码为pw',
            '        mysqladmin -uroot -p$initpw password $pw',
            '        echo "a 等于 b"',
            '    else',
            '       mysqladmin password $pw',
            '    fi',
            '}',
            '',
            'wgetMysql',
            '',
            'rpmMysql',
            '',
            'inputVersion $version',
            'mysqlVersion=$?',
            '',
            'yumMysql',
            '',
            'settingPermissions',
            '',
            'initMysql',
            '',
            'startMysql',
            '',
            'statusMysql',
            '',
            'changePassword $V $pw',
            '',
            '# 登陆mysql',
            'mysql -uroot -p$pw -e"show databases";',
            ''
        ]
        self.mkdir_shell_file(self.install_local_path, installContext)

        # 先卸载再安装
        # 将服务器上MySQL卸载清除，防止干扰
        # self.sftp_upload_installFile(self.uninstall_server_path, self.uninstall_local_path)
        self.send_command(self.uninstall_command)
        # 检查/等待是否【卸载】完成
        while self.check_mysql() != '0':
            time.sleep(5)

        # 上传本地安装MySQL安装脚本，并运行该脚本
        # self.sftp_upload_installFile(self.install_server_path, self.install_local_path)
        self.send_command(self.install_command)
        # 检查/等待是否【安装】完成
        while self.check_mysql() == '0':
            time.sleep(5)

        # 清除服务器的shell脚本文件
        self.send_command(self.rm_install_command)
        self.send_command(self.rm_uninstall_command)
        self.send_command('ls -l')

    def sftp_upload_installFile(self, server_path, local_path):
        '''
        上传文件到服务器
        :return:
        '''
        try:
            t = paramiko.Transport((self.ip, 22))
            t.connect(username=self.user, password=self.sPwd)
            sftp = paramiko.SFTPClient.from_transport(t)
            sftp.put(local_path, server_path)
            # sftp.get(local_path, server_path)
            t.close()
        except Exception as e:
            print(e)

    def check_server(self):
        '''
        登陆远程服务器，执行巡检
        输入用户名，密码登陆远程服务器，执行巡检，输入密码 三次 错误则报错执行下一主机登陆。
        :return:
        '''
        for n in range(3):
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(self.ip, 22, self.user, self.sPwd, timeout=10)
                std_in, std_out, std_err = ssh_client.exec_command('hostname')
                hostname = std_out.read()
                ssh_client.close()
                return '连接正常, 检索到主机名为: ', str(hostname)[2:][:-3]
            except Exception as e:
                # print(e)
                return '连接异常, 错误原因: ', e

    def send_command(self, command):
        '''
        在服务器运行 command 命令，并返回运行结果（没有交互）
        :param command: Linux命令行
        :return:
        '''
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(self.ip, 22, self.user, self.sPwd, timeout=10)
            std_in, std_out, std_err = ssh_client.exec_command(command)

            for line in std_out:
                print(line.strip("\n"))
            ssh_client.close()
        except Exception as e:
            print(e)


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master, )
        self.pack()
        # 检测服务其是否可以正常登陆，若有一台以上登陆异常为 1
        self.serverPass = 1
        # 判断在表格中输入次数，保证只有一个输入框
        self.countInput = 0

    def window_init(self):
        '''
        设置窗口标题、界面最大化
        :return:
        '''
        self.master.title('Auto Install Mysql System - v1.0')
        # 具体的函数如下所示，先获得当前屏幕的大小，然后设置窗口大小。
        width, height = self.master.maxsize()
        # self.master.geometry("{}x{}".format(width, height))
        # 窗口尺寸固定
        self.master.maxsize(500, 700)  # 窗口最大尺寸
        self.master.minsize(500, 700)  # 窗口最小尺寸

    def menu_init(self):
        '''
        设置顶部菜单栏
        :return:
        '''
        # 创建菜单栏 (Menu)
        menubar = Menu(self)
        self.master.config(menu=menubar)
        # 创建文件下拉菜单
        filemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="退出", menu=filemenu)
        filemenu.add_command(label="Exit", command=self.master.quit)

    def createWidgets(self):
        '''
        系统界面设计
        分三个部分：
            fm1: GUI 表格
            fm2: GUI 操作按键
            fm3: GUI 操作日志
        :return:
        '''
        # fm1-放数据
        self.fm1 = Frame(self, width=500, height=400, bg='red')
        self.fm1.pack(side=TOP, expand=YES, fill=BOTH)

        # fm2 -放按键
        self.fm2 = Frame(self, width=500, height=50, bg='green')
        self.fm2.pack(side=TOP, expand=YES, fill=BOTH)

        # fm3 -放日志文本框
        self.fm3 = Frame(self, width=500, height=150, bg='gray')
        self.fm3.pack(side=TOP, expand=YES, fill=BOTH)

    def design_showDataBox(self):
        '''
        设计 fm1 的GUI表格，即展示数据
            self.ipcode: IP地址
            self.sPwd: 服务器密码
            self.mysqlPwd: mysql密码
            self.version: mysql版本号
        :return:
        '''
        self.columns = ("IP地址", "服务器密码", "MySQL密码", "MySQL版本")
        self.treeview = ttk.Treeview(self.fm1, height=24, show="headings", columns=self.columns)  # 表格

        self.treeview.column("IP地址", width=150, anchor='center')  # 表示列,不显示
        self.treeview.column("服务器密码", width=120, anchor='center')
        self.treeview.column("MySQL密码", width=120, anchor='center')
        self.treeview.column("MySQL版本", width=120, anchor='center')

        self.treeview.heading("IP地址", text="IP地址")  # 显示表头
        self.treeview.heading("服务器密码", text="服务器密码")
        self.treeview.heading("MySQL密码", text="MySQL密码")
        self.treeview.heading("MySQL版本", text="MySQL版本")

        self.treeview.pack(side=TOP, fill=BOTH)

        '''
        self.ipcode :IP地址
        self.sPw :服务器密码
        self.mysqlPw :mysql密码
        self.version :mysql版本号
        '''
        self.ipcode = []
        self.sPwd = []
        self.mysqlPwd = []
        self.version = []

        for i in range(len(self.ipcode)):  # 写入数据
            self.treeview.insert('', i, values=(self.ipcode[i], self.sPwd[i], self.mysqlPwd[i], self.version[i]))

    def design_buttonBox(self):
        '''
        设计 fm2 的中部按键区
        分为6个按键，分别为：
            增加： 只增加一行数据，双击表格的文字进入插入文本框，点击OK按键完成添加并保持；
            保存： 保存 GUI 表格中的数据，到用户选择的文件数据表下
            批量加载数据： 从用户指定的数据表中加载数据； （数据格式需和GUI表格保持一致）
            连接测试： 对 GUI 表格中的数据，包含的服务器IP及对应密码进行测试登录，返回服务器主机名；
            全部安装： （经过内部测试许可后，）按GUI表中的信息安装Mysql；
            全部卸载：（经过内部测试许可后，）按GUI表中的信息卸载Mysql；
        部分小功能点：
            1. 双击 fm1 中GUI表格数据可进行编辑，一次只能对一个数据进行编辑；
            2. 单击 fm1 中GUI表格标题可对数据进行排序，默认升序；
        备注：
            window按键尺寸(width)：10，10，11，11，11，11
        :return:
        '''
        # 右侧底部按键
        self.treeview.bind('<Double-1>', self.set_cell_value)  # 双击左键进入编辑
        self.fm_foot1 = Button(self.fm2, text='增加', width=10, height=3, command=self.addData)

        # 标题点击排序
        for col in self.columns:
            self.treeview.heading(col, text=col, command=lambda _col=col: self.sort(col, False))

        self.fm_foot2 = Button(self.fm2, text='保存', width=10, height=3, command=self.saveData)
        self.fm_foot3 = Button(self.fm2, text='批量加载数据', width=11, height=3, command=self.loadData)
        self.fm_foot4 = Button(self.fm2, text='连接测试', width=11, height=3, command=self.testLink)
        self.fm_foot5 = Button(self.fm2, text='全部安装', width=11, height=3, command=self.start_install)
        self.fm_foot6 = Button(self.fm2, text='全部卸载', width=11, height=3, command=self.start_uninstall)

        self.fm_foot1.grid(row=0, column=0)
        self.fm_foot2.grid(row=0, column=1)
        self.fm_foot3.grid(row=0, column=2)
        self.fm_foot4.grid(row=0, column=3)
        self.fm_foot5.grid(row=0, column=4)
        self.fm_foot6.grid(row=0, column=5)

    def design_logTextBox(self):
        '''
        设计 fm3 的操作日志输出
        :return:
        '''
        # 滚动条
        sb = Scrollbar(self.fm3)
        sb.pack(side=RIGHT, fill=Y)

        self.logContext = ['    欢迎登陆远程服务器MySQL自动安装系统(v1.0)!']
        # 文本框
        self.listb = Listbox(self.fm3, width=70, height=20, yscrollcommand=sb.set)

        for item in self.logContext:  # 第一个小部件插入数据
            self.listb.insert(0, item)
        self.listb.pack(side=TOP, expand=True)

    def start_uninstall(self):
        '''
        【全部卸载】功能
        :return:
        '''
        # log文本框增加日志文本
        newLog = '开始卸载 MySQL , wait...'
        self.updata_logBox(newLog)

        # 判断服务器数据是否通过连接测试
        if self.serverPass == 0:
            for num in range(len(self.ipcode)):
                b = LinkServer(self.ipcode[num], self.sPwd[num], self.mysqlPwd[num], self.version[num])

                b.uninstall_mysql()
                print(self.ipcode[num] + ' 已卸载;')

                # log文本框增加日志文本
                newLog = self.ipcode[num] + ' 已卸载; '
                self.updata_logBox(newLog)
        else:
            # log文本框增加日志文本
            newLog = '检测到服务器数据未通过连接测试'
            self.updata_logBox(newLog)
            tkinter.messagebox.showinfo('警告', '未通过或未进行【连接测试】')

    def start_install(self):
        '''
        【全部安装】功能
        :return:
        '''

        # log文本框增加日志文本
        newLog = '开始进行 MySQL 安装, wait...'
        self.updata_logBox(newLog)

        # 判断服务器数据是否通过连接测试
        if self.serverPass == 0:
            # 等待时间提示窗口
            installorNot = tkinter.messagebox.askyesno('提示', '安装MySQL将耗费约' + str(
                len(self.ipcode) * 6) + '分钟, 请保持电脑网络连接正常。\n (具体时间因服务器处理速度或网络带宽有所差异）'
                                        '\n是否继续安装？')
            if installorNot:
                for num in range(len(self.ipcode)):
                    b = LinkServer(self.ipcode[num], self.sPwd[num], self.mysqlPwd[num], self.version[num])
                    # 检测服务器是否已经安装mysql
                    # 未安装为0 安装输出版本号
                    checkMysql = str(b.check_mysql())
                    if checkMysql == '0':
                        b.install_mysql()
                        print(self.ipcode[num] + ' 已安装; MySQL密码为: ' + self.mysqlPwd[num] + '; 版本为: ' + str(
                            self.version[num]))

                        # 检测是否安装完成，完成后输出日志
                        againCheck = '0'
                        while againCheck == '0':
                            againCheck = str(b.check_mysql())
                            time.sleep(5)
                        # log文本框增加日志文本
                        newLog = self.ipcode[num] + ' 已安装; MySQL密码为: ' + self.mysqlPwd[num] + '; 版本为: ' + str(
                            self.version[num])
                        self.updata_logBox(newLog)
                    else:
                        ret = tkinter.messagebox.askyesno('提示',
                                                          '检测到IP地址为' + self.ipcode[
                                                              num] + '已安装 MySQL, 版本为' + checkMysql + '。\n'
                                                          + '是否卸载后重新安装？ ')
                        # 在弹窗返回是
                        if ret:
                            b.uninstall_mysql()
                            # log文本框增加日志文本
                            newLog = self.ipcode[num] + ' 已卸载, 即将重新安装。'
                            self.updata_logBox(newLog)

                            b.install_mysql()
                            print(
                                self.ipcode[num] + ' 已安装; MySQL密码为: ' + self.mysqlPwd[num] + '; 版本为: ' + str(
                                    self.version[num]))

                            # log文本框增加日志文本
                            newLog = self.ipcode[num] + ' 已安装; MySQL密码为: ' + self.mysqlPwd[num] + '; 版本为: ' + str(
                                self.version[num])
                            self.updata_logBox(newLog)
                        else:
                            # log文本框增加日志文本
                            newLog = self.ipcode[num] + '已有安装MySQL; 版本为: ' + checkMysql + ', 将不会卸载。'
                            self.updata_logBox(newLog)

                # log文本框增加日志文本
                newLog = 'MySQL 安装完成!'
                self.updata_logBox(newLog)
            else:
                # log文本框增加日志文本
                newLog = 'MySQL 安装终止!'
                self.updata_logBox(newLog)
        else:
            # log文本框增加日志文本
            newLog = '检测到服务器数据未通过连接测试'
            self.updata_logBox(newLog)
            tkinter.messagebox.showinfo('警告', '未通过或未进行【连接测试】')

    def testLink(self):
        '''
        测试连接
        :return:
        '''
        # log文本框增加日志文本
        newLog = '开始进行服务器连接测试, wait...'
        self.updata_logBox(newLog)

        # 登陆异常服务器记录
        log = []
        # 检测是否有重复IP
        overlappingIP = []
        for num in range(len(self.ipcode)):
            # 检测是否有重复IP，统计ip出现次数
            # 出现不为 1 次为重复IP
            if self.ipcode.count(self.ipcode[num]) != 1:
                log.append(2)

            a = LinkServer(self.ipcode[num], self.sPwd[num], self.mysqlPwd[num], self.version[num])
            result, hostname = a.check_server()
            print('测试连接IP地址为: ' + self.ipcode[num] + '  ' + result + str(hostname))

            # log文本框增加日志文本
            newLog = '测试连接IP地址为: ' + self.ipcode[num] + '  ' + result + str(hostname)
            self.updata_logBox(newLog)

            if result == '连接异常, 错误原因: ':
                log.append(1)

        # 若log列表有1, 表示服务器信息中一个或多个信息错误，导致登陆异常
        if 1 in log:
            # log文本框增加日志文本
            newLog = '部分服务器登陆异常, 未通过【连接测试】, 需修正 '
            self.updata_logBox(newLog)
            # 弹窗提示
            self.serverPass = 1
            tkinter.messagebox.showinfo('警告', '部分服务器登陆异常, 未通过【连接测试】, 需修正')
        elif 2 in log:
            # log文本框增加日志文本
            newLog = '含有重复IP地址, 未通过【连接测试】, 需修正'
            self.updata_logBox(newLog)
            # 弹窗提示
            self.serverPass = 1
            tkinter.messagebox.showinfo('警告', '含有重复IP地址, 未通过【连接测试】, 需修正')
        else:
            self.serverPass = 0

        # log文本框增加日志文本
        newLog = '服务器连接测试完成!'
        self.updata_logBox(newLog)

    def saveData(self):
        '''
        保存数据
        :return:
        '''
        self.saveFile = tkinter.filedialog.asksaveasfilename() + '.xls'  # 返回文件名

        if self.saveFile != '.xls':
            writebook = xlwt.Workbook(self.saveFile)
            test = writebook.add_sheet('Sheet1')
            test.write(0, 0, 'IP地址')
            test.write(0, 1, '服务器密码')
            test.write(0, 2, 'MySQL密码')
            test.write(0, 3, '版本号')

            for line in range(len(self.ipcode)):
                test.write(line + 1, 0, self.ipcode[line])
                test.write(line + 1, 1, self.sPwd[line])
                test.write(line + 1, 2, self.mysqlPwd[line])
                test.write(line + 1, 3, self.version[line])

            writebook.save(self.saveFile)

            # log文本框增加日志文本
            newLog = '已保存至路径: ' + self.saveFile
            self.updata_logBox(newLog)

    def loadData(self):
        '''
        从获取的readFileAddr路径excel表中获取数据
        :return:
        '''
        # 数据文件格式提示窗
        tkinter.messagebox.showinfo('提示', 'Excel格式需与上方数据表格式相同')

        self.readFileAddr = tkinter.filedialog.askopenfilename()  # return /Users/Project/info.xlsx

        readExcel = xlrd.open_workbook(self.readFileAddr)
        sheet = readExcel.sheet_by_name('Sheet1')

        nrows = sheet.nrows  # 返回行：3
        ncols = sheet.ncols  # 返回列：2
        # print(ncols)

        for row in range(nrows - 1):
            ipOK = self.check_ip(sheet.cell(row + 1, 0).value)
            sPwdOK = self.check_sPwd(sheet.cell(row + 1, 1).value)
            mysqlPwdOK = self.check_mysqlPwd(sheet.cell(row + 1, 2).value)
            versionOK = self.check_version(sheet.cell(row + 1, 3).value)

            if (ipOK and sPwdOK and mysqlPwdOK and versionOK):
                self.ipcode.append(sheet.cell(row + 1, 0).value)
                self.sPwd.append(sheet.cell(row + 1, 1).value)
                self.mysqlPwd.append(sheet.cell(row + 1, 2).value)
                self.version.append(Decimal(sheet.cell(row + 1, 3).value).quantize(Decimal('0')))  # 精确到个位
                # 刷新展示
                self.flashTree()
            else:
                err = ''
                if not ipOK: err = err + 'IP地址不规范  '
                if not sPwdOK: err = err + '服务器密码不规范  '
                if not mysqlPwdOK: err = err + '设置MySQL密码不规范  '
                if not versionOK: err = err + 'MySQL版本号不规范  '

                tkinter.messagebox.showinfo('提示', 'Excel中数据格式不规范或数据不规范, 该行将被抛弃。\n'
                                                  '错误原因如下: ' + err)
                # log文本框增加日志文本
                newLog = 'Excel中数据格式不规范或数据不规范。\n错误原因如下: ' + err
                self.updata_logBox(newLog)

        # log文本框增加日志文本
        newLog = '已读取文件内容: ' + self.readFileAddr
        self.updata_logBox(newLog)

        # 因为更新了数据，所以服务器连接暂为异常 1
        self.serverPass = 1

    def check_ip(self, ip):
        '''
        检测IP是否符合规范
        符合返回 True
        :param ip: 传来ip
        :return:
        '''
        ipPass = False
        # 检测ip是否合法
        compile_ip = re.compile(
            '^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$')
        if compile_ip.match(ip):
            ipPass = True
        return ipPass

    def check_sPwd(self, sPwd):
        '''
        检测服务器密码是否符合规范
        符合返回 True
        :return:
        '''
        sPwdPass = False
        # 密码长度大于1
        if len(sPwd) >= 1:
            sPwdPass = True

        return sPwdPass

    def check_mysqlPwd(self, mysqlPwd):
        '''
        检测mysql设置密码是否符合规范
        符合返回 True
        :return:
        '''
        mysqlPwdPass = False

        # 检测mysql密码是否合法
        pwd = mysqlPwd
        # 判断密码长度是否合法
        lenOK = len(pwd) >= 8
        # 判断是否包含大写字母
        upperOK = re.compile('[A-Z]+').findall(pwd)
        # 判断是否包含数字
        lowerOK = re.compile('[0-9]+').findall(pwd)
        # 判断是否包含小写字母
        numOK = re.compile('[a-z]+').findall(pwd)
        # 判断是否包含符号
        symbolOK = re.compile('([^a-z0-9A-Z])+').findall(pwd)
        # 上述条件符合，执行
        if (lenOK and upperOK and lowerOK and numOK and symbolOK):
            mysqlPwdPass = True

        return mysqlPwdPass

    def check_version(self, version):
        '''
        检测版本号是否符合规范
        符合返回 True
        :return:
        '''
        versionPass = False
        # 版本为 55/56/57/80
        if version in ['55', '56', '57', '80', '55.0', '56.0', '57.0', '80.0', 55, 56, 57, 80]:
            versionPass = True

        return versionPass

    def flashTree(self):
        '''
        刷新显示列表
        :return:
        '''
        self.treeview.insert('', len(self.ipcode) - 1,
                             values=(
                                 self.ipcode[len(self.ipcode) - 1],
                                 self.sPwd[len(self.sPwd) - 1],
                                 self.mysqlPwd[len(self.mysqlPwd) - 1],
                                 self.version[len(self.version) - 1]
                             ))
        self.treeview.update()

    def set_cell_value(self, event):  # 双击进入编辑状态
        print("双击进入编辑状态")
        for item in self.treeview.selection():
            # 判断是否还有输入框，有-》销毁
            if self.countInput != 0:
                # 输入完成，销毁输入框和OK按键两个组件
                while self.entryedit.winfo_exists():
                    self.entryedit.destroy()
                while self.okb.winfo_exists():
                    self.okb.destroy()
            self.countInput = 1

            self.item = item
            self.item_text = self.treeview.item(item, "values")
            print(self.item_text) 
        self.column = self.treeview.identify_column(event.x)  # 列
        self.row = self.treeview.identify_row(event.y)  # 行
        if self.row != '':
            self.cn = int(str(self.column).replace('#', ''))
            self.rn = int(str(self.row).replace('I', ''))

            self.entryedit = Text(self.fm1, width=14, height=1, highlightcolor='black', relief=RIDGE, bd=3)
            self.okb = ttk.Button(self.fm1, text='OK', width=4, command=self.saveedit)

            w = [20, 140, 120, 115]
            X = 0
            for i in range(self.cn):
                X = X + w[i]

            self.entryedit.place(x=X, y=24 + (self.rn - 1) * 20)
            self.okb.place(x=25 + X, y=25 + self.rn * 20)

    def saveedit(self):
        '''
        若输入保存
        :return:
        '''
        # 审核输入合法性
        context, inputDesc = self.check_input()
        print(context)
        self.treeview.set(self.item, column=self.column, value=context)

        # 输入完成，销毁输入框和OK按键两个组件
        while self.entryedit.winfo_exists():
            self.entryedit.destroy()
        while self.okb.winfo_exists():
            self.okb.destroy()

        print(inputDesc)
        # log文本框增加日志文本
        # eg:添加新服务器密码: 88888758
        newLog = inputDesc
        self.updata_logBox(newLog)

        # 因为更新了数据，所以服务器连接暂为异常 1
        self.serverPass = 1

    def check_input(self):
        '''
        检测输入合法
        :return: 插入内容
        '''
        # 输入内容描述，输入合法为输入类别，不合法为错误描述
        inputDesc = '输入内容不规范'

        # 输入的内容
        context = self.entryedit.get(0.0, "end")
        context = context.splitlines()[0]
        # print(context)
        # 表格原内容
        oriContext = self.item_text[self.cn - 1]

        if self.cn == 1:
            # 检测ip是否合法
            if self.check_ip(context):
                context = context
                self.ipcode[self.rn - 1] = context
                inputDesc = '添加新IP地址: ' + context
            else:
                tkinter.messagebox.showinfo('提示', 'IP输入不合法或未输入。\n示例：10.20.131.222')
                context = oriContext
        elif self.cn == 2:
            # 检测服务器密码是否规范
            if self.check_sPwd(context):
                context = context
                self.sPwd[self.rn - 1] = context
                inputDesc = '添加新服务器密码: ' + context
            else:
                tkinter.messagebox.showinfo('提示', '服务器密码不正确或未输入')
                context = oriContext
        elif self.cn == 3:
            # 检测mysql密码是否合法
            if self.check_mysqlPwd(context):
                context = context
                self.mysqlPwd[self.rn - 1] = context
                inputDesc = '添加新MySQL密码: ' + context
            else:
                tkinter.messagebox.showinfo('提示', 'mysql密码输入不合法或未输入, 建议包含大、小写字母，数字和特殊符号，且大于8位。\n例：Mysql123@')
                context = oriContext
        elif self.cn == 4:
            # 检测mysql版本是否支持
            if self.check_version(context):
                context = context
                self.version[self.rn - 1] = context
                inputDesc = '添加新MySQL版本信息: ' + context
            else:
                tkinter.messagebox.showinfo('提示', '仅支持MySQL版本：55， 56， 57， 80')
                context = oriContext
        return context, inputDesc

    def sort(self, col, reverse):
        '''
        标题点击排序
        :param col: 列名
        :param reverse: 排列方式
        :return:
        '''
        l = [(self.treeview.set(k, col), k) for k in self.treeview.get_children('')]
        # print(self.treeview.get_children(''))
        l.sort(reverse=reverse)  # 排序方式
        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):  # 根据排序后索引移动
            self.treeview.move(k, '', index)
            # print(k)
        self.treeview.heading(col, command=lambda: self.sort(col, not reverse))  # 重写标题，使之成为再点倒序的标题

    def addData(self):
        '''
        【增加】功能
        :return:
        '''
        self.ipcode.append('IP')
        self.sPwd.append('服务器密码')
        self.mysqlPwd.append('mysql密码')
        self.version.append('版本号')
        self.treeview.insert('', len(self.ipcode) - 1,
                             values=(
                                 self.ipcode[len(self.ipcode) - 1],
                                 self.sPwd[len(self.sPwd) - 1],
                                 self.mysqlPwd[len(self.mysqlPwd) - 1],
                                 self.version[len(self.version) - 1]
                             ))
        self.treeview.update()

        # log文本框增加日志文本
        newLog = '已增加新行, 请双击编辑内容'
        self.updata_logBox(newLog)

        # 因为更新了数据，所以服务器连接暂为异常 1
        self.serverPass = 1

    def updata_logBox(self, newLog):
        '''
        更新fm3的日志文本框内容
        :return:
        '''
        # 格式化成2016-03-20 11:45:39形式
        localTime = time.strftime("%Y-%m-%d %H:%M", time.localtime())
        self.logContext.append('    ' + localTime + '  ' + newLog)
        self.listb.insert(len(self.logContext) - 1, self.logContext[len(self.logContext) - 1])
        self.listb.see(END)


if __name__ == '__main__':
    app = Application()
    # to do
    app.window_init()
    app.menu_init()
    app.createWidgets()
    # fm1的数据展示框
    app.design_showDataBox()
    # fm2的按键区
    app.design_buttonBox()
    # fm3的log文本框
    app.design_logTextBox()

    app.mainloop()
