// App.jsx
import React, { useEffect, useState } from 'react'
import Auth from './components/Auth'
import CameraUpload from './components/CameraUpload'
import ReportView from './components/ReportView' // Импортируем новый компонент
import { readToken, clearToken, getAiStatus, getHistory } from './api'

export default function App() {
    const [theme, setTheme] = useState('dark')
    const [token, setToken] = useState(readToken())
    const [report, setReport] = useState(null)
    const [history, setHistory] = useState([])
    const [showSplash, setShowSplash] = useState(true)
    const [fadeOut, setFadeOut] = useState(false)

    useEffect(() => {
        document.body.classList.remove('light', 'dark')
        document.body.classList.add(theme)
    }, [theme])

    function toggleTheme() {
        setTheme(prevTheme => (prevTheme === 'light' ? 'dark' : 'light'))
    }

    useEffect(() => {
        const t1 = setTimeout(() => {
            setFadeOut(true)
        }, 2000)

        const t2 = setTimeout(() => {
            setShowSplash(false)
        }, 2500)

        return () => {
            clearTimeout(t1)
            clearTimeout(t2)
        }
    }, [])

    useEffect(() => {
        if (!token) return setHistory([])
        getHistory().then((r) => setHistory(r.data || [])).catch(() => {})
    }, [token])

    function onLogin(tkn) {
        setToken(tkn)
    }

    function onLogout() {
        clearToken()
        setToken(null)
        setReport(null)
        setHistory([])
    }

    function onNewReport(r) {
        setReport(r)
        setHistory((h) => [{ id: r.id, result: r.result, date: r.timestamp }, ...h])
    }

    async function checkAI() {
        try {
            const r = await getAiStatus()
            alert('AI: ' + r.data.ai_status)
        } catch (e) {
            alert('Ошибка проверки AI')
        }
    }

    function shareReport(r) {
        const id = Date.now().toString(36)
        localStorage.setItem(`shared_report_${id}`, JSON.stringify(r))
        const url = `${window.location.origin}/share/${id}`
        navigator.clipboard?.writeText(url).then(() => alert('Ссылка скопирована:\n' + url))
    }

    useEffect(() => {
        const path = window.location.pathname
        if (path.startsWith('/share/')) {
            const id = path.split('/share/')[1]
            const payload = localStorage.getItem(`shared_report_${id}`)
            if (payload) setReport(JSON.parse(payload))
        }
    }, [])

    function goHome() {
        setReport(null)
    }

    if (showSplash) {
        return (
            <div className={`splash ${fadeOut ? 'fade-out' : ''}`}>
                <div className="logo">HealthPix</div>
                <div className="subtitle">Анализ здоровья по селфи</div>
            </div>
        )
    }

    if (!token) {
        return (
            <div className="page center">
                <Auth onLogin={onLogin} />
            </div>
        )
    }

    return (
        <div className="page">
            <header className="top">
                <div className="brand" style={{ cursor: 'pointer' }} onClick={goHome}>HealthPix</div>
                <div className="actions">
                    <button
                        className="btn ghost"
                        onClick={toggleTheme}
                        style={{ padding: '0 12px', fontSize: '24px' }}
                        aria-label="Toggle theme"
                    >
                        {theme === 'light' ? '🌙' : '☀️'}
                    </button>
                    <button className="btn" onClick={checkAI}>AI status</button>
                    <button className="btn outline" onClick={onLogout}>Выйти</button>
                </div>
            </header>

            <main className="container">
                <section className="left">
                    {!report ? (
                        <CameraUpload onNewReport={onNewReport} />
                    ) : (
                        <div className="card report">
                            <h3>Отчет анализа кожи</h3>
                            <div className="report-meta">{new Date(report.timestamp).toLocaleString()}</div>

                            <div className="report-body">
                                <img src={report.imageURL} alt="Анализируемое фото" className="report-image" />

                                {/* Используем новый компонент */}
                                <ReportView report={report} />
                            </div>

                            <div className="row gap" style={{ marginTop: 12 }}>
                                <button className="btn">Скачать отчёт</button>
                                <button className="btn outline" onClick={() => shareReport(report)}>Создать ссылку</button>
                                <button className="btn ghost" onClick={goHome}>Вернуться на главную</button>
                            </div>
                        </div>
                    )}
                </section>

                <aside className="right">
                    <div className="card">
                        <h4>История анализов</h4>
                        {history.length === 0 ? <div className="hint">История пуста</div> : (
                            <ul className="history-list">
                                {history.map((h) => (
                                    <li key={h.id}>
                                        <div className="hist-result">
                                            {(() => {
                                                try {
                                                    const data = JSON.parse(h.result)
                                                    return `Состояние: ${Math.round(data.overall_score * 100)}щ`
                                                } catch {
                                                    return h.result.substring(0, 50) + '...'
                                                }
                                            })()}
                                        </div>
                                        <div className="hist-date">{new Date(h.date).toLocaleString()}</div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </aside>
            </main>
        </div>
    )
}