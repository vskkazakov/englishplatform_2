// Enhanced futuristic platform for English learning

class EnglishFuturePlatform {
    constructor() {
        this.init();
    }

    init() {
        this.addAlertStyles();
        this.bindEvents();
        this.initAnimations();
        this.initParticleSystem();
    }

    bindEvents() {
        // Add click handlers for all feature buttons
        document.addEventListener('click', (e) => {
            const button = e.target.closest('.feature-btn');
            if (button) {
                const action = button.getAttribute('data-action');
                this.handleFeatureClick(action, button);
                e.preventDefault();
            }
        });

        // Add hover effects for feature cards
        const featureCards = document.querySelectorAll('.feature-card');
        featureCards.forEach(card => {
            card.addEventListener('mouseenter', (e) => {
                this.handleCardHover(e.target, true);
            });
            card.addEventListener('mouseleave', (e) => {
                this.handleCardHover(e.target, false);
            });
        });

        // Add scroll effects
        window.addEventListener('scroll', () => {
            this.handleScroll();
        });

        // Add click effect for orb
        const orb = document.querySelector('.orb');
        if (orb) {
            orb.addEventListener('click', () => {
                this.handleOrbClick();
            });
        }

        console.log('Events bound successfully');
    }

    handleFeatureClick(action, button) {
        console.log('Feature clicked:', action);

        const appUrls = {
            'dictionary': '/dictionary', // замените на реальные URL
            'tests': '/tests',
            'games': '/games',
        };

        if (!window.isAuthenticated && ['dictionary', 'tests', 'games'].includes(action)) {
            this.showFuturisticAlert(`
                <p>Чтобы воспользоваться этой функцией, пожалуйста, зарегистрируйтесь.</p>
                <a href="${window.registrationUrl}" class="btn-register" style="
                    display:inline-block;
                    margin-top:18px;
                    padding:12px 38px;
                    background:linear-gradient(45deg, #6A0DAD, #1E90FF);
                    color:#fff;
                    border-radius:30px;
                    font-weight:600;
                    font-size:16px;
                    box-shadow:0 2px 12px rgba(138,43,226,0.4);
                    text-decoration:none;
                    transition:background 0.3s;
                ">Перейти к регистрации</a>
            `);
            return;
        }

        // Если пользователь зарегистрирован и для action есть URL — перейти
        if (window.isAuthenticated && appUrls[action]) {
            window.location.href = appUrls[action];
        }
    }



    handleCardHover(card, isEntering) {
        const icon = card.querySelector('.feature-icon div');
        const title = card.querySelector('.feature-title');
        
        if (isEntering) {
            // Enhanced hover effects
            card.style.transform = 'translateY(-15px) scale(1.02)';
            card.style.boxShadow = '0 25px 50px rgba(138, 43, 226, 0.4), 0 0 60px rgba(30, 144, 255, 0.3)';
            
            if (icon) {
                icon.style.transform = 'scale(1.1) rotate(5deg)';
                icon.style.boxShadow = '0 0 30px rgba(138, 43, 226, 0.8), 0 0 50px rgba(30, 144, 255, 0.6)';
            }
            
            if (title) {
                title.style.textShadow = '0 0 20px rgba(138, 43, 226, 0.8)';
                title.style.transform = 'scale(1.05)';
            }
            
            this.createHoverParticles(card);
        } else {
            // Reset hover effects
            card.style.transform = 'translateY(0) scale(1)';
            card.style.boxShadow = '';
            
            if (icon) {
                icon.style.transform = 'scale(1) rotate(0deg)';
                icon.style.boxShadow = '';
            }
            
            if (title) {
                title.style.textShadow = '0 0 10px rgba(255, 255, 255, 0.5)';
                title.style.transform = 'scale(1)';
            }
        }
    }

    handleScroll() {
        const scrolled = window.pageYOffset;
        const parallax = scrolled * 0.3;
        
        // Parallax effect for hero visual
        const heroVisual = document.querySelector('.hero-visual');
        if (heroVisual) {
            heroVisual.style.transform = `translateY(${parallax}px)`;
        }

        // Fade in animation for feature cards
        const featureCards = document.querySelectorAll('.feature-card');
        featureCards.forEach((card, index) => {
            const cardTop = card.offsetTop;
            const cardHeight = card.offsetHeight;
            const windowHeight = window.innerHeight;
            
            if (scrolled + windowHeight > cardTop + cardHeight / 4) {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
                card.style.transition = `all 0.8s cubic-bezier(0.23, 1, 0.32, 1) ${index * 0.15}s`;
            }
        });
    }

