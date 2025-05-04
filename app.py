from flask import Flask, request, jsonify, render_template, send_from_directory
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask_cors import CORS
import re
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Подключение к Google Sheets
def get_sheet():
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    credentials_dict = json.loads(credentials_json)

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client.open("iphones").sheet1

# Фильтрация строки по параметрам
def match_row(row, filters):
    model_filter = filters.get("model", "").strip().lower()
    memory_filter = filters.get("memory", "").strip()
    battery_filter = filters.get("battery", "").strip().replace('%', '')

    row_model = str(row.get("Модель", "")).strip().lower()
    row_memory = str(row.get("Память (ГБ)", "")).strip()
    row_battery = str(row.get("Батарея (%)", "")).strip()

    # Проверка модели
    if model_filter and model_filter != row_model:
        return False

    # Проверка памяти
    if memory_filter and memory_filter != row_memory:
        return False

    # Проверка батареи
    if battery_filter and int(row_battery) < int(battery_filter):
        return False

    return True

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Обработка POST-запроса от HTML
@app.route("/bot", methods=["POST"])
def chatbot():
    try:
        filters = request.json
        sheet = get_sheet()
        data = sheet.get_all_records()

        results = [row for row in data if match_row(row, filters)]

        if results:
            reply_list = []
            for item in results[:3]:
                parts = []
                if item.get("Модель"):
                    parts.append(f"Модель: {item['Модель']}")
                if item.get("Память (ГБ)"):
                    parts.append(f"Память: {item['Память (ГБ)']} ГБ")
                if item.get("Батарея (%)"):
                    parts.append(f"Батарея: {item['Батарея (%)']}%")
                if item.get("Цена (₸)"):
                    parts.append(f"Цена: {item['Цена (₸)']} ₸")
                reply_list.append(". ".join(parts))
            return jsonify({"reply": reply_list})
        else:
            return jsonify({"reply": "К сожалению, ничего не найдено. Попробуйте изменить фильтры."})

    except Exception as e:
        return jsonify({"reply": f"Ошибка: {str(e)}"})

# Запуск приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
