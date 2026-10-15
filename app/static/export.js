document.getElementById("download-csv")
  .addEventListener("click", () => {
    const url = "/api/export/" +
      encodeURIComponent(selected) +
      "?range=" + encodeURIComponent(selectedRange) + "&lang=" + encodeURIComponent(document.documentElement.lang || "fr");

    window.location.href = url;
  });
