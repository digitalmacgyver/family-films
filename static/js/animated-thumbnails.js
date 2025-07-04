/**
 * Animated Thumbnails JavaScript
 * Handles sprite-based hover animations for film thumbnails
 */

class AnimatedThumbnail {
    constructor(element) {
        this.element = element;
        this.spriteOverlay = element.querySelector('.sprite-overlay');
        this.staticThumbnail = element.querySelector('.static-thumbnail');
        
        this.spriteUrl = element.dataset.spriteUrl;
        this.frameCount = parseInt(element.dataset.frameCount);
        this.frameInterval = parseFloat(element.dataset.frameInterval);
        this.spriteWidth = parseInt(element.dataset.spriteWidth);
        this.spriteHeight = parseInt(element.dataset.spriteHeight);
        
        this.animationTimer = null;
        this.currentFrame = 0;
        this.isHovering = false;
        
        this.init();
    }
    
    init() {
        // Check if we have valid animation data
        if (!this.spriteUrl || !this.frameCount || !this.spriteWidth) {
            console.warn('Invalid animation data for thumbnail');
            return;
        }
        
        // Set up sprite overlay
        this.setupSpriteOverlay();
        
        // Bind events
        this.element.addEventListener('mouseenter', this.startAnimation.bind(this));
        this.element.addEventListener('mouseleave', this.stopAnimation.bind(this));
        
        // Preload sprite image
        this.preloadSprite();
    }
    
    setupSpriteOverlay() {
        const totalWidth = this.spriteWidth * this.frameCount;
        
        // Get the actual thumbnail container dimensions
        const container = this.element.closest('.film-thumbnail-container');
        const thumbnail = this.element.querySelector('.static-thumbnail');
        
        this.spriteOverlay.style.backgroundImage = `url(${this.spriteUrl})`;
        
        // Scale the sprite to fit the thumbnail container
        if (container && thumbnail) {
            const containerRect = thumbnail.getBoundingClientRect();
            const scaleX = containerRect.width / this.spriteWidth;
            const scaledTotalWidth = totalWidth * scaleX;
            const scaledHeight = this.spriteHeight * scaleX;
            
            this.spriteOverlay.style.backgroundSize = `${scaledTotalWidth}px ${scaledHeight}px`;
        } else {
            // Fallback to original sizing
            this.spriteOverlay.style.backgroundSize = `${totalWidth}px ${this.spriteHeight}px`;
        }
        
        this.spriteOverlay.style.backgroundPosition = '0 0';
    }
    
    preloadSprite() {
        const img = new Image();
        img.onload = () => {
            this.element.classList.add('sprite-loaded');
        };
        img.onerror = () => {
            console.warn('Failed to load sprite:', this.spriteUrl);
            this.element.classList.add('sprite-error');
        };
        img.src = this.spriteUrl;
    }
    
    startAnimation() {
        if (this.isHovering || !this.spriteUrl) return;
        
        this.isHovering = true;
        this.currentFrame = 0;
        
        // Start the animation loop
        this.animationTimer = setInterval(() => {
            this.nextFrame();
        }, this.frameInterval * 1000);
        
        this.spriteOverlay.classList.add('animating');
    }
    
    stopAnimation() {
        this.isHovering = false;
        
        if (this.animationTimer) {
            clearInterval(this.animationTimer);
            this.animationTimer = null;
        }
        
        this.spriteOverlay.classList.remove('animating');
        this.currentFrame = 0;
        this.updateSpritePosition();
    }
    
    nextFrame() {
        this.currentFrame = (this.currentFrame + 1) % this.frameCount;
        this.updateSpritePosition();
    }
    
    updateSpritePosition() {
        // Calculate position as percentage for proper scaling
        const percentage = (this.currentFrame / this.frameCount) * 100;
        this.spriteOverlay.style.backgroundPosition = `${percentage}% 0`;
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
    
    const animatedThumbnails = document.querySelectorAll('.animated-thumbnail');
    const thumbnailInstances = [];
    
    animatedThumbnails.forEach(element => {
        try {
            const instance = new AnimatedThumbnail(element);
            thumbnailInstances.push(instance);
        } catch (error) {
            console.warn('Failed to initialize animated thumbnail:', error);
        }
    });
    
    console.log(`Initialized ${thumbnailInstances.length} animated thumbnails`);
});

// Performance optimization: Intersection Observer for lazy loading
if ('IntersectionObserver' in window) {
    const thumbnailObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const thumbnail = entry.target.querySelector('.animated-thumbnail');
                if (thumbnail && !thumbnail.classList.contains('initialized')) {
                    thumbnail.classList.add('initialized');
                    // Preload sprite when thumbnail comes into view
                    const spriteUrl = thumbnail.dataset.spriteUrl;
                    if (spriteUrl) {
                        const img = new Image();
                        img.src = spriteUrl;
                    }
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