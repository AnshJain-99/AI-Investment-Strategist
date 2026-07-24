document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById("stockSearchInput");
    const resultBox = document.getElementById("stockResults");
    const watchlistSearch = document.getElementById("watchlistSearch");

    /* -------------------------
       Search inside watchlist
    --------------------------*/

    if (watchlistSearch) {

        watchlistSearch.addEventListener("keyup", function () {

            const value = this.value.toLowerCase();

            document.querySelectorAll(".watchlist-card").forEach(card => {

                const symbol = card.dataset.symbol.toLowerCase();

                card.style.display = symbol.includes(value)
                    ? "block"
                    : "none";

            });

        });

    }

    /* -------------------------
       Live Stock Search
    --------------------------*/

    if (searchInput) {

        let timer;

        searchInput.addEventListener("keyup", function () {

            clearTimeout(timer);

            const query = this.value.trim();

            if (query.length < 2) {

                resultBox.innerHTML = "";

                return;

            }

            timer = setTimeout(async () => {

                const response = await fetch(`/api/search-stocks?q=${query}`);

                const stocks = await response.json();

                resultBox.innerHTML = "";

                if (!stocks.length) {

                    resultBox.innerHTML =
                        "<p class='text-center mt-3'>No stock found.</p>";

                    return;

                }

                stocks.forEach(stock => {

                    resultBox.innerHTML += `

                    <div class="search-item">

                        <div>

                            <strong>${stock.symbol}</strong>

                            <small>${stock.name}</small>

                        </div>

                        <button
                            class="btn btn-primary btn-sm add-stock"
                            data-symbol="${stock.symbol}">

                            Add

                        </button>

                    </div>

                    `;

                });

            }, 300);

        });

    }

    /* -------------------------
       Add Stock
    --------------------------*/

    document.addEventListener("click", async (e) => {

        if (!e.target.classList.contains("add-stock")) return;

        const symbol = e.target.dataset.symbol;

        const response = await fetch("/watchlist/add", {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify({

                symbol

            })

        });

        const result = await response.json();

        if (result.success) {

            location.reload();

        } else {

            alert(result.message);

        }

    });

    /* -------------------------
       Remove Stock
    --------------------------*/

    document.querySelectorAll(".remove-stock").forEach(btn => {

        btn.addEventListener("click", async function () {

            if (!confirm("Remove this stock?")) return;

            await fetch("/watchlist/remove", {

                method: "POST",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify({

                    symbol: this.dataset.symbol

                })

            });

            this.closest(".watchlist-card").remove();

        });

    });

    /* -------------------------
       Load Live Data
    --------------------------*/

    document.querySelectorAll(".watchlist-card").forEach(async card => {

        const symbol = card.dataset.symbol;

        try {

            const response = await fetch(`/api/stock-live/${symbol}`);

            console.log("Status:", response.status);

            const data = await response.json();

            console.log(symbol, data);

            document.getElementById(`company-${symbol}`).innerText =
                data.company;

            document.getElementById(`price-${symbol}`).innerText =
                "₹ " + data.price;

            const change =
                document.getElementById(`change-${symbol}`);

            const sign = data.change >= 0 ? "+" : "";

            change.innerHTML =
                data.change >= 0
                    ? `<i class="bi bi-arrow-up-right"></i> +${data.change}% Today`
                    : `<i class="bi bi-arrow-down-right"></i> ${data.change}% Today`;

            change.classList.remove("green", "red");

            if (data.change >= 0) {

                change.classList.add("green");

            } else {

                change.classList.add("red");

            }

        } catch (err) {

            console.log(err);

        }
        document.getElementById(`marketcap-${symbol}`).innerText =
            formatMarketCap(data.market_cap);

        document.getElementById(`pe-${symbol}`).innerText =
            data.pe ?? "--";

        document.getElementById(`high-${symbol}`).innerText =
            data.high52 ?? "--";

        document.getElementById(`low-${symbol}`).innerText =
            data.low52 ?? "--";

    });


});
function formatMarketCap(value) {

    if (!value) return "--";

    if (value >= 1e12)
        return (value / 1e12).toFixed(2) + " T";

    if (value >= 1e9)
        return (value / 1e9).toFixed(2) + " B";

    if (value >= 1e7)
        return (value / 1e7).toFixed(2) + " Cr";

    return value;

}