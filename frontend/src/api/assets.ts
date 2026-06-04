/**
 * 文件资产相关 API
 */
import { api } from './client'

export interface Asset {
  id: string
  filename: string
  mime_type: string
  size: number
  hash: string
  created_at: string
}

export interface AssetUploadResponse {
  asset: Asset
  download_url: string
}

export const assetsApi = {
  /** 获取资产详情 */
  get: (assetId: string) =>
    api.get<Asset>(`/assets/${assetId}`),

  /** 获取资产下载 URL */
  getDownloadUrl: (assetId: string) =>
    api.get<{ url: string; expires_at: string }>(`/assets/${assetId}/download`),

  /** 上传资产 */
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<AssetUploadResponse>('/assets', formData)
  },
}
