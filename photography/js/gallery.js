// Gallery loading and rendering functions
function renderAlbums(albums) {
    const albumGrid = document.getElementById('albumGrid');
    
    // Create intersection observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add visible class after a small delay to ensure CSS transition works
                setTimeout(() => {
                    entry.target.classList.add('visible');
                }, 100);
                observer.unobserve(entry.target); // Stop observing once visible
            }
        });
    }, {
        root: null,
        rootMargin: '50px', // Start loading slightly before they come into view
        threshold: 0.1
    });

    albums.forEach(album => {
        const card = document.createElement('div');
        card.className = 'album-item';
        
        const container = document.createElement('div');
        container.className = 'image-container relative group cursor-pointer';
        
        const img = document.createElement('img');
        img.src = album.coverImage;
        img.alt = album.title;
        img.loading = 'lazy';
        img.className = 'w-full h-full object-cover';
        
        img.onload = () => {
            // Remove loaded class and let intersection observer handle visibility
            observer.observe(card);
        };
        
        const overlay = document.createElement('div');
        overlay.className = 'absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-60 transition-opacity duration-300 flex items-center justify-center';
        
        const content = document.createElement('div');
        content.className = 'text-white text-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 p-4';
        
        const dateStr = album.date ? new Date(album.date).toLocaleDateString('en-US', { 
            year: 'numeric',
            month: 'long'
        }) : '';
        
        content.innerHTML = `
            <h3 class="text-xl font-semibold mb-2">${album.title}</h3>
            ${dateStr ? `<p class="text-sm mb-2">${dateStr}</p>` : ''}
            <p class="text-sm">${album.description || ''}</p>
        `;
        
        overlay.appendChild(content);
        container.appendChild(img);
        container.appendChild(overlay);
        card.appendChild(container);

        card.addEventListener('click', () => {
            window.location.href = `albums/${album.id}`;
        });

        albumGrid.appendChild(card);
    });
}

// Initialize gallery
function initGallery() {
    fetch('albums/albums.json')
        .then(response => response.json())
        .then(data => {
            // Sort albums by date (newest first)
            data.albums.sort((a, b) => new Date(b.date) - new Date(a.date));
            renderAlbums(data.albums);
        })
        .catch(error => {
            console.error('Error loading albums:', error);
            const albumGrid = document.getElementById('albumGrid');
            albumGrid.innerHTML = '<p class="text-red-500">Error loading albums</p>';
        });
}
