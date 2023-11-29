# ---encoding:utf-8---
# @Time    : 2023/11/21 14:41
# @Author  : caishengxiang
# @Email   : 383301857@qq.com
# @File    : update_ipv6.py
# @Project : caishengxiang
"""
访问和修改dnspod域名的类
get_domain无需参数，输出login_token对应的用户拥有的域名。
域名下包含记录，使用getrecord（domain_list）获取,每条记录对应一个子域名，也是最常用的。
对仅拥有一个域名一个公网ip的用户来说，日常使用仅需要在ip地址发生变化时，更新每条记录就可以了。
"""
# ---encoding:utf-8---
# @Time    : 2023/11/21 14:41
# @Author  : caishengxiang
# @Email   : 383301857@qq.com
# @File    : update_ipv6.py
# @Project : caishengxiang
"""
访问和修改dnspod域名的类
get_domain无需参数，输出login_token对应的用户拥有的域名。
域名下包含记录，使用getrecord（domain_list）获取,每条记录对应一个子域名，也是最常用的。
对仅拥有一个域名一个公网ip的用户来说，日常使用仅需要在ip地址发生变化时，更新每条记录就可以了。
"""
import requests
import logging
import re
import time
import socket


def get_global_ipv6_addresses():
    """获取ipv6"""
    addresses = []
    # 获取主机名
    hostname = socket.gethostname()
    # 获取主机的全部地址信息
    addresses_info = socket.getaddrinfo(
        hostname, None, socket.AF_INET6, socket.SOCK_STREAM, 0, socket.AI_ADDRCONFIG | socket.AI_V4MAPPED)
    for address_info in addresses_info:
        address = address_info[4][0]
        if not address.startswith('fe80'):
            addresses.append(address)
    print(address)
    return addresses


