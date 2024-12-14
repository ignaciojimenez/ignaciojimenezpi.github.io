class AlbumViewer {
    constructor() {
        this.currentImageIndex = 0;
        this.modal = document.getElementById('imageModal');
        this.gallery = document.getElementById('gallery');
        this.imageBuffer = new Map();
        this.targetHeight = 315;
        this.isResizing = false;
        this.albumId = this.getAlbumIdFromUrl();
        this.lastHeight = null;
        
        // Create modal if it doesn't exist
        if (!this.modal) {
            this.createModal();
            this.modal = document.getElementById('imageModal');
        }
        
        // Initialize button references
        this.initializeButtonReferences();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Create intersection observer for lazy loading
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('loaded');
                }
            });
        }, {
            root: null,
            rootMargin: '50px',
            threshold: 0.1
        });

        // Track initial width
        let initialWidth = window.innerWidth;

        // Debounce resize handler
        this.debouncedResize = this.debounce(() => {
            if (window.imagesData) {
                this.isResizing = false;
                this.reflow();
            }
        }, 150);

        // Setup resize handling
        window.addEventListener('resize', () => {
            const currentWidth = window.innerWidth;

            // Only trigger reflow if width has changed
            if (currentWidth !== initialWidth) {
                if (!this.isResizing) {
                    this.isResizing = true;
                    document.querySelectorAll('.gallery-item').forEach(item => {
                        item.classList.add('resizing');
                    });
                }
                this.debouncedResize();

                // Update initial width
                initialWidth = currentWidth;
            }
        });
    }

    getAlbumIdFromUrl() {
        const path = window.location.pathname;
        // Remove trailing slash if present
        const cleanPath = path.endsWith('/') ? path.slice(0, -1) : path;
        const parts = cleanPath.split('/');
        const albumId = parts[parts.length - 1];
        return albumId;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    getMaxImagesPerRow() {
        const width = window.innerWidth;
        if (width < 640) return 1;
        if (width < 1024) return 2;
        return 3;
    }

    init() {
        this.loadAlbumImages();
    }

    async loadAlbumImages() {
        try {
            if (!this.albumId) {
                throw new Error('No album ID specified');
            }
            
            // Load albums.json
            const albumsResponse = await fetch('/photography/albums/albums.json');
            if (!albumsResponse.ok) {
                throw new Error(`HTTP error! status: ${albumsResponse.status}`);
            }
            const albumsData = await albumsResponse.json();
            
            // Find current album
            const album = albumsData.albums.find(a => a.id === this.albumId);
            if (!album) {
                throw new Error('Album not found');
            }

            // Update page title and metadata
            document.title = `${album.title} - Ignacio Jiménez Pi`;
            if (album.description) {
                const metaDesc = document.querySelector('meta[name="description"]');
                if (metaDesc) {
                    metaDesc.content = album.description;
                }
            }

            // Process images with metadata
            window.imagesData = album.images.map(imagePath => {
                const filename = imagePath.split('/').pop();
                const imageMetadata = album.metadata[filename];
                
                if (!imageMetadata) {
                    console.warn(`No metadata found for image: ${filename}`);
                    return {
                        filename,
                        path: imagePath,
                        metadata: null
                    };
                }

                return {
                    filename,
                    path: imagePath,
                    metadata: {
                        original: {
                            path: imageMetadata.original.path,
                            webp: imageMetadata.original.webp,
                            width: imageMetadata.original.width,
                            height: imageMetadata.original.height
                        },
                        responsive: imageMetadata.responsive
                    }
                };
            });
            
            this.processImages(window.imagesData);
        } catch (error) {
            console.error('Error loading album:', error);
            this.showError(error.message);
        }
    }

    processImages(images) {
        if (!images || images.length === 0) return;
        
        const loadPromises = images.map((image, index) => {
            return new Promise((resolve) => {
                if (this.imageBuffer.has(image.filename)) {
                    resolve();
                    return;
                }

                // If we have metadata, use it instead of loading the image
                if (image.metadata) {
                    this.imageBuffer.set(image.filename, {
                        aspectRatio: image.metadata.original.width / image.metadata.original.height,
                        filename: image.filename
                    });
                    resolve();
                    return;
                }

                // Fallback to loading image if no metadata
                const img = new Image();
                img.src = image.path;
                
                img.onload = () => {
                    this.imageBuffer.set(image.filename, {
                        aspectRatio: img.width / img.height,
                        filename: image.filename
                    });
                    resolve();
                };
                
                img.onerror = () => {
                    console.error('Failed to load image:', image.path);
                    resolve();
                };
            });
        });

        Promise.all(loadPromises).then(() => {
            this.reflow(true);
        });
    }

    reflow(isInitial = false) {
        if (!window.imagesData) return;

        const existingItems = new Map();
        if (!isInitial) {
            document.querySelectorAll('.gallery-item').forEach(item => {
                const img = item.querySelector('img');
                if (img) {
                    existingItems.set(img.src.split('/').pop(), item);
                }
            });
        }

        this.gallery.innerHTML = '';
        let currentRow = [];
        let currentRowAspectRatios = [];
        const maxImagesPerRow = this.getMaxImagesPerRow();
        const containerWidth = this.gallery.clientWidth;
        const gap = 10;

        window.imagesData.forEach((image, index) => {
            const imageData = this.imageBuffer.get(image.filename);
            if (!imageData) return;

            currentRowAspectRatios.push(imageData.aspectRatio);
            
            let imageCard;
            if (existingItems.has(image.filename)) {
                imageCard = existingItems.get(image.filename);
                imageCard.style.removeProperty('width');
                imageCard.style.removeProperty('height');
            } else {
                imageCard = this.createImageCard(image.filename, index);
            }
            
            currentRow.push(imageCard);

            if (currentRow.length === maxImagesPerRow || index === window.imagesData.length - 1) {
                this.createRowFromImages(currentRow, currentRowAspectRatios, this.targetHeight, containerWidth, gap);
                currentRow = [];
                currentRowAspectRatios = [];
            }
        });

        // Remove resizing class after layout is complete
        requestAnimationFrame(() => {
            document.querySelectorAll('.gallery-item').forEach(item => {
                item.classList.remove('resizing');
            });
        });

        this.isResizing = false;
    }

    createRowFromImages(images, aspectRatios, targetHeight, containerWidth, gap) {
        const row = document.createElement('div');
        row.className = 'gallery-row';
        
        const totalNaturalWidth = aspectRatios.reduce((sum, ratio) => sum + (targetHeight * ratio), 0);
        const totalGapWidth = (images.length - 1) * gap;
        const scale = (containerWidth - totalGapWidth) / totalNaturalWidth;
        
        images.forEach((imageCard, i) => {
            const width = Math.floor(targetHeight * aspectRatios[i] * scale);
            
            requestAnimationFrame(() => {
                imageCard.style.width = `${width}px`;
                imageCard.style.height = `${targetHeight}px`;
            });
            
            row.appendChild(imageCard);
            
            if (!imageCard.classList.contains('loaded')) {
                this.observer.observe(imageCard);
            }
        });
        
        this.gallery.appendChild(row);
    }

    createImageCard(filename, index) {
        const imageCard = document.createElement('div');
        imageCard.className = 'gallery-item';
        
        const img = document.createElement('img');
        const imageData = window.imagesData[index];
        
        if (imageData.metadata?.responsive) {
            // Create srcset for responsive images including the original
            const srcsetEntries = [];
            
            // Add responsive sizes
            const sizes = ['thumbnail', 'small', 'medium', 'large'];
            sizes.forEach(size => {
                const sizeData = imageData.metadata.responsive[size];
                if (sizeData?.path) {
                    srcsetEntries.push(`${sizeData.path} ${sizeData.width}w`);
                }
            });
            
            // Add original
            if (imageData.metadata.original?.path) {
                srcsetEntries.push(`${imageData.metadata.original.path} ${imageData.metadata.original.width}w`);
            }
            
            if (srcsetEntries.length > 0) {
                img.srcset = srcsetEntries.join(', ');
                img.sizes = '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw';
                // Use medium size as fallback, or the first available size
                const mediumPath = imageData.metadata.responsive.medium?.path || imageData.metadata.original.path;
                img.src = mediumPath || imageData.path;
            } else {
                img.src = imageData.path;
            }
        } else {
            img.src = imageData.path;
        }
        
        img.alt = `Image ${index + 1}`;
        img.loading = 'lazy';
        
        imageCard.appendChild(img);
        imageCard.addEventListener('click', () => this.showModal(index));
        
        return imageCard;
    }

    createModal() {
        // Remove existing modal if it exists
        const existingModal = document.getElementById('imageModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Create the modal structure
        const modal = document.createElement('div');
        modal.id = 'imageModal';
        modal.className = 'modal';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        
        const img = document.createElement('img');
        img.id = 'modalImage';
        img.alt = '';
        modalContent.appendChild(img);
        
        const prevButton = document.createElement('button');
        prevButton.className = 'modal-prev';
        prevButton.setAttribute('aria-label', 'Previous image');
        prevButton.textContent = '←';
        modalContent.appendChild(prevButton);
        
        const nextButton = document.createElement('button');
        nextButton.className = 'modal-next';
        nextButton.setAttribute('aria-label', 'Next image');
        nextButton.textContent = '→';
        modalContent.appendChild(nextButton);
        
        const closeButton = document.createElement('button');
        closeButton.className = 'modal-close';
        closeButton.setAttribute('aria-label', 'Close modal');
        closeButton.textContent = '×';
        modalContent.appendChild(closeButton);
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        // Add styles if not already present
        if (!document.getElementById('modalStyles')) {
            const style = document.createElement('style');
            style.id = 'modalStyles';
            style.textContent = `
                #imageModal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 1000; }
                #imageModal.active { display: flex !important; }
                #imageModal .modal-content { position: relative; margin: auto; max-width: 90%; max-height: 90%; }
                #imageModal .modal-content img { max-width: 100%; max-height: 90vh; display: block; margin: 0 auto; }
                #imageModal .modal-prev,
                #imageModal .modal-next { 
                    position: absolute !important; 
                    top: 50% !important; 
                    transform: translateY(-50%) !important; 
                    background: rgba(255,255,255,0.1) !important; 
                    color: white !important; 
                    border: none !important; 
                    padding: 1rem !important; 
                    cursor: pointer !important; 
                    font-size: 1.5rem !important;
                    z-index: 1001 !important;
                }
                #imageModal .modal-prev.hidden,
                #imageModal .modal-next.hidden { 
                    display: none !important;
                    opacity: 0 !important;
                    visibility: hidden !important;
                    pointer-events: none !important;
                }
                #imageModal .modal-prev:hover,
                #imageModal .modal-next:hover { 
                    background: rgba(255,255,255,0.2) !important; 
                }
                #imageModal .modal-prev { left: 1rem !important; }
                #imageModal .modal-next { right: 1rem !important; }
                #imageModal .modal-close { 
                    position: absolute !important; 
                    top: -2rem !important; 
                    right: 0 !important; 
                    color: white !important; 
                    background: none !important; 
                    border: none !important;
                    font-size: 2rem !important; 
                    cursor: pointer !important; 
                    padding: 0.5rem !important;
                }
            `;
            document.head.appendChild(style);
        }
    }

    initializeButtonReferences() {
        if (this.modal) {
            this.prevButton = this.modal.querySelector('.modal-prev');
            this.nextButton = this.modal.querySelector('.modal-next');
            if (!this.prevButton || !this.nextButton) {
                console.warn('Navigation buttons not found in modal');
            }
        } else {
            console.warn('Modal not found during button initialization');
        }
    }

    updateNavigationButtons() {
        const prevButton = this.modal.querySelector('.modal-prev');
        const nextButton = this.modal.querySelector('.modal-next');
        
        if (prevButton && nextButton) {
            // At first image
            if (this.currentImageIndex === 0) {
                prevButton.style.display = 'none';
                prevButton.classList.add('hidden');
            } else {
                prevButton.style.display = 'block';
                prevButton.classList.remove('hidden');
            }
            
            // At last image
            if (this.currentImageIndex === window.imagesData.length - 1) {
                nextButton.style.display = 'none';
                nextButton.classList.add('hidden');
            } else {
                nextButton.style.display = 'block';
                nextButton.classList.remove('hidden');
            }
        }
    }

    showModal(index) {
        this.currentImageIndex = index;
        this.modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        this.showImage(index);
        this.modal.focus(); // Set focus to the modal
    }

    closeModal() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    showImage(index) {
        const modalImage = document.getElementById('modalImage');
        const imageData = window.imagesData[index];
        
        if (imageData.metadata?.responsive) {
            const largePath = imageData.metadata.responsive.large?.path || imageData.metadata.original.path;
            const largeWidth = imageData.metadata.responsive.large?.width || imageData.metadata.original.width;
            const srcset = `${largePath} ${largeWidth}w, ${imageData.metadata.original.path} ${imageData.metadata.original.width}w`;
            modalImage.srcset = srcset;
            modalImage.sizes = '100vw';
            modalImage.src = largePath || imageData.path;
        } else {
            modalImage.src = imageData.path;
        }
        
        this.currentImageIndex = index;
        // Force button update after setting new index
        requestAnimationFrame(() => {
            this.updateNavigationButtons();
        });
    }

    showNextImage() {
        const nextIndex = this.currentImageIndex + 1;
        if (nextIndex < window.imagesData.length) {
            this.showImage(nextIndex);
        }
    }

    showPrevImage() {
        const prevIndex = this.currentImageIndex - 1;
        if (prevIndex >= 0) {
            this.showImage(prevIndex);
        }
    }

    setupEventListeners() {
        // Existing keyboard event listener
        document.addEventListener('keydown', (e) => {
            if (this.modal.classList.contains('active')) {
                this.handleKeyPress(e);
            }
        });

        // Swipe gesture support for modal
        let touchStartX = 0;
        let touchEndX = 0;

        // Touch start event
        this.modal.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        // Touch end event
        this.modal.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe(touchStartX, touchEndX);
        }, { passive: true });

        // Optional: Mouse swipe support for desktop
        let mouseStartX = 0;
        let isMouseDown = false;

        this.modal.addEventListener('mousedown', (e) => {
            isMouseDown = true;
            mouseStartX = e.screenX;
        });

        document.addEventListener('mousemove', (e) => {
            if (!isMouseDown) return;
        });

        document.addEventListener('mouseup', (e) => {
            if (!isMouseDown) return;
            isMouseDown = false;
            this.handleSwipe(mouseStartX, e.screenX);
        });

        if (this.modal) {
            const prevButton = this.modal.querySelector('.modal-prev');
            const nextButton = this.modal.querySelector('.modal-next');
            const closeButton = this.modal.querySelector('.modal-close');

            if (prevButton) {
                prevButton.addEventListener('click', () => this.showPrevImage());
                
                // Add touch support for previous button
                prevButton.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    this.showPrevImage();
                }, { passive: false });
            }

            if (nextButton) {
                nextButton.addEventListener('click', () => this.showNextImage());
                
                // Add touch support for next button
                nextButton.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    this.showNextImage();
                }, { passive: false });
            }

            if (closeButton) {
                closeButton.addEventListener('click', () => this.closeModal());
            }
        } else {
            console.warn('Modal not found during event listener setup');
        }
    }

    handleKeyPress(e) {
        if (!this.modal.classList.contains('active')) return;
        
        switch(e.key) {
            case 'ArrowRight':
                this.showNextImage();
                break;
            case 'ArrowLeft':
                this.showPrevImage();
                break;
            case 'Escape':
                this.closeModal();
                break;
        }
    }

    handleSwipe(startX, endX) {
        const threshold = 50; // Minimum distance for a swipe
        const swipeDistance = endX - startX;

        if (Math.abs(swipeDistance) > threshold) {
            if (swipeDistance > 0) {
                // Swipe right (previous image)
                this.showPrevImage();
            } else {
                // Swipe left (next image)
                this.showNextImage();
            }
        }
    }
}
