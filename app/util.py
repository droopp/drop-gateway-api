
import subprocess as sp
from jinja2 import Template


def run_shell(cmd):
    return sp.check_output("{};exit 0".format(cmd), shell=True, stderr=sp.STDOUT).strip()


def make_ha_config(vip, servers):
    d = open("./conf/haproxy.cfg.sample").read()
    t = Template(d)
    out = t.render(vip=vip, servers=servers)
    with open("/etc/haproxy/haproxy.cfg", "w+") as f:
        f.write(out)
