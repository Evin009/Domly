import supabase from '../services/supabase.js'
import { runCommand } from '../services/smartrentMCP.js'
import { getDecryptedCredentials } from './authController.js'

// POST /commands/run
// Body: { command: '<text>' }
//
// Voice verification already happened locally in Electron (Picovoice Eagle).
// Backend just checks JWT, confirms user is enrolled, then sends command to MCP.
export async function executeCommand(req, res, next) {
  try {
    const { command } = req.body
    if (!command) return res.status(400).json({ error: 'command is required' })

    const userId = req.user.userId

    // Confirm enrollment before executing anything
    const { data: user, error } = await supabase
      .from('users')
      .select('is_enrolled')
      .eq('id', userId)
      .single()

    if (error) throw error
    if (!user.is_enrolled) {
      return res.status(403).json({ error: 'Voice not enrolled — complete enrollment first' })
    }

    const { sr_email, sr_password } = await getDecryptedCredentials(userId)
    const result = await runCommand(sr_email, sr_password, command)

    res.json({ result })
  } catch (err) {
    next(err)
  }
}
