async function loadBands() {
    try {
        const response = await fetch('bands.json');
        const data = await response.json();
        return data.bands;
    } catch (error) {
        console.error('Error loading bands:', error);
        return [];
    }
}

function sanitizeUrl(url) {
    // Only allow http/https URLs to prevent javascript: injection
    if (!url || typeof url !== 'string') return '#';
    const trimmed = url.trim();
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
        return trimmed;
    }
    return '#';
}

function sanitizeImageUrl(url) {
    // Basic validation for image URLs
    if (!url || typeof url !== 'string') return '';
    const trimmed = url.trim();
    
    // Allow absolute URLs, root-relative paths, and relative paths
    if (trimmed.startsWith('http://') || 
        trimmed.startsWith('https://') || 
        trimmed.startsWith('/') ||
        /^[a-zA-Z0-9][a-zA-Z0-9\-._/]*\.(jpg|jpeg|png|gif|webp|svg)$/i.test(trimmed)) {
        return trimmed;
    }
    return '';
}

function sanitizeText(text) {
    // Basic text sanitization
    if (!text || typeof text !== 'string') return '';
    return text.trim();
}

function createBandCard(band) {
    // Create elements safely using DOM methods
    const link = document.createElement('a');
    link.href = sanitizeUrl(band.spotifyUrl);
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.className = 'band-card';

    const img = document.createElement('img');
    const sanitizedImageUrl = sanitizeImageUrl(band.image);
    if (sanitizedImageUrl) {
        img.src = sanitizedImageUrl;
    }
    img.alt = sanitizeText(band.name);
    img.className = 'band-image';
    img.onerror = function() { this.classList.add('error'); };

    const overlay = document.createElement('div');
    overlay.className = 'band-overlay';

    const bandNameDiv = document.createElement('div');
    bandNameDiv.className = 'band-name';

    const h3Desktop = document.createElement('h3');
    h3Desktop.className = 'text-xl font-semibold mb-2';
    h3Desktop.textContent = sanitizeText(band.name);

    const metadataMobile = document.createElement('div');
    metadataMobile.className = 'band-metadata-mobile';

    const h3Mobile = document.createElement('h3');
    h3Mobile.textContent = sanitizeText(band.name);

    // Assemble the structure
    bandNameDiv.appendChild(h3Desktop);
    overlay.appendChild(bandNameDiv);
    metadataMobile.appendChild(h3Mobile);

    link.appendChild(img);
    link.appendChild(overlay);
    link.appendChild(metadataMobile);

    return link;
}

document.addEventListener('DOMContentLoaded', async () => {
    const bandGrid = document.querySelector('.band-grid');
    const bands = await loadBands();
    bands.forEach(band => {
        const bandCard = createBandCard(band);
        bandGrid.appendChild(bandCard);
    });
});
