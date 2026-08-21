// HomePlus prototype — nav, reveal, counters
(function () {
  // sticky nav
  const nav = document.querySelector(".nav");
  const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 24);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // mobile menu
  const burger = document.querySelector(".nav-burger");
  const links = document.querySelector(".nav-links");
  if (burger) {
    burger.addEventListener("click", () => links.classList.toggle("open"));
    links.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => links.classList.remove("open")));
  }

  // reveal on scroll
  const io = new IntersectionObserver(
    (entries) => entries.forEach((e) => e.isIntersecting && e.target.classList.add("in")),
    { threshold: 0.12 }
  );
  document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

  // animated counters
  const ease = (t) => 1 - Math.pow(1 - t, 3);
  const animate = (el) => {
    const target = parseFloat(el.dataset.count);
    const decimals = (el.dataset.count.split(".")[1] || "").length;
    const prefix = el.dataset.prefix || "";
    const suffix = el.dataset.suffix || "";
    const dur = 1400;
    const t0 = performance.now();
    const tick = (now) => {
      const p = Math.min(1, (now - t0) / dur);
      const v = (target * ease(p)).toFixed(decimals);
      el.textContent = prefix + Number(v).toLocaleString(undefined, { minimumFractionDigits: decimals }) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };
  const cio = new IntersectionObserver(
    (entries) =>
      entries.forEach((e) => {
        if (e.isIntersecting) {
          animate(e.target);
          cio.unobserve(e.target);
        }
      }),
    { threshold: 0.6 }
  );
  document.querySelectorAll("[data-count]").forEach((el) => cio.observe(el));
})();
