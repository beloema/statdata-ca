const sections = {
  overview: {
    title: "Canada at a Glance",
    description: "Explore Canada's key economic and demographic indicators.",
    datasets: null
  },
  economy: {
    title: "Canadian Economy",
    description: "Inflation, interest rates, currencies and economic growth.",
    datasets: [
      "inflation_rate",
      "inflation",
      "interest_rates",
      "exchange_rates",
      "gdp"
    ]
  },
  labour: {
    title: "Labour Market",
    description: "Employment trends and unemployment across Canada.",
    datasets: ["employment"]
  },
  population: {
    title: "Population & Demographics",
    description: "Canada's population and regional comparisons.",
    datasets: ["population"]
  }
};

const nav = document.getElementById("section-nav");
const labels = {
  overview: "Overview",
  economy: "Economy",
  labour: "Labour Market",
  population: "Population"
};

nav.innerHTML = Object.keys(sections).map(key => `
  <button type="button" data-section="${key}"
          aria-pressed="${key === "overview"}"
          class="${key === "overview" ? "active" : ""}">
    ${labels[key]}
  </button>
`).join("");

function navigate(section) {
  const config = sections[section];
  if (!config) return;

  document.getElementById("page-title").textContent = config.title;
  document.getElementById("page-subtitle").textContent =
    config.description;

  nav.querySelectorAll("button").forEach(button => {
    const active = button.dataset.section === section;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  const allowed = config.datasets || Object.keys(datasets);

  document.querySelectorAll("#cards .card").forEach((card, index) => {
    const key = Object.keys(datasets)[index];
    card.hidden = !allowed.includes(key);
  });

  if (!allowed.includes(selected)) {
    selectDataset(allowed[0]);
  }
}

nav.addEventListener("click", event => {
  const button = event.target.closest("button[data-section]");
  if (button) navigate(button.dataset.section);
});
