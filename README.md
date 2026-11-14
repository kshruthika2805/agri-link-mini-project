# AGRI-LINK Mini Project

## Platform
- Visual Studio Code
- Python 3.10 or newer
- Flask
- SQLite
- HTML + CSS + JavaScript

## Run

Open this folder in VS Code.

Open the VS Code Terminal and run:

```bash
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

macOS/Linux:
```bash
source venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
python app.py
```

Open the address shown in the terminal:
http://127.0.0.1:5000

## Demo
Use:
- Farmer: Ravi
- Phone: 9876543210
- Location: Thanjavur
- Crop: Paddy
- Quantity: 2100
- Quality: A Grade
- Production Cost: 25000
- Selling Cost: 2100

The application calculates:
- AI-style price prediction from recent demo market data
- Expected selling price
- Buyer ranking
- Transport cost
- Net Realisation
- Expected profit
- Best buyer
- Best time to sell
- Price trend
- Tamil/English interface

## Important
The market-price CSV is demo data for the mini-project. It is not a live government market-price feed.
