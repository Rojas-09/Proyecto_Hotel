/**
 * HotelBook Pro - Global JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    /* Reveal animations via IntersectionObserver */
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

    /* Navbar scroll behavior */
    const nav = document.querySelector('.main-nav');
    if (nav) {
        const onScroll = () => {
            nav.classList.toggle('scrolled', window.scrollY > 60);
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    /* Mobile menu toggle */
    const toggle = document.getElementById('mobile-toggle');
    const menu = document.getElementById('nav-menu');
    const icon = toggle?.querySelector('i');
    if (toggle && menu) {
        toggle.addEventListener('click', () => {
            menu.classList.toggle('active');
            icon?.classList.toggle('ti-menu-deep');
            icon?.classList.toggle('ti-x');
            document.body.style.overflow = menu.classList.contains('active') ? 'hidden' : 'auto';
        });
        menu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                menu.classList.remove('active');
                icon?.classList.add('ti-menu-deep');
                icon?.classList.remove('ti-x');
                document.body.style.overflow = 'auto';
            });
        });
    }
});

/* Utility: format COP currency */
const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
    }).format(value);
};

/* Utility: show inline error under a form field */
const showFieldError = (input, message) => {
    const existing = input.parentElement.querySelector('.field-error');
    if (existing) existing.remove();
    const err = document.createElement('span');
    err.className = 'field-error';
    err.style.cssText = 'color: #dc2626; font-size: 0.75rem; margin-top: 0.25rem; display: block;';
    err.textContent = message;
    input.parentElement.appendChild(err);
};

const clearFieldError = (input) => {
    const existing = input.parentElement.querySelector('.field-error');
    if (existing) existing.remove();
};

/* Utility: call API and handle response */
const apiRequest = async (url, options = {}) => {
    const token = localStorage.getItem('token');
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(url, { ...options, headers });
    const data = await res.json();

    if (!res.ok) {
        const msg = data?.error?.message || data?.message || 'Error desconocido';
        throw new Error(msg);
    }
    return data;
};

/* Store JWT from login response */
const storeAuth = (data) => {
    localStorage.setItem('token', data.data.token);
    localStorage.setItem('usuario', JSON.stringify(data.data.usuario));
};

const clearAuth = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
};

const getAuth = () => {
    const token = localStorage.getItem('token');
    const usuario = localStorage.getItem('usuario');
    return { token, usuario: usuario ? JSON.parse(usuario) : null };
};
