
import subprocess as sp
from jinja2 import Template


def run_shell(cmd):
    return sp.check_output("sudo {};exit 0".format(cmd), shell=True, stderr=sp.STDOUT).strip()


def make_ha_config(vip, servers):
    d = open("./conf/haproxy.cfg.sample").read()
    t = Template(d)
    out = t.render(vip=vip, servers=servers)
    with open("/etc/haproxy/haproxy.cfg", "w+") as f:
        f.write(out)


def do_service_stop0(name):
    res = run_shell("systemctl stop {} && echo \"ok\"".format(name))
    return res
