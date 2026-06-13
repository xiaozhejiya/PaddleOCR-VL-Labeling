import { describe, it, expect } from 'vitest'
import { computeCanWriteAnnotation } from '../workspaceGuards'

describe('computeCanWriteAnnotation', () => {
  it('revision_id 存在时只读', () => {
    expect(computeCanWriteAnnotation({
      can_create_annotation_revision: true,
      revision_id: 'rev_1',
      saving: false,
      save_status: 'saved',
    })).toBe(false)
  })

  it('无 can_create_annotation_revision 时只读', () => {
    expect(computeCanWriteAnnotation({
      can_create_annotation_revision: false,
      revision_id: null,
      saving: false,
      save_status: 'saved',
    })).toBe(false)
  })

  it('saving 时只读', () => {
    expect(computeCanWriteAnnotation({
      can_create_annotation_revision: true,
      revision_id: null,
      saving: true,
      save_status: 'saved',
    })).toBe(false)
  })

  it('conflict/autosaving/manual_saving 时禁止写入', () => {
    expect(computeCanWriteAnnotation({
      can_create_annotation_revision: true,
      revision_id: null,
      saving: false,
      save_status: 'conflict',
    })).toBe(false)
    expect(computeCanWriteAnnotation({
      can_create_annotation_revision: true,
      revision_id: null,
      saving: false,
      save_status: 'autosaving',
    })).toBe(false)
    expect(computeCanWriteAnnotation({
      can_create_annotation_revision: true,
      revision_id: null,
      saving: false,
      save_status: 'manual_saving',
    })).toBe(false)
  })

  it('满足条件时允许写入', () => {
    expect(computeCanWriteAnnotation({
      can_create_annotation_revision: true,
      revision_id: null,
      saving: false,
      save_status: 'saved',
    })).toBe(true)
  })
})

