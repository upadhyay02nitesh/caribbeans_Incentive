/* MODULE 5 — Planning estimate.
   Must mirror content/pricing.py estimate():
     per_person = round(island_rate * nights * tier_multiplier * SERVICE_FEE + addon_total)
   Reference: Saint Martin, 60 pax, 4 nights, Premium, transfers+boat+gala+decor
   -> $1,958 per person / $117,480 total. */
(() => {
  const root = document.getElementById("estimator");
  const dataEl = document.getElementById("estimator-data");
  if (!root || !dataEl) return;

  const islandRate = JSON.parse(dataEl.textContent || "{}");
  const serviceFee = window.__SERVICE_FEE__ || 1;

  const islandSelect = document.getElementById("est-island");
  const islandLabel = document.getElementById("est-island-label");
  const paxRange = document.getElementById("est-pax");
  const paxLabel = document.getElementById("est-pax-label");
  const nightsRange = document.getElementById("est-nights");
  const nightsLabel = document.getElementById("est-nights-label");
  const tierSelect = document.getElementById("est-tier");
  const addonInputs = root.querySelectorAll("input[type=checkbox][data-key]");
  const totalEl = document.getElementById("est-total");
  const perPersonEl = document.getElementById("est-per-person");
  const sum = (id) => document.getElementById(id);
  const sumIsland = sum("est-sum-island"), sumPax = sum("est-sum-pax"), sumNights = sum("est-sum-nights");
  const sumTier = sum("est-sum-tier"), sumAddons = sum("est-sum-addons");

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fmt = (n) => `$${Math.round(n).toLocaleString("en-US")}`;

  let shownTotal = 0;
  let raf = null;

  const animateTotal = (to) => {
    cancelAnimationFrame(raf);
    const from = shownTotal;
    if (reduceMotion || from === to) {
      shownTotal = to;
      totalEl.textContent = fmt(to);
      return;
    }
    const start = performance.now();
    const duration = 600;
    const step = (now) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      shownTotal = from + (to - from) * eased;
      totalEl.textContent = fmt(shownTotal);
      if (p < 1) raf = requestAnimationFrame(step);
      else shownTotal = to;
    };
    raf = requestAnimationFrame(step);
  };

  const paintRange = (range) => {
    const min = Number(range.min), max = Number(range.max), val = Number(range.value);
    range.style.setProperty("--pct", `${((val - min) / (max - min)) * 100}%`);
  };

  const recalc = () => {
    const island = islandSelect.value;
    const rate = islandRate[island] ?? 0;
    const pax = Number(paxRange.value);
    const nights = Number(nightsRange.value);
    const tierOption = tierSelect.options[tierSelect.selectedIndex];
    const multiplier = Number(tierOption.dataset.multiplier);

    let addonTotal = 0;
    addonInputs.forEach((input) => {
      if (input.checked) addonTotal += Number(input.dataset.price);
    });

    const perPerson = Math.round(rate * nights * multiplier * serviceFee + addonTotal);
    const total = perPerson * pax;

    islandLabel.textContent = islandSelect.options[islandSelect.selectedIndex].text;
    paxLabel.textContent = `${pax} people`;
    nightsLabel.textContent = `${nights} nights`;
    perPersonEl.textContent = `≈ ${fmt(perPerson)} per person`;
    const picked = [...addonInputs].filter((i) => i.checked).length;
    if (sumIsland) sumIsland.textContent = islandLabel.textContent;
    if (sumPax) sumPax.textContent = `${pax} guests`;
    if (sumNights) sumNights.textContent = `${nights} nights`;
    if (sumTier) sumTier.textContent = tierOption.text.split(" — ")[0];
    if (sumAddons) sumAddons.textContent = picked ? `${picked} selected · +${fmt(addonTotal)}/pp` : "None";
    paintRange(paxRange);
    paintRange(nightsRange);

    animateTotal(total);
  };

  [islandSelect, paxRange, nightsRange, tierSelect].forEach((el) => {
    el.addEventListener("input", recalc);
    el.addEventListener("change", recalc);
  });
  addonInputs.forEach((el) => el.addEventListener("change", recalc));

  // Pill / card radios drive the (visually hidden) selects the maths reads.
  root.querySelectorAll("[data-drives]").forEach((group) => {
    const select = document.getElementById(group.dataset.drives);
    if (!select) return;
    group.addEventListener("change", (e) => {
      if (e.target.type !== "radio") return;
      select.value = e.target.value;
      select.dispatchEvent(new Event("change"));
    });
    const current = group.querySelector(`input[value="${select.value}"]`);
    if (current) current.checked = true;
  });

  recalc();
})();
