// Gallery loading and rendering functions
function createResponsivePicture(imagePath, title, metadata) {
    const picture = document.createElement('picture');
    
    // Get album name and filename from the path (e.g., "urban/images/modern-architecture.jpg")
    const parts = imagePath.split('/');
    const albumName = parts[0];  // e.g., "urban"
    const filename = parts[parts.length - 1];  // e.g., "modern-architecture.jpg"
    
    // Base path for responsive images
    const responsiveBasePath = `albums/${albumName}/responsive`;
    
    // Add WebP sources
    ['xlarge', 'large', 'medium', 'small'].forEach(size => {
        const source = document.createElement('source');
        source.type = 'image/webp';
        source.srcset = `${responsiveBasePath}/${size}/${filename.replace('.jpg', '.webp')}`;
        
        switch(size) {
            case 'xlarge':
                source.media = '(min-width: 1600px)';
                break;
            case 'large':
                source.media = '(min-width: 1200px)';
                break;
            case 'medium':
                source.media = '(min-width: 800px)';
                break;
            default:
                source.media = '(max-width: 799px)';
        }
        picture.appendChild(source);
    });
    
    // Add JPEG sources
    ['xlarge', 'large', 'medium', 'small'].forEach(size => {
        const source = document.createElement('source');
        source.srcset = `${responsiveBasePath}/${size}/${filename}`;
        
        switch(size) {
            case 'xlarge':
                source.media = '(min-width: 1600px)';
                break;
            case 'large':
                source.media = '(min-width: 1200px)';
                break;
            case 'medium':
                source.media = '(min-width: 800px)';
                break;
            default:
                source.media = '(max-width: 799px)';
        }
        picture.appendChild(source);
    });
    
    // Add fallback image
    const img = document.createElement('img');
    img.src = `albums/${imagePath}`;
    img.alt = title;
    img.loading = 'lazy';
    img.className = 'w-full h-full object-cover transition-opacity duration-300 opacity-0';
    
    // Use medium size dimensions from metadata if available
    if (metadata && metadata.responsive && metadata.responsive.medium) {
        img.width = metadata.responsive.medium.width;
        img.height = metadata.responsive.medium.height;
    } else if (metadata && metadata.original) {
        // Fallback to original dimensions
        img.width = metadata.original.width;
        img.height = metadata.original.height;
    }
    
    picture.appendChild(img);
    return picture;
}

function createImage(imagePath, title) {
    const img = document.createElement('img');
    img.src = `albums/${imagePath}`; // Add albums prefix
    img.alt = title;
    img.loading = 'lazy';
    img.className = 'w-full h-full object-cover transition-opacity duration-300 opacity-0';
    return img;
}

function createAlbumCard(album, metadata) {
    const card = document.createElement('div');
    card.className = 'album-item';
    
    const container = document.createElement('div');
    container.className = 'image-container relative group cursor-pointer';
    
    // Add loading skeleton
    const skeleton = document.createElement('div');
    skeleton.className = 'absolute inset-0 bg-gray-200 animate-pulse';
    container.appendChild(skeleton);
    
    // Create responsive picture element
    const picture = createResponsivePicture(
        album.coverImage,
        album.title,
        metadata
    );
    
    // Create fallback image
    const img = createImage(album.coverImage, album.title);
    
    // Handle image load and error
    const imageElement = picture.querySelector('img') || img;
    imageElement.onerror = () => {
        console.error('Image failed to load:', imageElement.src);
        skeleton.classList.remove('animate-pulse');
        skeleton.classList.add('bg-gray-300');
        const errorText = document.createElement('div');
        errorText.className = 'absolute inset-0 flex items-center justify-center text-gray-500';
        errorText.textContent = 'Image not available';
        container.appendChild(errorText);
    };
    
    imageElement.onload = () => {
        skeleton.remove();
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target.querySelector('img');
                    if (img) {
                        img.classList.add('opacity-100');
                        img.classList.remove('opacity-0');
                    }
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            root: null,
            rootMargin: '50px',
            threshold: [0, 0.1, 0.5, 1]
        });
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
    container.appendChild(picture || img);
    container.appendChild(overlay);
    card.appendChild(container);

    // Add keyboard navigation
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', '0');
    card.addEventListener('click', () => {
        window.location.href = `/photography/albums/${album.id}`;
    });
    card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            window.location.href = `/photography/albums/${album.id}`;
        }
    });

    return card;
}

async function initGallery() {
    console.log('initGallery');
    const albumGrid = document.getElementById('albumGrid');
    if (!albumGrid) {
        console.error('Album grid element not found');
        return;
    }
    
    // Add loading state
    albumGrid.innerHTML = '<div class="w-full text-center py-8"><div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div></div>';
    
    try {
        // Fetch albums data
        const albumsResponse = await fetch('/photography/albums/albums.json');
        if (!albumsResponse.ok) {
            throw new Error(`HTTP error! status: ${albumsResponse.status}`);
        }
        const albumsData = await albumsResponse.json();
        
        // Validate albums data
        if (!albumsData.albums || !Array.isArray(albumsData.albums)) {
            throw new Error('Invalid album data format');
        }
        
        // Try to fetch metadata for each album
        const metadataMap = new Map();
        for (const album of albumsData.albums) {
            try {
                const metadataResponse = await fetch(`/photography/albums/${album.id}/metadata.json`);
                if (metadataResponse.ok) {
                    const metadata = await metadataResponse.json();
                    metadataMap.set(album.id, metadata);
                }
            } catch (error) {
                console.warn(`Could not load metadata for album ${album.id}:`, error);
            }
        }
        
        // Sort albums by date if available
        if (albumsData.albums.some(album => album.date)) {
            albumsData.albums.sort((a, b) => {
                if (!a.date) return 1;
                if (!b.date) return -1;
                return new Date(b.date) - new Date(a.date);
            });
        }
        
        // Clear loading state
        albumGrid.innerHTML = '';
        
        // Render albums
        albumsData.albums.forEach(album => {
            const albumMetadata = metadataMap.get(album.id);
            // If we have metadata for this album, get the cover image metadata
            const coverImageMetadata = albumMetadata ? albumMetadata[album.coverImage.split('/').pop()] : null;
            const card = createAlbumCard(album, coverImageMetadata);
            albumGrid.appendChild(card);
        });
        
    } catch (error) {
        console.error('Error loading gallery:', error);
        albumGrid.innerHTML = `
            <div class="w-full text-center py-8 text-red-600">
                <p>Error loading gallery: ${error.message}</p>
                <button onclick="initGallery()" class="mt-4 px-4 py-2 bg-gray-200 rounded hover:bg-gray-300">
                    Retry
                </button>
            </div>
        `;
    }
}

// Initialize gallery when DOM is ready
document.addEventListener('DOMContentLoaded', initGallery);
