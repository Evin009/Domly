import { Router } from 'express'
import { executeCommand } from '../controllers/commandController.js'
import { requireAuth } from '../middleware/authMiddleware.js'

const router = Router()

router.post('/run', requireAuth, executeCommand)

export default router
