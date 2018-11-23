
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
        res.append({"name": row["name"],
                    "active": row["active"],
                    "version": row["version"],
                    "priority": row["priority"],
                    "entry_ppool": row["entry_ppool"]
                    })

    return json.dumps(res, sort_keys=True, indent=4), 200
