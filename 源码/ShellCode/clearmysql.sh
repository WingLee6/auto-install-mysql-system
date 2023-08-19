#!/bin/bash

# step1 检测系统是否自带安装 MySQL
mysql=`rpm -qa | grep mysql`
mysqlResidualFile=`find / -name mysql`

# 判断mysql和mysqlResidualFile都不为空（-a）
if [ -z "$mysql" ] 
then
    echo "没有安装MySQL"
else
    # step2 若安装mysql，卸载
    echo "监测到mysql 安装包:"
    for line in ${mysql}
    do
        echo $line
    done
    echo "监测到mysql残留文件："
    for line in ${mysqlResidualFile}
    do
        echo $line
        
    done


    # 准备卸载MySQL
    read -p "是否立即卸载MySQL(y or n)" yesorno

    if [[ $yesorno = "y" || $yesorno = "Y" ]];
    then

	# 卸载mysql安装包 
        for line in ${mysql}
        do
            echo "正在卸载安装包：$line"
	    rpm -e --nodeps $line
        done

	# 删除残留的mysql目录或文件
        for line in ${mysqlResidualFile}
        do
            echo "正在删除残留文件：$line"
            rm -rf $line
        done

        echo "已彻底卸载MySQL";
    else 
        echo "MySQL未卸载"
    fi 
fi



inputVersion(){
    # 输入您想安装的MySQL版本号
    echo "目前可安装版本为:"
    echo "       mysql55-community ==> 输入55"
    echo "       mysql56-community ==> 输入56"
    echo "       mysql57-community ==> 输入57"
    echo "       mysql80-community ==> 输入80"
    read -p "输入您想安装的MySQL版本号" version

    version=8
    if [ $version == 55 ]
    then
       echo "55"
    elif [ $version == 56 ]
    then
       echo "56"
    elif [ $version == 57 ]
    then
       echo "57"
    elif [ $version == 80 ]
    then
       echo "80"
    else
       echo "没有符合的版本号"
       inputVersion
    fi
}
