
from drop_core import *


@app.route("/api/v1/stat/flows",  methods=['POST'])
@jwt_required()
def flows2():
    l = glob.glob(FLOWS_DIR + "/*.json")

    data = []
    for i in l:
        with open(i) as f:
            data.append(json.loads(f.read()))

    res = "<root><flows>"

    for row in data:
        res += """<row>
                    <name>{}</name>
                    <active>{}</active>
                    <version>{}</version>
                    <priority>{}</priority>
                    <entry>{}</entry>
                    <data>{}</data>
                 </row>""".format(row["name"], row["active"], row["version"],
                                  row["priority"],
                                  row["entry_ppool"],  json.dumps(row))

    return res + '</flows></root>', 200


@app.route("/api/v1/<name>/flows",  methods=['GET'])
@jwt_required()
def get_flow_list(name):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.get(_url + "/api/v1/flows",
                             headers={"Content-type": "application/json",
                                      "Authorization": _jwt
                                      })

            if r.status_code == 200:
                res[n["node"]] = [x["name"] for x in json.loads(r.text)]
            else:
                raise Exception(r.text)

        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/flows",  methods=['GET'])
@jwt_required()
def flows():

    l = glob.glob(FLOWS_DIR + "/*.json")

    data = []
    for i in l:
        with open(i) as f:
            data.append(json.loads(f.read()))

    res = []

    for row in data:
        try:
            res.append({"name": row["name"],
                        "active": row["active"],
                        "version": row["version"],
                        "priority": row["priority"],
                        "entry_ppool": row["entry_ppool"]
                        })
        except Exception as e:
            res.append({"error": "Bad flow structure: {}".format(e)})

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/flow/<sid>",  methods=['GET'])
@jwt_required()
def get_flow_status(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.get(_url + "/api/v1/flow0/" + sid,
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


@app.route("/api/v1/flow0/<name>",  methods=['GET'])
@jwt_required()
def get_flow_status0(name):

    l = "{}/{}.json".format(FLOWS_DIR, name)
    if not os.path.exists(l):
        return "Flow {} not found".format(name), 404

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


@app.route("/api/v1/<name>/flow/<sid>",  methods=['PUT'])
@jwt_required()
def do_flow_call(name, sid):

    _all = request.args.get('all', None)

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.put(_url + "/api/v1/flow0/" + sid,
                             headers={"Content-type": "application/json",
                                      "Authorization": _jwt
                                      },
                             data=request.data
                             )

            if r.status_code == 200:

                res[n["node"]] = r.text
                if _all is None:
                    break
            else:
                raise Exception(r.text)

        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/flow0/<name>",  methods=['PUT'])
@jwt_required()
def do_flow_call0(name):

    r = requests.post("http://localhost:{}/api/v1/{}".format(os.environ["API_PORT"], name),
                      data=request.data)

    return r.text, r.status_code


@app.route("/api/v1/<name>/flow/<sid>",  methods=['DELETE'])
@jwt_required()
def do_flow_stop(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue
        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:
            r = requests.delete(_url + "/api/v1/flow0/" + sid,
                                headers={"Content-type": "application/json",
                                         "Authorization": _jwt
                                         }
                                )
            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/flow0/<name>",  methods=['DELETE'])
@jwt_required()
def do_flow_stop0(name):

    l = "{}/{}.json".format(FLOWS_DIR, name)
    if not os.path.exists(l):
        return "Flow {} not found".format(name), 404

    with open(l, "a+") as f:
        row = json.loads(f.read())
        row["active"] = 0
        f.seek(0)
        f.truncate()

        f.write(json.dumps(row, sort_keys=True, indent=4))

    return "ok", 200


@app.route("/api/v1/<name>/flow/<sid>",  methods=['POST'])
@jwt_required()
def do_flow_start(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.post(_url + "/api/v1/flow0/" + sid,
                              headers={"Content-type": "application/json",
                                       "Authorization": _jwt
                                       })

            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/flow0/<name>",  methods=['POST'])
@jwt_required()
def do_flow_start0(name):

    l = "{}/{}.json".format(FLOWS_DIR, name)
    if not os.path.exists(l):
        return "Flow {} not found".format(name), 404

    with open(l, "a+") as f:
        row = json.loads(f.read())
        row["active"] = 1
        f.seek(0)
        f.truncate()

        f.write(json.dumps(row, sort_keys=True, indent=4))

    return "ok", 200


@app.route("/api/v1/<name>/flows/<sid>",  methods=['POST'])
@jwt_required()
def do_flow_install(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    data = request.data
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.post(_url + "/api/v1/flows0/" + sid,
                              headers={"Content-type": "application/json",
                                       "Authorization": _jwt,
                                       }, data=data)

            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/flows0/<name>",  methods=['POST'])
@jwt_required()
def do_flow_install0(name):

    try:
        data = make_json_flow(request.data)

        l = "{}/{}.json".format(FLOWS_DIR, name)

        with open(l, "a+") as f:
            row = json.loads(data)

            f.seek(0)
            f.truncate()

            f.write(json.dumps(row, sort_keys=True, indent=4))
    except Exception as e:
        return str(e), 500

    return "ok", 200


@app.route("/api/v1/<name>/flows/<sid>",  methods=['DELETE'])
@jwt_required()
def do_flow_remove(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.delete(_url + "/api/v1/flows0/" + sid,
                                headers={"Content-type": "application/json",
                                         "Authorization": _jwt,
                                         })

            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/flows0/<name>",  methods=['DELETE'])
@jwt_required()
def do_flow_remove0(name):
    try:
        l = "{}/{}.json".format(FLOWS_DIR, name)
        os.remove(l)
    except Exception as e:
        return str(e), 500

    return "ok", 200
