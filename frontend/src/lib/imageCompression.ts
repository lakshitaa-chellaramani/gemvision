/**
 * Image Compression Utility
 * Compresses images before upload to reduce file size
 */

export interface CompressionOptions {
  maxSizeMB?: number
  maxWidthOrHeight?: number
  quality?: number
  fileType?: string
}

/**
 * Compress an image file
 * @param file - The image file to compress
 * @param options - Compression options
 * @returns Compressed file
 */
export async function compressImage(
  file: File,
  options: CompressionOptions = {}
): Promise<File> {
  const {
    maxSizeMB = 0.5, // 500KB default
    maxWidthOrHeight = 1920,
    quality = 0.85,
    fileType = 'image/jpeg',
  } = options

  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = (e) => {
      const img = new Image()

      img.onload = () => {
        const canvas = document.createElement('canvas')
        let { width, height } = img

        // Calculate new dimensions while maintaining aspect ratio
        if (width > maxWidthOrHeight || height > maxWidthOrHeight) {
          if (width > height) {
            height = (height / width) * maxWidthOrHeight
            width = maxWidthOrHeight
          } else {
            width = (width / height) * maxWidthOrHeight
            height = maxWidthOrHeight
          }
        }

        canvas.width = width
        canvas.height = height

        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('Could not get canvas context'))
          return
        }

        // Draw image on canvas with new dimensions
        ctx.drawImage(img, 0, 0, width, height)

        // Convert canvas to blob with compression
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error('Could not compress image'))
              return
            }

            // Check if we need to compress more
            const targetSize = maxSizeMB * 1024 * 1024
            if (blob.size > targetSize && quality > 0.1) {
              // Recursively compress with lower quality
              const newQuality = quality * 0.8
              const newFile = new File([blob], file.name, { type: fileType })
              compressImage(newFile, {
                ...options,
                quality: newQuality,
              }).then(resolve).catch(reject)
              return
            }

            // Create new file from blob
            const compressedFile = new File([blob], file.name, {
              type: fileType,
              lastModified: Date.now(),
            })

            console.log(`📦 Image compressed: ${(file.size / 1024).toFixed(2)} KB → ${(compressedFile.size / 1024).toFixed(2)} KB`)
            resolve(compressedFile)
          },
          fileType,
          quality
        )
      }

      img.onerror = () => {
        reject(new Error('Could not load image'))
      }

      img.src = e.target?.result as string
    }

    reader.onerror = () => {
      reject(new Error('Could not read file'))
    }

    reader.readAsDataURL(file)
  })
}

/**
 * Compress multiple images
 * @param files - Array of image files
 * @param options - Compression options
 * @returns Array of compressed files
 */
export async function compressImages(
  files: File[],
  options: CompressionOptions = {}
): Promise<File[]> {
  return Promise.all(files.map((file) => compressImage(file, options)))
}

/**
 * Get image dimensions
 * @param file - Image file
 * @returns Width and height
 */
export async function getImageDimensions(
  file: File
): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = (e) => {
      const img = new Image()

      img.onload = () => {
        resolve({ width: img.width, height: img.height })
      }

      img.onerror = () => {
        reject(new Error('Could not load image'))
      }

      img.src = e.target?.result as string
    }

    reader.onerror = () => {
      reject(new Error('Could not read file'))
    }

    reader.readAsDataURL(file)
  })
}
