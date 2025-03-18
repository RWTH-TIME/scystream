type Listener<T> = (data: T) => void
type ErrorHandler = () => void

class WebSocketConnection<T> {
  private websocket: WebSocket | null = null
  private listeners: Listener<T>[] = []
  private errorHandler: ErrorHandler = () => { }
  private reconnectTimeout: NodeJS.Timeout | null = null
  private url: string

  constructor(url: string) {
    this.url = url
    this.connect()
  }

  private connect() {
    if (this.websocket) return

    this.websocket = new WebSocket(this.url)

    this.websocket.onopen = () => console.log(`WebSocket connected: ${this.url}`)

    this.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.listeners.forEach((listener) => listener(data))
    }

    this.websocket.onerror = (error) => {
      this.errorHandler()
      console.error(`WebSocket error:`, error)
    }

    this.websocket.onclose = () => {
      this.websocket = null
    }
  }

  addErrorHandler(callback: ErrorHandler) {
    this.errorHandler = callback
  }

  addListener(callback: Listener<T>) {
    this.listeners.push(callback)
  }

  removeListener(callback: Listener<T>) {
    this.listeners = this.listeners.filter((listener) => listener !== callback)
  }

  close() {
    if (this.websocket) {
      this.websocket.close()
      this.websocket = null
    }
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }
    this.listeners = []
  }
}

class WebSocketManager {
  private connections: Map<string, WebSocketConnection<unknown>> = new Map()

  getConnection<T>(url: string): WebSocketConnection<T> {
    if (!this.connections.has(url)) {
      const connection = new WebSocketConnection<T>(url)
      this.connections.set(url, connection as WebSocketConnection<unknown>)
    }
    return this.connections.get(url)! as WebSocketConnection<T>
  }

  removeConnection(url: string) {
    const connection = this.connections.get(url)
    if (connection) {
      connection.close()
      this.connections.delete(url)
    }
  }
}

export const webSocketManager = new WebSocketManager()
