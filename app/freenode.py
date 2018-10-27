
from drop_core import *
from cluster import get_cluster_nodes


@app.route("/api/v1/cassandra/seeds",  methods=['GET'])
def get_cassandra_seeds():

    c = s3.connect(DB_NAME)
    r = c.cursor()
    r.execute("""select node from node_world""")

    res = []
    for i in r.fetchall():
        res.append(i[0].split("@")[1])

    c.close()

    return ",".join(res[:3]), 200


@app.route("/api/v1/freenode",  methods=['GET'])
@jwt_required()
def get_freenode():

    c = s3.connect(DB_NAME)
    r = c.cursor()

    r.execute("""select uuid, node, hostname, active, date, group0, detail
                  from node_world s where s.group0 = 'None'
                 order by uuid desc
              """)

    res = []
    n = 0
    for i in r.fetchall():
        n += 1
        res.append({"uid": n,
                    "uuid": i[0],
                    "ip": i[1].split("@")[1],
                    "hostname": i[2],
                    "created": i[4]
                    # "detail": i[6]
                    })

    c.close()

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/freenode",  methods=['DELETE'])
@jwt_required()
def delete_freenode():

    nodes = json.loads(get_cluster_nodes("None")[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.delete(_url + "/api/v1/freenode0",
                                headers={"Content-type": "application/json",
                                         "Authorization": _jwt
                                         })
            res[n["node"]] = r.text
        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/freenode0",  methods=['DELETE'])
@jwt_required()
def delete_freenode0():

    c = s3.connect(DB_NAME)
    r = c.cursor()

    r.execute("""delete from node_world
                  where group0 = 'None' """)
    c.commit()

    c.close()

    return "ok", 200