    handleOrbClick() {
        const orb = document.querySelector('.orb');
        if (orb) {
            // Create explosion effect
            orb.style.animation = 'orbRotate 0.5s linear, orbFloat 4s ease-in-out infinite alternate';
            orb.style.transform = 'scale(1.1)';
            
            // Create energy burst particles
            this.createEnergyBurst(orb);
            
            // Show special message
            setTimeout(() => {
                this.showFuturisticAlert('⚡ ЭНЕРГЕТИЧЕСКОЕ ЯДРО АКТИВИРОВАНО! ⚡\\n\\nСистема обучения получила дополнительную мощность!\\nВсе функции платформы работают на максимальной производительности.');
            }, 500);
            
            setTimeout(() => {
                orb.style.transform = 'scale(1)';
            }, 500);
        }
    }

    showFuturisticAlert(message) {
        console.log('Showing alert:', message);
        
        // Remove existing alert if any
        const existingAlert = document.querySelector('.futuristic-alert-overlay');
        if (existingAlert) {
            existingAlert.remove();
        }

        // Create custom futuristic alert overlay
        const alertOverlay = document.createElement('div');
        alertOverlay.className = 'futuristic-alert-overlay';
        
        const alertBox = document.createElement('div');
        alertBox.className = 'futuristic-alert';
        
        const alertContent = document.createElement('div');
        alertContent.className = 'alert-content';
        alertContent.innerHTML = message.replace(/\\n/g, '<br>');
        
        const alertButton = document.createElement('button');
        alertButton.className = 'alert-btn';
        alertButton.innerHTML = 'Понятно';
        
        alertBox.appendChild(alertContent);
        alertBox.appendChild(alertButton);
        alertOverlay.appendChild(alertBox);
        document.body.appendChild(alertOverlay);

        // Animate in
        requestAnimationFrame(() => {
            alertOverlay.classList.add('show');
        });

        // Close functionality
        const closeAlert = () => {
            alertOverlay.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(alertOverlay)) {
                    document.body.removeChild(alertOverlay);
                }
            }, 300);
        };

        alertButton.addEventListener('click', closeAlert);
        alertOverlay.addEventListener('click', (e) => {
            if (e.target === alertOverlay) closeAlert();
        });

        // Auto close after 8 seconds
        setTimeout(closeAlert, 8000);
    }

    addAlertStyles() {
        if (document.querySelector('#alert-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'alert-styles';
        style.textContent = `
            .futuristic-alert-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.85);
                backdrop-filter: blur(15px);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: 0;
                transition: opacity 0.4s cubic-bezier(0.23, 1, 0.32, 1);
            }

            .futuristic-alert-overlay.show {
                opacity: 1;
            }

            .futuristic-alert {
                background: linear-gradient(145deg, rgba(15, 15, 35, 0.98), rgba(45, 27, 105, 0.95));
                border: 2px solid #8A2BE2;
                border-radius: 20px;
                padding: 40px;
                max-width: 500px;
                min-width: 400px;
                text-align: center;
                box-shadow:
                    0 25px 80px rgba(138, 43, 226, 0.6),
                    0 0 100px rgba(30, 144, 255, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
                animation: alertSlideIn 0.5s cubic-bezier(0.23, 1, 0.32, 1);
                position: relative;
                overflow: hidden;
            }

            .futuristic-alert::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 3px;
                background: linear-gradient(90deg, transparent, #8A2BE2, #1E90FF, #8A2BE2, transparent);
                animation: alertBeam 3s ease-in-out infinite;
            }

            .futuristic-alert::after {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(138, 43, 226, 0.1) 0%, transparent 50%);
                transform: translate(-50%, -50%);
                animation: alertPulse 2s ease-in-out infinite;
                pointer-events: none;
            }

            .alert-content {
                color: #ffffff;
                font-size: 18px;
                line-height: 1.7;
                margin-bottom: 30px;
                text-shadow: 0 0 15px rgba(255, 255, 255, 0.6);
                position: relative;
                z-index: 1;
                font-weight: 500;
            }

            .alert-btn {
                background: linear-gradient(45deg, #6A0DAD, #4B0082, #1E90FF);
                border: none;
                border-radius: 30px;
                padding: 15px 40px;
                color: #ffffff;
                font-weight: 600;
                font-size: 18px;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
                text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                position: relative;
                overflow: hidden;
                z-index: 1;
                box-shadow: 0 8px 25px rgba(138, 43, 226, 0.4);
            }

            .alert-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
                transition: left 0.5s ease;
            }

            .alert-btn:hover {
                transform: scale(1.08) translateY(-2px);
                box-shadow: 0 15px 40px rgba(138, 43, 226, 0.7);
            }

            .alert-btn:hover::before {
                left: 100%;
            }

            .alert-btn:active {
                transform: scale(1.02) translateY(0);
            }

            @keyframes alertSlideIn {
                0% {
                    transform: translateY(-80px) scale(0.8);
                    opacity: 0;
                    filter: blur(10px);
                }
                100% {
                    transform: translateY(0) scale(1);
                    opacity: 1;
                    filter: blur(0);
                }
            }

            @keyframes alertBeam {
                0% { left: -100%; }
                50% { left: 100%; }
                100% { left: 100%; }
            }

            @keyframes alertPulse {
                0%, 100% { opacity: 0.3; transform: translate(-50%, -50%) scale(1); }
                50% { opacity: 0.6; transform: translate(-50%, -50%) scale(1.1); }
            }

            @media (max-width: 480px) {
                .futuristic-alert {
                    min-width: 90%;
                    padding: 30px 20px;
                }
                .alert-content {
                    font-size: 16px;
                }
            }
        `;
        
        document.head.appendChild(style);
    }

    createClickRipple(element) {
        const ripple = document.createElement('div');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height) * 1.5;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(138,43,226,0.6) 30%, rgba(30,144,255,0.4) 60%, transparent 100%);
            transform: scale(0);
            animation: rippleEffect 0.8s cubic-bezier(0.23, 1, 0.32, 1);
            pointer-events: none;
            top: 50%;
            left: 50%;
            margin-left: ${-size/2}px;
            margin-top: ${-size/2}px;
            z-index: 2;
        `;
        
        element.style.position = 'relative';
        element.appendChild(ripple);
        
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.remove();
            }
        }, 800);

        // Add ripple animation if not exists
        if (!document.querySelector('#ripple-styles')) {
            const style = document.createElement('style');
            style.id = 'ripple-styles';
            style.textContent = `
                @keyframes rippleEffect {
                    0% { transform: scale(0); opacity: 1; }
                    100% { transform: scale(1); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    createHoverParticles(card) {
        const rect = card.getBoundingClientRect();
        
        for (let i = 0; i < 8; i++) {
            setTimeout(() => {
                const particle = document.createElement('div');
                particle.style.cssText = `
                    position: fixed;
                    width: ${Math.random() * 4 + 2}px;
                    height: ${Math.random() * 4 + 2}px;
                    background: ${Math.random() > 0.5 ? '#8A2BE2' : '#1E90FF'};
                    border-radius: 50%;
                    box-shadow: 0 0 15px currentColor;
                    pointer-events: none;
                    z-index: 1000;
                    animation: hoverParticleFloat 2.5s ease-out forwards;
                    left: ${rect.left + Math.random() * rect.width}px;
                    top: ${rect.top + Math.random() * rect.height}px;
                `;
                
                document.body.appendChild(particle);
                
                setTimeout(() => {
                    if (particle.parentNode) {
                        particle.remove();
                    }
                }, 2500);
            }, i * 150);
        }

        // Add particle animation if not exists
        if (!document.querySelector('#particle-styles')) {
            const style = document.createElement('style');
            style.id = 'particle-styles';
            style.textContent = `
                @keyframes hoverParticleFloat {
                    0% {
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                    100% {
                        opacity: 0;
                        transform: translateY(-80px) translateX(${Math.random() * 60 - 30}px) scale(0.2);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    createEnergyBurst(orb) {
        const rect = orb.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        for (let i = 0; i < 16; i++) {
            const particle = document.createElement('div');
            const angle = (i * 22.5) * Math.PI / 180;
            const distance = 120 + Math.random() * 80;
            const size = Math.random() * 6 + 3;
            
            particle.style.cssText = `
                position: fixed;
                width: ${size}px;
                height: ${size}px;
                background: linear-gradient(45deg, #8A2BE2, #1E90FF, #FFFFFF);
                border-radius: 50%;
                box-shadow: 0 0 20px currentColor;
                pointer-events: none;
                z-index: 1000;
                left: ${centerX}px;
                top: ${centerY}px;
                transform: translate(-50%, -50%);
            `;

            // Animate the particle
            particle.animate([
                {
                    opacity: 1,
                    transform: 'translate(-50%, -50%) scale(1)',
                    filter: 'brightness(2)'
                },
                {
                    opacity: 0,
                    transform: `translate(-50%, -50%) translateX(${Math.cos(angle) * distance}px) translateY(${Math.sin(angle) * distance}px) scale(0.1)`,
                    filter: 'brightness(0.5)'
                }
            ], {
                duration: 2000,
                easing: 'cubic-bezier(0.23, 1, 0.32, 1)'
            });

            document.body.appendChild(particle);
            
            setTimeout(() => {
                if (particle.parentNode) {
                    particle.remove();
                }
            }, 2000);
        }
    }

    initAnimations() {
        // Initialize scroll-triggered animations
        const featureCards = document.querySelectorAll('.feature-card');
        featureCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(60px)';
            card.style.transition = `all 0.8s cubic-bezier(0.23, 1, 0.32, 1) ${index * 0.2}s`;
        });

        // Trigger initial animations after a short delay
        setTimeout(() => {
            featureCards.forEach(card => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            });
        }, 500);
    }

    initParticleSystem() {
        // Add floating particles in background
        this.createBackgroundParticles();
    }

    createBackgroundParticles() {
        const particleContainer = document.createElement('div');
        particleContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        `;
        document.body.appendChild(particleContainer);

        for (let i = 0; i < 25; i++) {
            setTimeout(() => {
                this.createFloatingParticle(particleContainer);
            }, i * 300);
        }

        // Continuously create new particles
        setInterval(() => {
            this.createFloatingParticle(particleContainer);
        }, 4000);
    }

    createFloatingParticle(container) {
        const particle = document.createElement('div');
        const size = Math.random() * 4 + 1;
        const duration = Math.random() * 15 + 15;
        const delay = Math.random() * 8;
        const colors = ['#8A2BE2', '#1E90FF', '#4B0082', '#6A0DAD'];
        const color = colors[Math.floor(Math.random() * colors.length)];
        
        particle.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            background: ${color};
            border-radius: 50%;
            box-shadow: 0 0 ${size * 3}px ${color};
            left: ${Math.random() * 100}%;
            animation: floatingParticle ${duration}s linear infinite;
            animation-delay: ${delay}s;
            opacity: ${Math.random() * 0.6 + 0.2};
        `;
        
        container.appendChild(particle);
        
        setTimeout(() => {
            if (particle.parentNode) {
                particle.remove();
            }
        }, (duration + delay) * 1000);

        // Add floating animation if not exists
        if (!document.querySelector('#floating-styles')) {
            const style = document.createElement('style');
            style.id = 'floating-styles';
            style.textContent = `
                @keyframes floatingParticle {
                    0% {
                        transform: translateY(100vh) translateX(0) rotate(0deg);
                        opacity: 0;
                    }
                    10% {
                        opacity: var(--particle-opacity, 0.8);
                    }
                    90% {
                        opacity: var(--particle-opacity, 0.8);
                    }
                    100% {
                        transform: translateY(-100px) translateX(${Math.random() * 300 - 150}px) rotate(360deg);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
}

// Initialize the platform when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM loaded, initializing platform...');
        new EnglishFuturePlatform();
    });
} else {
    console.log('DOM already loaded, initializing platform...');
    new EnglishFuturePlatform();
}

// Add some keyboard shortcuts for enhanced interactivity
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.ctrlKey) {
        e.preventDefault();
        const orb = document.querySelector('.orb');
        if (orb) {
            orb.click();
        }
    }
});