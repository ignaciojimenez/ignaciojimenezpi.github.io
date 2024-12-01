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
    
    // Create and append all gallery items
    galleryImages.forEach((image, index) => {
        const galleryItem = document.createElement('div');
        galleryItem.className = 'gallery-item';
        
        galleryItem.innerHTML = `
            <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" 
                 data-src="${image.url}" 
                 alt="${image.alt}"
                 class="gallery-image ${image.size}"
                 data-index="${index}">
        `;
        
        galleryContainer.appendChild(galleryItem);
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

// Modal functionality
function initializeModal() {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const closeButton = document.querySelector('.close-modal');
    const prevButton = document.querySelector('.prev-image');
    const nextButton = document.querySelector('.next-image');

    function showImage(index) {
        currentImageIndex = index;
        const image = galleryImages[index];
        modalImage.src = image.url;
        modalImage.alt = image.alt;
    }

    function openModal(index) {
        showImage(index);
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }

    function showNextImage() {
        const nextIndex = (currentImageIndex + 1) % galleryImages.length;
        showImage(nextIndex);
    }

    function showPrevImage() {
        const prevIndex = (currentImageIndex - 1 + galleryImages.length) % galleryImages.length;
        showImage(prevIndex);
    }

    // Event Listeners
    document.querySelectorAll('.gallery-item img').forEach(img => {
        img.addEventListener('click', () => {
            openModal(parseInt(img.dataset.index));
        });
    });

    closeButton.addEventListener('click', closeModal);
    prevButton.addEventListener('click', showPrevImage);
    nextButton.addEventListener('click', showNextImage);

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (!modal.classList.contains('hidden')) {
            if (e.key === 'Escape') closeModal();
            if (e.key === 'ArrowLeft') showPrevImage();
            if (e.key === 'ArrowRight') showNextImage();
        }
    });

    // Close modal when clicking outside the image
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
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

    // Initialize modal
    initializeModal();

    // Initialize mobile menu
    initializeMobileMenu();

    // Smooth scroll for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('opacity-100');
                entry.target.classList.remove('opacity-0', 'translate-y-10');
            }
        });
    }, observerOptions);

    document.querySelectorAll('section').forEach(section => {
        section.classList.add('opacity-0', 'translate-y-10', 'transition-all', 'duration-700');
        observer.observe(section);
    });
});
