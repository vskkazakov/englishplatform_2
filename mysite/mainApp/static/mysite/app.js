// Simplified platform for English learning

class EnglishFuturePlatform {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initAnimations();
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

        console.log('Events bound successfully');
    }

    handleFeatureClick(action, button) {
        console.log('Feature clicked:', action);

        const appUrls = {
            'dictionary': '/dictionary',
            'tests': '/tests',
            'games': '/games',
            'students': '/students', // URL для учителей
            'teacher': '/teacher' // URL для учеников
        };

        // Проверяем, авторизован ли пользователь для защищённых функций
        if (!window.isAuthenticated && ['dictionary', 'tests', 'games', 'students', 'teacher'].includes(action)) {
            this.showAlert(`
            Чтобы воспользоваться этой функцией, пожалуйста, зарегистрируйтесь.
            <br><a href="${window.registrationUrl}" style="color:#22c55e; text-decoration: underline;">Перейти к регистрации</a>
            `);
            return;
        }

        // Если есть URL для действия — переходим по нему
        if (window.isAuthenticated && appUrls[action]) {
            window.location.href = appUrls[action];
        }
    }

    handleCardHover(card, isEntering) {
        if (isEntering) {
            // Simple hover effect
            card.style.transform = 'translateY(-8px)';
            card.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.15)';
        } else {
            // Reset hover effects
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '';
        }
    }

    showAlert(message) {
        console.log('Showing alert:', message);
        
        // Remove existing alert if any
        const existingAlert = document.querySelector('.alert-overlay');
        if (existingAlert) {
            existingAlert.remove();
        }

        // Create simple alert overlay
        const alertOverlay = document.createElement('div');
        alertOverlay.className = 'alert-overlay';
        
        const alertBox = document.createElement('div');
        alertBox.className = 'alert-box';
        
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

        // Add styles if not exists
        if (!document.querySelector('#alert-styles')) {
            const style = document.createElement('style');
            style.id = 'alert-styles';
            style.textContent = `
                .alert-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .alert-box {
                    background: white;
                    border-radius: 12px;
                    padding: 32px;
                    max-width: 500px;
                    text-align: center;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
                }

                .alert-content {
                    color: #333333;
                    font-size: 18px;
                    line-height: 1.6;
                    margin-bottom: 24px;
                }

                .alert-btn {
                    background: #22c55e;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: background-color 0.2s ease;
                }

                .alert-btn:hover {
                    background: #16a34a;
                }
            `;
            document.head.appendChild(style);
        }

        // Close functionality
        const closeAlert = () => {
            alertOverlay.remove();
        };

        alertButton.addEventListener('click', closeAlert);
        alertOverlay.addEventListener('click', (e) => {
            if (e.target === alertOverlay) closeAlert();
        });

        // Auto close after 8 seconds
        setTimeout(closeAlert, 8000);
    }

    initAnimations() {
        // Simple fade-in animation for feature cards
        const featureCards = document.querySelectorAll('.feature-card');
        featureCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.6s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
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