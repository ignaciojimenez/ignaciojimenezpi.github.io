// Grid-aware image loader for optimized loading
class GridAwareImageLoader {
    constructor() {
        this.queue = [];
        this.loading = new Set();
        this.loaded = new Set();
        this.gridConfig = this.determineGridConfig();
        this.visibleRows = Math.ceil(window.innerHeight / 300); // Assuming average row height
    }

    determineGridConfig() {
        const width = window.innerWidth;
        if (width >= 1280) return 4;      // xl breakpoint
        if (width >= 1024) return 3;      // lg breakpoint
        if (width >= 640) return 2;       // sm breakpoint
        return 1;                         // mobile
    }

    prioritizeImages(albums) {
        const columnsInView = this.gridConfig;
        const itemsInView = columnsInView * this.visibleRows;
        
        return {
            critical: albums.slice(0, itemsInView),          // Visible in viewport
            high: albums.slice(itemsInView, itemsInView * 2),// Just below viewport
            normal: albums.slice(itemsInView * 2)            // Rest of the images
        };
    }

    async loadImage(album, { priority }) {
        if (this.loading.has(album.id) || this.loaded.has(album.id)) {
            return;
        }

        this.loading.add(album.id);
        
        // Find the existing card for this album
        const existingCard = document.querySelector(`[data-album-id="${album.id}"]`);
        if (!existingCard) {
            console.warn(`Card not found for album ${album.id}`);
            this.loading.delete(album.id);
            return;
        }

        // Update existing card's image with proper priority
        const container = existingCard.querySelector('.image-container');
        if (!container) return;

        const existingPicture = container.querySelector('picture');
        if (existingPicture) {
            const img = existingPicture.querySelector('img');
            if (img) {
                img.fetchPriority = priority;
                img.loading = priority === 'high' ? 'eager' : 'lazy';
                
                // Force reload the image with new priority
                const currentSrc = img.src;
                img.src = '';
                img.src = currentSrc;
            }
        }

        this.loading.delete(album.id);
        this.loaded.add(album.id);
    }

    async queueImagesWithPriority(priorities) {
        // Load critical items immediately (first viewport)
        await Promise.all(priorities.critical.map(item => 
            this.loadImage(item, { priority: 'high' })));

        // Queue high priority items (just below viewport)
        setTimeout(() => {
            priorities.high.forEach(item => 
                this.loadImage(item, { priority: 'medium' }));
        }, 100);

        // Queue normal priority items with delays
        priorities.normal.forEach((item, index) => {
            setTimeout(() => {
                this.loadImage(item, { priority: 'low' });
            }, 200 + (index * 100)); // Progressive delay
        });
    }
}

