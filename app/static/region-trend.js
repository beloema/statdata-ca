let provinceTrendChart = null;

window.loadRegionTrend = async function(dataset) {
  if (!["employment", "population"].includes(dataset)) return;

  const select = document.getElementById("region-trend-select");
  const description = document.getElementById("region-trend-description");

  try {
    if (select.dataset.loadedFor !== dataset) {
      const response = await fetch("/api/regions/" + dataset);
      if (!response.ok) throw new Error("Regions unavailable");

      const data = await response.json();
      if (selected !== dataset) return;

      const regions = data.regions
        .map(r => r.region)
        .sort((a, b) => a.localeCompare(b));

      select.replaceChildren();

      regions.forEach(region => {
        select.add(new Option(region, region));
      });

      select.value = regions.includes("Quebec")
        ? "Quebec"
        : regions[0];

      select.dataset.loadedFor = dataset;
    }

    const region = select.value;
    const period = selectedRange;

    description.textContent = "Loading regional trends...";

    const params = new URLSearchParams({
      region: region,
      range: period
    });

    const response = await fetch(
      "/api/region-history/" + dataset + "?" + params
    );

    if (!response.ok) throw new Error("Trend data unavailable");

    const data = await response.json();

    if (selected !== dataset ||
        selectedRange !== period ||
        select.value !== region) return;

    description.textContent = dataset === "population"
      ? "Population growth comparison · Both series start at 100"
      : "Seasonally adjusted unemployment rates (%)";

    renderRegionalInsights(data, dataset);

    if (provinceTrendChart) provinceTrendChart.destroy();

    const accent = getComputedStyle(document.documentElement)
      .getPropertyValue("--accent").trim();

    provinceTrendChart = new Chart(
      document.getElementById("region-trend-chart"), {
        type: "line",
        data: {
          labels: data.dates,
          datasets: [
            {
              label: region,
              data: data.region_values,
              borderColor: accent,
              borderWidth: 2.5,
              pointRadius: 0,
              tension: 0.2
            },
            {
              label: "Canada",
              data: data.canada_values,
              borderColor: "#94a3b8",
              borderWidth: 2,
              borderDash: [6, 5],
              pointRadius: 0,
              tension: 0.2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            mode: "index",
            intersect: false
          },
          plugins: {
            legend: {
              position: "bottom"
            }
          },
          scales: {
            x: {
              ticks: { maxTicksLimit: 8 }
            },
            y: {
              title: {
                display: true,
                text: data.unit
              }
            }
          }
        }
      }
    );

  } catch (error) {
    description.textContent = error.message;
    console.error(error);
  }
};

document.getElementById("region-trend-select")
  .addEventListener("change", () => {
    loadRegionTrend(selected);
  });

document.getElementById("theme-toggle")
  ?.addEventListener("click", () => {
    if (["employment", "population"].includes(selected)) {
      loadRegionTrend(selected);
    }
  });


// Regional descriptive statistics and CSV export
let regionalExportData = null;

function renderRegionalInsights(data, dataset) {
  const dates = data.dates;
  const local = data.region_values;
  const national = data.canada_values;

  if (!dates.length) return;

  const last = local.length - 1;
  const isPopulation = dataset === "population";
  const unit = isPopulation ? "%" : "pp";

  const localChange = local[last] - local[0];
  const nationalChange = national[last] - national[0];
  const gap = local[last] - national[last];

  const format = n => (n > 0 ? "+" : "") + n.toFixed(2);
  const cards = isPopulation
    ? [
        ["Regional growth", format(localChange) + "%"],
        ["Canada growth", format(nationalChange) + "%"],
        ["Growth difference", format(localChange - nationalChange) + " pp"],
        ["Latest index", local[last].toFixed(2)]
      ]
    : [
        [data.region + " rate", local[last].toFixed(1) + "%"],
        ["Canada rate", national[last].toFixed(1) + "%"],
        ["Latest rate gap", format(gap) + " pp"],
        ["Regional rate change", format(localChange) + " pp"]
      ];

  const container = document.getElementById("regional-insights");
  container.replaceChildren();

  for (const [label, value] of cards) {
    const card = document.createElement("div");
    card.className = "analytics-card";

    const caption = document.createElement("div");
    caption.className = "label";
    caption.textContent = label;

    const number = document.createElement("div");
    number.className = "value";
    number.textContent = value;

    card.append(caption, number);
    container.appendChild(card);
  }

  regionalExportData = data;
  document.getElementById("regional-download").disabled = false;
}

document.getElementById("regional-download")
  .addEventListener("click", () => {
    if (!regionalExportData) return;

    const data = regionalExportData;
    const escapeCSV = value =>
      '"' + String(value).replaceAll('"', '""') + '"';

    const lines = [
      (document.documentElement.lang === "fr"
        ? ["date", "region", "valeur_region", "valeur_canada", "unite", "tableau_source"]
        : ["date", "region", "region_value", "canada_value", "unit", "source_table"])
    ];

    for (let i = 0; i < data.dates.length; i++) {
      lines.push([
        data.dates[i],
        document.documentElement.lang === "fr"
          ? (window.statdataTranslateRegion?.(data.region) || data.region)
          : data.region,
        data.region_values[i],
        data.canada_values[i],
        document.documentElement.lang === "fr"
          ? (window.statdataTranslateUnit?.(data.unit) || data.unit)
          : data.unit,
        data.dataset === "employment" ? "14-10-0287-01" : "17-10-0009-01"
      ]);
    }

    const csv = lines.map(row =>
      row.map(escapeCSV).join(",")
    ).join("\r\n");

    const blob = new Blob(
      ["\ufeff", csv],
      {type: "text/csv;charset=utf-8"}
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "statdata_" +
      data.dataset + "_" +
      data.region.toLowerCase().replaceAll(" ", "_") +
      "_" + selectedRange.toLowerCase() + ".csv";

    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
