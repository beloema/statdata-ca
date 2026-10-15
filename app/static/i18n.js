const translations = {
  "Overview": "Vue d'ensemble",
  "Economy": "Économie",
  "Labour Market": "Marché du travail",
  "Population": "Population",
  "Canada at a Glance": "Le Canada en un coup d'œil",
  "Canadian Economy": "Économie canadienne",
  "Population & Demographics": "Population et démographie",
  "Explore Canadian economic and demographic data from Statistics Canada.": "Explorez les données économiques et démographiques canadiennes de Statistique Canada.",
  "Explore Canada's key economic and demographic indicators.": "Explorez les principaux indicateurs économiques et démographiques du Canada.",
  "Inflation, interest rates, currencies and economic growth.": "Inflation, taux d'intérêt, devises et croissance économique.",
  "Employment trends and unemployment across Canada.": "Évolution de l'emploi et du chômage au Canada.",
  "Canada's population and regional comparisons.": "Population canadienne et comparaisons régionales.",
  "Consumer Price Index": "Indice des prix à la consommation",
  "Annual Inflation Rate": "Taux d'inflation annuel",
  "Target Interest Rate": "Taux directeur",
  "USD/CAD Exchange Rate": "Taux de change USD/CAD",
  "Unemployment Rate": "Taux de chômage",
  "Real GDP": "PIB réel",
  "Canadian Population": "Population canadienne",
  "Historical Trends": "Tendances historiques",
  "Historical Trend": "Évolution historique",
  "Statistical Analysis": "Analyse statistique",
  "12-Month Average": "Moyenne sur 12 mois",
  "12-Month Minimum": "Minimum sur 12 mois",
  "12-Month Maximum": "Maximum sur 12 mois",
  "Annual Change": "Variation annuelle",
  "Provincial & Territorial Comparisons": "Comparaisons provinciales et territoriales",
  "Regional Comparison": "Comparaison régionale",
  "Unemployment by Province": "Chômage par province",
  "Population by Province & Territory": "Population par province et territoire",
  "Regional Trends Over Time": "Évolution régionale dans le temps",
  "Compare with Canada": "Comparer avec le Canada",
  "Regional growth": "Croissance régionale",
  "Canada growth": "Croissance canadienne",
  "Growth difference": "Écart de croissance",
  "Latest index": "Indice récent",
  "Canada rate": "Taux canadien",
  "Latest rate gap": "Écart de taux actuel",
  "Regional rate change": "Variation du taux régional",
  "Download CSV": "Télécharger CSV",
  "Download Regional CSV": "Télécharger les données régionales",
  "All": "Tout",
  "Light mode": "Mode clair",
  "Dark mode": "Mode sombre",
  "Loading statistics...": "Chargement des statistiques...",
  "Loading regional data...": "Chargement des données régionales...",
  "Loading regional trends...": "Chargement des tendances régionales...",
  "Analytics unavailable": "Statistiques indisponibles",
  "Unable to load analytics.": "Impossible de charger les statistiques.",
  "Regional data unavailable": "Données régionales indisponibles",
  "Trend data unavailable": "Données historiques indisponibles",
  "Population growth comparison · Both series start at 100": "Comparaison de la croissance démographique · Indice de départ : 100",
  "Seasonally adjusted unemployment rates (%)": "Taux de chômage désaisonnalisé (%)",
  "Index (start = 100)": "Indice (base 100)",
  "Index (2002=100)": "Indice (2002=100)",
  "CAD per USD": "CAD par USD",
  "Persons": "Personnes",
  "Percent": "Pourcentage",
  "Statistics Canada": "Statistique Canada",
  "Data source": "Source des données",
  "Source": "Source",
  "Reference date": "Date de référence",
  "Latest observation": "Dernière observation",
  "Observations in past 12 months": "Observations sur 12 mois",
  "Unemployment rate (%)": "Taux de chômage (%)",
  "Unemployment rate": "Taux de chômage",
  "Millions of chained 2017 CAD, annualized": "Millions de dollars enchaînés de 2017, taux annuel",
  "Newfoundland and Labrador": "Terre-Neuve-et-Labrador",
  "Prince Edward Island": "Île-du-Prince-Édouard",
  "Nova Scotia": "Nouvelle-Écosse",
  "New Brunswick": "Nouveau-Brunswick",
  "Quebec": "Québec",
  "Ontario": "Ontario",
  "Manitoba": "Manitoba",
  "Saskatchewan": "Saskatchewan",
  "Alberta": "Alberta",
  "British Columbia": "Colombie-Britannique",
  "Yukon": "Yukon",
  "Northwest Territories": "Territoires du Nord-Ouest",
  "Nunavut": "Nunavut",
  "Canada": "Canada"
};

