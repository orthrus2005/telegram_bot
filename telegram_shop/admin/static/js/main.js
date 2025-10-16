// Основные JavaScript функции для админ-панели

// Показать уведомление
function showNotification(message, type = 'success') {
    const alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Добавляем уведомление в начало основного контента
    const mainContent = document.querySelector('main');
    const firstChild = mainContent.firstChild;
    mainContent.insertAdjacentHTML('afterbegin', alertHtml);
    
    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        const alert = mainContent.querySelector('.alert');
        if (alert) {
            bootstrap.Alert.getOrCreateInstance(alert).close();
        }
    }, 5000);
}

// Форматирование чисел (цен)
function formatPrice(price) {
    return new Intl.NumberFormat('ru-RU', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(price);
}

// Форматирование даты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Подтверждение действия
function confirmAction(message) {
    return new Promise((resolve) => {
        // Создаем модальное окно подтверждения
        const modalHtml = `
            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Подтверждение</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                            <button type="button" class="btn btn-primary" id="confirmButton">Подтвердить</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modalElement = document.getElementById('confirmModal');
        const modal = new bootstrap.Modal(modalElement);
        
        modalElement.querySelector('#confirmButton').addEventListener('click', () => {
            resolve(true);
            modal.hide();
        });
        
        modalElement.addEventListener('hidden.bs.modal', () => {
            resolve(false);
            modalElement.remove();
        });
        
        modal.show();
    });
}

// Загрузка данных через API
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showNotification('Ошибка при выполнении запроса: ' + error.message, 'error');
        throw error;
    }
}

// Обновление статуса заказа
async function updateOrderStatus(orderId, newStatus) {
    try {
        const result = await apiCall('/api/update_order_status', {
            method: 'POST',
            body: JSON.stringify({
                order_id: orderId,
                status: newStatus
            })
        });
        
        if (result.success) {
            showNotification('Статус заказа успешно обновлен');
            // Обновляем страницу через секунду
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification('Ошибка: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('Ошибка при обновлении статуса заказа', 'error');
    }
}

// Показать детали заказа
async function showOrderDetails(orderId) {
    try {
        // Показываем индикатор загрузки
        const modalContent = document.getElementById('orderDetailsContent');
        modalContent.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Загрузка...</span>
                </div>
                <p class="mt-2">Загрузка деталей заказа...</p>
            </div>
        `;
        
        const data = await apiCall(`/api/order_details/${orderId}`);
        
        if (data.error) {
            modalContent.innerHTML = `
                <div class="alert alert-danger">
                    Ошибка: ${data.error}
                </div>
            `;
        } else {
            modalContent.innerHTML = data.html;
        }
        
        new bootstrap.Modal(document.getElementById('orderDetailsModal')).show();
    } catch (error) {
        showNotification('Ошибка при загрузке деталей заказа', 'error');
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем обработчики для всех форм с подтверждением
    const forms = document.querySelectorAll('form[data-confirm]');
    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const confirmed = await confirmAction(this.getAttribute('data-confirm-message') || 'Вы уверены?');
            if (confirmed) {
                this.submit();
            }
        });
    });
    
    // Автоматически скрываем алерты через 5 секунд
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                bootstrap.Alert.getOrCreateInstance(alert).close();
            }
        }, 5000);
    });
    
    // Добавляем обработчики для всех кнопок удаления с подтверждением
    const deleteButtons = document.querySelectorAll('[data-delete-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            
            const message = this.getAttribute('data-delete-confirm');
            const url = this.getAttribute('data-delete-url');
            
            const confirmed = await confirmAction(message);
            if (confirmed && url) {
                try {
                    const result = await apiCall(url, { method: 'POST' });
                    if (result.success) {
                        showNotification('Удаление выполнено успешно');
                        location.reload();
                    } else {
                        showNotification('Ошибка при удалении: ' + result.message, 'error');
                    }
                } catch (error) {
                    showNotification('Ошибка при удалении', 'error');
                }
            }
        });
    });
});

// Утилиты для работы с локальным хранилищем
const storage = {
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    },
    
    get: (key, defaultValue = null) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    },
    
    remove: (key) => {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Error removing from localStorage:', error);
        }
    }
};

// Экспортируем функции для глобального использования
window.adminUtils = {
    showNotification,
    formatPrice,
    formatDate,
    confirmAction,
    apiCall,
    updateOrderStatus,
    showOrderDetails,
    storage
};