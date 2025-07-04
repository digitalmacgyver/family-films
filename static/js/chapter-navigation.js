// Simple chapter navigation without YouTube API dependency
function navigateToChapter(seconds) {
    console.log('Navigating to chapter at', seconds, 'seconds');
    
    const iframe = document.getElementById('youtube-player');
    if (!iframe) {
        console.error('YouTube player iframe not found');
        return;
    }
    
    // Get the base URL without parameters
    const currentSrc = iframe.src;
    const baseUrl = currentSrc.split('?')[0];
    
    // Build new URL with timestamp and autoplay
    const params = new URLSearchParams({
        enablejsapi: '1',
        origin: window.location.origin,
        start: seconds,
        autoplay: '1'
    });
    
    const newSrc = `${baseUrl}?${params.toString()}`;
    console.log('Updating iframe src to:', newSrc);
    
    // Update the iframe source - this will reload the video at the specified time
    iframe.src = newSrc;
}

// Set up chapter click handlers
document.addEventListener('DOMContentLoaded', function() {
    const chapterItems = document.querySelectorAll('.chapter-item');
    console.log('Setting up chapter navigation for', chapterItems.length, 'chapters');
    
    chapterItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Don't navigate if clicking on editor elements
            if (e.target.closest('.metadata-editor') || e.target.closest('.edit-chapter-btn')) {
                return;
            }
            
            const startTime = parseInt(this.dataset.startTime);
            const chapterId = this.dataset.chapterId;
            
            if (isNaN(startTime)) {
                console.error('Invalid start time:', this.dataset.startTime);
                return;
            }
            
            console.log('Chapter clicked:', chapterId, 'Start time:', startTime);
            
            // Update active state
            chapterItems.forEach(ch => ch.classList.remove('active'));
            this.classList.add('active');
            
            // Navigate to chapter
            navigateToChapter(startTime);
        });
    });
    
    // Also handle thumbnail clicks
    const thumbnails = document.querySelectorAll('.chapter-thumbnail');
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function(e) {
            e.stopPropagation();
            const chapterItem = this.closest('.chapter-item');
            if (chapterItem) {
                chapterItem.click();
            }
        });
    });
});