const reverseTranslations = Object.fromEntries(
  Object.entries(translations).map(([en, fr]) => [fr, en])
);

let currentLanguage = (() => {
  try {
    return localStorage.getItem("statdata-language") || "fr";
  } catch (_) {
    return "fr";
  }
})();

function translateText(value) {
  const dictionary = currentLanguage === "fr"
    ? translations : reverseTranslations;

  let result = value;

  // Translate longer phrases first.
  const entries = Object.entries(dictionary)
    .sort((a, b) => b[0].length - a[0].length);

  for (const [source, target] of entries) {
    if (result.trim() === source) {
      return result.replace(source, target);
    }
  }

  // Translate composite labels and dynamically generated headings.
  result = result.replace(
    / — Historical Trend| — Évolution historique/g,
    currentLanguage === "fr"
      ? " — Évolution historique"
      : " — Historical Trend"
  );

  result = result.replace(
    /^(Latest observation|Dernière observation):/,
    currentLanguage === "fr"
      ? "Dernière observation:"
      : "Latest observation:"
  );

  result = result.replace(
    /(Observations in past 12 months|Observations sur 12 mois):/,
    currentLanguage === "fr"
      ? "Observations sur 12 mois:"
      : "Observations in past 12 months:"
  );

  result = result.replace(
    /^(Reference date|Date de référence):/,
    currentLanguage === "fr"
      ? "Date de référence:"
      : "Reference date:"
  );

  for (const [source, target] of entries) {
    if (result.includes(source) &&
        (result.includes(" — ") || result.includes(" | ") ||
         result.includes(" rate") || result.includes(" taux"))) {
      result = result.replaceAll(source, target);
    }
  }

  return result;
}

function localizeDashboard() {
  document.documentElement.lang = currentLanguage;

  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT
  );

  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);

  for (const node of nodes) {
    if (["SCRIPT", "STYLE"].includes(node.parentElement?.tagName)) {
      continue;
    }

    const translated = translateText(node.nodeValue);
    if (translated !== node.nodeValue) {
      node.nodeValue = translated;
    }
  }

  // Preserve English region values for the API, translate labels only.
  document.querySelectorAll("#region-trend-select option")
    .forEach(option => {
      option.textContent =
        currentLanguage === "fr"
          ? (translations[option.value] || option.value)
          : option.value;
    });

  const button = document.getElementById("language-toggle");
  if (button) {
    button.textContent = currentLanguage === "fr" ? "EN" : "FR";
    button.setAttribute(
      "aria-label",
      currentLanguage === "fr"
        ? "Switch to English"
        : "Passer en français"
    );
  }
}

function setLanguage(language) {
  currentLanguage = language;
  try {
    localStorage.setItem("statdata-language", language);
  } catch (_) {}

  localizeDashboard();

  // Refresh chart language without changing database records.
  if (typeof chart !== "undefined" && chart) {
    const unit = datasets[selected]?.unit;
    if (unit) {
      chart.data.datasets[0].label =
        currentLanguage === "fr"
          ? (translations[unit] || unit)
          : unit;
    }
    chart.update("none");
  }

  if (typeof regionalChart !== "undefined" && regionalChart) {
    regionalChart.data.labels = regionalChart.data.labels.map(label =>
      currentLanguage === "fr"
        ? (translations[reverseTranslations[label] || label] || label)
        : (reverseTranslations[label] || label)
    );
    regionalChart.update("none");
  }
}

// Add language control beside the theme switch.
const themeButton = document.getElementById("theme-toggle");
const languageButton = document.createElement("button");

languageButton.id = "language-toggle";
languageButton.className = "theme-toggle";
languageButton.type = "button";

themeButton.parentElement.insertBefore(languageButton, themeButton);

languageButton.addEventListener("click", () => {
  setLanguage(currentLanguage === "fr" ? "en" : "fr");
});

// Translate content created asynchronously by Flask API responses.
// Translate content without observing our own changes.
const observer = new MutationObserver(() => {
  observer.disconnect();
  localizeDashboard();
  observer.observe(document.body, {
    subtree: true,
    childList: true
  });
});

observer.observe(document.body, {
  subtree: true,
  childList: true
});

setLanguage(currentLanguage);
