/**
 * API Client for GemVision Backend
 */
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Types
export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  phone?: string
  is_verified: boolean
  created_at: string
}

export interface TrialStatusResponse {
  trial_status: {
    ai_designer: {
      limit: number
      remaining: number
      unlimited: boolean
    }
    virtual_tryon: {
      limit: number
      remaining: number
      unlimited: boolean
    }
    qc_inspector: {
      limit: number
      remaining: number
      unlimited: boolean
    }
    '3d_generation': {
      limit: number
      remaining: number
      unlimited: boolean
    }
  }
}

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await api.post('/api/auth/login', {
      email,
      password,
    })
    return response.data
  },

  signup: async (data: {
    email: string
    username: string
    password: string
    full_name?: string
    phone?: string
  }) => {
    const response = await api.post('/api/auth/signup', data)
    return response.data
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me')
    return response.data
  },

  getTrialStatus: async () => {
    const response = await api.get('/api/auth/trial-status')
    return response.data
  },
}

// Waitlist API
export const waitlistAPI = {
  join: async () => {
    const response = await api.post('/api/waitlist/join')
    return response.data
  },

  getStatus: async () => {
    const response = await api.get('/api/waitlist/status')
    return response.data
  },
}

// Designer API
export const designerAPI = {
  generate: async (data: {
    prompt: string
    category: string
    style_preset: string
    realism_mode?: string
    num_images?: number
  }) => {
    const response = await api.post('/api/designer/generate', data)
    return response.data
  },

  getTemplates: async (category: string, style_preset: string) => {
    const response = await api.post('/api/designer/templates', {
      category,
      style_preset,
    })
    return response.data
  },

  getDesign: async (designId: number) => {
    const response = await api.get(`/api/designer/designs/${designId}`)
    return response.data
  },

  listDesigns: async (params?: {
    user_id?: number
    category?: string
    style_preset?: string
    is_idea?: boolean
    limit?: number
    offset?: number
  }) => {
    const response = await api.get('/api/designer/designs', { params })
    return response.data
  },

  saveAsIdea: async (designId: number, is_favorite?: boolean) => {
    const response = await api.post('/api/designer/save-idea', {
      design_id: designId,
      is_favorite,
    })
    return response.data
  },

  deleteDesign: async (designId: number) => {
    const response = await api.delete(`/api/designer/designs/${designId}`)
    return response.data
  },

  generate3D: async (
    input: File | string,
    removeBackground: boolean = true,
    exportFormat: string = 'glb'
  ) => {
    const formData = new FormData()

    if (typeof input === 'string') {
      // If input is a URL string
      formData.append('image_url', input)
    } else {
      // If input is a File object
      formData.append('file', input)
    }

    formData.append('remove_background', removeBackground.toString())
    formData.append('export_format', exportFormat)

    const response = await api.post('/api/designer/generate-3d', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  get3DFormats: async () => {
    const response = await api.get('/api/designer/3d-formats')
    return response.data
  },
}

// Try-On API
export const tryonAPI = {
  uploadHandPhoto: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/api/tryon/upload-hand-photo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  saveTryOn: async (data: {
    user_id?: number
    design_id?: number
    hand_photo_url: string
    overlay_image_url: string
    transform: {
      x: number
      y: number
      scale: number
      rotation: number
      opacity: number
      hue: number
    }
    finger_type: string
    anchor_points?: any
  }) => {
    const response = await api.post('/api/tryon/save', data)
    return response.data
  },

  saveSnapshot: async (tryonId: number, snapshotFile: File) => {
    const formData = new FormData()
    formData.append('tryon_id', tryonId.toString())
    formData.append('snapshot_file', snapshotFile)

    const response = await api.post('/api/tryon/save-snapshot', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  sendForApproval: async (tryonId: number, recipientEmail?: string) => {
    const response = await api.post(
      `/api/tryon/send-for-approval?tryon_id=${tryonId}`,
      recipientEmail ? { recipient_email: recipientEmail } : {}
    )
    return response.data
  },

  viewTryOn: async (tryonId: number) => {
    const response = await api.get(`/api/tryon/view/${tryonId}`)
    return response.data
  },

  listTryOns: async (params?: {
    user_id?: number
    design_id?: number
    limit?: number
    offset?: number
  }) => {
    const response = await api.get('/api/tryon/list', { params })
    return response.data
  },

  deleteTryOn: async (tryonId: number) => {
    const response = await api.delete(`/api/tryon/${tryonId}`)
    return response.data
  },

  generateAITryOn: async (data: {
    bodyPhoto: File
    jewelryPhoto: File
    jewelryType: string
    jewelryDescription: string
    targetArea?: string
    useExamples?: boolean
    autoDetect?: boolean
    designId?: number
  }) => {
    const formData = new FormData()
    formData.append('body_photo', data.bodyPhoto)
    formData.append('jewelry_photo', data.jewelryPhoto)
    formData.append('jewelry_type', data.jewelryType)
    formData.append('jewelry_description', data.jewelryDescription)
    if (data.targetArea) {
      formData.append('target_area', data.targetArea)
    }
    if (data.useExamples !== undefined) {
      formData.append('use_examples', data.useExamples.toString())
    }
    if (data.autoDetect !== undefined) {
      formData.append('auto_detect', data.autoDetect.toString())
    }
    if (data.designId) {
      formData.append('design_id', data.designId.toString())
    }

    const response = await api.post('/api/tryon/generate-ai-tryon', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

// QC Inspector API
export const qcAPI = {
  inspect: async (
    file: File,
    userId?: number,
    itemReference?: string,
    hasCADFile?: boolean,
    forceSimulated?: boolean
  ) => {
    const formData = new FormData()
    formData.append('file', file)
    if (userId) formData.append('user_id', userId.toString())
    if (itemReference) formData.append('item_reference', itemReference)
    if (hasCADFile !== undefined)
      formData.append('has_cad_file', hasCADFile.toString())
    if (forceSimulated !== undefined)
      formData.append('force_simulated', forceSimulated.toString())

    const response = await api.post('/api/qc/inspect', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  triage: async (data: {
    inspection_id: number
    decision: 'accept' | 'rework' | 'escalate'
    operator_notes?: string
    is_false_positive?: boolean
    selected_defects?: string[]
  }) => {
    const response = await api.post('/api/qc/triage', data)
    return response.data
  },

  createRework: async (data: {
    inspection_id: number
    selected_defects: string[]
    operator_notes?: string
    priority?: string
    assigned_station?: string
  }) => {
    const response = await api.post('/api/qc/rework', data)
    return response.data
  },

  updateRework: async (
    reworkJobId: number,
    data: {
      status: string
      operator?: string
      notes?: string
    }
  ) => {
    const response = await api.patch(`/api/qc/rework/${reworkJobId}`, data)
    return response.data
  },

  getInspection: async (inspectionId: number) => {
    const response = await api.get(`/api/qc/inspections/${inspectionId}`)
    return response.data
  },

  listInspections: async (params?: {
    user_id?: number
    decision?: string
    limit?: number
    offset?: number
  }) => {
    const response = await api.get('/api/qc/inspections', { params })
    return response.data
  },

  getReworkJob: async (reworkJobId: number) => {
    const response = await api.get(`/api/qc/rework/${reworkJobId}`)
    return response.data
  },

  listReworkJobs: async (params?: {
    status?: string
    priority?: string
    limit?: number
    offset?: number
  }) => {
    const response = await api.get('/api/qc/rework', { params })
    return response.data
  },
}

// Analytics API
export const analyticsAPI = {
  logEvent: async (data: {
    event_type: string
    event_action: string
    event_data?: any
    session_id?: string
    user_id?: number
  }) => {
    const response = await api.post('/api/analytics/log', data)
    return response.data
  },

  getDashboard: async (days?: number, userId?: number) => {
    const response = await api.get('/api/analytics/dashboard', {
      params: { days, user_id: userId },
    })
    return response.data
  },

  getTrends: async (days?: number, userId?: number) => {
    const response = await api.get('/api/analytics/trends', {
      params: { days, user_id: userId },
    })
    return response.data
  },

  getKPIs: async (days?: number, userId?: number) => {
    const response = await api.get('/api/analytics/kpis', {
      params: { days, user_id: userId },
    })
    return response.data
  },
}

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health')
  return response.data
}
