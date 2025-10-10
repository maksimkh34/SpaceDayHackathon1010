import React, { useEffect, useRef, useState } from 'react'
import { uploadImage } from '../api'

export default function CameraUpload({ onNewReport }) {
    const videoRef = useRef(null)
    const canvasRef = useRef(null)
    const [cameraOn, setCameraOn] = useState(false)
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [progress, setProgress] = useState(0)

    useEffect(() => {
        return () => stopCamera()
    }, [])

    async function startCamera() {
        try {
            const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
            videoRef.current.srcObject = s
            await videoRef.current.play()
            setCameraOn(true)
        } catch (err) {
            alert('Не удалось включить камеру: ' + err.message)
        }
    }

    function stopCamera() {
        const s = videoRef.current?.srcObject
        if (s) s.getTracks().forEach((t) => t.stop())
        if (videoRef.current) videoRef.current.srcObject = null
        setCameraOn(false)
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
                    {cameraOn ? (
                        <div className="camera-box">
                            <video ref={videoRef} playsInline muted />
                            <button className="btn small" onClick={capture}>Сделать фото</button>
                        </div>
                    ) : (
                        <div className="hint">Камера не включена. Можно выбрать файл.</div>
                    )}

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