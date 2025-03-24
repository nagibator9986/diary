$(document).ready(function() {
    // Анимация загрузки
    $('.btn').click(function() {
        $(this).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Загрузка...');
    });
    
    // Подтверждение удаления
    $('.delete-btn').click(function() {
        return confirm('Вы уверены, что хотите удалить эту запись?');
    });
    
    // Датапикер для форм
    $('.datepicker').attr('type', 'date');
    $('.datetimepicker').attr('type', 'datetime-local');
    
    // Подсветка активного пункта меню
    const currentUrl = window.location.pathname;
    $('.nav-link').each(function() {
        if ($(this).attr('href') === currentUrl) {
            $(this).addClass('active');
        }
    });
});
// Подтверждение удаления для всех элементов
document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        if (!confirm('Вы уверены, что хотите удалить эту запись?')) {
            e.preventDefault();
        }
    });
});

// Инициализация tooltips
$(function () {
    $('[data-bs-toggle="tooltip"]').tooltip()
});

// Анимация загрузки для всех кнопок
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Обработка...';
            submitBtn.disabled = true;
        }
    });
});

// Кастомная валидация форм
document.querySelectorAll('form').forEach(form => {
    form.setAttribute('novalidate', true);
    
    form.addEventListener('submit', function(e) {
        let isValid = true;
        
        this.querySelectorAll('[required]').forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            this.querySelector('.is-invalid').focus();
        }
    });
});