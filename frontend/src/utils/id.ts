/**
 * ID 生成工具
 */

/** 生成简单唯一 ID */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}
