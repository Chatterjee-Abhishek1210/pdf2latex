/**
 * ConversionProgress — Real-time conversion progress display
 * Shows step-by-step pipeline status with animated progress bar
 */
export default function ConversionProgress({ status, progress, message }) {
  const steps = [
    { id: 'upload', label: 'Upload', icon: '📤', desc: 'PDF received' },
    { id: 'parsing', label: 'Parsing', icon: '🔍', desc: 'Analyzing document structure' },
    { id: 'analyzing', label: 'Analyzing', icon: '🧠', desc: 'AI processing layout & content' },
    { id: 'generating', label: 'Generating', icon: '⚙️', desc: 'Creating LaTeX code' },
    { id: 'compiling', label: 'Compiling', icon: '📝', desc: 'Building output PDF' },
    { id: 'comparing', label: 'Comparing', icon: '🔬', desc: 'Measuring visual fidelity' },
    { id: 'complete', label: 'Complete', icon: '✅', desc: 'Ready to download' },
  ]

  const getStepState = (stepId) => {
    const statusOrder = ['upload', 'parsing', 'analyzing', 'generating', 'compiling', 'comparing', 'complete']
    const currentIdx = statusOrder.indexOf(status)
    const stepIdx = statusOrder.indexOf(stepId)

    if (status === 'complete') return 'complete'
    if (status === 'failed') return stepIdx <= currentIdx ? 'failed' : 'pending'
    if (stepIdx < currentIdx) return 'complete'
    if (stepIdx === currentIdx) return 'active'
    return 'pending'
  }

  return (
    <div className="glass-card animate-slide-up" style={{ padding: '2rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ 
          fontSize: '1.1rem', 
          fontWeight: 700, 
          marginBottom: '0.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          {status === 'complete' ? '✨' : status === 'failed' ? '❌' : '⚡'} 
          Conversion Progress
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: 0 }}>
          {message}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="progress-container" style={{ marginBottom: '2rem' }}>
        <div 
          className="progress-bar" 
          style={{ 
            width: `${progress}%`,
            background: status === 'failed' 
              ? 'linear-gradient(135deg, #e17055, #d63031)' 
              : 'var(--gradient-primary)',
          }} 
        />
      </div>

      {/* Progress percentage */}
      <div style={{ 
        textAlign: 'center', 
        marginBottom: '1.5rem',
        fontSize: '2rem',
        fontWeight: 800,
        background: 'var(--gradient-primary)',
        WebkitBackgroundClip: 'text',
        backgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
      }}>
        {Math.round(progress)}%
      </div>

      {/* Steps */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {steps.map((step) => {
          const stepState = getStepState(step.id)
          return (
            <div key={step.id} className={`status-step ${stepState}`}>
              <div className="step-icon">
                {stepState === 'complete' ? '✓' : step.icon}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ 
                  fontWeight: 600, 
                  fontSize: '0.9rem',
                  color: stepState === 'pending' ? 'var(--text-muted)' : 'var(--text-primary)',
                }}>
                  {step.label}
                </div>
                <div style={{ 
                  fontSize: '0.75rem', 
                  color: 'var(--text-muted)',
                }}>
                  {step.desc}
                </div>
              </div>
              {stepState === 'active' && (
                <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
