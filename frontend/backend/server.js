const express = require('express');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 4000;

// Middleware
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static('uploads'));

// Создаем папку для загрузок если её нет
if (!fs.existsSync('uploads')) {
    fs.mkdirSync('uploads');
}

// Настройка multer для загрузки файлов
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, 'uploads/');
    },
    filename: function (req, file, cb) {
        cb(null, Date.now() + '-' + file.originalname);
    }
});

const upload = multer({
    storage: storage,
    fileFilter: function (req, file, cb) {
        // Проверяем что файл - изображение
        if (file.mimetype.startsWith('image/')) {
            cb(null, true);
        } else {
            cb(new Error('Только изображения разрешены!'), false);
        }
    },
    limits: {
        fileSize: 10 * 1024 * 1024 // 10MB лимит
    }
});

// "База данных" в памяти
const users = [];
const analysisHistory = {};

// Middleware для проверки токена (упрощенная версия)
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ message: 'Токен отсутствует' });
    }

    // В реальном приложении здесь была бы проверка JWT токена
    // Для тестов просто проверяем что токен существует
    req.user = { username: token.split('-')[1] || 'testuser' };
    next();
};

// Маршруты аутентификации
app.post('/auth/register', (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
        return res.status(400).json({ message: 'Логин и пароль обязательны' });
    }

    if (users.find(u => u.username === username)) {
        return res.status(400).json({ message: 'Пользователь уже существует' });
    }

    users.push({ username, password });
    console.log(`Зарегистрирован новый пользователь: ${username}`);

    res.json({ message: 'Пользователь успешно создан' });
});

app.post('/auth/login', (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
        return res.status(400).json({ message: 'Логин и пароль обязательны' });
    }

    const user = users.find(u => u.username === username && u.password === password);

    if (!user) {
        // Для тестов - если пользователь не найден, автоматически создаем его
        users.push({ username, password });
        console.log(`Автоматически создан пользователь: ${username}`);
    }

    // Генерируем простой токен (в реальном приложении используйте JWT)
    const token = `mock-token-${username}-${Date.now()}`;

    res.json({
        token,
        user: { username }
    });
});

// Маршрут загрузки файла
app.post('/api/upload', authenticateToken, upload.single('file'), (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ message: 'Файл не загружен' });
        }

        console.log(`Файл загружен: ${req.file.filename} пользователем ${req.user.username}`);

        // Генерируем случайный результат анализа
        const healthResults = [
            "Анализ показал отличное состояние здоровья. Рекомендуется поддерживать текущий режим дня.",
            "Обнаружены незначительные признаки усталости. Рекомендуется больше отдыха и употребление витаминов.",
            "Визуальный осмотр в норме. Обратите внимание на водный баланс - пейте больше воды.",
            "Выглядите немного уставшим. Рекомендуется 7-8 часов сна ежедневно и сокращение времени за экранами.",
            "Отличные показатели! Продолжайте вести здоровый образ жизни.",
            "Обнаружены признаки стресса. Рекомендуются прогулки на свежем воздухе и медитация.",
            "Состояние в пределах нормы. Обратите внимание на регулярные физические нагрузки."
        ];

        const randomResult = healthResults[Math.floor(Math.random() * healthResults.length)];

        // Добавляем детали анализа
        const analysisResult = `РЕЗУЛЬТАТ АНАЛИЗА (ТЕСТОВЫЙ):\n\n${randomResult}\n\nДетали:\n- Цвет кожи: в норме\n- Глаза: ясные\n- Общий тонус: хороший\n- Рекомендации: соблюдать режим дня, сбалансированное питание\n\n⚠️ ВНИМАНИЕ: Это тестовый результат для демонстрации работы приложения.`;

        const analysisData = {
            status: 'success',
            result: analysisResult,
            timestamp: new Date().toISOString(),
            filename: req.file.filename,
            analysisId: `analysis-${Date.now()}`
        };

        // Сохраняем в историю
        if (!analysisHistory[req.user.username]) {
            analysisHistory[req.user.username] = [];
        }

        analysisHistory[req.user.username].unshift({
            id: analysisData.analysisId,
            result: analysisData.result.substring(0, 100) + '...',
            date: analysisData.timestamp,
            filename: req.file.filename
        });

        // Ограничиваем историю последними 10 анализами
        analysisHistory[req.user.username] = analysisHistory[req.user.username].slice(0, 10);

        // Имитируем обработку AI с задержкой
        setTimeout(() => {
            res.json(analysisData);
        }, 2000);

    } catch (error) {
        console.error('Ошибка загрузки:', error);
        res.status(500).json({ message: 'Ошибка при обработке файла' });
    }
});

// Маршрут статуса AI
app.get('/api/status', (req, res) => {
    res.json({
        ai_status: 'running',
        version: '1.0.0',
        model: 'health-analysis-v1',
        uptime: Math.floor(process.uptime())
    });
});

// Маршрут истории анализов
app.get('/api/history', authenticateToken, (req, res) => {
    const userHistory = analysisHistory[req.user.username] || [];
    res.json(userHistory);
});

// Маршрут для проверки работы сервера
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        users_count: users.length
    });
});

// Обработка ошибок multer
app.use((error, req, res, next) => {
    if (error instanceof multer.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ message: 'Файл слишком большой' });
        }
    }
    res.status(500).json({ message: error.message });
});

// Запуск сервера
app.listen(PORT, () => {
    console.log(`🚀 Сервер запущен на http://localhost:${PORT}`);
    console.log(`📊 API endpoints:`);
    console.log(`   POST /auth/register`);
    console.log(`   POST /auth/login`);
    console.log(`   POST /api/upload`);
    console.log(`   GET  /api/status`);
    console.log(`   GET  /api/history`);
    console.log(`   GET  /api/health`);
});