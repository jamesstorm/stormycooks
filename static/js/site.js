(function () {
  "use strict";
  var grid = document.getElementById("grid");
  if (!grid) return;
  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
  var search = document.getElementById("search");
  var tagsWrap = document.getElementById("tags");
  var none = document.getElementById("none");

  // Build tag list from all cards.
  var tagCounts = {};
  cards.forEach(function (c) {
    (c.getAttribute("data-tags") || "").split("|").forEach(function (t) {
      if (t) tagCounts[t] = (tagCounts[t] || 0) + 1;
    });
  });
  var tagKeys = Object.keys(tagCounts).sort(function (a, b) {
    return tagCounts[b] - tagCounts[a] || a.localeCompare(b);
  });
  tagKeys.forEach(function (t) {
    var el = document.createElement("span");
    el.className = "pill";
    el.textContent = t;
    el.setAttribute("data-tag", t);
    el.addEventListener("click", function () {
      el.classList.toggle("active");
      apply();
    });
    tagsWrap.appendChild(el);
  });

  var activeTags = {};

  function apply() {
    var q = (search ? search.value : "").trim().toLowerCase();
    Object.keys(activeTags).forEach(function (k) { delete activeTags[k]; });
    tagsWrap.querySelectorAll(".pill.active").forEach(function (p) {
      activeTags[p.getAttribute("data-tag")] = true;
    });
    var shown = 0;
    cards.forEach(function (c) {
      var title = c.getAttribute("data-title") || "";
      var tags = (c.getAttribute("data-tags") || "").split("|");
      var matchQ = !q || title.indexOf(q) !== -1 || tags.join(" ").indexOf(q) !== -1;
      var matchT = true;
      for (var k in activeTags) {
        if (activeTags[k] && tags.indexOf(k) === -1) { matchT = false; break; }
      }
      var show = matchQ && matchT;
      c.style.display = show ? "" : "none";
      if (show) shown++;
    });
    if (none) none.hidden = shown !== 0;
  }

  if (search) search.addEventListener("input", apply);
  apply();
})();