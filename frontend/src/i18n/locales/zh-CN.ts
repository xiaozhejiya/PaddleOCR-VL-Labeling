export default {
  common: {
    save: '保存',
    cancel: '取消',
    confirm: '确认',
    delete: '删除',
    edit: '编辑',
    create: '创建',
    search: '搜索',
    loading: '加载中...',
    noData: '暂无数据',
    success: '操作成功',
    error: '操作失败',
    retry: '重试',
    back: '返回',
  },
  auth: {
    login: '登录',
    register: '注册',
    logout: '退出登录',
    username: '用户名',
    password: '密码',
    email: '邮箱',
    forgotPassword: '忘记密码',
    noAccount: '没有账号？',
    hasAccount: '已有账号？',
  },
  project: {
    title: '项目列表',
    create: '创建项目',
    name: '项目名称',
    description: '项目描述',
    status: '状态',
    actions: '操作',
  },
  annotation: {
    saveStatus: {
      saved: '已保存',
      saving: '保存中...',
      dirty: '未保存',
      conflict: '冲突',
      readonly: '只读',
      autosave_pending: '待自动保存',
      autosaving: '自动保存中...',
      autosave_failed: '自动保存失败',
      manual_saving: '手动保存中...',
    },
  },
  workspace: {
    taskQueue: '任务队列',
    canvasPlaceholder: '标注画布开发中...',
    propertiesPanel: '属性面板',
    revisionLog: 'Revision 日志',
    leaveConfirm: '当前有未保存的修改，确定要离开吗？',
  },
  // 路由标题 i18n key
  routes: {
    auth: {
      login: '登录',
      register: '注册',
    },
    app: {
      home: '工作台',
    },
    projects: {
      index: '项目列表',
      detail: '项目详情',
      tabs: {
        jobs: '任务',
        exports: '导出',
      },
    },
    pages: {
      workspace: '标注工作台',
    },
    settings: {
      index: '设置',
    },
    error: {
      forbidden: '权限不足',
      notFound: '页面不存在',
    },
  },
  errors: {
    network: '网络错误，请检查网络连接',
    unauthorized: '未登录，请先登录',
    forbidden: '权限不足，无法访问该资源',
    notFound: '请求的资源不存在',
    server: '服务器错误，请稍后重试',
    unknown: '未知错误',
  },
}
