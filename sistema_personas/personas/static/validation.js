/**
 * Funcionalidad para manejo de huellas digitales
 */

class FingerprintHandler {
    constructor(options) {
        this.captureButton = options.captureButton;
        this.previewElement = options.previewElement;
        this.statusElement = options.statusElement;
        this.inputElement = options.inputElement;
        this.noPreviewElement = options.noPreviewElement;
        
        this.apiEndpoint = options.apiEndpoint || '/api/capturar-huella/';
        this.isConnected = false;
        this.isCapturing = false;
        
        this.init();
    }
    
    init() {
        // Configurar evento para captura de huella
        if (this.captureButton) {
            this.captureButton.addEventListener('click', () => this.captureFingerprint());
        }
        
        // Intentar conectarse con el lector de huellas
        this.connectToReader();
    }
    
    connectToReader() {
        // En una implementación real, aquí se conectaría con el lector de huellas.
        // Para este ejemplo, simulamos la conexión.
        
        this._updateStatus('Buscando dispositivo lector de huellas...', 'info');
        
        // Simulación de búsqueda de dispositivo
        setTimeout(() => {
            // En un caso real, verificaríamos si realmente hay conexión
            const simulateConnection = Math.random() > 0.3; // 70% de probabilidad de encontrar un dispositivo
            
            if (simulateConnection) {
                this.isConnected = true;
                this._updateStatus('Lector de huellas conectado y listo para usar.', 'success');
            } else {
                this.isConnected = false;
                this._updateStatus('No se detectó un lector de huellas. Por favor verifique la conexión.', 'warning');
            }
        }, 1500);
    }
    
    captureFingerprint() {
        if (this.isCapturing) {
            return; // Evitar múltiples capturas simultáneas
        }
        
        if (!this.isConnected) {
            this._updateStatus('No hay un lector de huellas conectado.', 'error');
            this.connectToReader(); // Intentar conectar nuevamente
            return;
        }
        
        this.isCapturing = true;
        this._updateStatus('Capturando huella digital... Por favor, mantenga el dedo en el lector.', 'info');
        
        if (this.captureButton) {
            this.captureButton.disabled = true;
            this.captureButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Capturando...';
        }
        
        // En una implementación real, aquí se comunicaría con el lector de huellas.
        // Para este ejemplo, simulamos la captura después de un tiempo.
        setTimeout(() => {
            // Simulación de captura (éxito/fallo)
            const captureSuccess = Math.random() > 0.2; // 80% de probabilidad de éxito
            
            if (captureSuccess) {
                this._processCapture();
            } else {
                this._captureError('No se pudo capturar la huella digital. Por favor, inténtelo nuevamente.');
            }
        }, 2000);
    }
    
    _processCapture() {
        // En un caso real, aquí procesaríamos la imagen capturada por el lector
        // Para este ejemplo, obtenemos una imagen de ejemplo
        
        // Simulación de obtención de imagen desde el servidor
        fetch('/static/img/fingerprint-example.png')
            .then(response => {
                if (!response.ok) {
                    throw new Error('No se pudo cargar la imagen de ejemplo');
                }
                return response.blob();
            })
            .then(blob => {
                // Crear un objeto File a partir del Blob
                const file = new File([blob], "huella_capturada.png", { type: "image/png" });
                
                if (this.inputElement) {
                    // Crear un DataTransfer para asignar el archivo al input
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    this.inputElement.files = dataTransfer.files;
                    
                    // Disparar evento change para que otras funciones se enteren
                    const event = new Event('change', { bubbles: true });
                    this.inputElement.dispatchEvent(event);
                }
                
                // Mostrar vista previa
                if (this.previewElement) {
                    const reader = new FileReader();
                    reader.onload = e => {
                        this.previewElement.src = e.target.result;
                        this.previewElement.style.display = 'block';
                        if (this.noPreviewElement) {
                            this.noPreviewElement.style.display = 'none';
                        }
                    };
                    reader.readAsDataURL(file);
                }
                
                this._updateStatus('Huella digital capturada correctamente.', 'success');
                this._resetCaptureButton();
            })
            .catch(error => {
                this._captureError(`Error al procesar la huella: ${error.message}`);
            });
    }
    
    _captureError(message) {
        this._updateStatus(message, 'error');
        this._resetCaptureButton();
    }
    
    _resetCaptureButton() {
        if (this.captureButton) {
            this.captureButton.disabled = false;
            this.captureButton.innerHTML = '<i class="fas fa-fingerprint me-2"></i>Capturar Huella con Lector';
        }
        this.isCapturing = false;
    }
    
    _updateStatus(message, type) {
        if (!this.statusElement) return;
        
        this.statusElement.textContent = message;
        this.statusElement.classList.remove('d-none', 'alert-success', 'alert-danger', 'alert-warning', 'alert-info');
        this.statusElement.classList.add('alert-' + (type === 'error' ? 'danger' : type));
        this.statusElement.classList.remove('d-none');
    }
    
    // Procesamiento de huella para obtener hash y QR
    processFingerprint(fingerprintImage) {
        // En una implementación real, esto sería una llamada a la API
        return new Promise((resolve, reject) => {
            // Crear un FormData para enviar la imagen
            const formData = new FormData();
            formData.append('imagen', fingerprintImage);
            
            // Enviar al endpoint de procesamiento
            fetch(this.apiEndpoint, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    reject(new Error(data.error));
                } else {
                    resolve({
                        huella_hex: data.huella_hex,
                        qr_code: data.qr_code
                    });
                }
            })
            .catch(error => {
                reject(error);
            });
        });
    }
    
    // Búsqueda por huella
    searchByFingerprint(fingerprintImage) {
        // En una implementación real, esto sería una llamada a la API
        return new Promise((resolve, reject) => {
            // Crear un FormData para enviar la imagen
            const formData = new FormData();
            formData.append('huella', fingerprintImage);
            
            // Enviar al endpoint de búsqueda
            fetch('/api/personas/buscar_por_huella/', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                return response.json();
            })
            .then(data => {
                if (data.message && !data.id) {
                    // No se encontró coincidencia
                    resolve(null);
                } else {
                    // Se encontró una persona
                    resolve(data);
                }
            })
            .catch(error => {
                reject(error);
            });
        });
    }
}

// Exportar para uso en otros archivos
window.FingerprintHandler = FingerprintHandler;