class Dnspod:
    """
    操作dnspod域名的类
    """

    def __init__(self, login_token, log_file):
        self._login_token = login_token
        self._format = 'json'

        # 设置 logger
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self._logger = logging.getLogger(__name__)
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

        self._add_domain_URL = 'https://dnsapi.cn/Domain.Create'  # 添加域名
        self._del_domain_URL = 'https://dnsapi.cn/Domain.Remove'  # 删除域名
        self._add_record_URL = 'https://dnsapi.cn/Record.Create'  # 添加记录
        self._alter_record_URL = 'https://dnsapi.cn/Record.Modify'  # 修改记录
        self._get_record_URL = 'https://dnsapi.cn/Record.List'  # 获取记录列表
        self._del_record_URL = 'https://dnsapi.cn/Record.Remove'  # 删除记录
        self._get_domain_list_URL = 'https://dnsapi.cn/Domain.List'  # 获取域名列表

    @staticmethod
    def get_outer_ip():
        """
        获取外网ip
        :return:
        """
        ipv6_addresses = get_global_ipv6_addresses()
        if not ipv6_addresses:
            raise Exception('没有 no ipv6')
        print('ipv6_addresses:', ipv6_addresses)
        return ipv6_addresses[0]

    def get_domain_list(self):
        """
        获取域名列表
        :return: 域名列表： ['xxx.xx', 'xxx.xx'] or []
        """
        try:
            r = requests.post(self._get_domain_list_URL, data={'login_token': self._login_token,
                                                               'format': self._format})
            response_record_json = r.json()
            if response_record_json['status']['code'] == '1':
                domains_list = [doms['name'] for doms in response_record_json['domains'] if doms['status'] == 'enable']
                for domain in domains_list:
                    self._logger.info(f"域名:{domain}")
                return domains_list
            else:
                return []
        except Exception as e:
            self._logger.error(e)

    def add_domain(self, domains_list):
        """
        添加域名
        :param domains_list:['xxx.xxx.xxx', 'xx2.xxx.xxx']
        :return: True or False
        """
        try:
            for domain in domains_list:
                r = requests.post(self._add_domain_URL, data={'login_token': self._login_token,
                                                              'format': self._format,
                                                              'domain': domain,
                                                              })
                response_record_json = r.json()
                if response_record_json["status"]["code"] == "1":
                    self._logger.info(
                        f'域名：{response_record_json["domain"]["domain"]}，添加成功;域名ID：{response_record_json["domain"]["id"]}')
                else:
                    self._logger.error(f'域名：{domain},添加失败，错误信息：{response_record_json["status"]["message"]}')
        except Exception as e:
            self._logger.error(e)

    def del_domain(self, domains_list):
        """
        删除域名
        :param domains_list:['xxx.xxx.xxx', 'xx2.xxx.xxx']
        :return: True or False
        """
        try:
            for domain in domains_list:
                r = requests.post(self._del_domain_URL, data={'login_token': self._login_token,
                                                              'format': self._format,
                                                              'domain': domain,
                                                              })
                response_record_json = r.json()
                if response_record_json["status"]["code"] == "1":
                    self._logger.info(f'删除域名：{domain}成功.')
                else:
                    self._logger.error(
                        f'删除域名：{domain},添加失败，错误信息：{response_record_json["status"]["message"]}')
        except Exception as e:
            self._logger.error(e)

    def add_record(self, domain, sub_domain_list, value, record_type='A', record_line_value='默认'):
        """
        添加域名和解析记录
        :param domain: 要添加记录的域名
        :param sub_domain_list: 要添加的子域名列表
        :param record_type: 添加记录类型：默认 A
        :param record_line_value: 线路类型， 使用 ‘默认’即可
        :param value: 要添加的值， A类型是ip地址。
        :return:
        """
        try:
            for sub_domain in sub_domain_list:
                r = requests.post(self._add_record_URL, data={'login_token': self._login_token,
                                                              'format': self._format,
                                                              'domain': domain,
                                                              'sub_domain': sub_domain,
                                                              'record_type': record_type,
                                                              'record_line': record_line_value,
                                                              'value': value,
                                                              })
                response_record_json = r.json()
                if response_record_json["status"]["code"] == "1":
                    self._logger.info(f'域名：{domain}，成功添加记录：{response_record_json["record"]["name"]} ')
                else:
                    self._logger.error(
                        f'域名：{domain}，添加：{sub_domain}，记录失败，错误信息：{response_record_json["status"]["message"]}')
        except Exception as e:
            self._logger.error(e)

    def get_record(self, domain):
        """
        获取域名下的记录
        :param domain: "xxx.xxx.xx"
        :return:
        """
        records_list = []
        try:
            r = requests.post(self._get_record_URL, data={'login_token': self._login_token,
                                                          'format': self._format,
                                                          'domain': domain,
                                                          })
            response_record_json = r.json()
            if response_record_json['status']['code'] == '1':
                self._logger.info(
                    f"域名：{response_record_json['domain']['name']}，"
                    f"共有：{response_record_json['info']['sub_domains']}个子域名"
                    f"和：{response_record_json['info']['record_total']}条解析记录.")
                for record in response_record_json['records']:
                    if record['type'] == 'AAAA':  # 只修改AAAA类型的记录，避免修改dnspod默认记录。
                        records_list.append({
                            'domain': domain,
                            'id': record['id'],
                            'name': record['name'],
                            'line': record['line'],
                            'type': record['type'],
                            'value': record['value']
                        })
        except Exception as e:
            self._logger.error(e)
            return []

        return records_list

    def alter_record(self, domain, sub_domain, record_id, value, record_type='AAAA', record_line='默认'):
        """
        修改解析记录
        :param domain: 域名，不可缺
        :param sub_domain: 子域名，可选，默认值为@
        :param record_id: 记录id
        :param value: 值
        :param record_type: 记录类型，默认 AAAA
        :param record_line: 线路类型，使用‘默认’即可
        :return:
        """
        try:
            r = requests.post(self._alter_record_URL, data={'login_token': self._login_token,
                                                            'format': self._format,
                                                            'domain': domain,
                                                            'sub_domain': sub_domain,
                                                            'record_id': record_id,
                                                            'record_type': record_type,
                                                            'record_line': record_line,
                                                            'value': value,
                                                            })
            response_record_json = r.json()
            if response_record_json['status']['code'] == '1':
                self._logger.info(f"修改记录{record_id}成功。value{value}")
            else:
                self._logger.error(f"记录ID：{record_id}修改失败，错误信息: {response_record_json['status']['message']}。")
        except Exception as e:
            self._logger.error(e)

    def del_record(self, domain, record_id):
        """
        删除解析记录
        :param domain: 域名，
        :param record_id: 记录id，通过get_record获取
        :return:
        """
        try:
            r = requests.post(self._del_record_URL, data={'login_token': self._login_token,
                                                          'format': self._format,
                                                          'domain': domain,
                                                          'record_id': record_id,
                                                          })
            response_record_json = r.json()
            if response_record_json['status']['code'] == '1':
                self._logger.info(
                    f"您正在解析记录，ID为：{record_id}，"
                    f"删除状态值为：{response_record_json['status']['code']}, "
                    f"信息为：{response_record_json['status']['message']}")
            else:
                self._logger.error(
                    f"您正在解析记录，ID为：{record_id}，"
                    f"删除状态值为：{response_record_json['status']['code']}, "
                    f"信息为：{response_record_json['status']['message']}")
        except Exception as e:
            self._logger.error(e)


class Config:
    log_file = ""
    login_token = ""
    domain = ""


def update_ip(login_token, domain, names=None, log_file='./ddns_log'):
    """
    @ login_token   由  ID,token 组成
    @ domain   域名
    @ log_file 日志地址
    """
    if names is None:
        names = ['www', '@']
    pod = Dnspod(login_token, log_file)
    ip_public = pod.get_outer_ip()
    print('http://[{}]:9999/'.format(ip_public))
    logging.info(ip_public)
    if ip_public:
        records = pod.get_record(domain)
        logging.info(str(records))
        for record in records:
            if not record['name'] in names:
                continue
            if ip_public == record['value']:
                logging.info('地址未改变，无需更改')
            else:
                logging.warning(
                    'alter_record:{},{},{},{}'.format(record['domain'], record['name'], record['id'], ip_public))
                # pod.alter_record(record['domain'], record['name'], record['id'], ip_public)


if __name__ == '__main__':
    update_ip(login_token="455994,ce7b7f1c9d6ade7bb63ed06ca85705cf", domain='caishengxiang.com', names=['harbor'])
