// Endpoints page functionality: search and copy routes
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('endpoint-search');
    const cards = document.querySelectorAll('.endpoint-search-item');

    // Filter cards based on search input
    if (searchInput) {
        const filterCards = () => {
            const query = searchInput.value.trim().toLowerCase();
            cards.forEach(card => {
                const haystack = (card.dataset.search || '').toLowerCase();
                card.classList.toggle('hidden-card', query && !haystack.includes(query));
            });
        };

        searchInput.addEventListener('input', filterCards);
    }

    // Copy endpoint routes to clipboard
    document.querySelectorAll('.copy-endpoint').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const route = button.dataset.copy || '';
            try {
                await navigator.clipboard.writeText(route);
                const original = button.textContent;
                button.textContent = 'Copiado';
                setTimeout(() => { 
                    button.textContent = original; 
                }, 1200);
            } catch (error) {
                console.error('Failed to copy:', error);
                button.textContent = 'No se pudo copiar';
                setTimeout(() => { 
                    button.textContent = 'Copiar ruta'; 
                }, 1200);
            }
        });
    });
});

