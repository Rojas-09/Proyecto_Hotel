/**
 * HotelBook Pro — API Client
 * Fetch wrapper con JWT (sessionStorage) + CSRF + manejo de errores 401/403.
 * No usa localStorage (XSS safety). No almacena datos sensibles en global vars.
 */

(function () {
    "use strict";

    const TOKEN_KEY = "hbp_token";
    const API_BASE = "";

    // ─── Token management ─────────────────────────────────────────────────────

    function getToken() {
        return sessionStorage.getItem(TOKEN_KEY);
    }

    function setToken(token) {
        sessionStorage.setItem(TOKEN_KEY, token);
    }

    function removeToken() {
        sessionStorage.removeItem(TOKEN_KEY);
    }

    window.HotelBookAPI = {
        isAuthenticated() {
            return !!getToken();
        },

        logout() {
            removeToken();
            sessionStorage.clear();
            window.location.href = "/logout";
        },

        // ─── Core fetch ────────────────────────────────────────────────────────

        async request(method, url, body = null, options = {}) {
            const token = getToken();
            const headers = { "Content-Type": "application/json" };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            // CSRF: enviar token si existe en la sesión
            const csrfEl = document.querySelector('meta[name="csrf-token"]');
            if (csrfEl) {
                headers["X-CSRF-Token"] = csrfEl.getAttribute("content");
            }

            const config = { method, headers, ...options };

            if (body && method !== "GET") {
                config.body = JSON.stringify(body);
            }

            let response;
            try {
                response = await fetch(API_BASE + url, config);
            } catch (err) {
                throw new Error("No se pudo conectar al servidor. Verifica tu conexión.");
            }

            // Manejo global de errores de autenticación
            if (response.status === 401) {
                removeToken();
                window.location.href = "/login?expired=1";
                throw new Error("Sesión expirada. Redirigiendo al login...");
            }

            if (response.status === 403) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data?.error?.message || "No tienes permisos para realizar esta acción.");
            }

            return response;
        },

        // ─── Convenience methods ───────────────────────────────────────────────

        async get(url) {
            const res = await this.request("GET", url);
            return res.json();
        },

        async post(url, body) {
            const res = await this.request("POST", url, body);
            return res.json();
        },

        async put(url, body) {
            const res = await this.request("PUT", url, body);
            return res.json();
        },

        async del(url, body = null) {
            const res = await this.request("DELETE", url, body);
            return res.json();
        },

        // ─── Auth ─────────────────────────────────────────────────────────────

        async login(email, password) {
            const data = await this.post("/api/v1/auth/login", { email, password });
            if (data.success && data.data?.token) {
                setToken(data.data.token);
            }
            return data;
        },

        async register(payload) {
            const data = await this.post("/api/v1/auth/register", payload);
            return data;
        },

        async getMe() {
            const data = await this.get("/api/v1/auth/me");
            return data;
        },

        // ─── Habitaciones ──────────────────────────────────────────────────────

        async getHabitaciones(params = {}) {
            const qs = new URLSearchParams(params).toString();
            return this.get(`/api/v1/habitaciones/${qs ? "?" + qs : ""}`);
        },

        async getHabitacion(id) {
            return this.get(`/api/v1/habitaciones/${id}`);
        },

        async getDisponibles(fechaEntrada, fechaSalida, tipo = null) {
            const params = new URLSearchParams({ fecha_entrada: fechaEntrada, fecha_salida: fechaSalida });
            if (tipo) params.set("tipo", tipo);
            return this.get(`/api/v1/habitaciones/disponibles?${params}`);
        },

        // ─── Reservas ─────────────────────────────────────────────────────────

        async getMisReservas() {
            return this.get("/api/v1/reservas/mis-reservas");
        },

        async getReserva(id) {
            return this.get(`/api/v1/reservas/${id}`);
        },

        async crearReserva(payload) {
            return this.post("/api/v1/reservas/", payload);
        },

        async confirmarReserva(id) {
            return this.put(`/api/v1/reservas/${id}/confirmar`, {});
        },

        async cancelarReserva(id, motivo = "") {
            return this.put(`/api/v1/reservas/${id}/cancelar`, { motivo });
        },

        async checkinReserva(id) {
            return this.put(`/api/v1/reservas/${id}/checkin`, {});
        },

        async checkoutReserva(id) {
            return this.put(`/api/v1/reservas/${id}/checkout`, {});
        },

        async getReservas(params = {}) {
            const qs = new URLSearchParams(params).toString();
            return this.get(`/api/v1/reservas/${qs ? "?" + qs : ""}`);
        },

        // ─── Pagos ────────────────────────────────────────────────────────────

        async procesarGarantia(reservaId, metodo) {
            return this.post(`/api/v1/pagos/garantia/${reservaId}`, { metodo });
        },

        async procesarLiquidacion(reservaId, metodo) {
            return this.post(`/api/v1/pagos/liquidacion/${reservaId}`, { metodo });
        },

        async getPagosReserva(reservaId) {
            return this.get(`/api/v1/pagos/reserva/${reservaId}`);
        },

        // ─── Huespedes ─────────────────────────────────────────────────────────

        async getHuespedes() {
            return this.get("/api/v1/huespedes/");
        },

        async buscarHuespedes(q) {
            return this.get(`/api/v1/huespedes/buscar?q=${encodeURIComponent(q)}`);
        },

        async getHuesped(id) {
            return this.get(`/api/v1/huespedes/${id}`);
        },

        // ─── Usuarios ──────────────────────────────────────────────────────────

        async getUsuarios(params = {}) {
            const qs = new URLSearchParams(params).toString();
            return this.get(`/api/v1/auth/usuarios${qs ? "?" + qs : ""}`);
        },

        async crearUsuario(payload) {
            return this.post("/api/v1/auth/usuarios", payload);
        },

        async editarUsuario(id, payload) {
            return this.put(`/api/v1/auth/usuarios/${id}`, payload);
        },

        async eliminarUsuario(id) {
            return this.del(`/api/v1/auth/usuarios/${id}`);
        },

        // ─── Reportes ─────────────────────────────────────────────────────────

        async getReporteOcupacion(fechaInicio, fechaFin) {
            return this.get(`/api/v1/reportes/ocupacion?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`);
        },

        async getReporteIngresos(fechaInicio, fechaFin) {
            return this.get(`/api/v1/reportes/ingresos?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`);
        },

        async descargarReporte(tipo, fechaInicio, fechaFin, formato = "xlsx") {
            const url = `/api/v1/reportes/${tipo}?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}&formato=${formato}`;
            const token = getToken();
            const res = await fetch(API_BASE + url, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) throw new Error("Error al descargar reporte.");
            const blob = await res.blob();
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `reporte_${tipo}_${fechaInicio}_${fechaFin}.${formato}`;
            a.click();
            URL.revokeObjectURL(a.href);
        },
    };

    // ─── Toast notifications ──────────────────────────────────────────────────

    window.showToast = function (message, type = "info") {
        let container = document.querySelector(".toast-container");
        if (!container) {
            container = document.createElement("div");
            container.className = "toast-container";
            document.body.appendChild(container);
        }
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    };

    // ─── Require auth helper ──────────────────────────────────────────────────

    window.requireAuth = function (roles = []) {
        const token = getToken();
        if (!token) {
            window.location.href = "/login";
            return false;
        }
        // Roles se validan contra el JWT payload (decodificado client-side)
        if (roles.length > 0) {
            try {
                const payload = JSON.parse(atob(token.split(".")[1]));
                if (!roles.includes(payload.rol)) {
                    window.location.href = "/";
                    return false;
                }
            } catch {
                window.location.href = "/login";
                return false;
            }
        }
        return true;
    };

    window.getUserRol = function () {
        const token = getToken();
        if (!token) return null;
        try {
            const payload = JSON.parse(atob(token.split(".")[1]));
            return payload.rol;
        } catch {
            return null;
        }
    };

    window.getUserId = function () {
        const token = getToken();
        if (!token) return null;
        try {
            const payload = JSON.parse(atob(token.split(".")[1]));
            return payload.user_id;
        } catch {
            return null;
        }
    };

    // ─── Form submit handler ──────────────────────────────────────────────────

    window.bindFormSubmit = function (formSelector, onSuccess, onError) {
        const form = document.querySelector(formSelector);
        if (!form) return;
        form.addEventListener("submit", async function (e) {
            e.preventDefault();
            const submitBtn = form.querySelector('[type="submit"]');
            const originalText = submitBtn ? submitBtn.textContent : "";
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner"></span> Procesando...';
            }
            try {
                const formData = new FormData(form);
                const payload = {};
                for (const [k, v] of formData.entries()) {
                    if (v !== "") payload[k] = v;
                }
                const result = await onSuccess(payload, form);
                if (result && result.redirect) {
                    window.location.href = result.redirect;
                }
            } catch (err) {
                if (onError) {
                    onError(err);
                } else {
                    window.showToast(err.message, "error");
                }
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }
            }
        });
    };

})();
