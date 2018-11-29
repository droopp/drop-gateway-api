
from drop_core import *
import requests
import gevent


@app.route("/api/v1/repo",  methods=['GET'])
@jwt_required()
def get_repo_list():

    enabled = run_shell("yum search --disablerepo '*' --enablerepo='" +
                        DROP_REPO + "' drop-plgn ")

    return json.dumps({"plugins": [".".join(x.split(".")[:-1]) for
                                   x in enabled.split("\n") if x.startswith("drop-plgn")]},
                      sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/plugin",  methods=['GET'])
@jwt_required()
def get_plugin_list(name):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.get(_url + "/api/v1/plugin0",
                             headers={"Content-type": "application/json",
                                      "Authorization": _jwt
                                      })

            res[n["node"]] = json.loads(r.text)
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/plugin0",  methods=['GET'])
@jwt_required()
def get_plugin_list0():

    enabled = run_shell("rpm -qa|grep \"drop-plgn-\"")

    return json.dumps({"plugins": [".".join(x.split(".")[:-1]) for
                                   x in enabled.split("\n") if x != ""]},
                      sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/plugin/<sid>",  methods=['GET'])
@jwt_required()
def get_plugin_status(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.get(_url + "/api/v1/plugin0/" + sid,
                             headers={"Content-type": "application/json",
                                      "Authorization": _jwt
                                      })

            if r.status_code == 200:
                res[n["node"]] = json.loads(r.text)
            else:
                raise Exception(r.text)

        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/plugin0/<name>",  methods=['GET'])
@jwt_required()
def get_plugin_status0(name):

    l = "{}/{}.json".format(FLOWS_DIR, name)
    if not os.path.exists(l):
        return "Plugin {} not found".format(name), 404

    res = {}
    with open(l) as f:
        row = json.loads(f.read())

        res = {"name": row["name"],
               "active": row["active"],
               "version": row["version"],
               "priority": row["priority"],
               "entry_ppool": row["entry_ppool"]
               }

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/plugin/<sid>",  methods=['POST'])
@jwt_required()
def do_plugin_start(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.post(_url + "/api/v1/plugin0/" + sid,
                              headers={"Content-type": "application/json",
                                       "Authorization": _jwt
                                       })

            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/plugin0/<name>",  methods=['POST'])
@jwt_required()
def do_plugin_start0(name):

    l = "{}/{}.json".format(FLOWS_DIR, name)
    if not os.path.exists(l):
        return "Plugin {} not found".format(name), 404

    with open(l, "a+") as f:
        row = json.loads(f.read())
        row["active"] = 1
        f.seek(0)
        f.truncate()

        f.write(json.dumps(row, sort_keys=True, indent=4))

    return "ok", 200


@app.route("/api/v1/<name>/plugin/<sid>",  methods=['PUT'])
@jwt_required()
def do_plugin_call(name, sid):

    _all = request.args.get('all', None)

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.put(_url + "/api/v1/plugin0/" + sid,
                             headers={"Content-type": "application/json",
                                      "Authorization": _jwt
                                      },
                             data=request.data
                             )

            if r.status_code == 200:

                res[n["node"]] = json.loads(r.text)
                if _all is None:
                    break
            else:
                raise Exception(r.text)

        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/plugin0/<name>",  methods=['PUT'])
@jwt_required()
def do_plugin_call0(name):

    r = requests.post("http://localhost:{}/api/v1/{}".format(os.environ["API_PORT"], name),
                      data=request.data)

    return r.text, r.status_code


def _gevent_p_install(par):

    node, _url, _jwt, sid = par

    try:

        r = requests.post(_url + "/api/v1/repo/plugin0/" + sid,
                          headers={"Content-type": "application/json",
                                   "Authorization": _jwt
                                   }
                          )

        return (node, json.loads(r.text))
    except Exception as e:
        return (node, str(e))


@app.route("/api/v1/<name>/repo/plugin/<sid>",  methods=['POST'])
@jwt_required()
def do_plugin_install(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    _res = []

    for n in nodes:
        if n["cluster"] != name:
            continue
        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        _res.append(gevent.spawn(_gevent_p_install, (n["node"], _url, _jwt, sid) ))

        # try:
        #     r = requests.post(_url + "/api/v1/repo/plugin0/" + sid,
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


@app.route("/api/v1/repo/plugin0/<name>",  methods=['POST'])
@jwt_required()
def do_plugin_install0(name):

    if not name.startswith("drop-plgn-"):
        res = "Illegal package name {} (drop-plgn.. only)\n".format(name)
    else:
        res = run_shell("yum install -y {} && echo \"ok\"".format(name))

    return json.dumps({"status": res.split("\n")[-2]},
                      sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/repo/plugin/<sid>",  methods=['DELETE'])
@jwt_required()
def do_plugin_remove(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue
        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:
            r = requests.delete(_url + "/api/v1/repo/plugin0/" + sid,
                                headers={"Content-type": "application/json",
                                         "Authorization": _jwt
                                         }
                                )
            res[n["node"]] = json.loads(r.text)
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/repo/plugin0/<name>",  methods=['DELETE'])
@jwt_required()
def do_plugin_remove0(name):

    if not name.startswith("drop-plgn-"):
        res = "Illegal package name {} (drop-plgn.. only)\n".format(name)
    else:
        res = run_shell("yum erase -y {} && echo \"ok\"".format(name))

    return json.dumps({"status": res.split("\n")[-2]},
                      sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/plugin/<sid>",  methods=['DELETE'])
@jwt_required()
def do_plugin_stop(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue
        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:
            r = requests.delete(_url + "/api/v1/plugin0/" + sid,
                                headers={"Content-type": "application/json",
                                         "Authorization": _jwt
                                         }
                                )
            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/plugin0/<name>",  methods=['DELETE'])
@jwt_required()
def do_plugin_stop0(name):

    l = "{}/{}.json".format(FLOWS_DIR, name)
    if not os.path.exists(l):
        return "Plugin {} not found".format(name), 404

    with open(l, "a+") as f:
        row = json.loads(f.read())
        row["active"] = 0
        f.seek(0)
        f.truncate()

        f.write(json.dumps(row, sort_keys=True, indent=4))

    return "ok", 200
