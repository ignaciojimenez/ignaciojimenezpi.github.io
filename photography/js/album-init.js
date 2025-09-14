// Album initialization script - moved from inline to comply with strict CSP
document.addEventListener('DOMContentLoaded', () => {
    window.albumViewer = new AlbumViewer();
    albumViewer.init();
});
