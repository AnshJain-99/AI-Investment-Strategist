document.addEventListener("DOMContentLoaded", () => {

    window.addEventListener("load", () => {

        const graph =
            document.querySelector(".js-plotly-plot");

        if (graph) {

            Plotly.relayout(graph, {
                height: 390
            });

        }

    });

    const marketChart = document.getElementById("market-chart");
    const rangeButtons = document.querySelectorAll(".market-range-button");
    const rangeDescription = document.getElementById("marketRangeDescription");

    function runChartScripts(container) {
        container.querySelectorAll("script").forEach((script) => {
            const executableScript = document.createElement("script");

            Array.from(script.attributes).forEach((attribute) => {
                executableScript.setAttribute(attribute.name, attribute.value);
            });

            executableScript.text = script.textContent;
            script.replaceWith(executableScript);
        });
    }

    async function loadMarketChart(button) {
        if (!marketChart || !button || button.classList.contains("loading")) {
            return;
        }

        const period = button.dataset.period;
        const label = button.dataset.label;

        rangeButtons.forEach((rangeButton) => {
            rangeButton.classList.remove("active");
            rangeButton.disabled = true;
        });

        button.classList.add("active", "loading");
        marketChart.classList.add("is-loading");

        try {
            const response = await fetch(
                `/api/dashboard-market-chart?period=${encodeURIComponent(period)}`
            );

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Chart unavailable");
            }

            marketChart.innerHTML = data.chart_html;
            runChartScripts(marketChart);

            if (rangeDescription) {
                rangeDescription.textContent =
                    `NIFTY 50 and SENSEX performance over the last ${label}`;
            }
        } catch (error) {
            marketChart.innerHTML = `
                <div class="chart-placeholder">
                    <i class="bi bi-wifi-off"></i>
                    <h5>Market chart unavailable</h5>
                    <p>Unable to load ${label} market data. Please try again.</p>
                </div>
            `;
        } finally {
            button.classList.remove("loading");
            marketChart.classList.remove("is-loading");

            rangeButtons.forEach((rangeButton) => {
                rangeButton.disabled = false;
            });
        }
    }

    rangeButtons.forEach((button) => {
        button.addEventListener("click", () => loadMarketChart(button));
    });

    const chart = document.getElementById("allocationChart");

    if (chart) {

        const legend = document.getElementById("portfolioLegend");

        const sectors = [

            ["Technology", 45, "#2563eb"],

            ["Finance", 35, "#16a34a"],

            ["Energy", 20, "#f59e0b"]

        ];

        new Chart(chart, {

            type: "doughnut",

            data: {

                labels: sectors.map(s => s[0]),

                datasets: [{

                    data: sectors.map(s => s[1]),

                    backgroundColor: sectors.map(s => s[2]),

                    borderWidth: 0

                }]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                cutout: "70%",

                plugins: {

                    legend: { display: false }

                }

            }

        });
        document.getElementById("bestStock").innerText = "TCS";
        document.getElementById("bestGain").innerText = "+4.82%";

        document.getElementById("worstStock").innerText = "RELIANCE";
        document.getElementById("worstLoss").innerText = "-1.43%";

        legend.innerHTML = "";

        sectors.forEach(item => {

            legend.innerHTML += `

<div class="legend-item">

<div class="legend-left">

<span class="legend-color"
style="background:${item[2]}"></span>

<strong>${item[0]}</strong>

</div>

<span>${item[1]}%</span>

</div>

`;

        });

    }
});
