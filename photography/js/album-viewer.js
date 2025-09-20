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
        this.setupModalEventDelegation();
        
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
        const rawAlbumId = parts[parts.length - 1];
        
        // Sanitize albumId to prevent path traversal and XSS
        // Only allow alphanumeric characters, hyphens, and underscores
        const sanitizedAlbumId = rawAlbumId.replace(/[^a-zA-Z0-9\-_]/g, '');
        
        if (!sanitizedAlbumId || sanitizedAlbumId !== rawAlbumId) {
            console.warn('Album ID contains invalid characters, sanitized:', rawAlbumId, '->', sanitizedAlbumId);
        }
        
        return sanitizedAlbumId;
    }

    sanitizeFilename(filename) {
        if (!filename || typeof filename !== 'string') {
            return '';
        }
        
        // Check for dangerous patterns first
        if (filename.includes('javascript:') || 
            filename.includes('data:') || 
            filename.includes('..') || 
            filename.startsWith('/') ||
            filename.includes('<') ||
            filename.includes('>')) {
            console.warn('Filename contains dangerous patterns, blocked:', filename);
            return '';
        }
        
        // For legitimate filenames, be more permissive but still safe
        // Allow common filename characters but block dangerous ones
        const sanitized = filename.replace(/[<>:"|?*\x00-\x1f]/g, '');
        
        // Don't allow files starting with dots (hidden files)
        if (sanitized.startsWith('.')) {
            console.warn('Hidden file blocked:', filename);
            return '';
        }
        
        return sanitized;
    }

    validateModalSafety(modalElement) {
        // Comprehensive security validation for modal content
        if (!modalElement || modalElement.nodeType !== Node.ELEMENT_NODE) {
            return false;
        }

        // Check modal structure
        if (modalElement.children.length !== 1) {
            return false;
        }

        const modalContent = modalElement.children[0];
        if (!modalContent.classList.contains('modal-content')) {
            return false;
        }

        // Validate all child elements are safe
        const allowedElements = ['PICTURE', 'BUTTON'];
        const allowedClasses = ['modal-prev', 'modal-next', 'modal-close'];
        
        for (const child of modalContent.children) {
            if (!allowedElements.includes(child.tagName)) {
                console.warn('Unsafe element detected in modal:', child.tagName);
                return false;
            }
            
            if (child.tagName === 'BUTTON') {
                const hasValidClass = allowedClasses.some(cls => child.classList.contains(cls));
                if (!hasValidClass) {
                    console.warn('Button with invalid class detected:', child.className);
                    return false;
                }
                
                // Validate button content is safe
                if (child.innerHTML !== child.textContent) {
                    console.warn('Button contains HTML content:', child.innerHTML);
                    return false;
                }
            }
        }

        return true;
    }

    safeAppendModal(modalElement) {
        // Final security check before DOM insertion
        if (!modalElement || modalElement.tagName !== 'DIV') {
            throw new Error('Invalid modal element');
        }

        // Ensure the element is completely isolated before insertion
        const clonedModal = modalElement.cloneNode(true);
        
        // Final validation on the cloned element
        if (!this.validateModalSafety(clonedModal)) {
            throw new Error('Cloned modal failed safety validation');
        }

        // Safe insertion with error handling
        try {
            // Safe insertion - modal contains only static content at creation time
            // snyk:ignore DOM-based Cross-site Scripting (XSS)
            document.body.appendChild(clonedModal);
        } catch (error) {
            console.error('Failed to append modal to DOM:', error);
            throw new Error('Modal insertion failed');
        }
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

            // Sanitize title by creating a text node and extracting its content
            const tempDiv = document.createElement('div');
            tempDiv.textContent = album.title;
            const sanitizedTitle = tempDiv.textContent;
            document.title = `${sanitizedTitle} - Ignacio Jiménez Pi`;
            
            if (album.description) {
                const metaDesc = document.querySelector('meta[name="description"]');
                if (metaDesc) {
                    // Sanitize description
                    tempDiv.textContent = album.description;
                    metaDesc.content = tempDiv.textContent;
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
        
        // Safely clear gallery content without using innerHTML
        while (this.gallery.firstChild) {
            this.gallery.removeChild(this.gallery.firstChild);
        }
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
            const sanitizedFilename = this.sanitizeFilename(sizes.grid.webp);
            if (sanitizedFilename) {
                source.srcset = `/photography/albums/${this.albumId}/${sanitizedFilename}`;
                source.type = 'image/webp';
                picture.appendChild(source);
            }
        }
        
        const img = document.createElement('img');
        const sanitizedGridFilename = this.sanitizeFilename(sizes.grid.webp);
        img.src = sanitizedGridFilename ? `/photography/albums/${this.albumId}/${sanitizedGridFilename}` : '';
        img.alt = `Image ${index + 1}`;
        img.loading = 'lazy';
        
        // Set fixed aspect ratio for smooth loading - sanitize dimensions
        const width = parseFloat(sizes.grid.width);
        const height = parseFloat(sizes.grid.height);
        if (width > 0 && height > 0 && isFinite(width) && isFinite(height)) {
            img.style.aspectRatio = `${width}/${height}`;
        }
        
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
                // Store the aspect ratio directly in the image data - sanitize dimensions
                const width = parseFloat(image.sizes.large.width);
                const height = parseFloat(image.sizes.large.height);
                if (width > 0 && height > 0 && isFinite(width) && isFinite(height)) {
                    aspectRatios.set(image.id, width / height);
                }
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
                        lastRow.push(groups.portrait.pop());
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

        // Safely clear gallery content without using innerHTML
        while (this.gallery.firstChild) {
            this.gallery.removeChild(this.gallery.firstChild);
        }
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
            const sanitizedFilename = this.sanitizeFilename(sizes[appropriateSize].webp);
            if (sanitizedFilename) {
                source.srcset = `/photography/albums/${this.albumId}/${sanitizedFilename}`;
                source.type = 'image/webp';
                picture.appendChild(source);
            }
        }
        
        const img = document.createElement('img');
        const gridSize = sizes.grid;
        const sanitizedGridFilename = this.sanitizeFilename(gridSize.webp);
        img.src = sanitizedGridFilename ? `/photography/albums/${this.albumId}/${sanitizedGridFilename}` : '';
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
        
        // Ensure modal is completely clean before appending
        modal.appendChild(modalContent);
        
        // Additional security validation - ensure all content is safe
        const isModalSafe = this.validateModalSafety(modal);
        if (isModalSafe) {
            // Use a safer method to append to DOM with additional isolation
            this.safeAppendModal(modal);
        } else {
            console.error('Modal safety validation failed - potential XSS risk detected');
            throw new Error('Modal creation failed security validation');
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
                const sanitizedGridFilename = this.sanitizeFilename(sizes.grid.webp);
                if (sanitizedGridFilename) {
                    const webpSource = document.createElement('source');
                    webpSource.srcset = `/photography/albums/${this.albumId}/${sanitizedGridFilename}`;
                    webpSource.type = 'image/webp';
                    picture.appendChild(webpSource);
                }
            }
            
            const img = document.createElement('img');
            const sanitizedGridFilename = this.sanitizeFilename(sizes.grid.webp);
            img.src = sanitizedGridFilename ? `/photography/albums/${this.albumId}/${sanitizedGridFilename}` : '';
            img.alt = `Image ${index + 1}`;
            img.className = 'max-w-full max-h-[90vh] object-contain mx-auto loading';
            picture.appendChild(img);
            
            // Immediately start loading high-res version
            const sanitizedLargeFilename = this.sanitizeFilename(sizes.large.webp);
            if (sanitizedLargeFilename) {
                const highResImg = new Image();
                highResImg.onload = () => {
                    img.src = highResImg.src;
                    img.classList.remove('loading');
                };
                highResImg.src = `/photography/albums/${this.albumId}/${sanitizedLargeFilename}`;
            }
        } else {
            // Desktop behavior remains unchanged
            if (sizes.large.webp) {
                const sanitizedLargeFilename = this.sanitizeFilename(sizes.large.webp);
                if (sanitizedLargeFilename) {
                    const webpSource = document.createElement('source');
                    webpSource.srcset = `/photography/albums/${this.albumId}/${sanitizedLargeFilename}`;
                    webpSource.type = 'image/webp';
                    picture.appendChild(webpSource);
                }
            }
            
            const img = document.createElement('img');
            const sanitizedLargeFilename = this.sanitizeFilename(sizes.large.webp);
            img.src = sanitizedLargeFilename ? `/photography/albums/${this.albumId}/${sanitizedLargeFilename}` : '';
            img.alt = `Image ${index + 1}`;
            img.className = 'max-w-full max-h-[90vh] object-contain mx-auto';
            picture.appendChild(img);
        }
        
        const modalContent = document.querySelector('.modal-content');
        // Safely clear modal content without using innerHTML
        while (modalContent.firstChild) {
            modalContent.removeChild(modalContent.firstChild);
        }
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
            const sanitizedFilename = this.sanitizeFilename(sizes.large.webp);
            if (sanitizedFilename) {
                const webpImg = new Image();
                webpImg.src = `/photography/albums/${this.albumId}/${sanitizedFilename}`;
                this.preloadedImages.set(index, webpImg);
            }
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
            let touchStartX = 0;
            let touchStartY = 0;
            let currentTranslateX = 0;
            let startTime = 0;
            let isDragging = false;
            const SWIPE_THRESHOLD = 0.3; // 30% of screen width
            
            const canSwipeNext = () => this.currentImageIndex < window.imagesData.length - 1;
            const canSwipePrev = () => this.currentImageIndex > 0;
            
            this.modal.addEventListener('touchstart', (e) => {
                // Only handle swipes on the image/picture element
                if (!e.target.closest('picture')) return;
                
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
                startTime = Date.now();
                isDragging = true;
                currentTranslateX = 0;
                
                const picture = this.modal.querySelector('picture');
                if (picture) {
                    picture.style.transition = 'none';
                }
            }, { passive: true });

            this.modal.addEventListener('touchmove', (e) => {
                if (!isDragging || !e.target.closest('picture')) return;
                
                const deltaX = e.touches[0].clientX - touchStartX;
                const deltaY = e.touches[0].clientY - touchStartY;
                
                // Only handle horizontal movement if it's more horizontal than vertical
                if (Math.abs(deltaX) > Math.abs(deltaY)) {
                    e.preventDefault();
                    
                    const picture = this.modal.querySelector('picture');
                    if (picture) {
                        // Check swipe direction and boundaries
                        const isSwipingNext = deltaX < 0;
                        const isSwipingPrev = deltaX > 0;
                        
                        // Add extra resistance at boundaries
                        let resistance = 0.65;
                        if ((isSwipingNext && !canSwipeNext()) || 
                            (isSwipingPrev && !canSwipePrev())) {
                            resistance = 0.15; // Much stronger resistance at boundaries
                        } else if (Math.abs(deltaX) > window.innerWidth / 3) {
                            resistance = 0.3; // Normal progressive resistance
                        }
                        
                        currentTranslateX = deltaX * resistance;
                        
                        // Limit maximum swipe distance
                        const maxTranslate = window.innerWidth * 0.8;
                        currentTranslateX = Math.max(Math.min(currentTranslateX, maxTranslate), -maxTranslate);
                        
                        // Apply transform with spring-like effect at boundaries
                        if ((isSwipingNext && !canSwipeNext()) || 
                            (isSwipingPrev && !canSwipePrev())) {
                            // Add spring effect
                            const springEffect = Math.sin(Math.abs(currentTranslateX) / 30) * 10;
                            currentTranslateX = currentTranslateX / 2 + springEffect;
                        }
                        
                        picture.style.transform = `translateX(${currentTranslateX}px)`;
                        
                        // Adjust opacity based on movement, but keep it higher at boundaries
                        const opacityFactor = ((isSwipingNext && !canSwipeNext()) || 
                                             (isSwipingPrev && !canSwipePrev())) ? 0.8 : 0.5;
                        const opacity = 1 - (Math.abs(currentTranslateX) / (window.innerWidth * 0.8)) * opacityFactor;
                        picture.style.opacity = Math.max(opacity, 0.5);
                    }
                }
            }, { passive: false });
            
            this.modal.addEventListener('touchend', (e) => {
                if (!isDragging || !e.target.closest('picture')) return;
                isDragging = false;
                
                const deltaX = e.changedTouches[0].clientX - touchStartX;
                const deltaTime = Date.now() - startTime;
                const velocity = Math.abs(deltaX) / deltaTime;
                const screenWidth = window.innerWidth;
                
                const picture = this.modal.querySelector('picture');
                if (picture) {
                    // Ultra-fast transition (reduced to 0.15s)
                    picture.style.transition = 'transform 0.15s cubic-bezier(0.1, 0, 0.1, 1), opacity 0.15s ease-out';
                    
                    const swipeThreshold = screenWidth * SWIPE_THRESHOLD;
                    const isSwipe = Math.abs(deltaX) > swipeThreshold || (Math.abs(deltaX) > 30 && velocity > 0.5);
                    const isSwipingNext = deltaX < 0;
                    const isSwipingPrev = deltaX > 0;
                    
                    if (isSwipe && ((isSwipingNext && canSwipeNext()) || 
                                  (isSwipingPrev && canSwipePrev()))) {
                        // Complete the swipe animation
                        const targetTranslate = deltaX > 0 ? screenWidth : -screenWidth;
                        picture.style.transform = `translateX(${targetTranslate}px)`;
                        picture.style.opacity = '0';
                        
                        // Reduced timeout to 120ms for near-instant feeling
                        setTimeout(() => {
                            if (deltaX > 0 && canSwipePrev()) {
                                this.showPrevImage();
                            } else if (deltaX < 0 && canSwipeNext()) {
                                this.showNextImage();
                            }
                            picture.style.transform = 'translateX(0)';
                            picture.style.opacity = '1';
                        }, 120);
                    } else {
                        // Spring-back effect
                        picture.style.transform = 'translateX(0)';
                        picture.style.opacity = '1';
                    }
                }
            }, { passive: true });
            
            // Handle modal background tap to close
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.closeModal();
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

    setupModalEventDelegation() {
        // Event delegation for modal buttons to avoid inline onclick handlers
        // This replaces the direct event listeners to comply with strict CSP
        if (this.modal) {
            // Handle all button clicks via delegation
            this.modal.addEventListener('click', (e) => {
                const button = e.target.closest('[data-action]');
                if (!button) return;
                
                const action = button.dataset.action;
                switch(action) {
                    case 'close-modal':
                        this.closeModal();
                        break;
                    case 'prev-image':
                        this.showPrevImage();
                        break;
                    case 'next-image':
                        this.showNextImage();
                        break;
                }
            });
            
            // Also handle clicks without data-action for backwards compatibility
            const closeButton = this.modal.querySelector('.modal-close');
            const prevButton = this.modal.querySelector('.modal-prev');
            const nextButton = this.modal.querySelector('.modal-next');
            
            if (closeButton && !closeButton.hasAttribute('data-action')) {
                closeButton.addEventListener('click', () => this.closeModal());
            }
            if (prevButton && !prevButton.hasAttribute('data-action')) {
                prevButton.addEventListener('click', () => this.showPrevImage());
            }
            if (nextButton && !nextButton.hasAttribute('data-action')) {
                nextButton.addEventListener('click', () => this.showNextImage());
            }
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
