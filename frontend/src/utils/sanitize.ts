/**
 * 内容净化工具
 * 防止 XSS，净化不可信 HTML
 */
import DOMPurify from 'dompurify'

/**
 * 净化 HTML 内容
 * 用于渲染服务端返回的 markdown/HTML 预览
 */
export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre', 'blockquote', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
  })
}

/**
 * 转义 HTML 特殊字符
 * 用于用户输入的文本渲染
 */
export function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}
