function chartColor() {
  return getComputedStyle(document.documentElement)
    .getPropertyValue("--accent").trim();
}

function chartFill() {
  return document.documentElement.dataset.theme === "dark"
    ? "rgba(133,171,255,.09)"
    : "rgba(57,106,245,.06)";
}

function styleChart(instance, regional = false) {
  if (!instance) return;

  const css = getComputedStyle(document.documentElement);
  const muted = css.getPropertyValue("--muted").trim();
  const grid = css.getPropertyValue("--grid").trim();

  instance.data.datasets.forEach(ds => {
    if (regional) {
      ds.backgroundColor = chartColor();
    } else {
      ds.borderColor = chartColor();
      ds.backgroundColor = chartFill();
    }
  });

  for (const axis of ["x", "y"]) {
    if (!instance.options.scales?.[axis]) continue;

    instance.options.scales[axis].ticks.color = muted;
    instance.options.scales[axis].grid.color = grid;
  }

  instance.update();
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;

  try {
    localStorage.setItem("statdata-theme", theme);
  } catch (_) {}

  const button = document.getElementById("theme-toggle");
  button.textContent = theme === "dark"
    ? "☀ Light mode"
    : "☾ Dark mode";

  button.setAttribute("aria-pressed", String(theme === "dark"));

  if (typeof Chart !== "undefined") {
    const css = getComputedStyle(document.documentElement);
    Chart.defaults.color = css.getPropertyValue("--muted").trim();
    Chart.defaults.borderColor = css.getPropertyValue("--grid").trim();
  }

  if (typeof chart !== "undefined") styleChart(chart);
  if (typeof regionalChart !== "undefined")
    styleChart(regionalChart, true);
}

document.getElementById("theme-toggle").addEventListener("click", () => {
  const current = document.documentElement.dataset.theme;
  applyTheme(current === "dark" ? "light" : "dark");
});

applyTheme(document.documentElement.dataset.theme);
