// Загрузка списка подарков
async function loadGifts() {
    try {
        const response = await fetch('/api/gifts');
        const data = await response.json();
        
        // Проверяем, что data.gifts существует и является массивом
        const gifts = Array.isArray(data.gifts) ? data.gifts : [];
        
        const userGift = document.getElementById('userGift');
        const groupGift = document.getElementById('groupGift');
        
        if (userGift) {
            userGift.innerHTML = '<option value="0">Все подарки</option>';
            gifts.forEach(gift => {
                const option = document.createElement('option');
                option.value = gift.id;
                option.textContent = gift.name;
                userGift.appendChild(option);
            });
        }
        
        if (groupGift) {
            groupGift.innerHTML = '<option value="0">Все подарки</option>';
            gifts.forEach(gift => {
                const option = document.createElement('option');
                option.value = gift.id;
                option.textContent = gift.name;
                groupGift.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading gifts:', error);
        showError('Ошибка при загрузке списка подарков');
    }
}

// Показать/скрыть оверлей загрузки
function toggleLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = show ? 'flex' : 'none';
}

// Показать ошибку
function showError(message) {
    console.error('Showing error:', message);
    const status = document.getElementById('auth-status');
    if (status) {
        status.innerHTML = `
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
                <strong class="font-bold">Ошибка!</strong>
                <span class="block sm:inline">${message}</span>
            </div>
        `;
    } else {
        console.error('Status element not found');
    }
}

// Проверка подарков у пользователя
async function checkUser() {
    const username = document.getElementById('username').value.trim();
    const giftId = document.getElementById('userGift').value;
    const resultsDiv = document.getElementById('userResults');
    
    if (!username) {
        resultsDiv.innerHTML = '';
        resultsDiv.appendChild(showError('Введите username пользователя'));
        return;
    }
    
    toggleLoading(true);
    resultsDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/check_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username.replace('@', ''),
                gift_id: giftId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.gifts.length === 0) {
                resultsDiv.innerHTML = `
                    <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative">
                        Подарки не найдены
                    </div>
                `;
            } else {
                const giftsHtml = data.gifts.map(gift => `
                    <div class="gift-card bg-white border rounded-lg p-4 mb-4 shadow-sm result-item">
                        <h3 class="font-semibold text-lg mb-2">${gift.name}</h3>
                        <p class="text-gray-600">Дата: ${new Date(gift.date).toLocaleString()}</p>
                    </div>
                `).join('');
                
                resultsDiv.innerHTML = `
                    <div class="mb-4">
                        <h3 class="font-semibold text-lg">Найдено подарков: ${data.total}</h3>
                    </div>
                    ${giftsHtml}
                `;
            }
        } else {
            resultsDiv.appendChild(showError(data.error || 'Произошла ошибка'));
        }
    } catch (error) {
        console.error('Error checking user:', error);
        resultsDiv.appendChild(showError('Ошибка при проверке пользователя'));
    } finally {
        toggleLoading(false);
    }
}

// Проверка подарков в группе
async function checkGroup() {
    const groupId = document.getElementById('groupId').value.trim();
    const giftId = document.getElementById('groupGift').value;
    const resultsDiv = document.getElementById('groupResults');
    
    if (!groupId) {
        resultsDiv.innerHTML = '';
        resultsDiv.appendChild(showError('Введите ID группы или ссылку'));
        return;
    }
    
    toggleLoading(true);
    resultsDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/check_group', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                group_id: groupId,
                gift_id: giftId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.participants.length === 0) {
                resultsDiv.innerHTML = `
                    <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative">
                        Пользователи с подарками не найдены
                    </div>
                `;
            } else {
                const participantsHtml = data.participants.map(participant => `
                    <div class="gift-card bg-white border rounded-lg p-4 mb-4 shadow-sm result-item">
                        <h3 class="font-semibold text-lg mb-2">
                            ${participant.first_name} ${participant.last_name || ''}
                            ${participant.username ? `(@${participant.username})` : ''}
                        </h3>
                        <p class="text-gray-600">Подарок: ${participant.gift}</p>
                        <p class="text-gray-600">Дата: ${new Date(participant.date).toLocaleString()}</p>
                    </div>
                `).join('');
                
                resultsDiv.innerHTML = `
                    <div class="mb-4">
                        <h3 class="font-semibold text-lg">Найдено пользователей: ${data.total}</h3>
                    </div>
                    ${participantsHtml}
                `;
            }
        } else {
            resultsDiv.appendChild(showError(data.error || 'Произошла ошибка'));
        }
    } catch (error) {
        console.error('Error checking group:', error);
        resultsDiv.appendChild(showError('Ошибка при проверке группы'));
    } finally {
        toggleLoading(false);
    }
}

// Проверка статуса авторизации
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        
        if (data.authorized) {
            showSearchForm();
        } else {
            showAuthForm();
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
        showError('Ошибка при проверке статуса авторизации');
    }
}

// Начало авторизации
async function startAuth() {
    try {
        const response = await fetch('/api/auth/start', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'code_sent') {
            const codeInput = document.getElementById('code-input');
            const startAuthBtn = document.getElementById('start-auth');
            
            if (codeInput) {
                codeInput.style.display = 'block';
                console.log('Showing code input form');
            } else {
                console.error('Code input element not found');
            }
            
            if (startAuthBtn) {
                startAuthBtn.style.display = 'none';
            }
        } else if (data.status === 'already_authorized') {
            showSearchForm();
        } else {
            showError(data.error || 'Ошибка при начале авторизации');
        }
    } catch (error) {
        console.error('Error starting auth:', error);
        showError('Ошибка при начале авторизации');
    }
}

