#!/bin/bash

pw=$1
version=$2
echo $pw
echo $version


# 更改安装MySQL版本号
# 参数：$1来自inputVersion()函数，为mysql版本代号
changeVersion(){
    version="mysql"$1
    addr="/etc/yum.repos.d/mysql-community.repo"

    # line = enabled=0所在行 = [mysql56-community]所在行 + 3
    line=`sed -n  "/${version}/=" $addr`
    line=`expr $line + 3`
     
    # 将第$line行'enabled=0'改为'=1'
    sed -i "${line}s/0/1/" $addr
    # sed  "${line}cenabled=1" $addr
    
    # 将默认的[mysql80-community]下的'enabled=1'改为'=0'
    version80="mysql80"
    line80=`sed -n  "/${version80}/=" $addr`
    line80=`expr $line80 + 3`
    sed -i "${line80}s/1/0/" $addr
}


# 输入版本号，并验证输入合法性
# 若输入版本号合法，则修改相应配置
# 若输入版本号不合法，再次调用该函数
inputVersion(){
    # 输入您想安装的MySQL版本号
    echo "目前可安装版本为:"
    echo "       mysql55-community ==> 输入55"
    echo "       mysql56-community ==> 输入56"
    echo "       mysql57-community ==> 输入57"
    echo "       mysql80-community ==> 输入80"
    
    # 测试样例：version=57
    version=$1
    # read -p "输入您想安装的MySQL版本号" version
 
    if [ $version == 55 ]
    then
    changeVersion $version
        echo "55"
    elif [ $version == 56 ]
    then
        changeVersion $version
    echo "56"
    elif [ $version == 57 ]
    then
    changeVersion $version
        echo "57"
    elif [ $version == 80 ]
    then
    echo "将安装mysql80-community"
    else
        echo "没有符合的版本号"
        inputVersion
    fi

    return $version
}

wgetMysql(){
    # 检测安装包是否存在
    mysqlRpm="mysql80-community-release-el7-3.noarch.rpm"
    if [ -e $mysqlRpm ]
    then
        echo "文件 mysql80-community-release-el7-3.noarch.rpm 存>在"
    else
       wget wget https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm
    fi
}

rpmMysql(){
    rpm -ivh mysql80-community-release-el7-3.noarch.rpm
}

yumMysql(){
    yum -y update
    yum -y install mysql-server
}

settingPermissions(){
    echo "权限设置"
    chown mysql:mysql -R /var/lib/mysql
}

initMysql(){
    # 初始化 MySQL
    echo "初始化 MySQL"
    mysqld --initialize
}

startMysql(){
    # 启动 MySQL
    echo "启动 MySQL"
    error=`systemctl start mysqld`

    # 检测报错：Job for mysqld.service failed because the control process exited with error code. See “systemctl status mysqld.service” and “journalctl -xe” for details.
    if [ -n !"$a" ]
    then
        rm -rf /var/lib/mysql
        service mysqld restart
    fi
}

statusMysql(){
    # 查看 MySQL 运行状态
    echo "查看 MySQL 运行状态"
    systemctl status mysqld
}

changePassword(){
    version=$1
    pw=$2

    echo $pw
    echo $version

    if [ $version -eq 57 -o $version -eq 80 ]
    then
        # 查看mysql尝试随机密码
        a=`cat /var/log/mysqld.log | grep 'temporary password'`
        echo ${a##*root@localhost: }
        initpw=${a##*root@localhost: }
        # 修改密码为pw
        mysqladmin -uroot -p$initpw password $pw
        echo "a 等于 b"
    else
       mysqladmin password $pw
    fi
    # 查看mysql尝试随机密码
    a=`cat /var/log/mysqld.log | grep 'temporary password'`
    echo ${a##*root@localhost: }
    initpw=${a##*root@localhost: }
    # 修改密码为pw
    mysqladmin -uroot -p$initpw password $pw
}


wgetMysql

rpmMysql

inputVersion $version
mysqlVersion=$?

yumMysql

settingPermissions

initMysql

startMysql

statusMysql

changePassword $mysqlVersion $pw


# 登陆mysql
mysql -uroot -p$pw -e"show databases";


