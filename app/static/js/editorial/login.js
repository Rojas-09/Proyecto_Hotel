/**
 * Login / Register Page Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    /* Tab switching */
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const formLogin = document.getElementById('form-login');
    const formRegister = document.getElementById('form-register');

    window.switchAuthTab = (tab) => {
        if (tab === 'login') {
            tabLogin.classList.add('active');
            tabRegister.classList.remove('active');
            formLogin.style.display = 'block';
            formRegister.style.display = 'none';
        } else {
            tabRegister.classList.add('active');
            tabLogin.classList.remove('active');
            formRegister.style.display = 'block';
            formLogin.style.display = 'none';
        }
    };

    /* Login form submission */
    const loginForm = document.getElementById('form-login');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = loginForm.querySelector('input[type="email"]').value.trim();
            const password = loginForm.querySelector('input[type="password"]').value;

            try {
                const data = await apiRequest('/api/v1/auth/login', {
                    method: 'POST',
                    body: JSON.stringify({ email, password }),
                });

                if (data.success) {
                    storeAuth(data);
                    const rol = data.data.usuario.rol;
                    if (rol === 'admin' || rol === 'gerente') {
                        window.location.href = '/admin/dashboard';
                    } else if (rol === 'recepcionista') {
                        window.location.href = '/recepcionista/dashboard';
                    } else {
                        window.location.href = '/mis-reservas';
                    }
                }
            } catch (err) {
                alert(err.message);
            }
        });
    }

    /* Register form submission */
    const registerForm = document.getElementById('form-register');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const inputs = registerForm.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]');
            const nombre = inputs[0].value.trim();
            const email = inputs[1].value.trim();
            const password = inputs[2].value;

            if (password.length < 8) {
                alert('La contraseña debe tener al menos 8 caracteres.');
                return;
            }

            try {
                const data = await apiRequest('/api/v1/auth/register', {
                    method: 'POST',
                    body: JSON.stringify({ nombre, email, password, rol: 'cliente' }),
                });

                if (data.success) {
                    storeAuth(data);
                    window.location.href = '/mis-reservas';
                }
            } catch (err) {
                alert(err.message);
            }
        });
    }
});
