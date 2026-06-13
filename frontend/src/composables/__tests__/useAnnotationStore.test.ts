import { describe, expect, it } from 'vitest'

import { useAnnotationStore } from '../useAnnotationStore'

describe('useAnnotationStore', () => {
  it('从后端 k12_annotations 加载 canonical revision', () => {
    const store = useAnnotationStore()

    store.loadFromRevision({
      id: 'rev_public_001',
      page_id: 'page_public_001',
      revision_no: 3,
      status: 'draft',
      qc_status: 'pending',
      data: {
        schema_version: 'k12_annotation_v0.1',
        page_id: 'page_public_001',
        k12_annotations: [
          {
            id: 'ann_question_001',
            label_name: 'question_block',
            label_namespace: 'k12',
            geometry: {
              bbox_xyxy: [10, 20, 110, 120],
              quad: [[10, 20], [110, 20], [110, 120], [10, 120]],
              polygon: [[10, 20], [110, 20], [110, 120], [10, 120]],
              geometry_source: 'manual',
            },
            read_order: 1,
            attributes: { question_number: '1' },
            source_refs: [{ type: 'human' }],
            status: 'draft',
          },
        ],
        relations: [],
        history: [{ revision_id: 'rev_public_001', revision_no: 3 }],
      },
    })

    expect(store.baseRevisionId.value).toBe('rev_public_001')
    expect(store.revisionNo.value).toBe(3)
    expect(store.objects.value).toEqual([
      {
        id: 'ann_question_001',
        type: 'question_block',
        label_namespace: 'k12',
        geometry: {
          bbox_xyxy: [10, 20, 110, 120],
          quad: [[10, 20], [110, 20], [110, 120], [10, 120]],
          polygon: [[10, 20], [110, 20], [110, 120], [10, 120]],
          geometry_source: 'manual',
        },
        read_order: 1,
        attributes: { question_number: '1' },
        source_refs: [{ type: 'human' }],
        status: 'draft',
        color: '#5e6ad2',
      },
    ])
  })

  it('保存时输出 canonical annotation_json，而不是私有 objects', () => {
    const store = useAnnotationStore()
    store.setImageBounds(200, 300)

    const created = store.addObject([-10, 20, 210, 120], {
      name: 'question_block',
      namespace: 'k12',
    })
    const draft = store.toDraft('page_public_001')
    const annotationJson = draft.data as {
      page_id: string
      schema_version: string
      k12_annotations: Array<Record<string, unknown>>
      relations: unknown[]
    }

    expect(draft.base_revision_id).toBeNull()
    expect(annotationJson.schema_version).toBe('k12_annotation_v0.1')
    expect(annotationJson.page_id).toBe('page_public_001')
    expect(annotationJson.relations).toEqual([])
    expect(annotationJson.k12_annotations).toEqual([
      {
        id: created.id,
        type: 'question_block',
        label_namespace: 'k12',
        geometry: {
          bbox_xyxy: [0, 20, 200, 120],
          quad: [[0, 20], [200, 20], [200, 120], [0, 120]],
          polygon: [[0, 20], [200, 20], [200, 120], [0, 120]],
          geometry_source: 'manual',
        },
        read_order: undefined,
        attributes: {},
        source_refs: [],
        status: 'draft',
      },
    ])
    expect('objects' in annotationJson).toBe(false)
  })

  it('moveObject 和 resizeObject 会 clamp 到图片边界', () => {
    const store = useAnnotationStore()
    store.setImageBounds(200, 120)

    const created = store.addObject([10, 20, 60, 80], {
      name: 'question_block',
      namespace: 'k12',
    })

    store.moveObject(created.id, 500, 500)
    expect(store.objects.value[0].geometry.bbox_xyxy).toEqual([150, 60, 200, 120])

    store.resizeObject(created.id, 3, 280, 180)
    expect(store.objects.value[0].geometry.bbox_xyxy).toEqual([150, 60, 200, 120])

    store.resizeObject(created.id, 7, -40, -10)
    expect(store.objects.value[0].geometry.bbox_xyxy).toEqual([0, 0, 200, 120])
  })

  it('read_order session 会清空旧排序并按点击顺序写入 1..N', () => {
    const store = useAnnotationStore()
    store.setImageBounds(300, 200)

    const first = store.addObject([10, 10, 60, 60], {
      name: 'question_block',
      namespace: 'k12',
    })
    const second = store.addObject([80, 10, 140, 60], {
      name: 'answer_area',
      namespace: 'k12',
    })
    const third = store.addObject([160, 10, 220, 60], {
      name: 'formula',
      namespace: 'k12',
    })

    store.setReadOrder(first.id, 9)
    store.setReadOrder(second.id, 7)

    store.startReadOrderSession()
    expect(store.objects.value.map(obj => obj.read_order)).toEqual([undefined, undefined, undefined])

    expect(store.assignNextReadOrder(second.id)).toBe(1)
    expect(store.assignNextReadOrder(first.id)).toBe(2)
    expect(store.assignNextReadOrder(third.id)).toBe(3)
    expect(store.assignNextReadOrder(second.id)).toBe(1)
    expect(store.objects.value.map(obj => obj.read_order)).toEqual([2, 1, 3])

    store.clearReadOrder()
    expect(store.objects.value.map(obj => obj.read_order)).toEqual([undefined, undefined, undefined])

    store.endReadOrderSession()
    expect(store.readOrderSession.value).toEqual({ active: false, counter: 0 })
  })

  it('updateObject 支持同步更新 label_namespace', () => {
    const store = useAnnotationStore()
    store.setImageBounds(200, 120)
    const created = store.addObject([10, 20, 60, 80], {
      name: 'question_block',
      namespace: 'k12',
    })

    store.updateObject(created.id, {
      type: 'figure',
      label_namespace: 'layout',
      color: '#101010',
    })

    expect(store.objects.value[0].type).toBe('figure')
    expect(store.objects.value[0].label_namespace).toBe('layout')
    expect(store.objects.value[0].color).toBe('#101010')
  })
})
