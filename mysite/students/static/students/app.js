let currentStudentId = null;
let currentStudentName = '';

function openShareCategoryModal(studentId, studentName) {
    console.log('Opening share category modal for student:', studentId, studentName);

    // ПРОВЕРЯЕМ, что studentId не undefined
    if (!studentId || studentId === 'undefined') {
        console.error('Student ID is undefined!');
        alert('Ошибка: ID студента не определен');
        return;
    }

    // Устанавливаем данные студента в модал
    $('#share-category-modal').data('student-id', studentId);
    $('#share-category-modal').data('student-name', studentName);
    $('#share-category-modal .modal-title').text(`Отправить категорию: ${studentName}`);

    // Загружаем категории учителя
    loadTeacherCategories();

    // Показываем модал
    $('#share-category-modal').modal('show');
}

// ИСПРАВЛЕНИЕ 2: В функции загрузки категорий
function loadTeacherCategories() {
    $.ajax({
        url: '/students/get-teacher-categories/',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                var categorySelect = $('#id_category');
                categorySelect.empty();
                categorySelect.append('<option value="">Выберите категорию</option>');

                response.categories.forEach(function(category) {
                    categorySelect.append(
                        `<option value="${category.id}">${category.name} (${category.word_count} слов)</option>`
                    );
                });
            } else {
                console.error('Error loading categories:', response.error);
                alert('Ошибка загрузки категорий: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            console.error('AJAX error:', error);
            alert('Ошибка загрузки категорий');
        }
    });
}

// ИСПРАВЛЕНИЕ 3: В функции отправки категории 
function submitShareCategory() {
    var studentId = $('#share-category-modal').data('student-id');
    var studentName = $('#share-category-modal').data('student-name');

    // ПРОВЕРЯЕМ, что studentId не undefined
    if (!studentId || studentId === 'undefined') {
        console.error('Student ID is undefined in submitShareCategory!');
        alert('Ошибка: ID студента не определен');
        return;
    }

    var categoryId = $('#id_category').val();
    var message = $('#id_message').val();

    if (!categoryId) {
        alert('Выберите категорию');
        return;
    }

    console.log('Submitting share category:', {studentId, categoryId, message});

    $.ajax({
        url: `/students/share-category/${studentId}/`, // Используем правильный studentId
        method: 'POST',
        data: {
            'category': categoryId,
            'message': message,
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                alert(response.message);
                $('#share-category-modal').modal('hide');
            } else {
                alert('Ошибка: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            console.error('AJAX error:', error);
            alert('Ошибка отправки категории');
        }
    });
}

// ИСПРАВЛЕНИЕ 4: Правильная инициализация кнопок
$(document).ready(function() {
    // Обработчик для кнопок "Отправить категорию"
    $(document).on('click', '.share-category-btn', function(e) {
        e.preventDefault();

        var studentId = $(this).data('student-id'); // Получаем из data-атрибута
        var studentName = $(this).data('student-name');

        console.log('Share category button clicked:', {studentId, studentName});

        // ПРОВЕРЯЕМ значения
        if (!studentId) {
            console.error('No student ID found in button data attributes');
            alert('Ошибка: не найден ID студента');
            return;
        }

        openShareCategoryModal(studentId, studentName);
    });

    // Обработчик для кнопки отправки в модале
    $('#submit-share-category').on('click', function() {
        submitShareCategory();
    });
});

function showRequestModal(studentId, studentName) {
    currentStudentId = studentId;
    currentStudentName = studentName;
    document.getElementById('requestModal').style.display = 'flex';
}

function closeRequestModal() {
    document.getElementById('requestModal').style.display = 'none';
    document.getElementById('requestForm').reset();
}

function showAddStudentsModal() {
    document.getElementById('addStudentsModal').style.display = 'flex';
    loadStudentsList(); // Загружаем список учеников при открытии
}

function closeAddStudentsModal() {
    document.getElementById('addStudentsModal').style.display = 'none';
    document.getElementById('studentSearchForm').reset();
}

function loadStudentsList(searchQuery = '') {
    const studentsList = document.getElementById('studentsList');
    studentsList.innerHTML = '<div class="loading">Загрузка учеников...</div>';
    
    // Загружаем список учеников через AJAX
    fetch(`/students/get-students-list/?search=${searchQuery}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayStudentsList(data.students);
            } else {
                studentsList.innerHTML = '<div class="error">Ошибка загрузки: ' + data.error + '</div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            studentsList.innerHTML = '<div class="error">Произошла ошибка при загрузке</div>';
        });
}

function displayStudentsList(students) {
    const studentsList = document.getElementById('studentsList');
    
    if (students.length === 0) {
        studentsList.innerHTML = '<div class="no-students">Ученики не найдены</div>';
        return;
    }
    
    let html = '<div class="students-grid">';
    students.forEach(student => {
        const hasRequest = student.has_request;
        const requestStatus = student.request_status;
        const isCurrentStudent = student.is_current_student;
        
        let buttonHtml = '';
        if (isCurrentStudent) {
            buttonHtml = '<button class="btn-success" disabled><span class="btn-icon">✅</span>Уже ученик</button>';
        } else if (hasRequest && requestStatus === 'pending') {
            buttonHtml = '<button class="btn-secondary" disabled><span class="btn-icon">⏳</span>Приглашение отправлено</button>';
        } else if (hasRequest && (requestStatus === 'rejected' || requestStatus === 'cancelled')) {
            buttonHtml = `<button class="btn-primary" onclick="sendRequestToStudent(${student.id}, '${student.name}')"><span class="btn-icon">🔄</span>Отправить повторно</button>`;
        } else {
            buttonHtml = `<button class="btn-primary" onclick="sendRequestToStudent(${student.id}, '${student.name}')"><span class="btn-icon">📝</span>Пригласить</button>`;
        }
        
        html += `
            <div class="student-card">
                <div class="student-header">
                    <div class="student-avatar">
                        <span class="avatar-placeholder">${student.name.charAt(0).toUpperCase()}</span>
                    </div>
                    <div class="student-info">
                        <h3 class="student-name">${student.name}</h3>
                        <span class="student-email">📧 ${student.email}</span>
                    </div>
                </div>
                <div class="student-actions">
                    ${buttonHtml}
                </div>
            </div>
        `;
    });
    html += '</div>';
    studentsList.innerHTML = html;
}

function sendRequestToStudent(studentId, studentName) {
    currentStudentId = studentId;
    currentStudentName = studentName;
    closeAddStudentsModal();
    showRequestModal(studentId, studentName);
}

function createHomework(studentId, studentName) {
    // Перенаправляем на страницу создания домашнего задания
    window.location.href = `/students/create-homework/${studentId}/`;
}

// Обработчик поиска учеников
document.getElementById('studentSearchForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const searchQuery = document.getElementById('studentSearchInput').value;
    loadStudentsList(searchQuery);
});

document.getElementById('requestForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    
    fetch(`/students/send-request/${currentStudentId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            closeRequestModal();
            location.reload(); // Обновляем страницу для отображения изменений
        } else {
            alert('Ошибка: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка при отправке приглашения');
    });
});

