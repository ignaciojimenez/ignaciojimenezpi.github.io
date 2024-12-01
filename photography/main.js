// Load albums from albums.json and create the gallery grid
document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('Loading albums...');
        // Fetch albums data
        const response = await fetch('albums/albums.json');
        const data = await response.json();
        console.log('Albums data:', data);
        
        // Get the gallery container
        const galleryContainer = document.getElementById('gallery');
        if (!galleryContainer) {
            console.error('Gallery container not found');
            return;
        }

        // Create and append album cards
        data.albums.forEach(album => {
            console.log('Creating card for album:', album);
            const albumCard = createAlbumCard(album);
            galleryContainer.appendChild(albumCard);
        });

        // Initialize image loading
        const images = document.querySelectorAll('.gallery-item img');
        images.forEach(img => {
            if (img.complete) {
                handleImageLoad(img);
            } else {
                img.addEventListener('load', () => handleImageLoad(img));
            }
            img.addEventListener('error', handleImageError);
        });

    } catch (error) {
        console.error('Error loading albums:', error);
    }
});

// Create an album card element
function createAlbumCard(album) {
    console.log('Creating album card with cover:', album.cover);
    
    const card = document.createElement('div');
    card.className = 'gallery-item';
    
    const link = document.createElement('a');
    link.href = `albums/${album.id}/`;
    link.className = 'block';
    
    // Create image container
    const imageContainer = document.createElement('div');
    imageContainer.className = 'image-container';
    
    // Create placeholder
    const placeholder = document.createElement('div');
    placeholder.className = 'placeholder';
    placeholder.innerHTML = '<svg class="animate-spin h-8 w-8 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';
    imageContainer.appendChild(placeholder);
    
    // Create image element
    const img = document.createElement('img');
    img.alt = album.title;
    img.style.opacity = '0';
    img.style.transition = 'opacity 0.3s ease-in';
    img.src = album.cover;
    
    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'overlay';
    
    // Create title container
    const titleContainer = document.createElement('div');
    titleContainer.className = 'title-container';
    titleContainer.innerHTML = `
        <h3 class="text-lg font-medium">${album.title}</h3>
        <p class="text-sm opacity-90">${album.description}</p>
    `;

    // Assemble the card
    imageContainer.appendChild(img);
    imageContainer.appendChild(overlay);
    imageContainer.appendChild(titleContainer);
    link.appendChild(imageContainer);
    card.appendChild(link);
    
    return card;
}

// Handle image load
function handleImageLoad(img) {
    console.log('Image loaded:', img.src);
    img.style.opacity = '1';
    const card = img.closest('.gallery-item');
    if (card) {
        // Get image dimensions
        const aspectRatio = img.naturalWidth / img.naturalHeight;
        
        // Assign appropriate size class based on aspect ratio
        if (aspectRatio > 2) {
            card.classList.add('full');
        } else if (aspectRatio > 1.5) {
            card.classList.add('extra-wide');
        } else if (aspectRatio > 1) {
            card.classList.add('wide');
        }
        
        // Add loaded class for entrance animation
        setTimeout(() => {
            card.classList.add('loaded');
        }, 100);
        
        // Remove placeholder
        const placeholder = card.querySelector('.placeholder');
        if (placeholder) {
            placeholder.style.opacity = '0';
            setTimeout(() => {
                placeholder.remove();
            }, 300);
        }
    }
}

// Handle image error
function handleImageError(img) {
    console.error('Failed to load image:', img.src);
    const placeholder = img.parentElement.querySelector('.placeholder');
    if (placeholder) {
        placeholder.innerHTML = '<span class="text-red-500">Failed to load image</span>';
    }
}

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', () => {
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
});
