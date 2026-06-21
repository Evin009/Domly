import { Router } from 'express'
import { markEnrolled } from '../controllers/voiceController.js'
import { requireAuth } from '../middleware/authMiddleware.js'

const router = Router()

router.post('/enrollment-complete', requireAuth, markEnrolled)

export default router
