// Sample gallery images with varying sizes
const galleryImages = [
    {
        url: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e',
        alt: 'Nature Landscape',
        size: 'large'
    },
    {
        url: 'https://images.unsplash.com/photo-1447684808650-354ae64db5b8',
        alt: 'Mountain View',
        size: 'small'
    },
    {
        url: 'https://images.unsplash.com/photo-1433086966358-54859d0ed716',
        alt: 'Waterfall',
        size: 'medium'
    },
    {
        url: 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05',
        alt: 'Foggy Forest',
        size: 'large'
    },
    {
        url: 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e',
        alt: 'Forest Path',
        size: 'medium'
    },
    {
        url: 'https://images.unsplash.com/photo-1472214103451-9374bd1c798e',
        alt: 'Sunset',
        size: 'small'
    },
    {
        url: 'https://images.unsplash.com/photo-1542224566-6e85f2e6772f',
        alt: 'Mountain Lake',
        size: 'large'
    },
    {
        url: 'https://images.unsplash.com/photo-1505028106030-e07ea1bd80c3',
        alt: 'Desert',
        size: 'medium'
    },
    {
        url: 'https://images.unsplash.com/photo-1439853949127-fa647821eba0',
        alt: 'Ocean',
        size: 'small'
    },
    {
        url: 'https://images.unsplash.com/photo-1455218873509-8097305ee378',
        alt: 'Winter Forest',
        size: 'large'
    },
    {
        url: 'https://images.unsplash.com/photo-1434725039720-aaad6dd32dfe',
        alt: 'Mountain Range',
        size: 'medium'
    },
    {
        url: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb',
        alt: 'Lake View',
        size: 'small'
    }
];

let currentImageIndex = 0;

// Gallery initialization
function initializeGallery() {
    const galleryContainer = document.querySelector('#gallery');
    
    // Create and append all album items
    albums.forEach(album => {
        const albumItem = document.createElement('div');
        albumItem.className = 'gallery-item';
        
        albumItem.innerHTML = `
            <a href="${album.url}" class="block relative group">
                <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" 
                     data-src="${album.coverImage}" 
                     alt="${album.title}"
                     class="gallery-image w-full">
                <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-opacity duration-300">
                    <div class="absolute inset-0 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                        <h2 class="text-white text-2xl font-light tracking-wide mb-2">${album.title}</h2>
                        <p class="text-white/80 text-sm font-light tracking-wide">${album.description}</p>
                    </div>
                </div>
            </a>
        `;
        
        galleryContainer.appendChild(albumItem);
    });
}

// Image loading with intersection observer
function initializeImageLoading(masonry) {
    const loadImage = (entry) => {
        const item = entry.target;
        const img = item.querySelector('img');
        
        // Start loading the image
        img.src = img.dataset.src;
        
        img.onload = () => {
            item.classList.add('loaded');
            masonry.layout();
        };
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                loadImage(entry);
                observer.unobserve(entry.target);
            }
        });
    }, {
        root: null,
        rootMargin: '50px',
        threshold: 0.1
    });

    // Observe all gallery items
    document.querySelectorAll('.gallery-item').forEach(item => {
        observer.observe(item);
    });
}

// Mobile menu functionality
function initializeMobileMenu() {
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', () => {
            const mobileMenu = document.createElement('div');
            mobileMenu.className = 'mobile-menu fixed inset-0 bg-white z-40 flex flex-col items-center justify-center';
            mobileMenu.innerHTML = `
                <button class="absolute top-4 right-4 close-menu">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
                <nav class="text-center">
                    <a href="/" class="block py-2 hover:text-gray-600">Home</a>
                    <a href="/photography" class="block py-2 hover:text-gray-600">Photography</a>
                    <a href="/music" class="block py-2 hover:text-gray-600">Music</a>
                </nav>
            `;
            
            document.body.appendChild(mobileMenu);
            document.body.style.overflow = 'hidden';
            
            const closeButton = mobileMenu.querySelector('.close-menu');
            closeButton.addEventListener('click', () => {
                mobileMenu.remove();
                document.body.style.overflow = '';
            });
        });
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    const galleryContainer = document.querySelector('#gallery');
    
    // Fetch albums data
    try {
        const response = await fetch('albums/albums.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        window.albums = data.albums; // Make albums available globally
        
        // Initialize gallery
        initializeGallery();

        // Initialize Masonry after all images are loaded
        imagesLoaded(galleryContainer, () => {
            const masonry = new Masonry(galleryContainer, {
                itemSelector: '.gallery-item',
                columnWidth: '.grid-sizer',
                gutter: 10,
                percentPosition: true,
                transitionDuration: '0.3s',
                initLayout: false,
                resize: true
            });

            // Initial layout
            masonry.layout();

            // Initialize image loading
            initializeImageLoading(masonry);
        });
    } catch (error) {
        console.error('Error loading albums:', error);
        galleryContainer.innerHTML = '<p class="text-red-500">Error loading albums. Please try again later.</p>';
    }

    // Initialize mobile menu
    initializeMobileMenu();
});
