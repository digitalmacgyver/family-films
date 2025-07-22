/**
 * Animated Thumbnails JavaScript
 * Handles Swiper-based hover animations for film thumbnails
 */

class SwiperThumbnail {
    constructor(element) {
        this.element = element;
        this.frameSwiper = element.querySelector('.frame-swiper');
        this.staticThumbnail = element.querySelector('.static-thumbnail');
        
        // Determine animation type and set appropriate frame count
        this.animationType = element.dataset.animationType || 'sprite';
        if (this.animationType === 'chapter') {
            // Count actual slides for chapter-based animation
            this.frameCount = element.querySelectorAll('.swiper-slide').length;
            this.frameInterval = parseFloat(element.dataset.frameInterval) || 1000; // Default 1 second for chapters
        } else {
            // Legacy sprite-based animation
            this.frameCount = parseInt(element.dataset.frameCount) || 0;
            this.frameInterval = parseFloat(element.dataset.frameInterval) || 800; // Default 0.8 seconds for sprites
        }
        
        this.swiperInstance = null;
        this.isHovering = false;
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        // Check if we have valid animation data
        if (!this.frameSwiper || this.frameCount === 0) {
            console.warn('Invalid animation data for thumbnail');
            return;
        }
        
        // Bind events
        this.element.addEventListener('mouseenter', this.startAnimation.bind(this));
        this.element.addEventListener('mouseleave', this.stopAnimation.bind(this));
    }
    
    initializeSwiper() {
        if (this.isInitialized || !this.frameSwiper) return;
        
        try {
            this.swiperInstance = new Swiper(this.frameSwiper, {
                loop: true,
                autoplay: false,
                speed: 300,
                allowTouchMove: false,
                simulateTouch: false,
                watchSlidesProgress: true,
                preloadImages: true,
                updateOnImagesReady: true
            });
            
            this.isInitialized = true;
            console.log('Swiper initialized for thumbnail');
        } catch (error) {
            console.warn('Failed to initialize Swiper:', error);
        }
    }
    
    startAnimation() {
        if (this.isHovering) return;
        
        this.isHovering = true;
        
        // Initialize Swiper if not already done
        if (!this.isInitialized) {
            this.initializeSwiper();
        }
        
        if (this.swiperInstance && this.frameCount > 1) {
            // Start autoplay with custom interval
            // frameInterval is already in milliseconds for chapters, needs conversion for sprites
            const delayMs = this.animationType === 'chapter' ? this.frameInterval : this.frameInterval * 1000;
            
            this.swiperInstance.params.autoplay = {
                delay: delayMs,
                disableOnInteraction: false
            };
            this.swiperInstance.autoplay.start();
        }
    }
    
    stopAnimation() {
        this.isHovering = false;
        
        if (this.swiperInstance) {
            this.swiperInstance.autoplay.stop();
            // Reset to first slide
            this.swiperInstance.slideTo(0, 300);
        }
    }
    
    destroy() {
        if (this.swiperInstance) {
            this.swiperInstance.destroy(true, true);
            this.swiperInstance = null;
            this.isInitialized = false;
        }
    }
}

// Mobile detection
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
           window.matchMedia('(max-width: 768px)').matches;
}

// Initialize animated thumbnails
document.addEventListener('DOMContentLoaded', function() {
    // Skip initialization on mobile devices
    if (isMobileDevice()) {
        console.log('Mobile device detected, skipping animated thumbnails');
        return;
    }
    
    const swiperThumbnails = document.querySelectorAll('.swiper-thumbnail');
    const thumbnailInstances = [];
    
    swiperThumbnails.forEach(element => {
        try {
            const instance = new SwiperThumbnail(element);
            thumbnailInstances.push(instance);
        } catch (error) {
            console.warn('Failed to initialize swiper thumbnail:', error);
        }
    });
    
    console.log(`Initialized ${thumbnailInstances.length} swiper thumbnails`);
});

// Performance optimization: Intersection Observer for lazy loading
if ('IntersectionObserver' in window) {
    const thumbnailObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const thumbnail = entry.target.querySelector('.swiper-thumbnail');
                if (thumbnail && !thumbnail.classList.contains('preloaded')) {
                    thumbnail.classList.add('preloaded');
                    // Preload frame images when thumbnail comes into view
                    const frameImages = thumbnail.querySelectorAll('.frame-image');
                    frameImages.forEach(img => {
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                        }
                    });
                }
            }
        });
    }, {
        rootMargin: '100px'
    });
    
    // Observe all film thumbnail containers
    document.addEventListener('DOMContentLoaded', function() {
        const containers = document.querySelectorAll('.film-thumbnail-container');
        containers.forEach(container => {
            thumbnailObserver.observe(container);
        });
    });
}