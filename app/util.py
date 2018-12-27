
import subprocess as sp
from jinja2 import Template
from yaml import load


def run_shell(cmd):
    return sp.check_output("sudo {};exit 0".format(cmd), shell=True, stderr=sp.STDOUT).strip()


def run_shell0(cmd):
    return sp.check_output("{};exit 0".format(cmd), shell=True, stderr=sp.STDOUT).strip()


def make_ha_config(vip, servers):
    d = open("./conf/haproxy.cfg.sample").read()
    t = Template(d)
    out = t.render(vip=vip, servers=servers)
    with open("/etc/haproxy/haproxy.cfg", "w+") as f:
        f.write(out)


def make_json_flow(yaml):

    flow = """
    {{
    "name": "{}",
    "active": 1,
    "priority": {},
    "version": 0,
    "entry_ppool": "",
    "start_scene": "start",
    "scenes":[
        {{
            "name" : "start",
            "cook": [
    """

    tail = """
              ]
            },

            {
                "name" : "stop",
                "cook": [
           """

    tail2 = """
             ]

             }
            ]
           }

           """

    d = load(yaml)
    flow = flow.format(d["name"], d.get("priority", 0))
    n = 0

    for v in d["func"]:

        data = {"name": v["name"],
                "image": v["image"],
                "cmd": v["cmd"],
                "mem": v.get("memory", 100),
                "timeout": v.get("timeout", 10000)
                }

        n += 1
        flow += '''
                {{"num":{},
                  "cmd":"system::local::start_pool::{name}::1"
                 }},'''.format(n, **data)

        tail += '''
                {{"num":{},
                  "cmd":"system::local::stop_pool::{name}"
                 }},'''.format(n, **data)

        n += 1
        flow += '''{{"num":{},
                     "cmd":"system::local::start_all_workers::{name}::-m {mem}m {image}::{cmd} ::{name}.log::{timeout}"
                }},'''.format(n, **data)

    # subscriptions add
    for v in d["func"]:

        sub = v.get("sub", [])

        for s in sub:
            n += 1
            flow += '''
                     {{"num":{},
                       "cmd":"system::local::subscribe::{}::{}::{}::{}"
                     }},'''.format(n, s["name"], v["name"],
                                   s.get("filter", "no"),
                                   s.get("type", "sone")
                                   )

    return flow[:-1] + tail[:-1] + tail2


def do_service_stop0(name):
    res = run_shell("systemctl stop {} && echo \"ok\"".format(name))
    return res
