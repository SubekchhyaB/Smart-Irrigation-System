function toggleOverride() {
    const isChecked = document.getElementById("overrideSwitch").checked;
    console.log("🔁 Toggle clicked. Sending value:", isChecked);

    fetch("/api/override", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ override: isChecked })
    })
    .then(res => {
        if (!res.ok) throw new Error("Network response was not ok");
        return res.json();
    })
    .then(data => {
        console.log("✅ Response received:", data);
        document.getElementById("pumpStatusText").innerText = isChecked
            ? "Pump override is ON"
            : "Pump override is OFF";
    })
    .catch(err => {
        console.error("❌ Error:", err);
        alert("Error updating pump override status: " + err.message);
    });
}

