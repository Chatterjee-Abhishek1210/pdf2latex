import { useState, useCallback, useRef } from 'react'

/**
 * Custom hook for managing the PDF-to-LaTeX conversion workflow.
 * Handles upload, conversion, progress tracking, and result fetching.
 */
export function useConversion() {
  const [state, setState] = useState({
    // Upload state
    file: null,
    fileName: '',
    fileSize: 0,
    
    // Job state
    jobId: null,
    status: 'idle', // idle, uploading, processing, complete, failed
    progress: 0,
    message: '',
    
    // Result state
    latexCode: '',
    ssimScore: null,
    
    // Error
    error: null,
  })

  const wsRef = useRef(null)

  const updateState = (updates) => {
    setState(prev => ({ ...prev, ...updates }))
  }

  /**
   * Upload a PDF file to the server
   */
  const uploadFile = useCallback(async (file) => {
    updateState({
      file,
      fileName: file.name,
      fileSize: file.size,
      status: 'uploading',
      progress: 0,
      message: 'Uploading PDF...',
      error: null,
      latexCode: '',
      ssimScore: null,
    })

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Upload failed')
      }

      const data = await response.json()
      
      updateState({
        jobId: data.job_id,
        status: 'uploaded',
        progress: 10,
        message: 'PDF uploaded successfully',
      })

      return data.job_id
    } catch (error) {
      updateState({
        status: 'failed',
        error: error.message,
        message: `Upload failed: ${error.message}`,
      })
      return null
    }
  }, [])

  /**
   * Start the conversion process
   */
  const startConversion = useCallback(async (jobId) => {
    const id = jobId || state.jobId
    if (!id) return

    updateState({
      status: 'processing',
      progress: 15,
      message: 'Starting conversion...',
    })

    try {
      // Start conversion via API
      const response = await fetch(`/api/convert/${id}`, {
        method: 'POST',
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Conversion failed to start')
      }

      // Connect WebSocket for progress updates
      connectWebSocket(id)

    } catch (error) {
      updateState({
        status: 'failed',
        error: error.message,
        message: `Conversion failed: ${error.message}`,
      })
    }
  }, [state.jobId])

  /**
   * Connect WebSocket for real-time progress updates
   */
  const connectWebSocket = useCallback((jobId) => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${wsProtocol}//localhost:8000/api/ws/${jobId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      updateState({
        status: data.status,
        progress: data.progress,
        message: data.message,
        ssimScore: data.ssim_score || state.ssimScore,
      })

      if (data.status === 'complete' || data.status === 'failed') {
        ws.close()
        if (data.status === 'complete') {
          fetchResult(jobId)
        }
      }
    }

    ws.onerror = () => {
      // Fallback to polling
      pollStatus(jobId)
    }

    ws.onclose = () => {
      wsRef.current = null
    }
  }, [])

  /**
   * Fallback: poll for status updates
   */
  const pollStatus = useCallback(async (jobId) => {
    const poll = async () => {
      try {
        const response = await fetch(`/api/status/${jobId}`)
        const data = await response.json()
        
        updateState({
          status: data.status,
          progress: data.progress,
          message: data.message,
          ssimScore: data.ssim_score,
        })

        if (data.status !== 'complete' && data.status !== 'failed') {
          setTimeout(poll, 1000)
        } else if (data.status === 'complete') {
          fetchResult(jobId)
        }
      } catch (error) {
        setTimeout(poll, 2000)
      }
    }

    poll()
  }, [])

  /**
   * Fetch the conversion result (LaTeX code)
   */
  const fetchResult = useCallback(async (jobId) => {
    try {
      const response = await fetch(`/api/result/${jobId}`)
      const data = await response.json()

      updateState({
        latexCode: data.latex_code || '',
        ssimScore: data.ssim_score,
        status: 'complete',
        progress: 100,
        message: 'Conversion complete!',
      })
    } catch (error) {
      console.error('Failed to fetch result:', error)
    }
  }, [])

  /**
   * Upload and convert in one step
   */
  const uploadAndConvert = useCallback(async (file) => {
    const jobId = await uploadFile(file)
    if (jobId) {
      await startConversion(jobId)
    }
  }, [uploadFile, startConversion])

  /**
   * Reset the state
   */
  const reset = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    setState({
      file: null,
      fileName: '',
      fileSize: 0,
      jobId: null,
      status: 'idle',
      progress: 0,
      message: '',
      latexCode: '',
      ssimScore: null,
      error: null,
    })
  }, [])

  return {
    ...state,
    uploadFile,
    startConversion,
    uploadAndConvert,
    fetchResult,
    reset,
  }
}
