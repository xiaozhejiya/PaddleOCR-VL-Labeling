/**
 * 文件资产相关 API
 * 后端：POST /projects/{project_id}/assets/upload
 */
import { api, ApiClientError, getAuthorizationHeader, parseApiErrorBody } from './client'

export interface Asset {
  id: string
  filename: string
  mime_type: string
  size: number
  hash: string
  created_at: string
}

/** 后端 AssetUploadData */
export interface AssetUploadData {
  asset_id: string
  document_id: string
  page_id: string
  sha256: string
  size_bytes: number
  mime_type: string
  width: number
  height: number
  asset_reused: boolean
}

/** 后端 AssetUploadResponse: { data, request_id } */
export interface AssetUploadResponse {
  data: AssetUploadData
  request_id: string
}

function createUploadNetworkError(): ApiClientError {
  return new ApiClientError({ message: 'errors.network', status: 0 })
}

function createUploadAbortError(): ApiClientError {
  return new ApiClientError({
    message: 'errors.network',
    status: 0,
    code: 'REQUEST_ABORTED',
  })
}

function createUploadUnknownError(status: number): ApiClientError {
  return new ApiClientError({ message: 'errors.unknown', status })
}

export const assetsApi = {
  /** 获取资产详情 */
  get: (assetId: string) =>
    api.get<Asset>(`/assets/${assetId}`),

  /** 获取资产下载 URL */
  getDownloadUrl: (assetId: string) =>
    api.get<{ url: string; expires_at: string }>(`/assets/${assetId}/download`),

  /** 上传资产到指定项目 */
  upload: (projectId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.upload<AssetUploadResponse>(
      `/projects/${projectId}/assets/upload`,
      formData,
    )
  },

  /** 上传资产（带进度回调），返回 promise 与 abort */
  uploadWithProgress: (
    projectId: string,
    file: File,
    onProgress: (percent: number) => void,
  ): { promise: Promise<AssetUploadResponse>; abort: () => void } => {
    const xhr = new XMLHttpRequest()
    xhr.timeout = 30000 // 30 秒超时
    const promise = new Promise<AssetUploadResponse>((resolve, reject) => {
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100))
        }
      }

      xhr.ontimeout = () => {
        reject(createUploadNetworkError())
      }

      xhr.onabort = () => {
        reject(createUploadAbortError())
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText) as AssetUploadResponse)
          } catch {
            reject(createUploadUnknownError(xhr.status))
          }
          return
        }

        try {
          const body = JSON.parse(xhr.responseText)
          reject(new ApiClientError(parseApiErrorBody(body, xhr.status)))
        } catch {
          reject(createUploadUnknownError(xhr.status))
        }
      }

      xhr.onerror = () => {
        reject(createUploadNetworkError())
      }

      const formData = new FormData()
      formData.append('file', file)

      xhr.open('POST', `/api/v1/projects/${projectId}/assets/upload`)
      xhr.withCredentials = true
      const authHeader = getAuthorizationHeader()
      if (authHeader) {
        xhr.setRequestHeader('Authorization', authHeader)
      }
      xhr.send(formData)
    })

    return {
      promise,
      abort: () => xhr.abort(),
    }
  },
}
