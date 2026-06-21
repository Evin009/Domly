import { useState, useRef } from 'react'
import { api } from '../api/client'

const SAMPLE_RATE = 16000
const RECORD_SECONDS = 8
const SAMPLES_NEEDED = 3

const PROMPTS = [
  'Hey Domly, turn on the lights',
  'Hey Domly, lock the front door',
  'Hey Domly, what is the temperature'
]

export default function Enrollment({ onComplete }) {
  const [step, setStep] = useState('intro')       // intro | recording | saving | done | error
  const [sampleIdx, setSampleIdx] = useState(0)
  const [countdown, setCountdown] = useState(RECORD_SECONDS)
  const [error, setError] = useState('')
  const audioSamplesRef = useRef([])              // collected base64 WAV buffers

  async function startRecording(idx) {
    setSampleIdx(idx)
    setCountdown(RECORD_SECONDS)
    setStep('recording')

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: SAMPLE_RATE, channelCount: 1, echoCancellation: false }
      })

      const recorder = new MediaRecorder(stream)
      const chunks = []
      recorder.ondataavailable = (e) => chunks.push(e.data)

      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(chunks, { type: 'audio/webm' })
        const arrayBuf = await blob.arrayBuffer()
        const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuf)))
        audioSamplesRef.current.push(base64)

        if (audioSamplesRef.current.length < SAMPLES_NEEDED) {
          setTimeout(() => startRecording(audioSamplesRef.current.length), 800)
        } else {
          await finishEnrollment()
        }
      }

      recorder.start()

      // countdown
      let rem = RECORD_SECONDS
      const tick = setInterval(() => {
        rem -= 1
        setCountdown(rem)
        if (rem <= 0) { clearInterval(tick); recorder.stop() }
      }, 1000)

    } catch (err) {
      setError(err.message || 'Microphone access denied')
      setStep('error')
    }
  }

  async function finishEnrollment() {
    setStep('saving')
    try {
      await api.enrollmentComplete()
      setStep('done')
      setTimeout(onComplete, 1500)
    } catch (err) {
      setError(err.message)
      setStep('error')
    }
  }

  function retry() {
    audioSamplesRef.current = []
    setStep('intro')
    setError('')
  }

  if (step === 'done') return (
    <div className="enrollment">
      <div className="enroll-icon success">✓</div>
      <h2>Voice enrolled!</h2>
      <p>Domly will now only respond to your voice.</p>
    </div>
  )

  if (step === 'error') return (
    <div className="enrollment">
      <div className="enroll-icon fail">✕</div>
      <h2>Something went wrong</h2>
      <p className="enroll-error">{error}</p>
      <button className="enroll-btn" onClick={retry}>Try Again</button>
    </div>
  )

  if (step === 'saving') return (
    <div className="enrollment">
      <div className="enroll-spinner" />
      <h2>Saving your voice...</h2>
    </div>
  )

  if (step === 'recording') return (
    <div className="enrollment">
      <div className="enroll-progress-bar">
        <div className="enroll-progress-fill" style={{ width: `${(sampleIdx / SAMPLES_NEEDED) * 100}%` }} />
      </div>
      <p className="enroll-step-count">Sample {sampleIdx + 1} of {SAMPLES_NEEDED}</p>
      <div className="enroll-recording-pulse">
        <div className="rec-ring" /><div className="rec-ring delay" />
        <div className="rec-dot" />
      </div>
      <p className="enroll-phrase">"{PROMPTS[sampleIdx]}"</p>
      <p className="enroll-hint">Recording… {countdown}s</p>
    </div>
  )

  return (
    <div className="enrollment">
      <div className="enroll-icon">🎙️</div>
      <h2>Set up your voice</h2>
      <p>Say 3 short phrases so Domly learns to recognise only your voice.</p>

      <div className="enroll-phrase-list">
        {PROMPTS.map((phrase, i) => (
          <div key={i} className={`enroll-phrase-item ${i < audioSamplesRef.current.length ? 'done' : ''}`}>
            <span className="enroll-phrase-num">{i + 1}</span>
            <span>"{phrase}"</span>
            {i < audioSamplesRef.current.length && <span className="enroll-check">✓</span>}
          </div>
        ))}
      </div>

      <button className="enroll-btn" onClick={() => startRecording(0)}>
        Start Recording
      </button>
    </div>
  )
}
