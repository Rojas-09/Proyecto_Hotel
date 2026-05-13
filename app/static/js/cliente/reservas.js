/**
 * Mis Reservas - Client JS
 */

document.addEventListener('DOMContentLoaded', async () => {
    const { token } = getAuth();
    if (!token) {
        window.location.href = '/login';
        return;
    }

    try {
        const data = await apiRequest('/api/v1/reservas/mis-reservas');
        renderReservas(data.data || []);
    } catch {
        /* show empty state */
    }
});

function renderReservas(reservas) {
    const container = document.getElementById('reservas-list');
    if (!reservas.length) return;

    const grid = document.createElement('div');
    grid.className = 'reservas-grid';

    reservas.forEach(r => {
        const statusClass = r.estado === 'confirmada' ? 'status-confirmada'
                          : r.estado === 'cancelada' ? 'status-cancelada'
                          : r.estado === 'completada' ? 'status-completada'
                          : 'status-pendiente';

        grid.innerHTML += `
            <article class="reserva-card" data-reveal>
                <img src="https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=200&q=80" alt="Habitación">
                <div class="reserva-meta">
                    <span>${r.habitacion_tipo || 'Habitación'} · #${r.habitacion_numero || '—'}</span>
                    <h3>Reserva #${r.id}</h3>
                    <span>${r.fecha_entrada} → ${r.fecha_salida}</span>
                </div>
                <span class="reserva-status ${statusClass}">${r.estado}</span>
            </article>
        `;
    });

    container.innerHTML = '';
    container.appendChild(grid);
}
