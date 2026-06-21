import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'

// Status states and what to show for each
const STATUS = {
  idle:       { label: 'Say "Hey Domly" to start',  pulse: false, glow: false,  error: false },
  requesting: { label: 'Requesting microphone…',     pulse: false, glow: false,  error: false },
  listening:  { label: 'Listening…',                 pulse: true,  glow: true,   error: false },
  processing: { label: 'Processing…',                pulse: true,  glow: true,   error: false },
  speaking:   { label: 'Speaking…',                  pulse: true,  glow: true,   error: false },
  rejected:   { label: 'Voice not recognised',       pulse: false, glow: false,  error: true  },
  mic_error:  { label: 'Microphone access denied',   pulse: false, glow: false,  error: true  }
}

export default function Home({ onReEnroll }) {
  const [status, setStatus] = useState('idle')
  const [conversation, setConversation] = useState([])  // [{ role, text }]
  const conversationEndRef = useRef(null)

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversation])

  // TODO (Phase 2): Initialise Porcupine here for wake word detection.
  // When wake word fires → call handleWakeWord()
  useEffect(() => {
    requestMic()
  }, [])

  async function requestMic() {
    setStatus('requesting')
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true })
      setStatus('idle')
    } catch {
      setStatus('mic_error')
    }
  }

  // Called by Porcupine callback when "Hey Domly" is detected.
  // TODO (Phase 2): wire this to actual Porcupine wake word event.
  async function handleWakeWord() {
    setStatus('listening')

    try {
      // TODO (Phase 2): run Eagle verification on the recorded audio.
      // For now, record via Web Speech API and send directly.
      const command = await listenForCommand()
      if (!command) { setStatus('idle'); return }

      setConversation(c => [...c, { role: 'user', text: command }])
      setStatus('processing')

      const { result } = await api.runCommand(command)
      setConversation(c => [...c, { role: 'assistant', text: result }])
      setStatus('speaking')

      // TODO (Phase 2): pipe result through TTS.
      await speakText(result)
      setStatus('idle')

    } catch (err) {
      console.error(err)
      setStatus('idle')
    }
  }

  function listenForCommand() {
    return new Promise((resolve) => {
      if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        resolve(null)
        return
      }
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition
      const recognition = new SR()
      recognition.lang = 'en-US'
      recognition.interimResults = false
      recognition.maxAlternatives = 1
      recognition.onresult = (e) => resolve(e.results[0][0].transcript)
      recognition.onerror = () => resolve(null)
      recognition.onend = () => {}
      recognition.start()
    })
  }

  function speakText(text) {
    return new Promise((resolve) => {
      const utt = new SpeechSynthesisUtterance(text)
      utt.onend = resolve
      utt.onerror = resolve
      window.speechSynthesis.speak(utt)
    })
  }

  const { label, pulse, glow, error: isError } = STATUS[status] ?? STATUS.idle
  const isRejected = status === 'rejected'

  return (
    <div className="home">
      <div className="home-logo">Domly</div>

      {/* Mic orb */}
      <div className={['mic-wrapper', pulse ? 'active' : '', glow ? 'glow' : '', isError ? 'denied' : ''].join(' ')}>
        {pulse && <div className="pulse-ring" />}
        {pulse && <div className="pulse-ring delay" />}
        <button
          className="mic-btn"
          onClick={status === 'idle' ? handleWakeWord : undefined}
          title={status === 'idle' ? 'Click to speak' : undefined}
          style={{ cursor: status === 'idle' ? 'pointer' : 'default' }}
        >
          <MicIcon />
        </button>
      </div>

      <p className={`mic-status ${isError || isRejected ? 'error' : ''}`}>{label}</p>

      {isRejected && (
        <button className="link-btn" onClick={onReEnroll}>Re-enroll my voice</button>
      )}

      {/* Conversation log */}
      {conversation.length > 0 && (
        <div className="conversation">
          {conversation.map((msg, i) => (
            <div key={i} className={`msg ${msg.role}`}>
              <span className="msg-label">{msg.role === 'user' ? 'You' : 'Domly'}</span>
              <p>{msg.text}</p>
            </div>
          ))}
          <div ref={conversationEndRef} />
        </div>
      )}
    </div>
  )
}

function MicIcon() {
  return (
    <svg width="36" height="36" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z" />
      <path d="M19 11a1 1 0 0 0-2 0 5 5 0 0 1-10 0 1 1 0 0 0-2 0 7 7 0 0 0 6 6.93V20H9a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2h-2v-2.07A7 7 0 0 0 19 11z" />
    </svg>
  )
}
