document.addEventListener("DOMContentLoaded", () => {

    const analysisButton =
        document.getElementById("viewAnalysisBtn");

    if (analysisButton) {

        analysisButton.addEventListener("click", function (e) {

            e.preventDefault();

            const stock =
                localStorage.getItem("selectedStock");

            if (!stock) {
                alert("Please search a stock first.");
                return;
            }

            window.location.href =
                "/analysis?symbol=" +
                encodeURIComponent(stock);

        });

    }

    window.addEventListener("load", () => {

        const graph =
            document.querySelector(".js-plotly-plot");

        if (graph) {

            Plotly.relayout(graph, {
                height: 390
            });

        }

    });

    const progress =
        document.querySelector(".progress-fill");

    if (progress) {

        progress.style.width =
            progress.dataset.confidence || "0%";

    }

});