// Автоматическое скрытие уведомлений через 5 секунд
setTimeout(function() {
    const messages = document.querySelectorAll('.message');
    messages.forEach(function(message) {
        message.style.opacity = '0';
        setTimeout(() => message.remove(), 300);
    });
}, 5000);
// Функции для модального окна добавления учеников
function showAddStudentsModal() {
    document.getElementById('addStudentsModal').style.display = 'flex';
    loadStudentsList();
}

function closeAddStudentsModal() {
    document.getElementById('addStudentsModal').style.display = 'none';
    document.getElementById('studentSearchForm').reset();
}

// Функции для модального окна приглашения
function showRequestModal(studentId, studentName) {
    currentStudentId = studentId;
    currentStudentName = studentName;
    document.getElementById('requestModal').style.display = 'flex';
}

function closeRequestModal() {
    document.getElementById('requestModal').style.display = 'none';
    document.getElementById('requestForm').reset();
}

// Функции для модального окна обмена категориями
function openShareCategoryModal(studentId, studentName) {
    currentStudentId = studentId;
    currentStudentName = studentName;
    
    document.getElementById('selectedStudentName').textContent = studentName;
    document.getElementById('shareCategoryModal').style.display = 'flex';
    
    // Загружаем категории учителя
    loadTeacherCategories();
}

function closeShareCategoryModal() {
    document.getElementById('shareCategoryModal').style.display = 'none';
    document.getElementById('shareCategoryForm').reset();
}

function loadTeacherCategories() {
    fetch('{% url "students:get_teacher_categories" %}')
        .then(response => response.json())
        .then(data => {
            const categorySelect = document.getElementById('categorySelect');
            categorySelect.innerHTML = '<option value="">Выберите категорию...</option>';
            
            if (data.success) {
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = `${category.name} (${category.word_count} слов)`;
                    categorySelect.appendChild(option);
                });
            } else {
                console.error('Ошибка загрузки категорий:', data.error);
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });
}

// Обработчик отправки формы для обмена категориями
document.getElementById('shareCategoryForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    
    fetch(`{% url "students:share_category" student_id=0 %}`.replace('0', currentStudentId), {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
            closeShareCategoryModal();
        } else {
            showMessage(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showMessage('Произошла ошибка при отправке категории', 'error');
    });
});

// Функция для показа сообщений
function showMessage(message, type) {
    // Используем существующую систему уведомлений или создаем простую
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-text">${message}</div>
        </div>
        <button class="message-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    // Добавляем в контейнер сообщений или создаем его
    let messagesContainer = document.querySelector('.messages-container');
    if (!messagesContainer) {
        messagesContainer = document.createElement('div');
        messagesContainer.className = 'messages-container';
        document.body.appendChild(messagesContainer);
    }
    
    messagesContainer.appendChild(messageDiv);
    
    // Автоматически удаляем через 5 секунд
    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.remove();
        }
    }, 5000);
}

// Обработчики кнопок
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.share-category-btn').forEach(button => {
        button.addEventListener('click', function() {
            const studentId = this.dataset.studentId;
            const studentCard = this.closest('.user-card, .student-card');
            const studentName = studentCard.querySelector('.user-name, .student-name').textContent.trim();
            openShareCategoryModal(studentId, studentName);
        });
    });
});

/* 
ПРИМЕР ПРАВИЛЬНОЙ HTML КНОПКИ:
<button class="btn btn-primary share-category-btn" 
        data-student-id="{{ relationship.student.id }}" 
        data-student-name="{{ relationship.student.get_full_name }}">
    📚 Отправить категорию
</button>
*/
