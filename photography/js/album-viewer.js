class AlbumViewer {
    constructor() {
        this.currentImageIndex = 0;
        this.modal = document.getElementById('imageModal');
        this.gallery = document.getElementById('gallery');
        this.imageBuffer = new Map();
        this.setupEventListeners();
        this.targetHeight = 315;
        this.isResizing = false;
        this.albumId = this.getAlbumIdFromUrl();
        
        // Create intersection observer
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

        // Debounce resize handler
        this.debouncedResize = this.debounce(() => {
            if (window.imagesData) {
                this.isResizing = false;
                this.reflow();
            }
        }, 150);

        window.addEventListener('resize', () => {
            if (!this.isResizing) {
                this.isResizing = true;
                document.querySelectorAll('.gallery-item').forEach(item => {
                    item.classList.add('resizing');
                });
            }
            this.debouncedResize();
        });
    }

    getAlbumIdFromUrl() {
        const path = window.location.pathname;
        // Remove trailing slash if present
        const cleanPath = path.endsWith('/') ? path.slice(0, -1) : path;
        const parts = cleanPath.split('/');
        const albumId = parts[parts.length - 1];
        console.log('Clean path:', cleanPath);
        console.log('Album ID:', albumId);
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
            const response = await fetch('/photography/albums/albums.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            // Find the current album
            const album = data.albums.find(a => a.id === this.albumId);
            if (!album) {
                throw new Error('Album not found');
            }

            // Load album metadata
            let metadata = null;
            try {
                console.log('Loading metadata for album:', this.albumId);
                const metadataResponse = await fetch(`/photography/albums/${this.albumId}/metadata.json`);
                if (metadataResponse.ok) {
                    metadata = await metadataResponse.json();
                    console.log('Raw metadata:', metadata);
                }
            } catch (error) {
                console.warn('Could not load metadata:', error);
            }

            // Update page title and metadata
            document.title = `${album.title} - Ignacio Jiménez Pi`;
            if (album.description) {
                const metaDesc = document.querySelector('meta[name="description"]');
                if (metaDesc) {
                    metaDesc.content = album.description;
                }
            }

            // Process images with metadata if available
            window.imagesData = album.images.map(imagePath => {
                const filename = imagePath.split('/').pop();
                console.log('Processing image:', filename, 'from path:', imagePath);
                
                // Get metadata for this image
                const imageMetadata = metadata?.[filename];
                console.log('Found metadata:', imageMetadata);

                if (imageMetadata) {
                    // Create a deep copy to avoid modifying the original metadata
                    const processedMetadata = JSON.parse(JSON.stringify(imageMetadata));
                    
                    // If metadata doesn't have paths, generate them
                    if (!processedMetadata.original.path) {
                        processedMetadata.original = {
                            ...processedMetadata.original,
                            path: `images/${filename}`,
                            webp: `images/${filename.replace('.jpg', '.webp')}`
                        };
                        
                        const sizes = ['thumbnail', 'small', 'medium', 'large'];
                        processedMetadata.responsive = {};
                        sizes.forEach(size => {
                            if (imageMetadata.responsive[size]) {
                                processedMetadata.responsive[size] = {
                                    ...imageMetadata.responsive[size],
                                    path: `responsive/${size}/${filename}`,
                                    webp: `responsive/${size}/${filename.replace('.jpg', '.webp')}`
                                };
                            }
                        });
                    } else {
                        // Clean up paths to be relative to the album
                        processedMetadata.original.path = processedMetadata.original.path
                            .replace(`albums/${this.albumId}/`, '')
                            .replace('albums/', '');
                        processedMetadata.original.webp = processedMetadata.original.webp
                            .replace(`albums/${this.albumId}/`, '')
                            .replace('albums/', '');
                        
                        Object.values(processedMetadata.responsive).forEach(size => {
                            size.path = size.path
                                .replace(`albums/${this.albumId}/`, '')
                                .replace('albums/', '');
                            size.webp = size.webp
                                .replace(`albums/${this.albumId}/`, '')
                                .replace('albums/', '');
                        });
                    }
                    
                    console.log('Processed metadata:', processedMetadata);
                    return {
                        filename,
                        path: imagePath,
                        metadata: processedMetadata
                    };
                }
                
                return {
                    filename,
                    path: imagePath,
                    metadata: null
                };
            });
            
            console.log('Processed image data:', window.imagesData);
            this.processImages(window.imagesData);
        } catch (error) {
            console.error('Error loading album:', error);
            this.gallery.innerHTML = '<p class="text-red-500">Error loading album</p>';
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
        const images = window.imagesData;
        if (!images || images.length === 0) return;

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

        images.forEach((image, index) => {
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

            if (currentRow.length === maxImagesPerRow || index === images.length - 1) {
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
            console.log('Creating srcset for image:', filename);
            console.log('Image data:', imageData);
            console.log('Responsive data:', imageData.metadata.responsive);
            
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
            
            console.log('Generated srcset entries:', srcsetEntries);
            
            if (srcsetEntries.length > 0) {
                img.srcset = srcsetEntries.join(', ');
                img.sizes = '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw';
                // Use medium size as fallback, or the first available size
                const mediumPath = imageData.metadata.responsive.medium?.path || imageData.metadata.responsive[sizes.find(size => imageData.metadata.responsive[size]?.path)]?.path;
                img.src = mediumPath || imageData.path;
            } else {
                img.src = imageData.path;
            }
        } else {
            console.log('No metadata found for image:', imageData);
            img.src = imageData.path;
        }
        
        img.alt = `Image ${index + 1}`;
        img.loading = 'lazy';
        
        imageCard.appendChild(img);
        imageCard.addEventListener('click', () => this.openModal(index));
        
        return imageCard;
    }

    setupEventListeners() {
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
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

    showImage(index) {
        const modalImage = document.getElementById('modalImage');
        const imageData = window.imagesData[index];
        
        if (imageData.metadata?.responsive) {
            // For modal view, use the largest available size or original
            const largePath = imageData.metadata.responsive.large?.path || imageData.metadata.original.path;
            const largeWidth = imageData.metadata.responsive.large?.width || imageData.metadata.original.width;
            const srcset = `${largePath} ${largeWidth}w, ${imageData.metadata.original.path} ${imageData.metadata.original.width}w`;
            modalImage.srcset = srcset;
            modalImage.sizes = '100vw'; // Modal takes full viewport width
            modalImage.src = largePath || imageData.path; // Fallback
        } else {
            modalImage.src = imageData.path;
        }
        
        this.currentImageIndex = index;
    }

    openModal(index) {
        this.modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        this.showImage(index);
    }

    closeModal() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    showNextImage() {
        const nextIndex = (this.currentImageIndex + 1) % window.imagesData.length;
        this.showImage(nextIndex);
    }

    showPrevImage() {
        const prevIndex = (this.currentImageIndex - 1 + window.imagesData.length) % window.imagesData.length;
        this.showImage(prevIndex);
    }
}
