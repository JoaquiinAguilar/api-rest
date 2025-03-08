/**
 * Sistema de Gestión de Personas - Captura de Huellas Digitales
 * 
 * Este módulo utiliza el SDK de Fingerprint para capturar y procesar huellas digitales
 * durante el proceso de registro de personas.
 */

// Variables globales
let fingerprintReader = null;
let myReaderVal = "";
let acquisitionStarted = false;
let currentFormat = Fingerprint.SampleFormat.PngImage;

/**
 * Inicializa la captura de huellas
 */
function initFingerprintCapture() {
    // Crear instancia del SDK
    fingerprintReader = new FingerprintCapture();
    
    // Populate readers dropdown
    populateReadersDropDown();
    
    // Asignar eventos a los botones
    document.getElementById('btnStartCapture').addEventListener('click', startCapture);
    document.getElementById('btnStopCapture').addEventListener('click', stopCapture);
    document.getElementById('btnRefreshReaders').addEventListener('click', populateReadersDropDown);
    document.getElementById('readersDropDown').addEventListener('change', onReaderSelected);
}

/**
 * Clase principal de captura de huellas
 */
class FingerprintCapture {
    constructor() {
        const _instance = this;
        this.acquisitionStarted = false;
        this.sdk = new Fingerprint.WebApi;
        
        // Configurar eventos del SDK
        this.sdk.onDeviceConnected = function(e) {
            showStatus("Dispositivo conectado. Coloque su dedo en el lector.");
            showCaptureStatus("Lector listo. Coloque su dedo en el lector.", "info");
        };
        
        this.sdk.onDeviceDisconnected = function(e) {
            showStatus("Dispositivo desconectado.");
            showCaptureStatus("El lector ha sido desconectado. Por favor, reconecte el dispositivo.", "warning");
            _instance.acquisitionStarted = false;
            updateButtonState();
        };
        
        this.sdk.onCommunicationFailed = function(e) {
            showStatus("Error de comunicación con el SDK.");
            showCaptureStatus("Ha ocurrido un error de comunicación con el lector. Intente nuevamente.", "danger");
            _instance.acquisitionStarted = false;
            updateButtonState();
        };
        
        this.sdk.onSamplesAcquired = function(s) {
            processFingerprintSample(s);
        };
        
        this.sdk.onQualityReported = function(e) {
            document.getElementById("qualityInputBox").value = Fingerprint.QualityCode[(e.quality)];
            
            // Si la calidad es buena, habilitar el botón de finalizar
            if (e.quality === Fingerprint.QualityCode.Good) {
                document.getElementById("btnFinalizar").disabled = false;
            }
        };
    }

    // Iniciar captura de huella
    startAcquisition() {
        if (this.acquisitionStarted) return;
        
        const _instance = this;
        showStatus("");
        
        this.sdk.startAcquisition(currentFormat, myReaderVal).then(function() {
            _instance.acquisitionStarted = true;
            acquisitionStarted = true;
            updateButtonState();
            showCaptureStatus("Captura iniciada. Coloque su dedo en el lector.", "info");
        }, function(error) {
            showStatus(error.message);
            showCaptureStatus("Error al iniciar la captura: " + error.message, "danger");
        });
    }

    // Detener captura de huella
    stopAcquisition() {
        if (!this.acquisitionStarted) return;
        
        const _instance = this;
        showStatus("");
        
        this.sdk.stopAcquisition().then(function() {
            _instance.acquisitionStarted = false;
            acquisitionStarted = false;
            updateButtonState();
            showCaptureStatus("Captura detenida.", "warning");
        }, function(error) {
            showStatus(error.message);
            showCaptureStatus("Error al detener la captura: " + error.message, "danger");
        });
    }

    // Enumerar dispositivos disponibles
    enumerateDevices() {
        return this.sdk.enumerateDevices();
    }

    // Obtener información del dispositivo
    getDeviceInfo(uid) {
        return this.sdk.getDeviceInfo(uid);
    }
}

/**
 * Procesa las muestras de huellas digitales adquiridas
 */
