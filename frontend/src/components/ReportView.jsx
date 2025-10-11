// components/ReportView.jsx
import React, { useEffect, useState } from 'react';

const ReportView = ({ report }) => {
    const data = JSON.parse(report.result);
    const [animatedScore, setAnimatedScore] = useState(0);
    const [showDetails, setShowDetails] = useState(false);
    const [isAnimating, setIsAnimating] = useState(true);

    // Получаем цвет для диаграммы в зависимости от уровня здоровья
    const getScoreColor = (score) => {
        if (score >= 0.8) return '#4CAF50'; // Отлично - зеленый
        if (score >= 0.6) return '#8BC34A'; // Хорошо - светло-зеленый
        if (score >= 0.4) return '#FFC107'; // Удовлетворительно - желтый
        return '#F44336'; // Требует внимания - красный
    };

    // Получаем цвет текста для контраста с фоном диаграммы
    const getTextColor = (score) => {
        return score >= 0.4 ? '#1a1a1a' : '#ffffff'; // Темный текст для светлых цветов, белый для темных
    };

    // Анимация общего уровня здоровья
    useEffect(() => {
        setIsAnimating(true);
        const duration = 1500;
        const startTime = Date.now();
        const startValue = 0;
        const endValue = data.overall_score;

        const animate = () => {
            const now = Date.now();
            const progress = Math.min((now - startTime) / duration, 1);

            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = startValue + (endValue - startValue) * easeOutQuart;

            setAnimatedScore(currentValue);

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                setIsAnimating(false);
            }
        };

        requestAnimationFrame(animate);
    }, [data.overall_score]);

    const toggleDetails = () => {
        setShowDetails(!showDetails);
    };

    const scoreColor = getScoreColor(data.overall_score);
    const textColor = getTextColor(data.overall_score);

    return (
        <div className="report-view">
            {/* Главный блок с общим уровнем состояния */}
            <div className="overall-score-card">
                <h3>Общий уровень состояния кожи</h3>
                <div className="score-circle-large">
                    <div
                        className="score-progress"
                        style={{
                            background: `conic-gradient(
                ${scoreColor} ${animatedScore * 360}deg, 
                #e0e0e0 0deg
              )`
                        }}
                    >
                        <div className="score-inner">
              <span
                  className="score-percent-large"
                  style={{ color: textColor }}
              >
                {Math.round(animatedScore * 100)}%
              </span>
                            <span
                                className="score-label"
                                style={{ color: textColor }}
                            >
                оценка
              </span>
                        </div>
                    </div>
                    {isAnimating && (
                        <div
                            className="score-pulse"
                            style={{ borderColor: scoreColor }}
                        />
                    )}
                </div>
                <div
                    className="score-description"
                    style={{ color: scoreColor }}
                >
                    {data.overall_score >= 0.8 ? 'Отличное состояние' :
                        data.overall_score >= 0.6 ? 'Хорошее состояние' :
                            data.overall_score >= 0.4 ? 'Удовлетворительное' : 'Требует внимания'}
                </div>
            </div>

            {/* Аккордеон с детальным анализом */}
            <div className="accordion-section">
                <button
                    className={`accordion-header ${showDetails ? 'active' : ''}`}
                    onClick={toggleDetails}
                >
                    <span>Детальный анализ</span>
                    <span className="accordion-arrow">▼</span>
                </button>
                <div className={`accordion-content ${showDetails ? 'show' : ''}`}>
                    <div className="metrics-grid-detailed">
                        {Object.entries(data.metrics).map(([key, value]) => (
                            <div key={key} className="metric-card">
                                <div className="metric-info">
                                    <span className="metric-name">{translateMetric(key)}</span>
                                    <span
                                        className="metric-value-badge"
                                        style={{ backgroundColor: getMetricColor(value) }}
                                    >
                    {Math.round(value * 100)}%
                  </span>
                                </div>
                                <div className="metric-bar-detailed">
                                    <div
                                        className="metric-fill-detailed"
                                        style={{
                                            width: `${value * 100}%`,
                                            backgroundColor: getMetricColor(value)
                                        }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Рекомендации */}
            <div className="recommendations-section">
                <h4>Рекомендации по уходу</h4>
                <div className="recommendations-grid">
                    {data.report.recommendations.map((rec, index) => (
                        <div key={index} className="recommendation-card">
                            <div className="recommendation-icon">💡</div>
                            <div className="recommendation-text">{rec}</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

// Вспомогательные функции
function translateMetric(key) {
    const translations = {
        'pigmentation': 'Пигментация',
        'texture_roughness': 'Неровность текстуры',
        'puffiness': 'Отечность',
        'pore_size': 'Размер пор',
        'redness': 'Покраснение',
        'dark_circles': 'Тёмные круги',
        'mild_acne': 'Лёгкие акне',
        'moderate_acne': 'Умеренные акне',
        'severe_acne': 'Тяжёлые акне',
        'wrinkles': 'Морщины',
        'vascularity': 'Сосудистые проявления',
        'paleness': 'Бледность',
        'jaundice': 'Желтизна',
        'oiliness': 'Жирность',
        'acne_spots': 'Пятна от акне',
        'cyanosis': 'Цианоз'
    };
    return translations[key] || key;
}

function getMetricColor(value) {
    if (value < 0.3) return '#4CAF50';
    if (value < 0.6) return '#FFC107';
    if (value < 0.8) return '#FF9800';
    return '#F44336';
}

export default ReportView;