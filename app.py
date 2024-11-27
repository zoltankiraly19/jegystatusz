from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

# Állapotkódok a felhasználói-barát megjelenítés
STATUS_OPTIONS = {
    "Nyitott": "1",
    "Függőben": "2",
    "Függőben Másoknál": "3",
    "Megoldva": "6",
    "Bezárva": "7",
    "Törölve": "8"
}


STATUS_LABELS = {value: key for key, value in STATUS_OPTIONS.items()}

# Formázó függvény az incidensek szöveges megjelenítéséhez
def format_incidents(incidents):
    formatted_text = ""
    for inc in incidents:
        formatted_text += (
            f"A jegy száma: {inc['number']}\n"
            f"Rövid hiba leírás: {inc['short_description']}\n"
            f"Státusz: {inc['status']}\n"
            f"Link: {inc['link']}\n\n"
        )
    return formatted_text

@app.route('/get_incidents', methods=['POST'])
def get_incidents():
    request_data = request.json
    felhasználónév = request_data.get('felhasználónév')
    jelszó = request_data.get('jelszó')
    állapot_nev = request_data.get('állapot')  #  pl. "Nyitott"

    # Konvertáljuk az állapotot kódra, ha szöveges formában érkezett
    állapot = STATUS_OPTIONS.get(állapot_nev)
    if not állapot:
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
                        "status": STATUS_LABELS.get(inc["state"], inc["state"]),
                        "link": f"https://dev227667.service-now.com/incident.do?sys_id={inc['sys_id']}"
                    }
                    for inc in incidents
                ]

                # Válasz az incidensekkel
                formatted_text = format_incidents(formatted_incidents)
                return Response(formatted_text, content_type="text/plain; charset=utf-8")
            else:
                return jsonify({"error": "Incidensek lekérése sikertelen"}), 400
        else:
            return jsonify({"error": "Felhasználói azonosító lekérése sikertelen."}), 400
    else:
        return jsonify({"error": "Authentication failed", "details": response.text}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
