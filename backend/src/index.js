import 'dotenv/config'
import express from 'express'
import cors from 'cors'

import authRoutes from './routes/auth.js'
import voiceRoutes from './routes/voice.js'
import commandRoutes from './routes/commands.js'
import { errorHandler } from './middleware/errorMiddleware.js'

const app = express()

app.use(cors())
app.use(express.json())

app.use('/auth', authRoutes)
app.use('/voice', voiceRoutes)
app.use('/commands', commandRoutes)

app.get('/health', (_req, res) => res.json({ status: 'ok' }))

app.use(errorHandler)

const PORT = process.env.PORT ?? 3001
app.listen(PORT, () => console.log(`Domly backend running on :${PORT}`))
