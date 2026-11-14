from flask import Flask, render_template, request, jsonify
import sqlite3
import csv
import os
from statistics import mean

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "agri_link.db")
CSV_PATH = os.path.join(BASE_DIR, "data", "market_prices.csv")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            farmer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS buyers (
            buyer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            crop TEXT NOT NULL,
            price_per_kg REAL NOT NULL,
            demand TEXT NOT NULL,
            reliability REAL NOT NULL,
            distance_km REAL NOT NULL
        )
    """)

    cur.execute("SELECT COUNT(*) FROM buyers")
    if cur.fetchone()[0] == 0:
        buyers = [
            ("ABC Rice Mill", "Thanjavur", "Paddy", 28.50, "High", 95, 18),
            ("Delta Agro Traders", "Trichy", "Paddy", 30.00, "Medium", 90, 65),
            ("Kaveri Foods", "Chennai", "Paddy", 31.00, "High", 88, 320),
            ("Green Harvest FPO", "Kumbakonam", "Paddy", 29.00, "High", 93, 35),
            ("Tamil Nadu Grains", "Mayiladuthurai", "Paddy", 28.75, "Medium", 92, 48)
        ]
        cur.executemany("""
            INSERT INTO buyers
            (name, location, crop, price_per_kg, demand, reliability, distance_km)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, buyers)

    conn.commit()
    conn.close()


def load_prices(crop):
    rows = []
    if not os.path.exists(CSV_PATH):
        return rows

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["crop"].strip().lower() == crop.strip().lower():
                rows.append({
                    "date": row["date"],
                    "price": float(row["price"])
                })
    return rows


def predict_price(crop):
    prices = load_prices(crop)
    if not prices:
        return 25.0, "Stable", []

    last_prices = [x["price"] for x in prices[-5:]]
    current = last_prices[-1]

    if len(last_prices) >= 2:
        change = last_prices[-1] - last_prices[-2]
    else:
        change = 0

    # Simple demo prediction using recent average + trend.
    predicted = round(mean(last_prices) + (change * 0.5), 2)

    if change > 0.10:
        trend = "Increasing"
    elif change < -0.10:
        trend = "Decreasing"
    else:
        trend = "Stable"

    return predicted, trend, prices


def calculate_buyer_score(price, distance, demand, reliability):
    demand_score = {"High": 100, "Medium": 70, "Low": 40}.get(demand, 40)

    # Higher price, higher demand, higher reliability and shorter distance are better.
    price_score = min((price / 35.0) * 100, 100)
    distance_score = max(0, 100 - (distance / 5.0))
    distance_score = min(distance_score, 100)

    score = (
        0.40 * price_score +
        0.25 * distance_score +
        0.20 * demand_score +
        0.15 * reliability
    )
    return round(score, 2)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}

    farmer_name = str(data.get("farmer_name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    location = str(data.get("location", "")).strip()
    crop = str(data.get("crop", "")).strip()
    quality = str(data.get("quality", "")).strip()
    quantity = float(data.get("quantity", 0) or 0)
    production_cost = float(data.get("production_cost", 0) or 0)
    selling_cost = float(data.get("selling_cost", 0) or 0)

    if not all([farmer_name, phone, location, crop, quality]):
        return jsonify({"error": "Please fill all required fields."}), 400

    if quantity <= 0:
        return jsonify({"error": "Quantity must be greater than 0."}), 400

    if production_cost < 0 or selling_cost < 0:
        return jsonify({"error": "Costs cannot be negative."}), 400

    predicted_price, trend, price_history = predict_price(crop)

    # Quality adjustment for the demo.
    quality_factor = {
        "A Grade": 1.05,
        "B Grade": 1.00,
        "C Grade": 0.94
    }.get(quality, 1.00)

    expected_price = round(predicted_price * quality_factor, 2)
    expected_selling_price = round(expected_price * quantity, 2)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO farmers(name, phone, location)
        VALUES (?, ?, ?)
    """, (farmer_name, phone, location))
    farmer_id = cur.lastrowid

    cur.execute("""
        SELECT * FROM buyers
        WHERE crop = ?
        ORDER BY price_per_kg DESC
    """, (crop,))
    buyer_rows = cur.fetchall()
    conn.commit()
    conn.close()

    buyers = []
    for b in buyer_rows:
        transport_cost = round(b["distance_km"] * 4.0, 2)
        gross_revenue = round(b["price_per_kg"] * quantity, 2)
        net_realisation = round(
            gross_revenue - production_cost - selling_cost - transport_cost, 2
        )
        score = calculate_buyer_score(
            b["price_per_kg"],
            b["distance_km"],
            b["demand"],
            b["reliability"]
        )

        buyers.append({
            "name": b["name"],
            "location": b["location"],
            "price": b["price_per_kg"],
            "demand": b["demand"],
            "reliability": b["reliability"],
            "distance": b["distance_km"],
            "transport_cost": transport_cost,
            "gross_revenue": gross_revenue,
            "net_realisation": net_realisation,
            "score": score
        })

    buyers.sort(key=lambda x: x["net_realisation"], reverse=True)

    best_buyer = buyers[0] if buyers else None
    best_nrs = best_buyer["net_realisation"] if best_buyer else round(
        expected_selling_price - production_cost - selling_cost, 2
    )
    expected_profit = best_nrs

    if trend == "Increasing":
        best_time = "Within the next 3–5 days"
    elif trend == "Decreasing":
        best_time = "Sell as soon as a good buyer is available"
    else:
        best_time = "Within the next 5–7 days"

    return jsonify({
        "farmer_id": farmer_id,
        "crop": crop,
        "quantity": quantity,
        "quality": quality,
        "predicted_price": predicted_price,
        "expected_price": expected_price,
        "expected_selling_price": expected_selling_price,
        "production_cost": production_cost,
        "selling_cost": selling_cost,
        "trend": trend,
        "best_time": best_time,
        "best_buyer": best_buyer,
        "buyers": buyers,
        "expected_profit": expected_profit,
        "price_history": price_history,
        "message": "Analysis completed successfully."
    })

init_db()




if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
