from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

# Állapotok a legördülő menü számára a ServiceNow állapotkódok alapján
STATUS_OPTIONS = [
    {"label": "Nyitott", "value": "1"},
    {"label": "Függőben", "value": "2"},
    {"label": "Függőben Másoknál", "value": "3"},
    {"label": "Megoldva", "value": "6"},
    {"label": "Bezárva", "value": "7"},
    {"label": "Törölve", "value": "8"}
]

# Fordított szótár az állapot nevekhez
STATUS_LABELS = {option["value"]: option["label"] for option in STATUS_OPTIONS}


@app.route('/get_incidents_with_status_options', methods=['POST'])
def get_incidents_with_status_options():
    request_data = request.json
    felhasználónév = request_data.get('felhasználónév')
    jelszó = request_data.get('jelszó')
    állapot = request_data.get('állapot')  # Például: "1", "2", "3", "6", "7", "8"

    # Ellenőrizzük, hogy az állapot érvényes-e
    if állapot not in STATUS_LABELS:
        return jsonify({"error": "Érvénytelen állapot"}), 400

    # Token megszerzése a ServiceNow-tól
    auth_data = {
        'grant_type': 'password',
        'client_id': '45f3f2fb2ead4928ab994c64c664dfdc',
        'client_secret': 'fyHL1.@d&7',
        'username': felhasználónév,
        'password': jelszó
    }

    response = requests.post('https://dev227667.service-now.com/oauth_token.do', data=auth_data)
    if response.status_code == 200:
        access_token = response.json().get('access_token')

        # Felhasználói sys_id lekérése a tokennel
        headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
        response_user = requests.get(
            f"https://dev227667.service-now.com/api/now/table/sys_user?sysparm_query=user_name={felhasználónév}",
            headers=headers
        )
        if response_user.status_code == 200:
            caller_id = response_user.json().get('result', [])[0].get("sys_id")

            # Incidensek lekérése a kiválasztott állapot alapján
            query = f"caller_id={caller_id}^state={állapot}"
            response_incidents = requests.get(
                f"https://dev227667.service-now.com/api/now/table/incident?sysparm_query={query}",
                headers=headers
            )

            if response_incidents.status_code == 200:
                incidents = response_incidents.json().get('result', [])
                formatted_incidents = [
                    {
                        "number": inc["number"],
                        "short_description": inc["short_description"],
                        "status": STATUS_LABELS.get(inc["state"], inc["state"])
                    }
                    for inc in incidents
                ]

                # Állapotopciók és incidensek összeállítása válaszként
                response_data = {
                    "status_options": STATUS_OPTIONS,
                    "incidents": formatted_incidents
                }

                # Válasz JSON formátumban, ékezetek megőrzésével
                return Response(json.dumps(response_data, ensure_ascii=False),
                                content_type="application/json; charset=utf-8")
            else:
                return jsonify({"error": "Incidensek lekérése sikertelen"}), 400
        else:
            return jsonify({"error": "Felhasználói azonosító lekérése sikertelen."}), 400
    else:
        return jsonify({"error": "Authentication failed", "details": response.text}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