// Отправка кода
async function sendCode() {
    const apiId = document.getElementById('api-id').value;
    const apiHash = document.getElementById('api-hash').value;
    const phone = document.getElementById('phone').value;
    
    if (!apiId || !apiHash || !phone) {
        showError('Заполните все поля');
        return;
    }

    try {
        const response = await fetch('http://localhost:8080/api/auth/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_id: apiId,
                api_hash: apiHash,
                phone: phone
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'code_sent') {
            document.getElementById('send-code').disabled = true;
            document.getElementById('code').focus();
        } else {
            showError(data.error || 'Ошибка при отправке кода');
        }
    } catch (error) {
        console.error('Error sending code:', error);
        showError('Ошибка при отправке кода');
    }
}

// Отправка кода подтверждения
async function submitCode() {
    const code = document.getElementById('code').value;
    if (!code) {
        showError('Введите код');
        return;
    }

    try {
        console.log('Sending code to server...', code);
        const response = await fetch('http://localhost:8080/api/auth/code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ code })
        });
        
        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Server response:', data);
        
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка сервера');
        }
        
        if (data.status === 'success') {
            console.log('Code accepted, showing search form');
            showSearchForm();
        } else if (data.status === 'password_required') {
            console.log('Password required, showing password modal');
            document.getElementById('password-modal').classList.remove('hidden');
            document.getElementById('password').focus();
        } else {
            console.error('Error from server:', data.error);
            showError(data.error || 'Ошибка при вводе кода');
        }
    } catch (error) {
        console.error('Error submitting code:', error);
        showError(error.message || 'Ошибка при вводе кода');
    }
}

// Отправка пароля
async function submitPassword() {
    const password = document.getElementById('password').value;
    if (!password) {
        showError('Введите пароль');
        return;
    }

    try {
        console.log('Sending password to server...');
        const response = await fetch('http://localhost:8080/api/auth/password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ password })
        });
        
        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Server response:', data);
        
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка сервера');
        }
        
        if (data.status === 'success') {
            console.log('Password accepted, showing search form');
            document.getElementById('password-modal').classList.add('hidden');
            showSearchForm();
        } else {
            console.error('Error from server:', data.error);
            showError(data.error || 'Ошибка при вводе пароля');
        }
    } catch (error) {
        console.error('Error submitting password:', error);
        showError(error.message || 'Ошибка при вводе пароля');
    }
}

function toggleSearchInput() {
    const searchType = document.getElementById('search-type').value;
    document.getElementById('user-input').style.display = searchType === 'user' ? 'block' : 'none';
    document.getElementById('group-input').style.display = searchType === 'group' ? 'block' : 'none';
}

async function startSearch() {
    const searchType = document.getElementById('search-type').value;
    const giftId = document.getElementById('gift-select').value;
    let query = '';
    
    if (searchType === 'user') {
        query = document.getElementById('username').value;
        if (!query) {
            showError('Введите username пользователя');
            return;
        }
    } else {
        query = document.getElementById('group-link').value;
        if (!query) {
            showError('Введите ссылку на группу');
            return;
        }
    }

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: searchType,
                gift_id: giftId,
                query: query
            })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showResults(data.results);
        } else {
            showError(data.error || 'Ошибка при поиске');
        }
    } catch (error) {
        console.error('Error starting search:', error);
        showError('Ошибка при поиске');
    }
}

// Показать форму авторизации
function showAuthForm() {
    const authModal = document.getElementById('authModal');
    const mainContent = document.getElementById('mainContent');
    
    if (authModal) authModal.classList.remove('hidden');
    if (mainContent) mainContent.classList.add('hidden');
}

// Показать форму поиска
function showSearchForm() {
    const authModal = document.getElementById('authModal');
    const mainContent = document.getElementById('mainContent');
    
    if (authModal) authModal.classList.add('hidden');
    if (mainContent) mainContent.classList.remove('hidden');
}

// Показать результаты
function showResults(results) {
    const resultsContent = document.getElementById('results-content');
    if (!resultsContent) return;
    
    resultsContent.innerHTML = '';
    
    if (results.length === 0) {
        resultsContent.innerHTML = '<p>Подарки не найдены</p>';
    } else {
        const ul = document.createElement('ul');
        results.forEach(result => {
            const li = document.createElement('li');
            li.textContent = result;
            ul.appendChild(li);
        });
        resultsContent.appendChild(ul);
    }
    
    document.getElementById('search-results').style.display = 'block';
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация обработчиков событий
    const sendCodeBtn = document.getElementById('send-code');
    const submitCodeBtn = document.getElementById('submit-code');
    const submitPasswordBtn = document.getElementById('submit-password');
    const passwordInput = document.getElementById('password');
    
    if (sendCodeBtn) {
        sendCodeBtn.addEventListener('click', sendCode);
    }
    
    if (submitCodeBtn) {
        submitCodeBtn.addEventListener('click', submitCode);
    }
    
    if (submitPasswordBtn) {
        submitPasswordBtn.addEventListener('click', submitPassword);
    }
    
    if (passwordInput) {
        passwordInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                submitPassword();
            }
        });
    }
    
    // Загрузка списка подарков
    loadGifts();
}); 