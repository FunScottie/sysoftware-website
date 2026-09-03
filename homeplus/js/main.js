// HomePlus prototype — shared site chrome, navigation, reveal, and counters
(function () {
  const quoteUrl = "https://home-plus-mortgage.secure-clix.com/";
  const isProfile = window.location.pathname.includes("/team/");
  const root = isProfile ? "../" : "";
  const page = window.location.pathname.split("/").pop() || "index.html";

  // Keep repeated navigation/footer content consistent across every static page.
  const navLinks = document.querySelector(".nav-links");
  if (navLinks) {
    const loanPages = ["buy-a-home.html", "refinance.html", "loan-options.html", "compare-rates.html"];
    const companyPages = ["why-homeplus.html", "about-us.html", "team.html", "reviews.html", "contact.html"];
    const active = (pages) => (pages.includes(page) || (isProfile && pages.includes("team.html"))) ? " active" : "";
    const item = (href, label, pages = [href]) =>
      `<a class="nav-dropdown-link${active(pages)}" href="${root}${href}">${label}</a>`;

    navLinks.setAttribute("aria-label", "Primary navigation");
    navLinks.innerHTML = `
      <div class="nav-group">
        <button class="nav-group-trigger${active(loanPages)}" type="button" aria-expanded="false">
          <span>Loans</span><i aria-hidden="true"></i>
        </button>
        <div class="nav-dropdown" aria-label="Loans">
          ${item("buy-a-home.html", "Buy a Home")}
          ${item("refinance.html", "Refinance")}
          ${item("loan-options.html", "Loan Options")}
          ${item("compare-rates.html", "Compare Rates")}
        </div>
      </div>
      <a class="nav-primary-link${active(["resources.html"])}" href="${root}resources.html">Resources</a>
      <div class="nav-group">
        <button class="nav-group-trigger${active(companyPages)}" type="button" aria-expanded="false">
          <span>About Us</span><i aria-hidden="true"></i>
        </button>
        <div class="nav-dropdown" aria-label="About Us">
          ${item("about-us.html", "Company Information")}
          ${item("why-homeplus.html", "Why HomePlus")}
          ${item("team.html", "Our Team")}
          ${item("reviews.html", "Reviews")}
          ${item("contact.html", "Contact")}
        </div>
      </div>
      <a class="nav-quote-link" href="${quoteUrl}">Get a Free Quote</a>
      <a class="nav-phone" href="tel:8008107587">800.810.PLUS</a>
      <a class="nav-join-cta${active(["join-the-team.html"])}" href="${root}join-the-team.html">
        <span>Join the Team</span><span class="nav-join-arrow" aria-hidden="true">→</span>
      </a>`;
  }

  document.querySelectorAll("a").forEach((link) => {
    const label = link.textContent.trim().toLowerCase();
    const href = link.getAttribute("href") || "";
    const isMortgageAction = /quote|pre-approval|preapproved|pre-approved|check my rate|run my numbers|start here/.test(label);
    if (isMortgageAction && !href.startsWith("#") && !link.closest(".team-card")) link.href = quoteUrl;
  });

  const footer = document.querySelector(".footer");
  if (footer) {
    footer.innerHTML = `
      <div class="wrap">
        <div class="footer-mission">
          <img class="f-logo" src="${root}assets/logo_white.png" alt="HomePlus Mortgage" />
          <p>Our mission is to provide our customers with the highest level of customer service and a competitive mortgage rate and term.</p>
        </div>
        <div class="footer-top">
          <div>
            <h4>Corporate Headquarters</h4>
            <p>HomePlus Corporation<br />9655 Granite Ridge Drive, Suite 200<br />San Diego, CA 92123</p>
          </div>
          <div>
            <h4>Contact</h4>
            <ul>
              <li><a href="tel:8008107587">800-810-PLUS (7587)</a></li>
              <li><a href="tel:6193258282">619-325-8282</a></li>
              <li>Fax: 800-378-6031</li>
              <li><a href="mailto:approvaldept@homeplusmortgage.com">approvaldept@homeplusmortgage.com</a></li>
            </ul>
          </div>
          <div>
            <h4>Loans</h4>
            <ul>
              <li><a href="${root}buy-a-home.html">Buy a Home</a></li>
              <li><a href="${root}refinance.html">Refinance</a></li>
              <li><a href="${root}loan-options.html">Loan Options</a></li>
              <li><a href="${root}compare-rates.html">Compare Rates</a></li>
              <li><a href="${root}resources.html">Resources</a></li>
            </ul>
          </div>
          <div>
            <h4>Company</h4>
            <ul>
              <li><a href="${root}about-us.html">Company Information</a></li>
              <li><a href="${root}team.html">Our Team</a></li>
              <li><a href="${root}reviews.html">Reviews</a></li>
              <li><a href="${root}join-the-team.html">Join the Team</a></li>
              <li><a href="${root}contact.html">Contact</a></li>
            </ul>
          </div>
        </div>
        <div class="footer-legal">
          <p>© ${new Date().getFullYear()} HomePlus Corporation dba HomePlus Mortgage · NMLS 78669 · Real Estate Broker, CA DRE License #01426454</p>
          <div class="footer-legal-links">
            <a href="https://www.nmlsconsumeraccess.org" target="_blank" rel="noopener">NMLS Consumer Access</a>
            <a href="https://homeplusmortgage.com/legal/" target="_blank" rel="noopener">State &amp; Federal Disclosures / Licenses</a>
            <a href="https://homeplusmortgage.com/privacy-policy/" target="_blank" rel="noopener">Privacy Policy</a>
            <a href="https://homeplusmortgage.com/wp-content/uploads/2018/01/Consumer-Complaint-and-Recovery-Fund-Notice.pdf" target="_blank" rel="noopener">Texas Complaint / Recovery Fund Notice</a>
          </div>
          <div class="ehl" aria-label="Equal Housing Lender">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 1 10h2v12h7v-7h4v7h7V10h2L12 2zm0 5.7 4.5 3.3H7.5L12 7.7zM8.2 12.5h7.6v1.6H8.2v-1.6zm0 3h7.6v1.6H8.2v-1.6z"/></svg>
            HOMEPLUS CORPORATION IS AN EQUAL HOUSING LENDER
          </div>
        </div>
      </div>`;
  }

  // sticky nav
  const nav = document.querySelector(".nav");
  const onScroll = () => nav && nav.classList.toggle("scrolled", window.scrollY > 24 || document.body.classList.contains("team-site"));
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // mobile menu
  const burger = document.querySelector(".nav-burger");
  const links = document.querySelector(".nav-links");
  if (burger && links) {
    const groups = [...links.querySelectorAll(".nav-group")];
    const closeGroups = (except) => groups.forEach((group) => {
      if (group === except) return;
      group.classList.remove("open");
      group.querySelector(".nav-group-trigger")?.setAttribute("aria-expanded", "false");
    });

    groups.forEach((group) => {
      const trigger = group.querySelector(".nav-group-trigger");
      trigger?.addEventListener("click", () => {
        const open = !group.classList.contains("open");
        closeGroups(group);
        group.classList.toggle("open", open);
        trigger.setAttribute("aria-expanded", String(open));
      });
    });

    burger.addEventListener("click", () => {
      const open = links.classList.toggle("open");
      document.body.classList.toggle("menu-open", open);
      burger.setAttribute("aria-expanded", String(open));
      burger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      if (!open) closeGroups();
    });
    links.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => {
      links.classList.remove("open");
      document.body.classList.remove("menu-open");
      burger.setAttribute("aria-expanded", "false");
      burger.setAttribute("aria-label", "Open menu");
      closeGroups();
    }));

    document.addEventListener("click", (event) => {
      if (!links.contains(event.target) && event.target !== burger) closeGroups();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      closeGroups();
      links.classList.remove("open");
      document.body.classList.remove("menu-open");
      burger.setAttribute("aria-expanded", "false");
      burger.setAttribute("aria-label", "Open menu");
    });
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
