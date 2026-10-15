/* STATDATA.CA localization. No DOM-mutating observation loop; chart labels are localized
   with a Chart.js plugin, and data identifiers stay in English for API consistency. */
(() => {
  "use strict";

  const fr = {
    "Overview": "Vue d’ensemble",
    "Economy": "Économie",
    "Labour Market": "Marché du travail",
    "Population": "Population",
    "Canada at a Glance": "Le Canada en un coup d’œil",
    "Canadian Economy": "Économie canadienne",
    "Population & Demographics": "Population et démographie",
    "Explore Canadian economic and demographic data from Statistics Canada.": "Explorez les données économiques et démographiques canadiennes de Statistique Canada.",
    "Explore Canada's key economic and demographic indicators.": "Explorez les principaux indicateurs économiques et démographiques du Canada.",
    "Inflation, interest rates, currencies and economic growth.": "Inflation, taux d’intérêt, devises et croissance économique.",
    "Employment trends and unemployment across Canada.": "Évolution de l’emploi et du chômage au Canada.",
    "Canada's population and regional comparisons.": "Population canadienne et comparaisons régionales.",
    "Consumer Price Index": "Indice des prix à la consommation",
    "Annual Inflation Rate": "Taux d’inflation annuel",
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
    "Download Regional CSV": "Télécharger les données régionales (CSV)",
    "Download CSV": "Télécharger CSV",
    "Data source": "Source des données",
    "Source": "Source",
    "Reference date": "Date de référence",
    "Latest observation": "Dernière observation",
    "Observations in past 12 months": "Observations des 12 derniers mois",
    "Unemployment rate (%)": "Taux de chômage (%)",
    "Unemployment rate": "Taux de chômage",
    "Unemployment": "Chômage",
    "Population growth comparison · Both series start at 100": "Comparaison de la croissance démographique · Les deux séries commencent à 100",
    "Seasonally adjusted unemployment rates (%)": "Taux de chômage désaisonnalisés (%)",
    "Index (start = 100)": "Indice (base 100)",
    "Index (2002=100)": "Indice (2002=100)",
    "CPI (2002=100)": "IPC (2002=100)",
    "CAD per USD": "CAD par USD",
    "Persons": "Personnes",
    "Percent": "Pourcentage",
    "Millions of chained 2017 CAD, annualized": "Millions de dollars enchaînés de 2017, taux annuel",
    "Loading statistics...": "Chargement des statistiques…",
    "Loading regional data...": "Chargement des données régionales…",
    "Loading regional trends...": "Chargement des tendances régionales…",
    "Unable to load analytics.": "Impossible de charger les statistiques.",
    "Analytics unavailable": "Statistiques indisponibles",
    "Regional data unavailable": "Données régionales indisponibles",
    "Trend data unavailable": "Données historiques indisponibles",
    "All": "Tout",
    "1Y": "1 an",
    "5Y": "5 ans",
    "10Y": "10 ans",
    "Light mode": "Mode clair",
    "Dark mode": "Mode sombre",
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

  let language;
  try { language = localStorage.getItem("statdata-language") === "en" ? "en" : "fr"; }
  catch (_) { language = "fr"; }

  const sourceNodes = new WeakMap();
  const phrases = Object.entries(fr).sort((a, b) => b[0].length - a[0].length);
  const locale = () => language === "fr" ? "fr-CA" : "en-CA";

  function renderDate(raw, compact = false) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(raw))) return raw;
    const date = new Date(raw + "T00:00:00Z");
    if (Number.isNaN(date.getTime())) return raw;
    return new Intl.DateTimeFormat(locale(), {
      timeZone: "UTC", day: compact ? undefined : "numeric",
      month: "short", year: "numeric"
    }).format(date);
  }

  function translate(text) {
    if (language === "en" || !text) return text;
    let output = String(text);
    for (const [english, french] of phrases) {
      // Longer phrases first; labels from trusted code, not from user input.
      output = output.replaceAll(english, french);
    }
    return output;
  }

  function formatNumber(value, digits) {
    return new Intl.NumberFormat(locale(), {
      minimumFractionDigits: digits, maximumFractionDigits: digits
    }).format(value);
  }

  function translateNumbers(raw, parent) {
    if (!parent?.classList?.contains("value")) return raw;
    const match = /^([+\-]?)(\d+(?:\.\d+)?)(\s*%|\s*pp|[TM])?$/.exec(raw.trim());
    if (!match) return raw;
    const fraction = (match[2].split(".")[1] || "").length;
    const number = formatNumber(Number(match[2]), fraction);
    let suffix = match[3] || "";
    if (suffix === "T" || suffix === "M") suffix = " " + suffix;
    if (language === "fr") {
      if (suffix.trim() === "%") suffix = " %";
      if (suffix.trim() === "pp") suffix = " p.p.";
    }
    return match[1] + number + suffix;
  }

  function translateNode(raw, parent) {
    // ISO dates remain ISO in CSV; only visible UI receives locale formatting.
    let value = String(raw).replace(/\b\d{4}-\d{2}-\d{2}\b/g, v => renderDate(v));
    if (language === "fr") {
      const dynamicRate = value.trim().match(/^(.+) rate$/);
      if (dynamicRate && Object.prototype.hasOwnProperty.call(fr, dynamicRate[1])) {
        value = value.replace(dynamicRate[0], "Taux — " + (fr[dynamicRate[1]] || dynamicRate[1]));
      } else {
        value = translate(value);
      }
    }
    return translateNumbers(value, parent);
  }

  function localizeUI() {
    document.documentElement.lang = language;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      if (["SCRIPT", "STYLE"].includes(node.parentElement?.tagName)) continue;
      if (!sourceNodes.has(node)) sourceNodes.set(node, node.nodeValue);
      const replacement = translateNode(sourceNodes.get(node), node.parentElement);
      if (node.nodeValue !== replacement) node.nodeValue = replacement;
    }
    const select = document.getElementById("region-trend-select");
    if (select) {
      for (const option of select.options) {
        const nextLabel = language === "fr" ? (fr[option.value] || option.value) : option.value;
        if (option.textContent !== nextLabel) option.textContent = nextLabel;
      }
    }
    const switcher = document.getElementById("language-toggle");
    if (switcher) {
      const nextLabel = language === "fr" ? "EN" : "FR";
      if (switcher.textContent !== nextLabel) switcher.textContent = nextLabel;
      switcher.setAttribute("aria-label", language === "fr" ? "Switch to English" : "Passer en français");
    }
  }

  // The chart plugin handles Chart.js canvas labels (which DOM translation cannot reach).
  const chartLocalePlugin = {
    id: "statdataChartLocale",
    beforeUpdate(instance) {
      instance.options.locale = locale();
      if (!instance.$statdataOriginalLabels) {
        instance.$statdataOriginalLabels = [...(instance.data.labels || [])];
      }
      if (instance.canvas.id === "regional-chart") {
        instance.data.labels = instance.$statdataOriginalLabels.map(v => translate(v));
      }
      for (const series of instance.data.datasets) {
        if (series.$statdataEnglishLabel === undefined) {
          series.$statdataEnglishLabel = series.label || "";
        }
        series.label = translate(series.$statdataEnglishLabel);
      }
      instance.options.plugins ||= {};
      instance.options.plugins.tooltip ||= {};
      instance.options.plugins.tooltip.callbacks ||= {};
      instance.options.plugins.tooltip.callbacks.title = items => {
        const label = items[0]?.label || "";
        return translate(renderDate(label));
      };
      instance.options.plugins.tooltip.callbacks.label = context => {
        const number = context.parsed?.y ?? context.parsed?.x;
        const numberText = typeof number === "number"
          ? new Intl.NumberFormat(locale(), { maximumFractionDigits: 3 }).format(number)
          : context.formattedValue;
        return `${context.dataset.label}: ${numberText}`;
      };
      if (instance.options.scales?.x?.type !== "linear" && instance.canvas.id !== "regional-chart") {
        const scale = instance.options.scales?.x;
        if (scale?.ticks) {
          scale.ticks.callback = function(value) {
            return translate(renderDate(this.getLabelForValue(value), true));
          };
        }
      }
      if (instance.options.scales?.y?.title?.text) {
        const title = instance.options.scales.y.title;
        if (!instance.$statdataYAxisTitle) instance.$statdataYAxisTitle = title.text;
        title.text = translate(instance.$statdataYAxisTitle);
      }
    }
  };

  function updateCharts() {
    if (typeof Chart === "undefined") return;
    Chart.defaults.locale = locale();
    Object.values(Chart.instances).forEach(instance => instance.update("none"));
  }

  if (typeof Chart !== "undefined") Chart.register(chartLocalePlugin);

  const originalRangeButtons = document.querySelectorAll(".ranges button");
  for (const button of originalRangeButtons) {
    if (!button.dataset.range) button.dataset.range = button.textContent.trim().toUpperCase();
  }

  const themeButton = document.getElementById("theme-toggle");
  if (themeButton) {
    const button = document.createElement("button");
    button.id = "language-toggle";
    button.className = "theme-toggle";
    button.type = "button";
    themeButton.parentElement.insertBefore(button, themeButton);
    button.addEventListener("click", () => {
      language = language === "fr" ? "en" : "fr";
      try { localStorage.setItem("statdata-language", language); } catch (_) {}
      localizeUI();
      updateCharts();
    });
  }

  // New cards and labels replace DOM nodes. Observe additions only; changing the text
  // of an existing node does not retrigger this observer (no infinite loop).
  const observer = new MutationObserver(mutations => {
    if (mutations.some(m => m.addedNodes.length || m.removedNodes.length)) localizeUI();
  });
  observer.observe(document.body, { childList: true, subtree: true });

  window.statdataTranslateRegion = name => language === "fr" ? (fr[name] || name) : name;
  window.statdataTranslateUnit = name => translate(name);
  window.statdataLanguage = () => language;
  window.statdataFormatDate = renderDate;
  window.statdataFormatNumber = formatNumber;

  localizeUI();
  updateCharts();
})();
