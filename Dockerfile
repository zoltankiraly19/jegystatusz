# Alap Docker image, amely a Python 3.9-et tartalmazza
FROM python:3.9-slim

# Munkakönyvtár létrehozása az alkalmazás számára
WORKDIR /app

# Másoljuk a requirements.txt fájlt, majd telepítjük a függőségeket
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Az alkalmazás fájlok másolása a konténerbe
COPY . .

# Az alkalmazás futtatása
CMD ["python", "app.py"]

# Port megadása, amit a Flask használ
EXPOSE 5000
