
from drop_core import *


@app.route("/api/v1/<name>/service",  methods=['GET'])
@jwt_required()
def get_service_list(name):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.get(_url + "/api/v1/service0",
                             headers={"Content-type": "application/json",
                                      "Authorization": _jwt
                                      })
            res[n["node"]] = json.loads(r.text)
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/service0",  methods=['GET'])
@jwt_required()
def get_service_list0():

    enabled = run_shell("systemctl list-unit-files | grep enabled |awk '{print $1}'")
    running = run_shell("systemctl | grep running |awk '{print $1}'")

    return json.dumps({"enabled": enabled.split("\n"),
                       "running": running.split("\n")},
                      sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/service/<sid>",  methods=['GET'])
@jwt_required()
def get_service_status(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.get(_url + "/api/v1/service0/" + sid,
                             headers={"Content-type": "application/json",
                                      "Authorization": _jwt
                                      })
            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/service0/<name>",  methods=['GET'])
@jwt_required()
def get_service_status0(name):

    res = run_shell("systemctl status {}|grep 'Active:'".format(name))
    return res, 200


@app.route("/api/v1/<name>/service/<sid>",  methods=['POST'])
@jwt_required()
def do_service_start(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.post(_url + "/api/v1/service0/" + sid,
                              headers={"Content-type": "application/json",
                                       "Authorization": _jwt
                                       })
            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/service0/<name>",  methods=['POST'])
@jwt_required()
def do_service_start0(name):

    res = run_shell("systemctl start {} && echo \"ok\"".format(name))
    return res, 200


@app.route("/api/v1/<name>/service/<sid>/<code>",  methods=['PATCH'])
@jwt_required()
def do_service_conf(name, sid, code):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.patch(_url + "/api/v1/{}/service0/{}/{}".format(n["node"], sid, code),
                               headers={"Content-type": "application/json",
                                        "Authorization": _jwt
                                        })
            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/service0/<sid>/<code>",  methods=['PATCH'])
@jwt_required()
def do_service_conf0(name, sid, code):

    c = s3.connect(DB_NAME)
    r = c.cursor()

    r.execute("""select detail from  node_world
                 where node = '{}'
                  and  group0 != 'None'
              """.format(name))

    for i in r:
        _detail = json.loads(i[0])
        _serv = _detail.get("service", {})
        _serv[sid] = code
        _detail["service"] = _serv

        r.execute("""update node_world
                    set detail = '""" + json.dumps(_detail) + """',
                        date = CURRENT_TIMESTAMP
                    where
                        node = '{}'
                """.format(name))
        c.commit()

    c.close()

    return "ok", 200


@app.route("/api/v1/<name>/service/<sid>",  methods=['DELETE'])
@jwt_required()
def do_service_stop(name, sid):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.delete(_url + "/api/v1/service0/" + sid,
                                headers={"Content-type": "application/json",
                                         "Authorization": _jwt
                                         })
            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/service0/<name>",  methods=['DELETE'])
@jwt_required()
def do_service_stop0(name):

    res = run_shell("systemctl stop {} && echo \"ok\"".format(name))
    return res, 200
