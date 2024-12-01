from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

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

@app.route('/get_incidents', methods=['POST'])
def get_incidents():
    request_data = request.json
    felhasználónév = request_data.get('felhasználónév')
    jelszó = request_data.get('jelszó')
    állapot_nev = request_data.get('állapot')  # pl. "Nyitott"

    # Állapot kódra konvertálása
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

        # Felhasználói sys_id lekérése
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

                # Külön változókba töltjük az adatokat
                formatted_incidents = []

                for inc in incidents:
                    formatted_incidents.append(
                        f"Incidens szám: {inc['number']}\n"
                        f"Állapot: {STATUS_LABELS.get(str(inc['state']), 'Ismeretlen állapot')}\n"
                        f"Rövid leírás: {inc['short_description']}\n"
                        f"Link: https://dev227667.service-now.com/incident.do?sys_id={inc['sys_id']}\n"
                    )

                # A formázott válasz elküldése a kívánt formátumban (minden egyes jegy külön blokkban)
                incidents_response = "\n\n".join(formatted_incidents)

                return jsonify({
                    "message": "Incidensek sikeresen lekérve",
                    "incidents": incidents_response  # Külön sorokban jelenítjük meg az incidenseket
                }), 200
            else:
                return jsonify({"error": "Incidensek lekérése sikertelen", "details": response_incidents.text}), 400
        else:
            return jsonify({"error": "Felhasználói azonosító lekérése sikertelen", "details": response_user.text}), 400
    else:
        return jsonify({"error": "Authentication failed", "details": response.text}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
