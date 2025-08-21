// Мобильная навигация - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Функция для создания мобильного меню
    function createMobileMenu() {
        const nav = document.querySelector('.nav');
        if (!nav) return;
        
        // Проверяем, нужно ли создавать мобильное меню
        if (window.innerWidth > 480) return;
        
        // Проверяем, не создано ли уже меню
        if (nav.querySelector('.nav-toggle')) return;
        
        // Создаем кнопку-гамбургер
        const toggle = document.createElement('button');
        toggle.className = 'nav-toggle';
        toggle.innerHTML = '☰';
        toggle.setAttribute('aria-label', 'Открыть меню');
        
        // Создаем контейнер для меню
        const menu = document.createElement('div');
        menu.className = 'nav-menu';
        
        // Перемещаем все ссылки в меню
        const links = Array.from(nav.querySelectorAll('.nav-link'));
        const userGreeting = nav.querySelector('.user-greeting');
        const btnLogin = nav.querySelector('.btn-login');
        
        links.forEach(link => {
            menu.appendChild(link.cloneNode(true));
            link.remove();
        });
        
        if (userGreeting) {
            const greetingClone = userGreeting.cloneNode(true);
            menu.appendChild(greetingClone);
            userGreeting.remove();
        }
        
        if (btnLogin) {
            const btnClone = btnLogin.cloneNode(true);
            menu.appendChild(btnClone);
            btnLogin.remove();
        }
        
        // Добавляем элементы в навигацию
        nav.appendChild(toggle);
        nav.appendChild(menu);
        
        // Обработчик клика по кнопке
        toggle.addEventListener('click', function() {
            const isOpen = menu.classList.contains('active');
            
            if (isOpen) {
                menu.classList.remove('active');
                toggle.innerHTML = '☰';
                toggle.setAttribute('aria-label', 'Открыть меню');
            } else {
                menu.classList.add('active');
                toggle.innerHTML = '✕';
                toggle.setAttribute('aria-label', 'Закрыть меню');
            }
        });
        
        // Закрытие меню при клике вне его
        document.addEventListener('click', function(event) {
            if (!nav.contains(event.target)) {
                menu.classList.remove('active');
                toggle.innerHTML = '☰';
                toggle.setAttribute('aria-label', 'Открыть меню');
            }
        });
        
        // Закрытие меню при нажатии Escape
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                menu.classList.remove('active');
                toggle.innerHTML = '☰';
                toggle.setAttribute('aria-label', 'Открыть меню');
            }
        });
    }
    
    // Функция для удаления мобильного меню
    function removeMobileMenu() {
        const nav = document.querySelector('.nav');
        if (!nav) return;
        
        const toggle = nav.querySelector('.nav-toggle');
        const menu = nav.querySelector('.nav-menu');
        
        if (toggle && menu) {
            // Возвращаем ссылки обратно
            const menuLinks = Array.from(menu.querySelectorAll('.nav-link'));
            const menuGreeting = menu.querySelector('.user-greeting');
            const menuBtn = menu.querySelector('.btn-login');
            
            menuLinks.forEach(link => {
                nav.appendChild(link);
            });
            
            if (menuGreeting) {
                nav.appendChild(menuGreeting);
            }
            
            if (menuBtn) {
                nav.appendChild(menuBtn);
            }
            
            // Удаляем мобильные элементы
            toggle.remove();
            menu.remove();
        }
    }
    
    // Функция для обработки изменения размера окна
    function handleResize() {
        if (window.innerWidth <= 480) {
            createMobileMenu();
        } else {
            removeMobileMenu();
        }
    }
    
    // Инициализация при загрузке
    handleResize();
    
    // Обработчик изменения размера окна
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(handleResize, 250);
    });
    
    // Улучшения для сенсорных устройств
    if ('ontouchstart' in window) {
        // Добавляем задержку для предотвращения двойного клика
        document.addEventListener('touchstart', function() {}, {passive: true});
        
        // Улучшенная обработка касаний для кнопок
        const buttons = document.querySelectorAll('.btn, .nav-link');
        buttons.forEach(button => {
            button.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
            }, {passive: true});
            
            button.addEventListener('touchend', function() {
                this.style.transform = '';
            }, {passive: true});
        });
    }
    
    // Улучшения для устройств с высоким DPI
    if (window.devicePixelRatio > 1) {
        document.documentElement.style.setProperty('--border-radius', '2px');
    }
    
    // Поддержка жестов для мобильных устройств
    let touchStartX = 0;
    let touchStartY = 0;
    
    document.addEventListener('touchstart', function(event) {
        touchStartX = event.touches[0].clientX;
        touchStartY = event.touches[0].clientY;
    }, {passive: true});
    
    document.addEventListener('touchend', function(event) {
        const touchEndX = event.changedTouches[0].clientX;
        const touchEndY = event.changedTouches[0].clientY;
        
        const deltaX = touchEndX - touchStartX;
        const deltaY = touchEndY - touchStartY;
        
        // Свайп влево для закрытия мобильного меню
        if (deltaX < -50 && Math.abs(deltaY) < 50) {
            const menu = document.querySelector('.nav-menu');
            const toggle = document.querySelector('.nav-toggle');
            
            if (menu && menu.classList.contains('active')) {
                menu.classList.remove('active');
                if (toggle) {
                    toggle.innerHTML = '☰';
                    toggle.setAttribute('aria-label', 'Открыть меню');
                }
            }
        }
    }, {passive: true});
    
    // Улучшения для доступности
    document.addEventListener('keydown', function(event) {
        // Навигация с помощью клавиатуры
        if (event.key === 'Tab') {
            const menu = document.querySelector('.nav-menu');
            if (menu && menu.classList.contains('active')) {
                const focusableElements = menu.querySelectorAll('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
                if (event.shiftKey && document.activeElement === firstElement) {
                    event.preventDefault();
                    lastElement.focus();
                } else if (!event.shiftKey && document.activeElement === lastElement) {
                    event.preventDefault();
                    firstElement.focus();
                }
            }
        }
    });
    
    // Автоматическое скрытие мобильного меню при переходе на другую страницу
    const links = document.querySelectorAll('a[href]');
    links.forEach(link => {
        link.addEventListener('click', function() {
            const menu = document.querySelector('.nav-menu');
            const toggle = document.querySelector('.nav-toggle');
            
            if (menu && menu.classList.contains('active')) {
                menu.classList.remove('active');
                if (toggle) {
                    toggle.innerHTML = '☰';
                    toggle.setAttribute('aria-label', 'Открыть меню');
                }
            }
        });
    });
    
    // Улучшения для производительности
    let ticking = false;
    
    function updateOnScroll() {
        const header = document.querySelector('.header');
        if (header) {
            const scrollTop = window.pageYOffset;
            if (scrollTop > 10) {
                header.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
            } else {
                header.style.boxShadow = 'none';
            }
        }
        ticking = false;
    }
    
    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(updateOnScroll);
            ticking = true;
        }
    }, {passive: true});
});
