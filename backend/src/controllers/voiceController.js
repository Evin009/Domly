import supabase from '../services/supabase.js'

// POST /voice/enrollment-complete
// Called by Electron after Eagle finishes enrolling the user's voice locally.
// Backend just flips the is_enrolled flag in Supabase.
export async function markEnrolled(req, res, next) {
  try {
    const { error } = await supabase
      .from('users')
      .update({ is_enrolled: true })
      .eq('id', req.user.userId)

    if (error) throw error

    res.json({ success: true })
  } catch (err) {
    next(err)
  }
}
