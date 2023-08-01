# -*-coding:utf-8-*-
"""
pip install paramiko
pip install pyecharts

如需监控网络 服务器：
sudo yum install epel-release
sudo yum install nload
"""
import time
import os
import datetime
import re
import pathlib
from concurrent.futures import ThreadPoolExecutor

try:
    import paramiko
except:
    raise Exception('you need: pip install paramiko')

from caishengxiang.utils.draw_tools.echarts_draw import Draw


def get_cpu_usage(content):
    """
    return 使用率(%)
    """
    lines = content.split('\n')
    cpu_line = [x for x in lines if 'Cpu(s)' in x][0]
    cpu_strs = cpu_line.split(':')[1].split(',')
    cpu_id_str = cpu_strs[3].strip()
    cpu_id = float(cpu_id_str.split()[0])
    usage = 100 - cpu_id
    return round(usage, 2)


def get_memory_usage(content):
    """
    return 字节
    """
    lines = content.split('\n')
    mem_line = [x for x in lines if x.startswith('KiB Mem')][0]
    mem_infos = mem_line.split(',')
    used = [x for x in mem_infos if 'used' in x][0]
    used = used.split()[0]
    return int(used)


def get_top_content(hostname, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, username=username, password=password)
    stdin, stdout, stderr = ssh.exec_command('top -bn 1')
    output = stdout.read()
    top_content = output.decode()
    ssh.close()
    return top_content


class Monitor:
    def __init__(self, hostname, username, password, save_dir="./monitors"):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.save_dir = os.path.abspath(save_dir)
        pathlib.Path(self.save_dir).mkdir(parents=True, exist_ok=True)
        # self.cpu_draw = Draw(y_name='使用率%', x_name='时间', title='{}: cpu监控'.format(hostname),
        #                      save_path=os.path.join(save_dir, '{}_cpu.html'.format(hostname)))
        #
        # self.mem_draw = Draw(y_name='使用量(GiB)', x_name='时间', title='{}: 内存监控'.format(hostname),
        #                      save_path=os.path.join(save_dir, '{}_mem.html'.format(hostname)))
        self.monitor_map = dict()

        self.draw_map = dict()
        self.thread_pool = ThreadPoolExecutor(max_workers=10)

    def _get_content(self, command: str = 'top -bn 1'):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self.hostname, username=self.username, password=self.password)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read()
        top_content = output.decode()
        ssh.close()
        return top_content

    def add_monitor(self, command, content_handle, y_name='使用率%', x_name='时间', title='cpu监控'):
        if self.monitor_map.get(title):
            raise Exception('已经存在同名监控:{}'.format(title))
        content = self._get_content(command)

    def look(self):
        top_content = get_top_content(self.hostname, self.username, self.password)
        time_str = str(datetime.datetime.now())
        cpu = get_cpu_usage(top_content)
        print('host:', self.hostname, 'time:', datetime.datetime.now(), '\ncpu:', cpu, '%')
        mem = get_memory_usage(top_content)
        print('mem', mem, 'KiB', round(mem / 1024, 2), 'MiB', round(mem / (1024 * 1024), 2), 'GiB\n')
        self.cpu_draw.add_data(x_data=time_str, y_data=cpu)
        self.mem_draw.add_data(x_data=time_str, y_data=round(mem / (1024 * 1024), 2))
        return cpu, mem

    def start_server(self, host='0.0.0.0', port=8888):
        """启动监控web服务"""
        pass


# def monitor(hostname, username, password):
#     top_content = get_top_content(hostname, username, password)
#
#     cpu = get_cpu_usage(top_content)
#     print('host:', hostname, 'time:', datetime.datetime.now(), '\ncpu:', cpu, '%')
#     mem = get_memory_usage(top_content)
#     print('mem', mem, 'KiB', round(mem / 1024, 2), 'MiB', round(mem / (1024 * 1024), 2), 'GiB\n')
#     return cpu, mem

if __name__ == '__main__':
    from pyecharts.globals import CurrentConfig, OnlineHostType

    dir_path = os.path.dirname(__file__)
    assets_path = os.path.join(dir_path, 'assets')
    CurrentConfig.ONLINE_HOST = assets_path + '/'

    monitor1 = Monitor(hostname='10.76.69.231', username='root', password='Admin_123qianxin', save_dir="./monitors")
    monitor1.add_monitor()
    monitor2 = Monitor(hostname='10.76.69.232', username='root', password='Admin_123qianxin', save_dir="./monitors")
    monitor3 = Monitor(hostname='10.76.69.233', username='root', password='Admin_123qianxin', save_dir="./monitors")

    look_time = 600  # 秒
    for i in range(look_time):
        monitor1.look()
        monitor2.look()
        monitor3.look()
        time.sleep(1)
