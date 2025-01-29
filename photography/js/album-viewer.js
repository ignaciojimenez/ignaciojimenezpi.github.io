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
        this.preloadedImages = new Map();
        this.ratioTypeCache = new Map();
        this.initialLoadComplete = false;
        
        // Add mobile detection
        this.isMobile = window.innerWidth < 640;
        
        if (!this.modal) {
            this.createModal();
            this.modal = document.getElementById('imageModal');
        }
        
        this.initializeButtonReferences();
        this.setupEventListeners();
        
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('loaded');
                }
            });
        }, {
            root: null,
            rootMargin: '100% 0px', // Load images one viewport ahead
            threshold: 0.1
        });

        // Use ResizeObserver instead of resize event for better performance
        this.resizeObserver = new ResizeObserver(
            this.debounce(() => {
                // Only respond to resize events after initial load
                if (window.imagesData && this.initialLoadComplete && !this.isResizing) {
                    this.isResizing = true;
                    requestAnimationFrame(() => {
                        document.querySelectorAll('.gallery-item').forEach(item => {
                            item.classList.add('resizing');
                        });
                        this.reflow();
                        this.isResizing = false;
                    });
                }
            }, 150)
        );
        
        // Only observe resize on desktop
        if (this.gallery && !this.isMobile) {
            this.resizeObserver.observe(this.gallery);
        }
    }

    getAlbumIdFromUrl() {
        const path = window.location.pathname;
        const cleanPath = path.endsWith('/') ? path.slice(0, -1) : path;
        const parts = cleanPath.split('/');
        return parts[parts.length - 1];
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
        if (this.isMobile) return 1;
        const width = window.innerWidth;
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
            
            const albumsResponse = await fetch('/photography/albums/albums.json');
            if (!albumsResponse.ok) {
                throw new Error(`HTTP error! status: ${albumsResponse.status}`);
            }
            const albumsData = await albumsResponse.json();
            
            const album = albumsData.albums.find(a => a.id === this.albumId);
            if (!album) {
                throw new Error('Album not found');
            }

            document.title = `${album.title} - Ignacio Jiménez Pi`;
            if (album.description) {
                const metaDesc = document.querySelector('meta[name="description"]');
                if (metaDesc) {
                    metaDesc.content = album.description;
                }
            }

            if (this.isMobile) {
                // Mobile-optimized path
                this.processMobileImages(album.images);
            } else {
                // Desktop path - unchanged
                this.processImages(album.images);
            }
        } catch (error) {
            console.error('Error loading album:', error);
            this.showError(error.message);
        }
    }

    processMobileImages(images) {
        if (!images || images.length === 0) return;
        
        // No need for aspect ratios or sorting on mobile
        window.imagesData = images;
        
        // Create a simple vertical layout
        const fragment = document.createDocumentFragment();
        
        images.forEach((image, index) => {
            const imageCard = this.createMobileImageCard(image, index);
            fragment.appendChild(imageCard);
        });
        
        this.gallery.innerHTML = '';
        this.gallery.appendChild(fragment);
        
        // Show gallery immediately
        requestAnimationFrame(() => {
            this.gallery.style.opacity = '1';
        });
        
        this.initialLoadComplete = true;
        this.preloadAllHighResImages();
    }

    createMobileImageCard(imageData, index) {
        const imageCard = document.createElement('div');
        imageCard.className = 'gallery-item';
        
        const picture = document.createElement('picture');
        const sizes = imageData.sizes;
        
        if (sizes.grid && sizes.grid.webp) {
            const source = document.createElement('source');
            source.srcset = `/photography/albums/${this.albumId}/${sizes.grid.webp}`;
            source.type = 'image/webp';
            picture.appendChild(source);
        }
        
        const img = document.createElement('img');
        img.src = `/photography/albums/${this.albumId}/${sizes.grid.webp}`;
        img.alt = `Image ${index + 1}`;
        img.loading = 'lazy';
        
        // Set fixed aspect ratio for smooth loading
        img.style.aspectRatio = `${sizes.grid.width}/${sizes.grid.height}`;
        
        picture.appendChild(img);
        imageCard.appendChild(picture);
        imageCard.addEventListener('click', () => this.showModal(index));
        
        // Observe for lazy loading
        this.observer.observe(imageCard);
        
        return imageCard;
    }

    processImages(images) {
        if (!images || images.length === 0) return;
        
        // Pre-calculate all aspect ratios in one pass
        const aspectRatios = new Map();
        images.forEach(image => {
            if (image.sizes && image.sizes.large) {
                // Store the aspect ratio directly in the image data
                aspectRatios.set(image.id, image.sizes.large.width / image.sizes.large.height);
            }
        });
        
        // Update the imageBuffer in bulk
        this.imageBuffer = aspectRatios;
        
        // Sort images once and proceed with layout
        window.imagesData = this.sortByAspectRatioDiversity(images);
        this.reflow(true);
        
        if (this.gallery && !this.initialLoadComplete) {
            this.resizeObserver.observe(this.gallery);
            this.initialLoadComplete = true;
        }
        
        // Show gallery after initial layout
        if (this.gallery) {
            requestAnimationFrame(() => {
                this.gallery.style.opacity = '1';
            });
        }
        this.preloadAllHighResImages();
    }

    sortByAspectRatioDiversity(images) {
        // Pre-calculate ratio types for all images at once
        const ratioTypes = new Map();
        const groups = {
            portrait: [],
            landscape: []
        };
        
        // Single pass grouping
        images.forEach(img => {
            const ratio = this.imageBuffer.get(img.id);
            const type = ratio < 1 ? 'portrait' : 'landscape';
            ratioTypes.set(img.id, type);
            groups[type].push(img);
        });
        
        // Cache all ratio types
        this.ratioTypeCache = ratioTypes;

        const getRatioType = (image) => ratioTypes.get(image.id);

        const shuffle = (array) => {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
            return array;
        };

        groups.portrait = shuffle([...groups.portrait]);
        groups.landscape = shuffle([...groups.landscape]);

        const maxPerRow = this.getMaxImagesPerRow();
        const sortedImages = [];
        const totalImages = images.length;
        const completeRows = Math.floor(totalImages / maxPerRow);
        const remainingImages = totalImages % maxPerRow;

        const getRowPattern = (row) => row.map(img => getRatioType(img)[0]).join('');

        let lastRowPattern = '';

        const threeImagePatterns = [
            ['landscape', 'portrait', 'landscape'],   // LPL
            ['portrait', 'landscape', 'portrait'],    // PLP
            ['landscape', 'landscape', 'portrait'],   // LLP
            ['portrait', 'landscape', 'landscape'],   // PLL
            ['landscape', 'portrait', 'portrait'],    // LPP
            ['portrait', 'portrait', 'landscape']     // PPL
        ];

        const getNextRowPattern = (lastPattern, availableGroups) => {
            if (maxPerRow !== 3) return null; 

            const viablePatterns = threeImagePatterns.filter(pattern => {
                const neededCounts = {
                    portrait: pattern.filter(t => t === 'portrait').length,
                    landscape: pattern.filter(t => t === 'landscape').length
                };
                return neededCounts.portrait <= availableGroups.portrait.length &&
                       neededCounts.landscape <= availableGroups.landscape.length;
            });

            const shuffledPatterns = shuffle([...viablePatterns]);
            
            const patternStr = lastPattern.split('').join('');
            return shuffledPatterns.find(p => p.map(t => t[0]).join('') !== patternStr) || 
                   shuffledPatterns[0];
        };

        for (let row = 0; row < completeRows; row++) {
            const currentRow = [];
            
            if (maxPerRow === 3) {
                const nextPattern = getNextRowPattern(lastRowPattern, groups);
                
                if (nextPattern) {
                    nextPattern.forEach(type => {
                        const img = groups[type].pop();
                        currentRow.push(img);
                    });
                } else {
                    for (let i = 0; i < maxPerRow; i++) {
                        const preferredType = i === 0 ? 'landscape' : 
                            getRatioType(currentRow[currentRow.length - 1]) === 'portrait' ? 'landscape' : 'portrait';
                        const img = groups[preferredType].length > 0 ? 
                            groups[preferredType].pop() : 
                            (groups.landscape.length > 0 ? groups.landscape.pop() : groups.portrait.pop());
                        currentRow.push(img);
                    }
                }
            } else {
                for (let i = 0; i < maxPerRow; i++) {
                    const preferredType = i === 0 ? 'landscape' : 
                        getRatioType(currentRow[currentRow.length - 1]) === 'portrait' ? 'landscape' : 'portrait';
                    const img = groups[preferredType].length > 0 ? 
                        groups[preferredType].pop() : 
                        (groups.landscape.length > 0 ? groups.landscape.pop() : groups.portrait.pop());
                    currentRow.push(img);
                }
            }

            lastRowPattern = getRowPattern(currentRow);
            sortedImages.push(...currentRow);
        }

        if (remainingImages > 0) {
            const lastRow = [];
            
            // For a single remaining image, ONLY use landscape
            // If no landscape is available, steal one from earlier in the sequence
            if (remainingImages === 1) {
                if (groups.landscape.length > 0) {
                    lastRow.push(groups.landscape.pop());
                } else {
                    // Look for a landscape image in the sorted images (from the end)
                    for (let i = sortedImages.length - 1; i >= 0; i--) {
                        const ratio = this.imageBuffer.get(sortedImages[i].id);
                        if (ratio >= 1) {
                            // Found a landscape image, swap it
                            const landscapeImg = sortedImages[i];
                            if (groups.portrait.length > 0) {
                                // Replace it with a portrait image
                                sortedImages[i] = groups.portrait.pop();
                            } else {
                                // If no portrait available, remove it and adjust arrays
                                sortedImages.splice(i, 1);
                            }
                            lastRow.push(landscapeImg);
                            break;
                        }
                    }
                    // If still no landscape found (unlikely), use first available image
                    if (lastRow.length === 0) {
                        lastRow.push(groups.portrait.length > 0 ? groups.portrait.pop() : sortedImages.pop());
                    }
                }
            } else if (remainingImages === 2) {
                // For two remaining images, prefer two landscapes
                // If not possible, ensure at least the second one is landscape
                const firstType = groups.landscape.length > 0 ? 'landscape' : 'portrait';
                lastRow.push(groups[firstType].pop());

                // For second image, ensure landscape if possible
                if (groups.landscape.length > 0) {
                    lastRow.push(groups.landscape.pop());
                } else {
                    // Look for a landscape image in sorted images if none available
                    let foundLandscape = false;
                    for (let i = sortedImages.length - 1; i >= 0; i--) {
                        const ratio = this.imageBuffer.get(sortedImages[i].id);
                        if (ratio >= 1) {
                            const landscapeImg = sortedImages[i];
                            if (groups.portrait.length > 0) {
                                sortedImages[i] = groups.portrait.pop();
                            } else {
                                sortedImages.splice(i, 1);
                            }
                            lastRow.push(landscapeImg);
                            foundLandscape = true;
                            break;
                        }
                    }
                    if (!foundLandscape && groups.portrait.length > 0) {
                        lastRow.push(groups.portrait.pop());
                    }
                }
            } else {
                // For 3+ remaining images, ensure no trailing portrait
                const lastIsLandscape = groups.landscape.length > 0;
                
                // Handle all but the last image
                for (let i = 0; i < remainingImages - 1; i++) {
                    const preferredType = i === 0 ? 'landscape' : 
                        getRatioType(lastRow[lastRow.length - 1]) === 'portrait' ? 'landscape' : 'portrait';
                    const img = groups[preferredType].length > 0 ? 
                        groups[preferredType].pop() : 
                        (groups.landscape.length > 0 ? groups.landscape.pop() : groups.portrait.pop());
                    lastRow.push(img);
                }

                // Handle last image - ensure landscape if possible
                if (lastIsLandscape) {
                    lastRow.push(groups.landscape.pop());
                } else {
                    // Try to swap with a previous landscape
                    let foundLandscape = false;
                    for (let i = sortedImages.length - 1; i >= 0; i--) {
                        const ratio = this.imageBuffer.get(sortedImages[i].id);
                        if (ratio >= 1) {
                            const landscapeImg = sortedImages[i];
                            if (groups.portrait.length > 0) {
                                sortedImages[i] = groups.portrait.pop();
                            } else {
                                sortedImages.splice(i, 1);
                            }
                            lastRow.push(landscapeImg);
                            foundLandscape = true;
                            break;
                        }
                    }
                    if (!foundLandscape) {
                        lastRow.push(groups.portrait.pop());
                    }
                }
            }
            
            sortedImages.push(...lastRow);
        }

        return sortedImages;
    }

    preloadAllHighResImages() {
        if (!window.imagesData) return;
        
        window.imagesData.forEach((_, index) => {
            this.preloadImage(index);
        });
    }

    reflow(isInitial = false) {
        if (!window.imagesData) return;

        const fragment = document.createDocumentFragment();
        const existingItems = new Map();
        
        if (!isInitial) {
            document.querySelectorAll('.gallery-item').forEach(item => {
                const img = item.querySelector('img');
                if (img) {
                    const id = img.src.split('/').pop();
                    existingItems.set(id, item);
                    // Preserve loaded state during reflow
                    if (item.classList.contains('loaded')) {
                        item.setAttribute('data-was-loaded', 'true');
                    }
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
            const imageData = this.imageBuffer.get(image.id);
            if (!imageData) return;

            currentRowAspectRatios.push(imageData);
            
            let imageCard;
            if (existingItems.has(image.id)) {
                imageCard = existingItems.get(image.id);
                imageCard.style.removeProperty('width');
                imageCard.style.removeProperty('height');
                // Restore loaded state immediately if it was loaded before
                if (imageCard.getAttribute('data-was-loaded') === 'true') {
                    imageCard.classList.add('loaded');
                    imageCard.removeAttribute('data-was-loaded');
                }
            } else {
                imageCard = this.createImageCard(image, index);
            }
            
            currentRow.push(imageCard);

            if (currentRow.length === maxImagesPerRow || index === window.imagesData.length - 1) {
                const row = document.createElement('div');
                row.className = 'gallery-row';
                this.createRowFromImages(row, currentRow, currentRowAspectRatios, this.targetHeight, containerWidth, gap);
                fragment.appendChild(row);
                currentRow = [];
                currentRowAspectRatios = [];
            }
        });

        this.gallery.appendChild(fragment);

        // Only handle resizing class for non-initial loads
        if (!isInitial) {
            requestAnimationFrame(() => {
                document.querySelectorAll('.gallery-item').forEach(item => {
                    item.classList.remove('resizing');
                });
            });
        }
    }

    createRowFromImages(row, images, aspectRatios, targetHeight, containerWidth, gap) {
        const totalNaturalWidth = aspectRatios.reduce((sum, ratio) => sum + (targetHeight * ratio), 0);
        const totalGapWidth = (images.length - 1) * gap;
        const scale = (containerWidth - totalGapWidth) / totalNaturalWidth;
        
        images.forEach((imageCard, i) => {
            const width = Math.floor(targetHeight * aspectRatios[i] * scale);
            
            imageCard.style.width = `${width}px`;
            imageCard.style.height = `${targetHeight}px`;
            
            row.appendChild(imageCard);
            
            if (!imageCard.classList.contains('loaded')) {
                this.observer.observe(imageCard);
            }
        });
    }

    createImageCard(imageData, index) {
        const imageCard = document.createElement('div');
        imageCard.className = 'gallery-item';
        
        const picture = document.createElement('picture');
        const sizes = imageData.sizes;
        
        // Only create sources for current viewport
        const currentWidth = window.innerWidth;
        const appropriateSize = currentWidth < 640 ? 'grid' :
                              currentWidth < 1024 ? 'small' : 'medium';
        
        if (sizes[appropriateSize] && sizes[appropriateSize].webp) {
            const source = document.createElement('source');
            source.srcset = `/photography/albums/${this.albumId}/${sizes[appropriateSize].webp}`;
            source.type = 'image/webp';
            picture.appendChild(source);
        }
        
        const img = document.createElement('img');
        const gridSize = sizes.grid;
        img.src = `/photography/albums/${this.albumId}/${gridSize.webp}`;
        img.alt = `Image ${index + 1}`;
        img.loading = 'lazy';
        picture.appendChild(img);
        
        imageCard.appendChild(picture);
        imageCard.addEventListener('click', () => this.showModal(index));
        
        return imageCard;
    }

    createModal() {
        const existingModal = document.getElementById('imageModal');
        if (existingModal) {
            existingModal.remove();
        }

        const modal = document.createElement('div');
        modal.id = 'imageModal';
        modal.className = 'modal';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        
        const picture = document.createElement('picture');
        modalContent.appendChild(picture);
        
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
        
        if (!document.getElementById('modalStyles')) {
            const style = document.createElement('style');
            style.id = 'modalStyles';
            style.textContent = `
                #imageModal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 1000; }
                #imageModal.active { display: flex !important; }
                #imageModal .modal-content { position: relative; margin: auto; max-width: 90%; max-height: 90%; }
                #imageModal .modal-content picture { 
                    max-width: 100%; 
                    max-height: 90vh; 
                    display: block; 
                    margin: 0 auto; 
                    transition: opacity 0.2s ease-out, filter 0.2s ease-out; 
                    opacity: 1;
                }
                #imageModal .modal-content picture img.loading { 
                    filter: blur(10px);
                    opacity: 0.6;
                }
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
            if (this.currentImageIndex === 0) {
                prevButton.style.display = 'none';
                prevButton.classList.add('hidden');
            } else {
                prevButton.style.display = 'block';
                prevButton.classList.remove('hidden');
            }
            
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
        const imageData = window.imagesData[index];
        const sizes = imageData.sizes;
        
        const picture = document.createElement('picture');
        
        if (this.isMobile) {
            // On mobile, use grid size for initial display, then upgrade to large
            if (sizes.grid.webp) {
                const webpSource = document.createElement('source');
                webpSource.srcset = `/photography/albums/${this.albumId}/${sizes.grid.webp}`;
                webpSource.type = 'image/webp';
                picture.appendChild(webpSource);
            }
            
            const img = document.createElement('img');
            img.src = `/photography/albums/${this.albumId}/${sizes.grid.webp}`;
            img.alt = `Image ${index + 1}`;
            img.className = 'max-w-full max-h-[90vh] object-contain mx-auto loading';
            picture.appendChild(img);
            
            // Immediately start loading high-res version
            const highResImg = new Image();
            highResImg.onload = () => {
                img.src = highResImg.src;
                img.classList.remove('loading');
            };
            highResImg.src = `/photography/albums/${this.albumId}/${sizes.large.webp}`;
        } else {
            // Desktop behavior remains unchanged
            if (sizes.large.webp) {
                const webpSource = document.createElement('source');
                webpSource.srcset = `/photography/albums/${this.albumId}/${sizes.large.webp}`;
                webpSource.type = 'image/webp';
                picture.appendChild(webpSource);
            }
            
            const img = document.createElement('img');
            img.src = `/photography/albums/${this.albumId}/${sizes.large.webp}`;
            img.alt = `Image ${index + 1}`;
            img.className = 'max-w-full max-h-[90vh] object-contain mx-auto';
            picture.appendChild(img);
        }
        
        const modalContent = document.querySelector('.modal-content');
        modalContent.innerHTML = '';
        modalContent.appendChild(picture);
        
        this.modal.classList.add('active');
        this.updateNavigationButtons();
        this.preloadAdjacentImages(index);
        
        document.body.style.overflow = 'hidden';
    }

    preloadAdjacentImages(currentIndex) {
        if (currentIndex + 1 < window.imagesData.length) {
            this.preloadImage(currentIndex + 1);
        }
        if (currentIndex - 1 >= 0) {
            this.preloadImage(currentIndex - 1);
        }
    }

    preloadImage(index) {
        if (this.preloadedImages.has(index)) return;

        const imageData = window.imagesData[index];
        const sizes = imageData.sizes;
        if (sizes && sizes.large && sizes.large.webp) {
            const webpImg = new Image();
            webpImg.src = `/photography/albums/${this.albumId}/${sizes.large.webp}`;
            this.preloadedImages.set(index, webpImg);
        }
    }

    closeModal() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    showNextImage() {
        const nextIndex = this.currentImageIndex + 1;
        if (nextIndex < window.imagesData.length) {
            this.showModal(nextIndex);
        }
    }

    showPrevImage() {
        const prevIndex = this.currentImageIndex - 1;
        if (prevIndex >= 0) {
            this.showModal(prevIndex);
        }
    }

    setupEventListeners() {
        if (this.isMobile) {
            // Mobile-optimized touch handling
            let touchStartX = 0;
            let touchStartY = 0;
            let touchEndX = 0;
            let touchEndY = 0;
            let startTime = 0;
            let initialTransform = 0;
            
            this.modal.addEventListener('touchstart', (e) => {
                // Close modal if background is tapped (not the content or controls)
                // Check if the clicked element is the modal itself (background) and not its children
                if (e.target === this.modal || e.target.classList.contains('modal-content')) {
                    e.preventDefault(); // Prevent any default behavior
                    e.stopPropagation(); // Stop event from bubbling to elements behind the modal
                    this.closeModal();
                    return;
                }
                
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
                startTime = Date.now();
                
                // Reset transform
                const picture = this.modal.querySelector('picture');
                if (picture) {
                    initialTransform = 0;
                    picture.style.transform = `translateX(0)`;
                    picture.style.transition = 'none';
                }
            }, { passive: false });

            this.modal.addEventListener('touchmove', (e) => {
                if (e.target === this.modal) return; // Don't track swipes on background
                
                const deltaX = e.touches[0].clientX - touchStartX;
                const deltaY = e.touches[0].clientY - touchStartY;
                
                // Only handle horizontal movement if it's more horizontal than vertical
                if (Math.abs(deltaX) > Math.abs(deltaY)) {
                    e.preventDefault(); // Prevent page scroll
                    
                    const picture = this.modal.querySelector('picture');
                    if (picture) {
                        // Add resistance to the swipe
                        const resistance = 0.4;
                        const transform = deltaX * resistance;
                        picture.style.transform = `translateX(${transform}px)`;
                    }
                }
            }, { passive: false });
            
            this.modal.addEventListener('touchend', (e) => {
                if (e.target === this.modal) return; // Don't handle swipes on background
                
                touchEndX = e.changedTouches[0].clientX;
                touchEndY = e.changedTouches[0].clientY;
                
                const deltaX = touchEndX - touchStartX;
                const deltaY = touchEndY - touchStartY;
                const deltaTime = Date.now() - startTime;
                
                const picture = this.modal.querySelector('picture');
                if (picture) {
                    picture.style.transition = 'transform 0.3s ease-out';
                }
                
                // Handle swipe if:
                // 1. Horizontal movement is dominant
                // 2. Minimum distance is met
                // 3. Maximum time is not exceeded
                if (Math.abs(deltaX) > Math.abs(deltaY) * 2 && 
                    Math.abs(deltaX) > 50 && 
                    deltaTime < 300) {
                    
                    if (deltaX > 0) {
                        this.showPrevImage();
                    } else {
                        this.showNextImage();
                    }
                } else {
                    // Reset position if swipe wasn't decisive
                    if (picture) {
                        picture.style.transform = `translateX(0)`;
                    }
                }
            }, { passive: true });
            
            // Simpler close button for mobile
            const closeButton = this.modal.querySelector('.modal-close');
            if (closeButton) {
                closeButton.addEventListener('click', () => this.closeModal(), { passive: true });
            }
        } else {
            // Desktop event listeners
            document.addEventListener('keydown', (e) => {
                if (this.modal.classList.contains('active')) {
                    this.handleKeyPress(e);
                }
            });

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
        }

        // Common event listeners for both mobile and desktop
        const closeButton = this.modal.querySelector('.modal-close');
        const prevButton = this.modal.querySelector('.modal-prev');
        const nextButton = this.modal.querySelector('.modal-next');
        
        if (closeButton) closeButton.addEventListener('click', () => this.closeModal());
        if (prevButton) prevButton.addEventListener('click', () => this.showPrevImage());
        if (nextButton) nextButton.addEventListener('click', () => this.showNextImage());
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
        const threshold = 50;
        const swipeDistance = endX - startX;

        if (Math.abs(swipeDistance) > threshold) {
            if (swipeDistance > 0) {
                this.showPrevImage();
            } else {
                this.showNextImage();
            }
        }
    }
}
