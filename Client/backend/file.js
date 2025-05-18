const {logger} = require('../logger.js')

require('dotenv').config();
const apiBaseUrl = process.env.API_BASE_URL;
const dataBaseUrl = process.env.DATA_BASE_URL;
const axios = require('axios');
const crypto = require('crypto');

async function handleUpload(event, {fileName, fileType, fileBuffer, sid}) {
    logger.info(`Upload Attempt File: ${fileName}`);

    // Step 1: Generate a random AES key and encrypt data with AES key 
    const file = Buffer.from(fileBuffer);
    const aesKey = crypto.randomBytes(32);
    const iv = Buffer.alloc(16, 0);  // TODO: Add IV in API
    const cipher = crypto.createCipheriv('aes-256-cbc', aesKey, iv);
    let encryptedData = cipher.update(file, 'utf8', 'hex');
    encryptedData += cipher.final('hex');

    // Step 2: Ask KMS Public Key and Encrypt AES key
    try{
        logger.info(`${apiBaseUrl}get_public_key`);
        const response = await axios.post(`${apiBaseUrl}get_public_key`, {file_name:fileName}, {
            headers: {'Content-Type': 'application/json', 'sid': sid}, 
        });
        if (response.status==200){
            logger.info("Successfully ask KMS Public Key");
            pubKey = response.data.kms_public_key;
            pubKey = Buffer.from(pubKey, 'base64').toString('utf-8');
            const encryptedKey = crypto.publicEncrypt(
                {
                    key: pubKey,
                    padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
                    oaepHash: "sha256",
                },
                aesKey
            );

            // Step 3: Send encrypted data and encrypted key to data server 
            try{
                logger.info(`${dataBaseUrl}upload`);
                const response = await axios.post(`${dataBaseUrl}upload`, {
                    file_name: fileName, 
                    encrypted_data:encryptedData, 
                    encrypted_aes_key: encryptedKey}, 
                    {
                        headers: {'Content-Type': 'application/json'}
                    });
                if (response.status==200){
                    logger.info(response.data.status);
                }
            }catch(err){
                return { success: false, error: err.response?.data?.status || err.message };
            }

            return{
                success: true,
                fileName: fileName
            }
            
        }
    }catch(err){
        return { success: false, error: err.message };
    }
}

module.exports = { handleUpload };