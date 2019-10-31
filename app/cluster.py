from drop_core import *


@app.route("/api/v1/cluster",  methods=['GET'])
@jwt_required()
def cluster_list():

    c = s3.connect(DB_NAME)
    r = c.cursor()

    r.execute("""select s.group0, s.uuid, s.detail, s.node
                  from node_world s
                   where s.group0 != 'None'
                     and s.detail like '%is_vip\": 1%'
                     and s.active = 1
                group by s.group0
              """)

    res = []
    for i in r.fetchall():
        res.append({"cluster": i[0],
                    "vip_host": {"uuid": i[1],
                                 "name": i[3],
                                 "vip": json.loads(i[2])["vip"]
                                 }
                    })
    c.close()

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/cluster",  methods=['POST'])
@jwt_required()
def cluster_create():

    data = json.loads(request.data)
    node_ids = data["node_ids"]

    nodes = json.loads(get_cluster_nodes("None")[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    _nodes = []
    for n in nodes:
        if n["cluster"] == "None" and (str(n["uid"]) in node_ids
                                       or node_ids == ['*']):
            _nodes.append(n["node"])

    data["node_ids"] = _nodes

    for n in nodes:
        if n["cluster"] != "None" or not (str(n["uid"]) in node_ids
                                          or node_ids == ['*']):
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.post(_url + "/api/v1/cluster0",
                              headers={"Content-type": "application/json",
                                       "Authorization": _jwt
                                       }, data=json.dumps(data))
            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/cluster0",  methods=['POST'])
@jwt_required()
def cluster_create0():

    data = json.loads(request.data)

    name = data["name"]
    node_ids = data["node_ids"]
    vip = data["vip"]
    date = time.time()
    data = json.dumps({"vip": vip, "timestamp": date})

    c = s3.connect(DB_NAME)
    r = c.cursor()

    r.execute("""update node_world
                 set group0 = '""" + name + """',
                     detail = '""" + data + """',
                     date = CURRENT_TIMESTAMP
                 where
                     group0 != '""" + name + """'
                 and node IN ({})
             """.format(','.join(['?']*len(node_ids))), node_ids)

    c.commit()
    c.close()

    if os.environ.get("IS_HAPROXY") == "1":
        servs = [{"id": x.split("@")[0], "name": x.split("@")[1]}
                 for x in node_ids]
        make_ha_config(vip, servs)

    return "ok", 200


@app.route("/api/v1/cluster/<name>",  methods=['DELETE'])
@jwt_required()
def delete_cluster(name):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.delete(_url + "/api/v1/cluster0/" + name,
                                headers={"Content-type": "application/json",
                                         "Authorization": _jwt
                                         })
            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


def stop_all_services(r, name):

    r.execute("""select detail
                  from node_world s where s.group0 = '{}'
                  LIMIT 1
              """.format(name))

    for i in r.fetchall():

        _serv = None

        try:
            _serv = json.loads(i[0]).get("service")
        except:
            pass

        if _serv is not None:
            for k in _serv.iterkeys():
                do_service_stop0(k)


@app.route("/api/v1/cluster0/<name>",  methods=['DELETE'])
@jwt_required()
def delete_cluster0(name):

    c = s3.connect(DB_NAME)
    r = c.cursor()
    date = time.time()
    data = json.dumps({"vip": "127.0.0.1",
                       "timestamp": date})

    #  stop all services

    stop_all_services(r, name)

    #  clear service and vip data

    r.execute("""update node_world
                 set group0 = 'None',
                     detail = '{}',
                     date = CURRENT_TIMESTAMP
                 where group0 = '{}'""".format(data, name))
    c.commit()

    c.close()

    if os.environ.get("IS_HAPROXY") == "1":
        servs = [{"id": x.split("@")[0], "name": x.split("@")[1]}
                 for x in ["localhost@127.0.0.1"]]
        make_ha_config("127.0.0.1", servs)

    return "ok", 200


@app.route("/api/v1/cluster/<name>/node",  methods=['POST'])
@jwt_required()
def cluster_node_do(name):

    data = json.loads(request.data)

    name = data["name"]
    node_ids = data["node_ids"]
    op = data["op"]

    _jwt = request.headers.get('Authorization')
    res = {}

    for n in node_ids:

        _url = "http://{}:{}".format(n.split("@")[1], os.environ["PORT"])

        try:
            if op == "add":
                r = requests.post(_url + "/api/v1/cluster0/{}/{}".format(name, n),
                                  headers={"Content-type": "application/json",
                                           "Authorization": _jwt
                                           }
                                  )
            elif op == "rm":
                r = requests.delete(_url + "/api/v1/cluster/{}/{}".format(name, n),
                                    headers={"Content-type": "application/json",
                                             "Authorization": _jwt
                                             }
                                    )

            elif op == "stop":
                r = requests.delete(_url + "/api/v1/service0/{}".format("drop-core"),
                                    headers={"Content-type": "application/json",
                                             "Authorization": _jwt
                                             }
                                    )

            elif op == "start":
                r = requests.post(_url + "/api/v1/service0/{}".format("drop-core"),
                                  headers={"Content-type": "application/json",
                                           "Authorization": _jwt
                                           }
                                  )

            res[n] = r.text
        except Exception as e:
            res[n] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/cluster0/<name>/<nid>",  methods=['POST'])
@jwt_required()
def cluster_node_create(name, nid):

    c = s3.connect(DB_NAME)
    r = c.cursor()

    r.execute("""select detail, node from  node_world
                 where group0 = '{}'
                 -- LIMIT 1
              """.format(name))

    _det = ""
    node_ids = [nid]
    _vip = ""

    for i in r:
        node_ids.append(i[1])
        _det = i[0]
        _vip = json.loads(_det)["vip"]

    r.execute("""update node_world
                set group0 = '""" + name + """',
                    detail = '""" + _det + """',
                    date = CURRENT_TIMESTAMP
                where
                    node = '{}'
            """.format(nid))
    c.commit()

    c.close()

    if os.environ.get("IS_HAPROXY") == "1":
        servs = [{"id": x.split("@")[0], "name": x.split("@")[1]}
                 for x in node_ids]
        make_ha_config(_vip, servs)

    return "ok", 200


@app.route("/api/v1/cluster/<name>/<nid>",  methods=['DELETE'])
@jwt_required()
def delete_node_cluster(name, nid):

    c = s3.connect(DB_NAME)
    r = c.cursor()
    date = time.time()
    data = json.dumps({"vip": "127.0.0.1",
                       "timestamp": date})

    #  stop all services

    stop_all_services(r, name)

    #  clear service and vip data

    r.execute("""update node_world
                 set group0 = 'None',
                     detail = '{}',
                     date = CURRENT_TIMESTAMP
                 where group0 = '{}'
                  and  node = '{}'
              """.format(data, name, nid))
    c.commit()
    c.close()

    if os.environ.get("IS_HAPROXY") == "1":
        servs = [{"id": x.split("@")[0], "name": x.split("@")[1]}
                 for x in ["localhost@127.0.0.1"]]
        make_ha_config("127.0.0.1", servs)

    return "ok", 200


@app.route("/api/v1/cluster/<name>/nodes",  methods=['GET'])
@jwt_required()
def get_cluster_nodes(name):

    c = s3.connect(DB_NAME)
    r = c.cursor()

    r.execute("""select uuid, node, hostname, active, date, group0, detail
                  from node_world s where s.group0 = '{}'
                order by uuid desc
              """.format(name))

    res = []
    n = 0
    for i in r.fetchall():
        n += 1

        _serv = None
        try:
            _serv = json.loads(i[6]).get("service")
        except:
            pass

        res.append({"uid": n,
                    "uuid": i[0],
                    "node": i[1],
                    "ip": i[1].split("@")[1],
                    "hostname": i[2],
                    "status": (lambda x: x == 1 and "UP" or "DOWN")(i[3]),
                    "created": i[4],
                    "cluster": i[5],
                    "serv_conf": _serv
                    })

    c.close()

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/version",  methods=['GET'])
@jwt_required()
def get_cluster_version(name):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:
            r = requests.get(_url + "/api/v1/node/version",
                             headers={"Content-type": "application/json",
                                      "Authorization": _jwt
                                      })
            res[n["node"]] = json.loads(r.text)
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/node/version",  methods=['GET'])
@jwt_required()
def get_cluster_version0():

    res = {}
    ver = run_shell("rpm -qa|grep \"drop-\"|sort|sha1sum").split(" ")[0]
    res["rpm"] = ver
    ver = run_shell0("cat /var/lib/drop/flows/* | sort|sha1sum").split(" ")[0]
    res["flows"] = ver

    if os.environ.get("IS_DOCKER") == "1":

        ver = run_shell0("docker images|sort|sha1sum").split(" ")[0]
        res["docker"] = ver

        res["all"] = run_shell0("echo " + res["rpm"] + res["docker"] + res["flows"] + " | sort|sha1sum").split(" ")[0]

    else:
        res["all"] = run_shell0("echo " + res["rpm"] + res["flows"] + " | sort|sha1sum").split(" ")[0]

    return json.dumps(res, sort_keys=True, indent=4), 200
