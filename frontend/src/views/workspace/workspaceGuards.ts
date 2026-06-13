export type SaveStatus =
  | 'saved'
  | 'dirty'
  | 'autosave_pending'
  | 'autosaving'
  | 'autosave_failed'
  | 'manual_saving'
  | 'conflict'
  | 'readonly'

export const SAVE_STATUS_KEY = 'saveStatus' as const
export const UPDATE_SAVE_STATUS_KEY = 'updateSaveStatus' as const

export function computeCanWriteAnnotation(params: {
  can_create_annotation_revision: boolean
  revision_id?: string | null
  saving: boolean
  save_status?: SaveStatus | null
}): boolean {
  if (!params.can_create_annotation_revision) return false
  if (params.revision_id) return false
  if (params.saving) return false
  if (!params.save_status) return true
  if (params.save_status === 'readonly') return false
  if (params.save_status === 'conflict') return false
  if (params.save_status === 'autosaving') return false
  if (params.save_status === 'manual_saving') return false
  return true
}