// Gallery loading and rendering functions
function createResponsivePicture(imagePath, title, metadata, albumId, priority = 'auto') {
    const picture = document.createElement('picture');
    
    // Base path for images
    const basePath = `/photography/albums/${albumId}`;
    
    // Add WebP sources with priority
    ['large', 'medium', 'small'].forEach(size => {
        const source = document.createElement('source');
        source.type = 'image/webp';
        source.srcset = `${basePath}/${imagePath}`; // Use the full path from JSON
        
        switch(size) {
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
    
    // Add image element
    const img = document.createElement('img');
    img.src = `${basePath}/${imagePath}`; // Use the full path from JSON
    img.alt = title;
    img.loading = priority === 'high' ? 'eager' : 'lazy';
    img.fetchPriority = priority;
    img.className = 'w-full h-full object-cover transition-opacity duration-300 opacity-0';
    
    if (metadata && metadata.sizes && metadata.sizes.medium) {
        img.width = metadata.sizes.medium.width;
        img.height = metadata.sizes.medium.height;
    }
    
    picture.appendChild(img);
    return picture;
}

function createAlbumCard(album, metadata, priority = 'auto') {
    const card = document.createElement('div');
    card.className = 'album-card opacity-0';
    card.setAttribute('data-album-id', album.id);
    
    const container = document.createElement('div');
    container.className = 'image-container relative group cursor-pointer aspect-[3/2]';
    
    // Add loading skeleton
    const skeleton = document.createElement('div');
    skeleton.className = 'absolute inset-0 bg-gray-200 animate-pulse';
    container.appendChild(skeleton);
    
    // Create responsive picture element with priority
    const picture = createResponsivePicture(
        album.coverImage.webp,
        album.title,
        metadata,
        album.id,
        priority
    );
    
    // Handle image load and error
    const imageElement = picture.querySelector('img');
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
        imageElement.classList.add('opacity-100');
        imageElement.classList.remove('opacity-0');
        card.classList.add('opacity-100');
    };
    
    const overlay = document.createElement('div');
    overlay.className = 'absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-60 transition-opacity duration-300 flex items-center justify-center';
    
    const content = document.createElement('div');
    content.className = 'text-white text-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 p-4';
    
    // Don't show date for favorite albums
    const dateStr = (album.favorite) ? '' : (album.date ? new Date(album.date).toLocaleDateString('en-US', { 
        year: 'numeric',
        month: 'long'
    }) : '');
    
    content.innerHTML = `
        <h3 class="text-xl font-semibold mb-2">${album.title}</h3>
        ${dateStr ? `<p class="text-sm mb-2">${dateStr}</p>` : ''}
        <p class="text-sm">${album.description || ''}</p>
    `;
    
    overlay.appendChild(content);
    container.appendChild(picture);
    container.appendChild(overlay);
    
    // Add mobile-specific metadata
    const mobileMetadata = document.createElement('div');
    mobileMetadata.className = 'album-metadata-mobile';
    
    // Don't show year for favorite albums
    const year = (album.favorite) ? '' : (album.date ? new Date(album.date).getFullYear() : '');
    mobileMetadata.innerHTML = `
        <h3>${year} ${album.title}</h3>
    `;
    container.appendChild(mobileMetadata);
    
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
    const albumGrid = document.getElementById('albumGrid');
    if (!albumGrid) {
        console.error('Album grid element not found');
        return;
    }
    
    // Add loading state
    albumGrid.innerHTML = '<div class="w-full text-center py-8"><div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div></div>';
    
    try {
        // Use the preloaded resource instead of making a new fetch
        const preloadLink = document.querySelector('link[rel="preload"][href$="albums.json"]');
        const albumsResponse = await fetch(preloadLink?.href || '/photography/albums/albums.json', {
            cache: 'force-cache'
        });
        
        if (!albumsResponse.ok) {
            throw new Error(`HTTP error! status: ${albumsResponse.status}`);
        }
        
        const albumsData = await albumsResponse.json();
        
        // Validate and extract albums array
        if (!albumsData.albums || !Array.isArray(albumsData.albums)) {
            throw new Error('Invalid album data format');
        }
        
        const albums = albumsData.albums;
        albumGrid.innerHTML = ''; // Clear loading spinner
        
        // Sort albums by special flag first, then by date (newest first)
        const sortedAlbums = [...albums].sort((a, b) => {
            // If album has a 'favorite' flag, it comes first
            if (a.favorite && !b.favorite) return -1;
            if (!a.favorite && b.favorite) return 1;
            
            // Otherwise sort by date (newest first)
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return dateB - dateA;
        });
        
        // Initialize grid-aware loader
        const loader = new GridAwareImageLoader();
        const priorities = loader.prioritizeImages(sortedAlbums);
        
        // Create all album cards with placeholders
        sortedAlbums.forEach(album => {
            const card = createAlbumCard(album, album.metadata);
            albumGrid.appendChild(card);
        });
        
        // Start loading images with priority
        await loader.queueImagesWithPriority(priorities);
        
    } catch (error) {
        console.error('Error loading albums:', error);
        albumGrid.innerHTML = '<div class="text-center text-red-600 py-8">Error loading albums</div>';
    }
}

// Initialize gallery when DOM is ready
document.addEventListener('DOMContentLoaded', initGallery);
