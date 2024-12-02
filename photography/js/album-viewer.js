class AlbumViewer {
    constructor() {
        this.currentImageIndex = 0;
        this.modal = document.getElementById('imageModal');
        this.gallery = document.getElementById('gallery');
        this.imageBuffer = [];
        this.loadedImages = 0;
        this.setupEventListeners();
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
                this.setupResizeHandler();
            })
            .catch(error => {
                console.error('Error loading album:', error);
                this.gallery.innerHTML = '<p class="text-red-500">Error loading album</p>';
            });
    }

    processImages(images) {
        this.gallery.innerHTML = '';
        images.forEach((filename, index) => {
            const imageCard = this.createImageCard(filename, index);
            this.loadImage(imageCard, filename, index);
        });
    }

    createImageCard(filename, index) {
        const imageCard = document.createElement('div');
        imageCard.className = 'gallery-item';
        imageCard.onclick = () => this.openModal(index);

        const imageContainer = document.createElement('div');
        imageContainer.className = 'image-container';
        imageCard.appendChild(imageContainer);

        const placeholder = document.createElement('div');
        placeholder.className = 'placeholder';
        placeholder.innerHTML = '<svg class="animate-spin h-8 w-8 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';
        imageContainer.appendChild(placeholder);

        return imageCard;
    }

    loadImage(imageCard, filename, index) {
        const img = document.createElement('img');
        img.style.opacity = '0';
        img.style.transition = 'opacity 0.3s ease-in';
        img.dataset.index = index;
        img.alt = filename.replace(/\.[^/.]+$/, '').replace(/-/g, ' ');
        img.src = `images/${filename}`;

        img.onload = () => this.handleImageLoad(img, imageCard, index);
        img.onerror = () => this.handleImageError(imageCard);

        const imageContainer = imageCard.querySelector('.image-container');
        imageContainer.appendChild(img);
    }

    handleImageLoad(img, imageCard, index) {
        img.style.opacity = '1';
        const placeholder = imageCard.querySelector('.placeholder');
        if (placeholder) {
            placeholder.style.opacity = '0';
            setTimeout(() => placeholder.remove(), 300);
        }

        this.imageBuffer[index] = {
            img,
            card: imageCard,
            aspectRatio: img.naturalWidth / img.naturalHeight
        };
        this.loadedImages++;

        setTimeout(() => {
            imageCard.classList.add('loaded');
        }, 100);

        this.createGalleryRows();
    }

    handleImageError(imageCard) {
        const placeholder = imageCard.querySelector('.placeholder');
        if (placeholder) {
            placeholder.innerHTML = '<span class="text-red-500">Failed to load image</span>';
        }
        this.loadedImages++;
    }

    createGalleryRows() {
        if (this.loadedImages < window.imagesData.length) return;

        this.gallery.innerHTML = '';
        const containerWidth = this.gallery.clientWidth;
        const targetRowHeight = 300;
        let currentRow = [];
        let currentRowWidth = 0;

        this.imageBuffer.forEach((imgData, index) => {
            if (!imgData) return;
            
            const { card, aspectRatio } = imgData;
            const imgWidth = targetRowHeight * aspectRatio;
            
            if (currentRow.length > 0 && (currentRowWidth + imgWidth > containerWidth || currentRow.length === 3)) {
                this.finalizeRow(currentRow, currentRowWidth, containerWidth, targetRowHeight);
                currentRow = [];
                currentRowWidth = 0;
            }

            currentRow.push({ card, width: imgWidth });
            currentRowWidth += imgWidth;

            if (index === this.imageBuffer.length - 1 && currentRow.length > 0) {
                this.finalizeRow(currentRow, currentRowWidth, containerWidth, targetRowHeight);
            }
        });
    }

    finalizeRow(row, rowWidth, containerWidth, targetHeight) {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'gallery-row';
        
        const gap = 10;
        const totalGapWidth = (row.length - 1) * gap;
        const scale = (containerWidth - totalGapWidth) / rowWidth;
        
        row.forEach(item => {
            const width = Math.floor(item.width * scale);
            item.card.style.width = `${width}px`;
            item.card.style.height = `${Math.floor(targetHeight)}px`;
            rowDiv.appendChild(item.card);
        });

        this.gallery.appendChild(rowDiv);
    }

    setupResizeHandler() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => this.createGalleryRows(), 100);
        });
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
