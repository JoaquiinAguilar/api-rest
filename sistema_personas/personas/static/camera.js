/**
 * Funcionalidad para captura de fotos con la cámara
 */

class CameraCapture {
    constructor(options) {
        this.videoElement = options.videoElement;
        this.canvasElement = options.canvasElement;
        this.startButton = options.startButton;
        this.captureButton = options.captureButton;
        this.imagePreview = options.imagePreview;
        this.hiddenInput = options.hiddenInput;
        this.feedbackElement = options.feedbackElement;
        
        this.stream = null;
        this.initialized = false;
        
        this.init();
    }
    
    init() {
        // Verificar disponibilidad de la API
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this._showFeedback('Su navegador no soporta acceso a la cámara.', 'error');
            this.startButton.disabled = true;
            return;
        }
        
        // Configurar eventos
        this.startButton.addEventListener('click', () => this.startCamera());
        this.captureButton.addEventListener('click', () => this.captureImage());
        
        this.initialized = true;
    }
    
    startCamera() {
        // Configuración de la cámara (preferiblemente frontal para fotos de personas)
        const constraints = {
            video: {
                facingMode: 'user',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        };
        
        // Iniciar la cámara
        navigator.mediaDevices.getUserMedia(constraints)
            .then(stream => {
                this.stream = stream;
                this.videoElement.srcObject = stream;
                this.videoElement.play();
                
                // Mostrar video y botón de captura
                this.videoElement.style.display = 'block';
                this.captureButton.style.display = 'inline-block';
                this.startButton.disabled = true;
                
                this._showFeedback('Cámara iniciada. Capture su imagen cuando esté listo.', 'success');
            })
            .catch(error => {
                console.error("Error al acceder a la cámara: ", error);
                this._showFeedback(`Error al acceder a la cámara: ${error.message}`, 'error');
            });
    }
    
    captureImage() {
        if (!this.stream) {
            this._showFeedback('La cámara no está activa.', 'error');
            return;
        }
        
        // Obtener contexto del canvas
        const context = this.canvasElement.getContext('2d');
        
        // Ajustar tamaño del canvas al video
        this.canvasElement.width = this.videoElement.videoWidth;
        this.canvasElement.height = this.videoElement.videoHeight;
        
        // Dibujar frame actual del video en el canvas
        context.drawImage(this.videoElement, 0, 0, this.canvasElement.width, this.canvasElement.height);
        
        // Convertir a base64
        const imageData = this.canvasElement.toDataURL('image/png');
        
        // Guardar en input oculto para enviar con el formulario
        if (this.hiddenInput) {
            this.hiddenInput.value = imageData;
        }
        
        // Mostrar vista previa
        if (this.imagePreview) {
            this.imagePreview.src = imageData;
            this.imagePreview.style.display = 'block';
        }
        
        // Mostrar el canvas
        this.canvasElement.style.display = 'block';
        this.videoElement.style.display = 'none';
        
        // Detener la cámara
        this.stopCamera();
        
        this._showFeedback('Imagen capturada correctamente.', 'success');
    }
    
    stopCamera() {
        if (this.stream) {
            const tracks = this.stream.getTracks();
            tracks.forEach(track => track.stop());
            this.stream = null;
            
            // Restaurar estado de botones
            this.startButton.disabled = false;
            this.captureButton.style.display = 'none';
        }
    }
    
    _showFeedback(message, type) {
        if (this.feedbackElement) {
            this.feedbackElement.textContent = message;
            
            // Quitar clases anteriores
            this.feedbackElement.classList.remove('alert-success', 'alert-danger', 'alert-info');
            
            // Añadir clase según tipo
            switch (type) {
                case 'success':
                    this.feedbackElement.classList.add('alert-success');
                    break;
                case 'error':
                    this.feedbackElement.classList.add('alert-danger');
                    break;
                default:
                    this.feedbackElement.classList.add('alert-info');
            }
            
            this.feedbackElement.style.display = 'block';
        }
    }
}

// Exportar para uso en otros archivos
window.CameraCapture = CameraCapture;