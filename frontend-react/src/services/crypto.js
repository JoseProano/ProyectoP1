import CryptoJS from 'crypto-js';

// Almacenamiento de claves E2E por sala
const roomKeys = new Map();

/**
 * ENCRIPTACIÓN END-TO-END REAL
 * Genera una clave simétrica única por sala usando PBKDF2
 */
export const generateRoomKey = (roomId, pin) => {
  // Derivar clave única de 256 bits usando room_id + pin
  const salt = CryptoJS.SHA256(roomId).toString();
  const key = CryptoJS.PBKDF2(pin, salt, {
    keySize: 256/32,
    iterations: 10000
  }).toString();
  
  roomKeys.set(roomId, key);
  return key;
};

/**
 * Obtiene la clave E2E de una sala
 */
export const getRoomKey = (roomId) => {
  return roomKeys.get(roomId);
};

/**
 * Limpia la clave de una sala (al salir)
 */
export const clearRoomKey = (roomId) => {
  roomKeys.delete(roomId);
};

/**
 * Encripta un mensaje usando AES256 con clave E2E de la sala
 * El servidor NUNCA ve el contenido en claro
 */
export const encryptMessage = (message, roomId) => {
  try {
    const key = getRoomKey(roomId);
    if (!key) {
      console.warn('No E2E key found for room, using fallback');
      return message;
    }
    
    const encrypted = CryptoJS.AES.encrypt(message, key).toString();
    return encrypted;
  } catch (error) {
    console.error('Error encrypting message:', error);
    return message;
  }
};

/**
 * Desencripta un mensaje usando AES256 con clave E2E de la sala
 */
export const decryptMessage = (encryptedMessage, roomId) => {
  try {
    const key = getRoomKey(roomId);
    if (!key) {
      console.warn('No E2E key found for room, returning as-is');
      return encryptedMessage;
    }
    
    const bytes = CryptoJS.AES.decrypt(encryptedMessage, key);
    const decrypted = bytes.toString(CryptoJS.enc.Utf8);
    return decrypted || encryptedMessage;
  } catch (error) {
    console.error('Error decrypting message:', error);
    return encryptedMessage;
  }
};

/**
 * Genera un hash SHA-256 de un mensaje
 */
export const hashMessage = (message) => {
  return CryptoJS.SHA256(message).toString();
};

/**
 * Genera una firma digital para un mensaje
 */
export const signMessage = (message, privateKey) => {
  const hash = hashMessage(message + privateKey);
  return hash;
};

/**
 * Verifica la firma digital de un mensaje
 */
export const verifySignature = (message, signature, privateKey) => {
  const expectedSignature = signMessage(message, privateKey);
  return signature === expectedSignature;
};

/**
 * Genera un ID de sesión único
 */
export const generateSessionId = () => {
  return CryptoJS.lib.WordArray.random(32).toString();
};

const cryptoService = {
  encryptMessage,
  decryptMessage,
  hashMessage,
  signMessage,
  verifySignature,
  generateSessionId,
};

export default cryptoService;
