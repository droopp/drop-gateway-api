

from drop_core import *


@app.route("/api/v1/<name>/stats/nodes",  methods=['GET'])
def get_nodes_stat(name):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.get(_url + "/api/v1/stats0/nodes",
                             headers={"Content-type": "application/json",
                                      "Authorization": _jwt
                                      })

            res = json.loads(r.text)
            break

        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/stats/logs/<node>/<name>",  methods=['POST'])
def get_nodes_log(node, name):

    res = ""

    _url = "http://{}:{}/api/v1/logs/{}".format(node, os.environ["PORT"], name)

    try:

        r = requests.get(_url,
                         headers={"Content-type": "application/json"
                                  })

        res = r.text
    except Exception as e:
        res = str(e)

    return res, 200


@app.route("/api/v1/logs/<name>",  methods=['GET'])
def get_nodes_log0(name):

    res = {}

    try:

        with open("{}/{}.log".format(os.environ["LOGS_DIR"], name)) as f:
            content = f.read().splitlines()
            res["text"] = "<br>".join(content[len(content)-30:])

    except Exception as e:
        res["text"] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/stats0/nodes",  methods=['GET'])
def get_nodes_stat0():

    d = {"messages": [],
         "system": []}

    c = s3.connect(DB_NAME)

    cur = c.cursor()
    cur.execute("""select * from node_list""")

    for i in cur.fetchall():
        d["messages"].append({"node": i[0],
                              "active": i[1],
                              "date": i[2],
                              "messages": i[3]
                              })

    cur.execute("""select s.node, l.active, s.cpu_count, s.ram_count,
                     s.disk_count, MAX(s.date), AVG(s.cpu_percent),
                     AVG(s.ram_percent), AVG(s.disk_percent), AVG(s.net_count)
                     from node_stat s left join (select node, active, MAX(date) from node_list) l
                      on s.node = l.node
                     where s.date > DATETIME('NOW', '-1 minutes')
                     group by s.node
            """)

    for i in cur.fetchall():
        d["system"].append({"node": i[0],
                            "cpu_count": i[2],
                            "ram_count": i[3],
                            "disk_count": i[4],
                            "date": i[5],
                            "cpu_per": i[6],
                            "ram_per": i[7],
                            "disk_per": i[8]
                            })

    c.close()

    return json.dumps(d, sort_keys=True, indent=4), 200


@app.route("/api/v1/<name>/stats/ppools", methods=['GET'])
def get_ppools_stats(name):

    nodes = json.loads(get_cluster_nodes(name)[0])
    _jwt = request.headers.get('Authorization')
    res = {}

    for n in nodes:
        if n["cluster"] != name:
            continue

        _url = "http://{}:{}".format(n["ip"], os.environ["PORT"])

        try:

            r = requests.get(_url + "/api/v1/stats0/ppools",
                             headers={"Content-type": "application/json",
                                      "Authorization": _jwt
                                      })

            res = json.loads(r.text)
            break

        except Exception as e:
            res[n["node"]] = str(e)

    return json.dumps(res, sort_keys=True, indent=4), 200


@app.route("/api/v1/stats0/ppools", methods=['GET'])
def get_ppools_stats0():

    d = {"metrics": [],
         "system": []}

    c = s3.connect(DB_NAME)
    cur = c.cursor()

    cur.execute("""select s.node, s.name, l.ram_count,
                         s.date, AVG(s.count), AVG(s.cpu_percent),
                         AVG(s.ram_percent)
                         from ppool_stat s left join (select node, ram_count, MAX(date)
                                                      from node_stat group by node) l
                          on s.node = l.node
                         where s.date > DATETIME('NOW', '-1 minutes')
                         group by s.node, s.name
                """)

    for i in cur.fetchall():
        d["system"].append({"node": i[0],
                            "name": i[1],
                            "date": i[3],
                            "ram": i[2],
                            "count": i[4],
                            "cpu_per": i[5],
                            "ram_per": i[6]
                            })

    cur.execute('''
                    select node, name, MAX(date), MAX(error), MAX(timeout),
                        MIN(running), MAX(ok),
                        round(MAX(elapsed)/1000,2),  round(AVG(elapsed)/1000,2),
                        round(MAX(error) + MAX(timeout) + SUM(nomore),2),
                        SUM(nomore)
                    from ppool_list
                        where  date > DATETIME('NOW', '-1 minutes')
                            and date < DATETIME('NOW')
                    group by node, name
                    ''')

    for i in cur:
        d["metrics"].append({"node": i[0],
                             "name": i[1],
                             "date": i[2],
                             "error": i[3],
                             "timeout": i[4],
                             "running": i[5],
                             "ok": i[6],
                             "max": i[7],
                             "avg": i[8],
                             "nomore": i[10]
                             })
    c.close()

    return json.dumps(d, sort_keys=True, indent=4), 200
