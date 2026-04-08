async function play(choice) {
    const response = await fetch("/play", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ choice })
    });

    const data = await response.json();

    document.getElementById("result").innerText =
        `You: ${data.player} | Computer: ${data.computer} → ${data.winner}`;
}