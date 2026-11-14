let tamil = false;

function money(value) {
    return "₹" + Number(value).toLocaleString("en-IN", {
        maximumFractionDigits: 2
    });
}

function toggleLanguage() {
    tamil = !tamil;
    const btn = document.getElementById("languageBtn");

    if (tamil) {
        btn.textContent = "English";
        document.getElementById("title").textContent = "விவசாயி முடிவு பலகை";
        document.getElementById("subtitle").textContent = "கணிக்கவும் → ஒப்பிடவும் → இணைக்கவும் → விற்கவும்";
        document.getElementById("formTitle").textContent = "🌱 பயிர் விவரங்களை உள்ளிடவும்";
        document.getElementById("farmerNameLabel").textContent = "விவசாயி பெயர்";
        document.getElementById("locationLabel").textContent = "இடம்";
        document.getElementById("cropLabel").textContent = "பயிர்";
        document.getElementById("quantityLabel").textContent = "அளவு (கிலோ)";
        document.getElementById("qualityLabel").textContent = "தரம்";
        document.getElementById("productionLabel").textContent = "உற்பத்தி செலவு (₹)";
        document.getElementById("sellingLabel").textContent = "விற்பனை செலவு (₹)";
        document.getElementById("analyzeBtn").textContent = "🤖 பயிரை பகுப்பாய்வு செய்யவும்";
    } else {
        btn.textContent = "தமிழ்";
        document.getElementById("title").textContent = "Farmer Decision Dashboard";
        document.getElementById("subtitle").textContent = "Predict → Compare → Connect → Sell";
        document.getElementById("formTitle").textContent = "🌱 Enter Crop Details";
        document.getElementById("farmerNameLabel").textContent = "Farmer Name";
        document.getElementById("locationLabel").textContent = "Location";
        document.getElementById("cropLabel").textContent = "Crop";
        document.getElementById("quantityLabel").textContent = "Quantity (kg)";
        document.getElementById("qualityLabel").textContent = "Quality";
        document.getElementById("productionLabel").textContent = "Production Cost (₹)";
        document.getElementById("sellingLabel").textContent = "Selling Cost (₹)";
        document.getElementById("analyzeBtn").textContent = "🤖 ANALYZE MY CROP";
    }
}

function startVoice() {
    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        document.getElementById("voiceStatus").textContent =
            "Voice input is not supported in this browser.";
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = tamil ? "ta-IN" : "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    document.getElementById("voiceStatus").textContent = "Listening...";

    recognition.start();

    recognition.onresult = function(event) {
        const text = event.results[0][0].transcript;
        document.getElementById("voiceStatus").textContent =
            "Heard: " + text;
    };

    recognition.onerror = function() {
        document.getElementById("voiceStatus").textContent =
            "Could not understand voice input. Please type the details.";
    };
}

async function analyzeCrop() {
    const errorBox = document.getElementById("errorBox");
    errorBox.textContent = "";

    const payload = {
        farmer_name: document.getElementById("farmer_name").value,
        phone: document.getElementById("phone").value,
        location: document.getElementById("location").value,
        crop: document.getElementById("crop").value,
        quantity: document.getElementById("quantity").value,
        quality: document.getElementById("quality").value,
        production_cost: document.getElementById("production_cost").value,
        selling_cost: document.getElementById("selling_cost").value
    };

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Analysis failed.");
        }

        showResults(data);
    } catch (error) {
        errorBox.textContent = error.message;
    }
}

function showResults(data) {
    document.getElementById("results").classList.remove("hidden");

    document.getElementById("predictedPrice").textContent =
        money(data.expected_price) + " / kg";

    document.getElementById("expectedRevenue").textContent =
        money(data.expected_selling_price);

    document.getElementById("nrs").textContent =
        money(data.best_buyer ? data.best_buyer.net_realisation : data.expected_selling_price);

    document.getElementById("profit").textContent =
        money(data.expected_profit);

    document.getElementById("trend").textContent =
        data.trend + " | " + data.best_time;

    const buyer = data.best_buyer;

    if (buyer) {
        document.getElementById("recommendationText").innerHTML = `
            <div class="recommendation-box">
                <div class="rec-item">
                    <b>🏆 Best Buyer</b>
                    ${buyer.name}
                </div>
                <div class="rec-item">
                    <b>📍 Location</b>
                    ${buyer.location}
                </div>
                <div class="rec-item">
                    <b>💰 Buyer Price</b>
                    ${money(buyer.price)} / kg
                </div>
                <div class="rec-item">
                    <b>🚚 Transport Cost</b>
                    ${money(buyer.transport_cost)}
                </div>
                <div class="rec-item">
                    <b>📊 Net Realisation</b>
                    ${money(buyer.net_realisation)}
                </div>
                <div class="rec-item">
                    <b>⏰ Best Time</b>
                    ${data.best_time}
                </div>
            </div>
        `;
    }

    drawChart(data.price_history);
    drawBuyerTable(data.buyers);

    document.getElementById("results").scrollIntoView({
        behavior: "smooth"
    });
}

function drawChart(history) {
    const chart = document.getElementById("chart");
    chart.innerHTML = "";

    if (!history || history.length === 0) {
        chart.innerHTML = "<p>No price history available.</p>";
        return;
    }

    const prices = history.map(x => x.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = Math.max(max - min, 1);

    history.slice(-7).forEach(item => {
        const box = document.createElement("div");
        box.className = "bar-box";

        const value = document.createElement("div");
        value.className = "bar-value";
        value.textContent = "₹" + item.price;

        const bar = document.createElement("div");
        bar.className = "bar";
        bar.style.height = `${30 + ((item.price - min) / range) * 65}%`;

        const label = document.createElement("div");
        label.className = "bar-label";
        label.textContent = item.date;

        box.appendChild(value);
        box.appendChild(bar);
        box.appendChild(label);
        chart.appendChild(box);
    });
}

function drawBuyerTable(buyers) {
    const tbody = document.getElementById("buyerTable");
    tbody.innerHTML = "";

    buyers.forEach((buyer, index) => {
        const tr = document.createElement("tr");

        if (index === 0) {
            tr.className = "best-row";
        }

        tr.innerHTML = `
            <td>${index === 0 ? "🏆 " : ""}${buyer.name}</td>
            <td>${money(buyer.price)}</td>
            <td>${buyer.distance} km</td>
            <td>${money(buyer.transport_cost)}</td>
            <td>${money(buyer.net_realisation)}</td>
            <td>${buyer.score}</td>
        `;

        tbody.appendChild(tr);
    });
}
