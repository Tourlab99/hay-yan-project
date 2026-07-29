// Point this at wherever backend/app.py is running.
// Same-origin deployment (Flask serving these files itself) can leave this as an empty string.
const API_BASE = '';

document.addEventListener('DOMContentLoaded', () => {

    // Handle tour filter search form redirect (used on index.html and tours.html)
    const filterForm = document.getElementById('tour-filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', (e) => {
            e.preventDefault();

            const date = document.getElementById('filter-date').value;
            const type = document.getElementById('filter-type').value;
            const difficulty = document.getElementById('filter-difficulty').value;

            const params = new URLSearchParams({ date, type, difficulty });
            window.location.href = `tours.html?${params.toString()}`;
        });
    }

    // On tours.html: read ?id= from the URL and highlight / scroll to that tour
    const tourId = new URLSearchParams(window.location.search).get('id');
    if (tourId) {
        const card = document.querySelector(`[data-tour-id="${tourId}"]`);
        if (card) {
            card.classList.add('highlight');
            setTimeout(() => card.scrollIntoView({ behavior: 'smooth', block: 'center' }), 200);
        }
    }

    // Handle newsletter subscription (footer, on every page)
    const newsletterForm = document.getElementById('newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const emailInput = newsletterForm.querySelector('input[type="email"]');
            const email = emailInput ? emailInput.value : '';
            if (!email) return;

            try {
                await fetch(`${API_BASE}/api/newsletter`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, page: window.location.pathname })
                });
            } catch (err) {
                console.error('Newsletter signup failed to reach the server:', err);
            }

            alert(`Շնորհակալություն! Ապագա ուխտագնացությունների մասին կտեղեկացնենք ${email} հասցեին:`);
            emailInput.value = '';
        });
    }

    // Trailer button click handler (home hero)
    const trailerBtn = document.querySelector('.hero-trailer-btn');
    if (trailerBtn) {
        trailerBtn.addEventListener('click', () => {
            alert('Երթուղու տեսանյութը բացվում է...');
        });
    }

    // Contact page form
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        // Pre-fill message if arriving from a "Book This Tour" link
        const interest = new URLSearchParams(window.location.search).get('interest');
        const messageField = document.getElementById('contact-message');
        if (interest && messageField && !messageField.value) {
            messageField.value = `Ես հետաքրքրված եմ «${interest}» ուխտագնացությամբ: Խնդրում եմ ինձ ավելի շատ տեղեկություններ ուղարկել:`;
        }

        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nameField = document.getElementById('contact-name');
            const emailField = document.getElementById('contact-email');
            const name = nameField ? nameField.value : '';
            const email = emailField ? emailField.value : '';
            const message = messageField ? messageField.value : '';

            const submitBtn = contactForm.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.disabled = true;

            try {
                const res = await fetch(`${API_BASE}/api/contact`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, message, interest: interest || null })
                });
                if (!res.ok) throw new Error('Server responded with an error');

                alert(`Շնորհակալություն, ${name || 'ուխտավոր'}! Ձեր հաղորդագրությունը ուղարկվեց, մենք շուտով կպատասխանենք:`);
                contactForm.reset();
            } catch (err) {
                console.error('Contact form failed to reach the server:', err);
                alert('Չհաջողվեց ուղարկել հաղորդագրությունը: Խնդրում ենք փորձել կրկին կամ զանգահարել մեզ ուղղակիորեն:');
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    }

    // Highlight the active nav link based on current page
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-links a').forEach((link) => {
        const linkPage = link.getAttribute('href').split('?')[0];
        if (linkPage === currentPage) {
            link.classList.add('active');
        }
    });

});
