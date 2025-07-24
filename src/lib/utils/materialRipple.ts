/**
 * Material Design Ripple Effect Utility
 * Creates ripple effects that start from the touch/click point
 */

export interface RippleOptions {
  color?: string;
  duration?: number;
  opacity?: number;
}

/**
 * Add ripple effect to an element
 */
export function addRippleEffect(element: HTMLElement, options: RippleOptions = {}): void {
  const {
    color = 'rgba(255, 255, 255, 0.3)',
    duration = 600,
    opacity = 1
  } = options;

  // Remove existing ripple listeners to avoid duplicates
  removeRippleEffect(element);

  const rippleHandler = (event: MouseEvent | TouchEvent) => {
    createRipple(element, event, { color, duration, opacity });
  };

  // Store the handler for later removal
  (element as any)._rippleHandler = rippleHandler;

  // Add event listeners for both mouse and touch events
  element.addEventListener('mousedown', rippleHandler);
  element.addEventListener('touchstart', rippleHandler);
}

/**
 * Remove ripple effect from an element
 */
export function removeRippleEffect(element: HTMLElement): void {
  const handler = (element as any)._rippleHandler;
  if (handler) {
    element.removeEventListener('mousedown', handler);
    element.removeEventListener('touchstart', handler);
    delete (element as any)._rippleHandler;
  }
}

/**
 * Create a ripple effect at the specified position
 */
function createRipple(
  element: HTMLElement, 
  event: MouseEvent | TouchEvent, 
  options: RippleOptions
): void {
  const rect = element.getBoundingClientRect();
  
  // Get the touch/click position
  let clientX: number, clientY: number;
  
  if (event instanceof TouchEvent && event.touches.length > 0) {
    clientX = event.touches[0].clientX;
    clientY = event.touches[0].clientY;
  } else if (event instanceof MouseEvent) {
    clientX = event.clientX;
    clientY = event.clientY;
  } else {
    // Fallback to center if we can't determine position
    clientX = rect.left + rect.width / 2;
    clientY = rect.top + rect.height / 2;
  }

  // Calculate position relative to the element
  const x = clientX - rect.left;
  const y = clientY - rect.top;

  // Calculate the maximum distance to ensure the ripple covers the entire element
  const maxDistance = Math.max(
    Math.sqrt(x * x + y * y),
    Math.sqrt((rect.width - x) * (rect.width - x) + y * y),
    Math.sqrt(x * x + (rect.height - y) * (rect.height - y)),
    Math.sqrt((rect.width - x) * (rect.width - x) + (rect.height - y) * (rect.height - y))
  );

  // Create ripple element
  const ripple = document.createElement('span');
  ripple.className = 'material-ripple';
  ripple.style.cssText = `
    position: absolute;
    border-radius: 50%;
    background: ${options.color};
    pointer-events: none;
    transform: translate(-50%, -50%);
    animation: material-ripple ${options.duration}ms ease-out;
    left: ${x}px;
    top: ${y}px;
    width: 0;
    height: 0;
    z-index: 1000;
  `;

  // Ensure the element has relative positioning
  const originalPosition = getComputedStyle(element).position;
  if (originalPosition === 'static') {
    element.style.position = 'relative';
  }

  // Ensure overflow is hidden
  element.style.overflow = 'hidden';

  // Add ripple to element
  element.appendChild(ripple);

  // Trigger the animation
  requestAnimationFrame(() => {
    ripple.style.width = `${maxDistance * 2}px`;
    ripple.style.height = `${maxDistance * 2}px`;
    ripple.style.opacity = options.opacity?.toString() || '1';
  });

  // Remove ripple after animation
  setTimeout(() => {
    if (ripple.parentNode) {
      ripple.parentNode.removeChild(ripple);
    }
  }, options.duration || 600);
}

/**
 * Initialize Material Design ripple effects for all buttons in Material Design theme
 */
export function initializeMaterialRipples(): void {
  // Add CSS animation if not already present
  if (!document.querySelector('#material-ripple-styles')) {
    const style = document.createElement('style');
    style.id = 'material-ripple-styles';
    style.textContent = `
      @keyframes material-ripple {
        0% {
          width: 0;
          height: 0;
          opacity: 1;
        }
        100% {
          opacity: 0;
        }
      }
      
      .material-ripple {
        transition: width 0.6s ease, height 0.6s ease;
      }
    `;
    document.head.appendChild(style);
  }

  // Find all buttons and clickable elements in Material Design theme
  const selector = '.md-theme button, .md-theme .btn, .md-theme [role="button"]';
  const elements = document.querySelectorAll(selector) as NodeListOf<HTMLElement>;
  
  elements.forEach(element => {
    addRippleEffect(element);
  });
}

/**
 * Clean up all Material Design ripple effects
 */
export function cleanupMaterialRipples(): void {
  const selector = '.md-theme button, .md-theme .btn, .md-theme [role="button"]';
  const elements = document.querySelectorAll(selector) as NodeListOf<HTMLElement>;
  
  elements.forEach(element => {
    removeRippleEffect(element);
  });

  // Remove CSS styles
  const styleElement = document.querySelector('#material-ripple-styles');
  if (styleElement) {
    styleElement.remove();
  }
}

/**
 * Auto-initialize ripples when Material Design theme is applied
 */
export function autoInitializeRipples(): void {
  // Watch for theme changes
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
        const target = mutation.target as HTMLElement;
        if (target === document.documentElement) {
          if (target.classList.contains('md-theme')) {
            initializeMaterialRipples();
          } else {
            cleanupMaterialRipples();
          }
        }
      }
    });
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  });

  // Initialize immediately if Material Design theme is already active
  if (document.documentElement.classList.contains('md-theme')) {
    initializeMaterialRipples();
  }
}
