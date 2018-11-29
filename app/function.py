
from drop_core import *
import requests
import gevent

@app.route("/api/v1/f_repo",  methods=['GET'])
@jwt_required()
def get_f_repo_list():

    _jwt = request.headers.get('Authorization')

    r = requests.get("http://{}/v2/_catalog".format(os.environ["DROP_DOCKER_REGISTRY"]),
                     headers={"Content-type": "application/json",
                              "Authorization": _jwt
                   })

    enabled = json.loads(r.text)["repositories"]

    return json.dumps({"funs": [x for x in enabled]}, sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/fun",  methods=['GET'])
@jwt_required()
def get_fun_list(name):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.get(_url + "/api/v1/fun0",
                             headers={"Content-type": "application/json",
                                      "Authorization": _jwt
                                      })

            res[n["node"]] = json.loads(r.text)
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/fun0",  methods=['GET'])
@jwt_required()
def get_fun_list0():

    enabled = run_shell0("docker images")

    return json.dumps({"funs": [x for x in enabled.split("\n") if x != ""]},
                      sort_keys=True, indent=4), 200


def _gevent_install(par):

    node, _url, _jwt, sid, ver = par

    try:
        r = requests.post(_url + "/api/v1/repo/fun0/{}/{}".format(sid, ver),
                          headers={"Content-type": "application/json",
                                   "Authorization": _jwt
                                   }
                          )

        return (node, json.loads(r.text))
    except Exception as e:
        return (node, str(e))


@app.route("/api/v1/<name>/repo/fun/<sid>/<ver>",  methods=['POST'])
@jwt_required()
def do_fun_install(name, sid, ver):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    _res = []

    for n in nodes:
        if n["cluster"] != name:
            continue
        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        _res.append(gevent.spawn(_gevent_install, (n["node"], _url, _jwt, sid, ver) ))

        # try:
        #     r = requests.post(_url + "/api/v1/repo/fun0/{}/{}".format(sid, ver),
        #                       headers={"Content-type": "application/json",
        #                                "Authorization": _jwt
        #                                }
        #                       )
        #
        #     res[n["node"]] = json.loads(r.text)
        # except Exception as e:
        #     res[n["node"]] = str(e)

    gevent.joinall(_res)
    for r in _res:
        _n, _v = r.value
        res[_n] = _v

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/repo/fun0/<name>/<ver>",  methods=['POST'])
@jwt_required()
def do_fun_install0(name, ver):

    res = run_shell0("docker pull {}/{}:{} && echo \"ok\"".format(os.environ["DROP_DOCKER_REGISTRY"], 
                                                                   name, ver))
    res = run_shell0("docker tag {0}/{1}:{2} {1}:{2} && echo \"ok\"".format(os.environ["DROP_DOCKER_REGISTRY"], 
                                                                   name, ver))

    return json.dumps({"status": res.split("\n")[-1]},
                      sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/repo/fun/<sid>/<ver>",  methods=['DELETE'])
@jwt_required()
def do_fun_remove(name, sid, ver):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue
        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:
            r = requests.delete(_url + "/api/v1/repo/fun0/{}/{}".format(sid, ver),
                                headers={"Content-type": "application/json",
                                         "Authorization": _jwt
                                         }
                                )
            res[n["node"]] = json.loads(r.text)
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/repo/fun0/<name>/<ver>",  methods=['DELETE'])
@jwt_required()
def do_fun_remove0(name, ver):

    res = run_shell0("docker rmi {}/{}:{} && echo \"ok\"".format(os.environ["DROP_DOCKER_REGISTRY"], 
                                                                 name, ver))
    res = run_shell0("docker rmi {}:{} && echo \"ok\"".format(name, ver))
 
    return json.dumps({"status": res.split("\n")[-1]},
                      sort_keys=True, indent=4), 200



