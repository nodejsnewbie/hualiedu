const loadedScripts = new Map()

export const loadExternalScript = (src) => {
  if (loadedScripts.has(src)) {
    return loadedScripts.get(src)
  }

  const promise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = src
    script.async = true
    script.onload = () => resolve(script)
    script.onerror = () => reject(new Error(`Failed to load script: ${src}`))
    document.body.appendChild(script)
  })

  loadedScripts.set(src, promise)
  return promise
}
