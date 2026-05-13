/**
 * Home Page JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    /* Reveal animations */
    const reveals = document.querySelectorAll('[data-reveal]');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    reveals.forEach(el => observer.observe(el));

    /* Search: min date = today */
    const checkin = document.querySelector('input[name="fecha_entrada"]');
    const checkout = document.querySelector('input[name="fecha_salida"]');
    if (checkin) {
        checkin.min = new Date().toISOString().split('T')[0];
        checkin.addEventListener('change', () => {
            if (checkout) checkout.min = checkin.value;
        });
    }

    /* Smooth scroll for hero CTA */
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', e => {
            const target = document.querySelector(anchor.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});
