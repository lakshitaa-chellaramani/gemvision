/**
 * Type definitions for GemVision
 */

export type JewelleryCategory = 'ring' | 'necklace' | 'earring' | 'bracelet'

export type StylePreset = 'bridal' | 'minimalist' | 'traditional' | 'antique' | 'heavy-stone'

export type RealismMode = 'realistic' | 'photoreal' | 'cad' | 'sketch'

export type FingerType = 'index' | 'middle' | 'ring' | 'little'

export type QCDecision = 'accept' | 'rework' | 'escalate'

export type DefectSeverity = 'low' | 'medium' | 'high'

export type ReworkStatus = 'pending' | 'in_progress' | 'completed' | 'verified'

export interface ImageData {
  url: string
  revised_prompt?: string
  seed: string
}

export interface Design {
  id: number
  generation_id: string
  category: JewelleryCategory
  style_preset: StylePreset
  prompt: string
  realism_mode: RealismMode
  images: string[]
  materials: string[]
  colors: string[]
  confidence: number
  is_favorite: boolean
  is_idea: boolean
  created_at: string
}

export interface GenerateDesignRequest {
  prompt: string
  category: JewelleryCategory
  style_preset: StylePreset
  realism_mode?: RealismMode
  num_images?: number
  user_id?: number
}

export interface GenerateDesignResponse {
  generation_id: string
  design_id: number
  prompt: string
  enhanced_prompt: string
  category: JewelleryCategory
  style_preset: StylePreset
  realism_mode: RealismMode
  images: ImageData[]
  materials: string[]
  colors: string[]
  confidence: number
  created_at: string
}

export interface TryOnTransform {
  x: number
  y: number
  scale: number
  rotation: number
  opacity: number
  hue: number
}

export interface AnchorPoints {
  knuckle?: { x: number; y: number }
  base?: { x: number; y: number }
}

export interface TryOn {
  id: number
  design_id?: number
  snapshot_url?: string
  finger_type: FingerType
  is_approved: boolean
  sent_for_approval: boolean
  created_at: string
}

export interface Defect {
  id: string
  type: string
  label: string
  bbox: {
    x: number
    y: number
    width: number
    height: number
  }
  confidence: number
  severity: DefectSeverity
  description: string
}

export interface InspectionResult {
  inspection_id: number
  status: 'passed' | 'failed' | 'review' | 'passed_with_notes'
  recommendation: string
  defects: Defect[]
  defect_count: number
  image_url: string
  thumbnail_url?: string
  detection_mode: 'simulated' | 'ml'
  file_type: 'cad' | 'image' | 'pdf'
  has_cad_file: boolean
  confidence_note: string
  confidence_threshold: number
  image_analysis: {
    brightness: number
    contrast: number
    lighting_quality: string
    has_glint: boolean
    resolution: [number, number]
    file_type?: string
  }
  requires_reshoot: boolean
  lighting_warning: string
  created_at: string
}

export interface ReworkJob {
  id: number
  defect_type: string
  defect_severity: DefectSeverity
  defect_description: string
  evidence_images: string[]
  assigned_to_station: string
  assigned_operator?: string
  priority: string
  status: ReworkStatus
  lifecycle_events: Array<{
    timestamp: string
    status: string
    action: string
    notes: string
  }>
  created_at: string
  assigned_at?: string
  completed_at?: string
  verified_at?: string
  verified_by?: string
}

// 3D Model Types
export type Model3DFormat = 'glb' | 'obj' | 'ply' | 'stl'

export interface Model3DStats {
  vertices: number
  faces: number
  is_watertight: boolean
  volume: number | null
  surface_area: number
}

export interface Model3DResult {
  success: boolean
  generation_id: string
  model_url: string
  thumbnail_url: string
  format: Model3DFormat
  mime_type: string
  file_size: number
  stats: Model3DStats
  background_removed: boolean
  created_at: string
  error?: string
}

export interface Generate3DRequest {
  file: File
  remove_background?: boolean
  export_format?: Model3DFormat
}
