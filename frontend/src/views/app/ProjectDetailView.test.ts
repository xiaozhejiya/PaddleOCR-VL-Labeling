import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const {
  push,
  replace,
  listMock,
  getCapabilitiesMock,
  deleteMock,
} = vi.hoisted(() => ({
  push: vi.fn(),
  replace: vi.fn(),
  listMock: vi.fn(),
  getCapabilitiesMock: vi.fn(),
  deleteMock: vi.fn(),
}))

import ProjectDetailView from './ProjectDetailView.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { project_id: '10' },
    query: {},
  }),
  useRouter: () => ({
    push,
    replace,
  }),
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

vi.mock('@/api/pages', () => ({
  pagesApi: {
    list: listMock,
    getCapabilities: getCapabilitiesMock,
    delete: deleteMock,
  },
}))

vi.mock('@/api/assets', () => ({
  assetsApi: {
    uploadWithProgress: vi.fn(),
  },
}))

vi.mock('./projectDetailErrors', () => ({
  formatProjectDetailError: vi.fn(() => 'error'),
}))

function createWrapper() {
  return mount(ProjectDetailView, {
    global: {
      stubs: {
        RouterLink: {
          template: '<a><slot /></a>',
        },
      },
    },
  })
}

describe('ProjectDetailView', () => {
  beforeEach(() => {
    push.mockReset()
    replace.mockReset()
    listMock.mockReset()
    getCapabilitiesMock.mockReset()
    deleteMock.mockReset()

    listMock.mockResolvedValue({
      items: [
        {
          page_id: 'page_1',
          project_id: 10,
          filename: 'page.png',
          status: 'imported',
          width: 100,
          height: 200,
        },
      ],
      total: 1,
    })
    deleteMock.mockResolvedValue(undefined)
  })

  it('无 can_import_pages 时不显示删除按钮', async () => {
    getCapabilitiesMock.mockResolvedValue({
      can_import_pages: false,
    })

    const wrapper = createWrapper()
    await flushPromises()

    const deleteButtons = wrapper.findAll('button').filter(button =>
      button.classes().includes('text-danger') && button.classes().includes('p-2'),
    )
    expect(deleteButtons).toHaveLength(0)
  })

  it('有 can_import_pages 时显示删除按钮', async () => {
    getCapabilitiesMock.mockResolvedValue({
      can_import_pages: true,
    })

    const wrapper = createWrapper()
    await flushPromises()

    const deleteButtons = wrapper.findAll('button').filter(button =>
      button.classes().includes('text-danger') && button.classes().includes('p-2'),
    )
    expect(deleteButtons).toHaveLength(1)
  })
})
