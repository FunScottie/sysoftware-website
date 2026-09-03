// HomePlus prototype — shared site chrome, navigation, reveal, and counters
(function () {
  const quoteUrl = "https://home-plus-mortgage.secure-clix.com/";
  const isProfile = window.location.pathname.includes("/team/");
  const root = isProfile ? "../" : "";

  // Keep repeated navigation/footer content consistent across every static page.
  const navLinks = document.querySelector(".nav-links");
  if (navLinks && !navLinks.querySelector('a[href$="team.html"]')) {
    const reviewsLink = navLinks.querySelector('a[href$="reviews.html"]');
    const teamLink = document.createElement("a");
    teamLink.href = root + "team.html";
    teamLink.textContent = "Our Team";
    reviewsLink ? navLinks.insertBefore(teamLink, reviewsLink) : navLinks.prepend(teamLink);
  }

  document.querySelectorAll("a").forEach((link) => {
    const label = link.textContent.trim().toLowerCase();
    const isMortgageAction = /quote|pre-approval|preapproved|pre-approved|check my rate|run my numbers|start here/.test(label);
    if (isMortgageAction && !link.closest(".team-card")) link.href = quoteUrl;
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
              <li><a href="${root}about-us.html">About Us</a></li>
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
    burger.addEventListener("click", () => {
      const open = links.classList.toggle("open");
      burger.setAttribute("aria-expanded", String(open));
      burger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
    links.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => {
      links.classList.remove("open");
      burger.setAttribute("aria-expanded", "false");
    }));
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
