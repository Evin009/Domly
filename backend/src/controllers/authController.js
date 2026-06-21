import jwt from 'jsonwebtoken'
import crypto from 'crypto'
import supabase from '../services/supabase.js'
import { validateCredentials } from '../services/smartrentMCP.js'

const ALGO = 'aes-256-gcm'
const KEY = Buffer.from(process.env.ENCRYPTION_KEY, 'hex')

function encrypt(text) {
  const iv = crypto.randomBytes(12)
  const cipher = crypto.createCipheriv(ALGO, KEY, iv)
  const enc = Buffer.concat([cipher.update(text, 'utf8'), cipher.final()])
  return [iv, cipher.getAuthTag(), enc].map(b => b.toString('hex')).join(':')
}

function decrypt(payload) {
  const [ivHex, tagHex, encHex] = payload.split(':')
  const decipher = crypto.createDecipheriv(ALGO, KEY, Buffer.from(ivHex, 'hex'))
  decipher.setAuthTag(Buffer.from(tagHex, 'hex'))
  return decipher.update(Buffer.from(encHex, 'hex')) + decipher.final('utf8')
}

function signToken(userId, srEmail) {
  return jwt.sign({ userId, srEmail }, process.env.JWT_SECRET, { expiresIn: '30d' })
}

export async function login(req, res, next) {
  try {
    const { sr_email, sr_password } = req.body
    if (!sr_email || !sr_password) {
      return res.status(400).json({ error: 'SmartRent email and password required' })
    }

    // Validate credentials against SmartRent via MCP
    const valid = await validateCredentials(sr_email, sr_password)
    if (!valid) {
      return res.status(401).json({ error: 'Invalid SmartRent credentials' })
    }

    // Upsert user in Supabase (first login creates the row)
    const { data: user, error } = await supabase
      .from('users')
      .upsert(
        { sr_email, sr_password_enc: encrypt(sr_password) },
        { onConflict: 'sr_email', ignoreDuplicates: false }
      )
      .select('id, sr_email, azure_speaker_profile_id')
      .single()

    if (error) throw error

    res.json({
      token: signToken(user.id, user.sr_email),
      is_enrolled: !!user.azure_speaker_profile_id,
    })
  } catch (err) {
    next(err)
  }
}

export async function me(req, res, next) {
  try {
    const { data: user, error } = await supabase
      .from('users')
      .select('id, sr_email, azure_speaker_profile_id')
      .eq('id', req.user.userId)
      .single()

    if (error) throw error

    res.json({
      id: user.id,
      sr_email: user.sr_email,
      is_enrolled: !!user.azure_speaker_profile_id,
    })
  } catch (err) {
    next(err)
  }
}

// Used internally by other services to get the decrypted SR password
export async function getDecryptedCredentials(userId) {
  const { data, error } = await supabase
    .from('users')
    .select('sr_email, sr_password_enc')
    .eq('id', userId)
    .single()

  if (error) throw error
  return { sr_email: data.sr_email, sr_password: decrypt(data.sr_password_enc) }
}
