class AlbumViewer {
    constructor() {
        this.currentImageIndex = 0;
        this.modal = document.getElementById('imageModal');
        this.gallery = document.getElementById('gallery');
        this.imageBuffer = new Map();
        this.setupEventListeners();
        this.targetHeight = 315;
        this.isResizing = false;
        
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

    loadAlbumImages() {
        fetch('images.json')
            .then(response => response.json())
            .then(data => {
                document.title = data.title || 'Urban - Ignacio Jiménez Pi';
                window.imagesData = data.images;
                this.processImages(data.images);
            })
            .catch(error => {
                console.error('Error loading album:', error);
                this.gallery.innerHTML = '<p class="text-red-500">Error loading album</p>';
            });
    }

    processImages(images) {
        if (!images || images.length === 0) return;
        
        const loadPromises = images.map((filename, index) => {
            return new Promise((resolve) => {
                if (this.imageBuffer.has(filename)) {
                    resolve();
                    return;
                }

                const img = new Image();
                img.src = `images/${filename}`;
                
                img.onload = () => {
                    this.imageBuffer.set(filename, {
                        aspectRatio: img.width / img.height,
                        filename
                    });
                    resolve();
                };
                
                img.onerror = () => {
                    console.error(`Failed to load image: ${filename}`);
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

        images.forEach((filename, index) => {
            const imageData = this.imageBuffer.get(filename);
            if (!imageData) return;

            currentRowAspectRatios.push(imageData.aspectRatio);
            
            let imageCard;
            if (existingItems.has(filename)) {
                imageCard = existingItems.get(filename);
                imageCard.style.removeProperty('width');
                imageCard.style.removeProperty('height');
            } else {
                imageCard = this.createImageCard(filename, index);
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
        img.src = `images/${filename}`;
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
        modalImage.src = `images/${window.imagesData[index]}`;
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
