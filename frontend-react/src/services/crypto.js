import CryptoJS from 'crypto-js';

// Clave de encriptación (debería venir del backend o generarse por sesión)
const ENCRYPTION_KEY = process.env.REACT_APP_ENCRYPTION_KEY || 'secure-chat-encryption-key-2024';

/**
 * Encripta un mensaje usando AES256
 */
export const encryptMessage = (message) => {
  try {
    const encrypted = CryptoJS.AES.encrypt(message, ENCRYPTION_KEY).toString();
    return encrypted;
  } catch (error) {
    console.error('Error encrypting message:', error);
    return message;
  }
};

/**
 * Desencripta un mensaje usando AES256
 */
export const decryptMessage = (encryptedMessage) => {
  try {
    const bytes = CryptoJS.AES.decrypt(encryptedMessage, ENCRYPTION_KEY);
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
