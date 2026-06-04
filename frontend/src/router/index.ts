import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

/**
 * 路由 Meta 类型定义
 * 参考：doc/开发文档/前端/frontend_routing_spec.md 第 10 章
 */
export type AppRouteMeta = {
  requiresAuth: boolean
  layout: 'auth' | 'app' | 'annotationWorkspace' | 'plain'
  titleKey: string
  projectContextSource: 'none' | 'routeParam' | 'pageLoader'
  projectParamName?: 'project_id'
  workspaceRoute?: boolean
  capability?: string
  navKey?: string
  allowWhenAuthenticated?: boolean
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'root',
    redirect: '/app/projects',
  },
  {
    path: '/auth',
    component: () => import('@/views/auth/AuthLayout.vue'),
    children: [
      {
        path: 'login',
        name: 'auth.login',
        component: () => import('@/views/auth/LoginView.vue'),
        meta: {
          requiresAuth: false,
          layout: 'auth',
          titleKey: 'routes.auth.login',
          projectContextSource: 'none',
          allowWhenAuthenticated: false,
        } as AppRouteMeta,
      },
      {
        path: 'register',
        name: 'auth.register',
        component: () => import('@/views/auth/RegisterView.vue'),
        meta: {
          requiresAuth: false,
          layout: 'auth',
          titleKey: 'routes.auth.register',
          projectContextSource: 'none',
          allowWhenAuthenticated: false,
        } as AppRouteMeta,
      },
    ],
  },
  {
    path: '/app',
    component: () => import('@/views/app/AppLayout.vue'),
    meta: {
      requiresAuth: true,
      layout: 'app',
      titleKey: 'routes.app.home',
      projectContextSource: 'none',
    } as AppRouteMeta,
    children: [
      {
        path: '',
        name: 'app.home',
        redirect: '/app/projects',
      },
      {
        path: 'projects',
        name: 'projects.index',
        component: () => import('@/views/app/ProjectsView.vue'),
        meta: {
          requiresAuth: true,
          layout: 'app',
          titleKey: 'routes.projects.index',
          projectContextSource: 'none',
          navKey: 'projects',
        } as AppRouteMeta,
      },
      {
        path: 'projects/:project_id',
        name: 'projects.detail',
        component: () => import('@/views/app/ProjectDetailView.vue'),
        meta: {
          requiresAuth: true,
          layout: 'app',
          titleKey: 'routes.projects.detail',
          projectContextSource: 'routeParam',
          projectParamName: 'project_id',
          navKey: 'projects',
        } as AppRouteMeta,
      },
      {
        path: 'settings',
        name: 'settings.index',
        component: () => import('@/views/app/SettingsView.vue'),
        meta: {
          requiresAuth: true,
          layout: 'app',
          titleKey: 'routes.settings.index',
          projectContextSource: 'none',
          navKey: 'settings',
        } as AppRouteMeta,
      },
    ],
  },
  {
    path: '/app/pages/:page_id',
    component: () => import('@/views/workspace/AnnotationWorkspaceLayout.vue'),
    meta: {
      requiresAuth: true,
      layout: 'annotationWorkspace',
      titleKey: 'routes.pages.workspace',
      projectContextSource: 'pageLoader',
      workspaceRoute: true,
    } as AppRouteMeta,
    children: [
      {
        path: '',
        name: 'pages.workspace',
        component: () => import('@/views/workspace/AnnotationWorkspace.vue'),
      },
    ],
  },
  {
    path: '/403',
    name: 'error.forbidden',
    component: () => import('@/views/ErrorForbiddenView.vue'),
    meta: {
      requiresAuth: false,
      layout: 'plain',
      titleKey: 'routes.error.forbidden',
      projectContextSource: 'none',
    } as AppRouteMeta,
  },
  {
    path: '/404',
    name: 'error.notFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: {
      requiresAuth: false,
      layout: 'plain',
      titleKey: 'routes.error.notFound',
      projectContextSource: 'none',
    } as AppRouteMeta,
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * redirect 安全校验
 * 只允许站内相对路径，不允许 // 开头或包含协议
 */
function isValidRedirect(redirect: string): boolean {
  if (!redirect.startsWith('/')) return false
  if (redirect.startsWith('//')) return false
  if (redirect.includes(':')) return false
  if (redirect === '/auth/login') return false
  return true
}

/**
 * 全局导航守卫
 * 参考：doc/开发文档/前端/frontend_routing_spec.md 第 11 章
 */
router.beforeEach(async (to, _from, next) => {
  // 未匹配路由进入 404
  if (to.matched.length === 0) {
    next({ name: 'error.notFound' })
    return
  }

  const meta = to.meta as AppRouteMeta
  const { ensureSession } = useAuth()

  // 确保会话已初始化
  const loggedIn = await ensureSession()

  // 需要登录但未登录 → 跳转登录页，携带 redirect
  if (meta.requiresAuth && !loggedIn) {
    next({
      name: 'auth.login',
      query: { redirect: to.fullPath },
    })
    return
  }

  // 已登录访问登录/注册页 → 跳转 redirect 或默认页
  if (meta.allowWhenAuthenticated === false && loggedIn) {
    const redirect = to.query.redirect as string
    if (redirect && isValidRedirect(redirect)) {
      next(redirect)
    } else {
      next({ name: 'projects.index' })
    }
    return
  }

  next()
})

export default router
