

import React, { useEffect, useState } from 'react'
import Auth from './components/Auth'
import CameraUpload from './components/CameraUpload'
import { readToken, clearToken, getAiStatus, getHistory } from './api'

export default function App() {
    const [token, setToken] = useState(readToken())
    const [report, setReport] = useState(null)
    const [history, setHistory] = useState([])
    const [showSplash, setShowSplash] = useState(true)

    useEffect(() => {
        const t = setTimeout(() => setShowSplash(false), 1200)
        return () => clearTimeout(t)
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
        setHistory((h) => [ { id: r.id, result: r.result, date: r.timestamp }, ...h ])
    }

    async function checkAI() {
        try {
            const r = await getAiStatus()
            alert('AI: ' + r.data.ai_status)
        } catch (e) {
            alert('Ошибка проверки AI')
        }
    }

    function saveReportPdf(r) {
        const html = `\n      <html><body><h1>Report</h1><p>${new Date(r.timestamp).toLocaleString()}</p><img src="${r.imageURL}" style="max-width:90%" /><pre>${r.result}</pre></body></html>`
        const w = window.open('', '_blank')
        w.document.write(html)
        w.document.close()
        setTimeout(() => w.print(), 300)
    }

    function shareReport(r) {
        const id = Date.now().toString(36)
        localStorage.setItem(`shared_report_${id}`, JSON.stringify(r))
        const url = `${window.location.origin}/share/${id}`
        navigator.clipboard?.writeText(url).then(() => alert('Ссылка скопирована:\n' + url))
    }

    // handle shared report in URL
    useEffect(() => {
        const path = window.location.pathname
        if (path.startsWith('/share/')) {
            const id = path.split('/share/')[1]
            const payload = localStorage.getItem(`shared_report_${id}`)
            if (payload) setReport(JSON.parse(payload))
        }
    }, [])

    if (showSplash) {
        return (
            <div className="splash">
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
                <div className="brand">HealthPix</div>
                <div className="actions">
                    <button className="btn small" onClick={checkAI}>AI status</button>
                    <button className="btn outline" onClick={onLogout}>Выйти</button>
                </div>
            </header>

            <main className="container">
                <section className="left">
                    <CameraUpload onNewReport={onNewReport} />

                    {report && (
                        <div className="card report">
                            <h3>Отчет</h3>
                            <div className="report-meta">{new Date(report.timestamp).toLocaleString()}</div>
                            <div className="report-body">
                                <img src={report.imageURL} alt="report" />
                                <pre>{report.result}</pre>
                            </div>
                            <div className="row gap">
                                <button className="btn" onClick={() => saveReportPdf(report)}>Сохранить как PDF</button>
                                <button className="btn outline" onClick={() => shareReport(report)}>Создать ссылку</button>
                            </div>
                        </div>
                    )}
                </section>

                <aside className="right">
                    <div className="card">
                        <h4>История</h4>
                        {history.length === 0 ? <div className="hint">История пуста</div> : (
                            <ul className="history-list">
                                {history.map((h) => (
                                    <li key={h.id}>
                                        <div className="hist-result">{h.result}</div>
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


