/**
 * 文件工具函数
 */

/** 允许的图片类型 */
export const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/tiff']

/** 允许的文档类型 */
export const ALLOWED_DOCUMENT_TYPES = ['application/pdf']

/** 最大文件大小 (100MB) */
export const MAX_FILE_SIZE = 100 * 1024 * 1024

/**
 * 校验文件类型
 */
export function isAllowedFileType(file: File, allowedTypes: string[]): boolean {
  return allowedTypes.includes(file.type)
}

/**
 * 校验文件大小
 */
export function isAllowedFileSize(file: File, maxSize: number = MAX_FILE_SIZE): boolean {
  return file.size <= maxSize
}

/**
 * 获取文件扩展名
 */
export function getFileExtension(filename: string): string {
  const lastDot = filename.lastIndexOf('.')
  return lastDot === -1 ? '' : filename.slice(lastDot + 1).toLowerCase()
}

/**
 * 格式化文件大小（带单位）
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`
}
