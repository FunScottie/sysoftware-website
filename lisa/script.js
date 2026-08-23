// TODO: replace with Lisa's real inbox before treating inquiries as live.
const LISA_CONTACT_EMAIL = 'REPLACE-WITH-LISAS-EMAIL@example.com';

const menuButton = document.querySelector('[data-menu-button]');
const navigation = document.querySelector('[data-nav]');
const header = document.querySelector('[data-header]');
const prototypeForm = document.querySelector('[data-prototype-form]');
const formStatus = document.querySelector('[data-form-status]');

function closeMenu() {
  if (!menuButton || !navigation) return;
  menuButton.setAttribute('aria-expanded', 'false');
  navigation.classList.remove('is-open');
  document.body.classList.remove('menu-open');
}

if (menuButton && navigation) {
  menuButton.addEventListener('click', () => {
    const isOpen = menuButton.getAttribute('aria-expanded') === 'true';
    menuButton.setAttribute('aria-expanded', String(!isOpen));
    navigation.classList.toggle('is-open', !isOpen);
    document.body.classList.toggle('menu-open', !isOpen);
  });

  navigation.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
  });
}

function updateHeader() {
  header?.classList.toggle('is-scrolled', window.scrollY > 8);
}

updateHeader();
window.addEventListener('scroll', updateHeader, { passive: true });

prototypeForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  const data = new FormData(prototypeForm);
  const name = data.get('name')?.toString().trim() || '';
  const contact = data.get('contact')?.toString().trim() || '';
  const helpFor = data.get('help-for')?.toString().trim() || '';
  const message = data.get('message')?.toString().trim() || '';

  const subject = `Here With Lisa — inquiry from ${name || 'a website visitor'}`;
  const body = [
    `Name: ${name}`,
    `Best way to reach them: ${contact}`,
    `Looking for help for: ${helpFor}`,
    '',
    message || '(no additional details provided)',
  ].join('\n');

  const mailtoUrl = `mailto:${LISA_CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

  formStatus.textContent = `Thanks${name ? `, ${name}` : ''} — opening an email to Lisa with your details. Prefer to talk right now? Call or text (619) 376-5343.`;
  window.location.href = mailtoUrl;
});

document.querySelectorAll('[data-year]').forEach((element) => {
  element.textContent = new Date().getFullYear();
});