function processFingerprintSample(sample) {
    try {
        if (currentFormat === Fingerprint.SampleFormat.PngImage) {
            // Procesando imagen PNG
            const samples = JSON.parse(sample.samples);
            const imageSrc = "data:image/png;base64," + Fingerprint.b64UrlTo64(samples[0]);
            
            // Mostrar la imagen
            const preview = document.getElementById('preview');
            preview.src = imageSrc;
            preview.style.display = 'block';
            document.getElementById('noPreview').style.display = 'none';
            
            // Guardar la imagen en el formulario para enviar
            document.getElementById('huella').value = Fingerprint.b64UrlTo64(samples[0]);
            
            // Calcular el hash SHA-256 de la imagen
            const imgData = Fingerprint.b64UrlTo64(samples[0]);
            calculateSHA256(imgData).then(hash => {
                document.getElementById('huella_hex').value = hash;
                showCaptureStatus("Huella capturada correctamente", "success");
                document.getElementById("btnFinalizar").disabled = false;
            });
        }
    } catch (error) {
        console.error("Error al procesar la muestra de huella:", error);
        showCaptureStatus("Error al procesar la huella digital: " + error.message, "danger");
    }
}

/**
 * Calcula el hash SHA-256 de los datos de la imagen
 */
async function calculateSHA256(base64Data) {
    try {
        // Convertir base64 a array de bytes
        const binaryString = window.atob(base64Data);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Usar Crypto API para calcular hash
        const hashBuffer = await crypto.subtle.digest('SHA-256', bytes);
        
        // Convertir buffer a cadena hexadecimal
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        
        return hashHex;
    } catch (error) {
        console.error("Error al calcular hash SHA-256:", error);
        return null;
    }
}

/**
 * Actualiza el estado de los botones de acuerdo al estado de la captura
 */
function updateButtonState() {
    const startButton = document.getElementById('btnStartCapture');
    const stopButton = document.getElementById('btnStopCapture');
    
    if (acquisitionStarted) {
        startButton.disabled = true;
        stopButton.disabled = false;
    } else {
        startButton.disabled = !myReaderVal;
        stopButton.disabled = true;
    }
}

/**
 * Inicia la captura de huella
 */
function startCapture() {
    if (!myReaderVal) {
        showCaptureStatus("Por favor, seleccione un lector de huellas primero.", "warning");
        return;
    }
    
    fingerprintReader.startAcquisition();
}

/**
 * Detiene la captura de huella
 */
function stopCapture() {
    fingerprintReader.stopAcquisition();
}

/**
 * Popula el dropdown con los lectores disponibles
 */
function populateReadersDropDown() {
    myReaderVal = "";
    const allReaders = fingerprintReader.enumerateDevices();
    
    allReaders.then(function(readers) {
        const dropdown = document.getElementById("readersDropDown");
        dropdown.innerHTML = "";
        
        // Primer elemento (por defecto)
        const defaultOption = document.createElement("option");
        defaultOption.selected = "selected";
        defaultOption.value = "";
        defaultOption.text = "Seleccione un lector";
        dropdown.add(defaultOption);
        
        // Añadir lectores encontrados
        for (let i = 0; i < readers.length; i++) {
            const option = document.createElement("option");
            option.value = readers[i];
            option.text = 'Digital Persona (' + readers[i] + ')';
            dropdown.add(option);
        }
        
        // Si no hay lectores, mostrar mensaje de alerta
        if (readers.length === 0) {
            showCaptureStatus("No se ha detectado ningún lector de huellas. Por favor, conecte un dispositivo.", "warning");
        } else if (readers.length === 1) {
            // Si solo hay un lector, seleccionarlo automáticamente
            dropdown.selectedIndex = 1;
            onReaderSelected();
        }
        
        updateButtonState();
        
    }, function(error) {
        showStatus(error.message);
        showCaptureStatus("Error al buscar lectores de huellas: " + error.message, "danger");
    });
}

/**
 * Manejador del cambio de selección del lector
 */
function onReaderSelected() {
    const dropdown = document.getElementById("readersDropDown");
    myReaderVal = dropdown.options[dropdown.selectedIndex].value;
    updateButtonState();
    
    // Si se seleccionó un lector, mostrar mensaje informativo
    if (myReaderVal) {
        showCaptureStatus("Lector seleccionado. Presione 'Iniciar Captura' para comenzar.", "info");
    }
}

/**
 * Muestra un mensaje de estado
 */
function showStatus(message) {
    const status = document.getElementById('status');
    if (status) {
        if (message) {
            status.innerHTML = message;
            status.classList.remove('d-none');
        } else {
            status.classList.add('d-none');
        }
    }
}

/**
 * Muestra un mensaje en el contenedor de estado de captura
 */
function showCaptureStatus(message, type) {
    const captureStatus = document.getElementById('captureStatus');
    if (captureStatus) {
        captureStatus.innerHTML = message;
        captureStatus.className = 'alert alert-' + type;
        captureStatus.classList.remove('d-none');
    }
}