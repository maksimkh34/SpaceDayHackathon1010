// FILE: src/components/CameraUpload.jsx
import React, { useEffect, useRef, useState } from 'react'
import { uploadImage } from '../api'

export default function CameraUpload({ onNewReport }) {
    const videoRef = useRef(null)
    const canvasRef = useRef(null)
    const [cameraOn, setCameraOn] = useState(false)
    const [streamObj, setStreamObj] = useState(null)
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [progress, setProgress] = useState(0)

    // Очистка при размонтировании
    useEffect(() => {
        return () => {
            stopCamera()
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    async function startCamera() {
        try {
            // сначала попросим поток
            const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })

            // сохраним объект потока в стейт (чтобы можно было остановить)
            setStreamObj(s)

            // Включаем отображение видео (сам элемент уже в DOM, т.к. мы всегда рендерим <video>)
            setCameraOn(true)

            // Привязываем поток к видео. Иногда videoRef.current может появиться мгновенно — но проверяем на всякий случай.
            if (videoRef.current) {
                videoRef.current.srcObject = s
                try {
                    // попытаться запустить воспроизведение (некоторые браузеры требуют этого)
                    await videoRef.current.play()
                } catch (playErr) {
                    // если autoplay блокируется, всё равно оставляем видео элемент с потоком
                    console.warn('video.play() failed:', playErr)
                }
            }
        } catch (err) {
            console.error('camera start error', err)
            alert('Не удалось включить камеру: ' + (err.message || err))
            // гарантированно выключаем состояние
            setCameraOn(false)
            if (streamObj) stopCamera()
        }
    }

    function stopCamera() {
        try {
            if (streamObj) {
                streamObj.getTracks().forEach((t) => t.stop())
            } else {
                const s = videoRef.current?.srcObject
                if (s && s.getTracks) s.getTracks().forEach((t) => t.stop())
            }
        } catch (e) {
            console.warn('stopCamera error', e)
        } finally {
            if (videoRef.current) {
                try { videoRef.current.srcObject = null } catch (e) {}
            }
            setStreamObj(null)
            setCameraOn(false)
        }
    }

    function capture() {
        const v = videoRef.current
        const canvas = canvasRef.current
        if (!v || !canvas) return
        canvas.width = v.videoWidth || 640
        canvas.height = v.videoHeight || 480
        const ctx = canvas.getContext('2d')
        ctx.drawImage(v, 0, 0, canvas.width, canvas.height)
        canvas.toBlob((blob) => {
            if (!blob) return
            const f = new File([blob], `selfie_${Date.now()}.jpg`, { type: 'image/jpeg' })
            setFile(f)
        }, 'image/jpeg', 0.9)
    }

    function onFile(e) {
        const f = e.target.files && e.target.files[0]
        if (f) setFile(f)
    }

    async function doUpload() {
        if (!file) return alert('Сначала выберите фото')
        setUploading(true)
        setProgress(0)
        try {
            const res = await uploadImage(file, (evt) => {
                if (evt.total) setProgress(Math.round((evt.loaded / evt.total) * 100))
            })
            const data = res.data
            const report = {
                id: Date.now().toString(36),
                result: data.result,
                timestamp: data.timestamp || new Date().toISOString(),
                imageURL: URL.createObjectURL(file),
                imageName: file.name,
            }
            onNewReport(report)
        } catch (err) {
            alert('Ошибка при загрузке: ' + (err?.response?.data?.message || err.message))
        } finally {
            setUploading(false)
            setProgress(0)
        }
    }

    return (
        <div className="card">
            <h3>Селфи / Загрузка</h3>

            <div className="controls">
                <div className="row">
                    {!cameraOn ? (
                        <button className="btn" onClick={startCamera}>Включить камеру</button>
                    ) : (
                        <button className="btn" onClick={stopCamera}>Отключить камеру</button>
                    )}

                    <label className="btn file-btn">
                        Выбрать фото
                        <input type="file" accept="image/*" onChange={onFile} />
                    </label>
                </div>

                <div className="preview">
                    {/* video всегда в DOM, но скрыт если камера выключена */}
                    <div className="camera-box" style={{ position: 'relative' }}>
                        <video
                            ref={videoRef}
                            style={{ width: '100%', height: '280px', objectFit: 'cover', borderRadius: 8, display: cameraOn ? 'block' : 'none' }}
                            playsInline
                            muted
                        />
                        {!cameraOn && <div className="hint">Камера не включена. Можно выбрать файл.</div>}
                        {cameraOn && (
                            <button className="btn small" onClick={capture} style={{ position: 'absolute', right: 12, bottom: 12 }}>
                                Сделать фото
                            </button>
                        )}
                    </div>

                    {file && (
                        <div className="file-preview">
                            <img src={URL.createObjectURL(file)} alt="preview" />
                            <div className="row gap">
                                <button className="btn" onClick={doUpload} disabled={uploading}>{uploading ? 'Загрузка...' : 'Загрузить'}</button>
                                <button className="btn outline" onClick={() => setFile(null)}>Сбросить</button>
                            </div>
                        </div>
                    )}

                    {uploading && (
                        <div className="progress">
                            <div className="bar" style={{ width: `${progress}%` }}></div>
                            <span>{progress}%</span>
                        </div>
                    )}
                </div>

                <canvas ref={canvasRef} style={{ display: 'none' }} />
            </div>
        </div>
    )
}
