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
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-cbc', aesKey, iv);
    let encryptedData = cipher.update(file, 'utf8', 'hex');
    encryptedData += cipher.final('hex');

    // Step 2: Ask KMS Public Key and Encrypt AES key
    try{
        logger.info(`${apiBaseUrl}get_public_key`);
        const response = await axios.post(`${apiBaseUrl}get_public_key`, {file_name:fileName}, {
            headers: {'Content-Type': 'application/json', 'sid': sid}, 
        });
        if (response.data.code==200){
            logger.info("Successfully ask KMS Public Key");
            let pubKey = response.data.kms_public_key;

            logger.info(`KMS Public Key: ${pubKey}`);
            console.log(typeof response.data.kms_public_key, response.data.kms_public_key.slice(0, 30));

            pubKey = Buffer.from(pubKey, 'base64').toString('utf-8');
            logger.info(`Successfully decode KMS Public Key: ${pubKey}`);
            const encryptedKey = crypto.publicEncrypt(
                {
                    key: pubKey,
                    padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
                    oaepHash: "sha256",
                },
                aesKey
            ).toString('base64');
            logger.info("Successfully encrypt AES key");
            const encryptedIV = crypto.publicEncrypt(
                {
                    key: pubKey,
                    padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
                    oaepHash: "sha256",
                },
                iv
            ).toString('base64');
            logger.info("Successfully encrypt IV");

            // Step 3: Send encrypted data and encrypted key to data server 
            try{
                logger.info(`${dataBaseUrl}upload`);
                console.log(typeof encryptedData, typeof encryptedKey, typeof encryptedIV, typeof fileName);
                const response = await axios.post(`${dataBaseUrl}upload`, {
                    file_name: fileName, 
                    encrypted_data:encryptedData, 
                    encrypted_aes_key: encryptedKey, 
                    encrypted_aes_initial_vector: encryptedIV},
                    {
                        headers: {'Content-Type': 'application/json'}
                    });
                console.log(response.data);
                if (response.data.code==200){
                    logger.info(`Successfully upload file: ${fileName}`);
                }else{
                    return { success: false, error: response.data.message };
                }
            }catch(err){
                logger.error(`Failed to upload file: ${fileName}`);
                if (axios.isAxiosError(error)) {
                    console.error("Axios error:", error.response?.status, error.response?.data);
                    return { success: false, error: error.response?.data?.status || error.message };
                } else {
                    console.error("Unexpected error:", error);
                    return { success: false, error: error.message };
                }
            }

            return{
                success: true,
                fileName: fileName
            }
            
        }else{
            return { success: false, error: response.data.message };
        }
    }catch(err){
        if (axios.isAxiosError(error)) {
            console.error("Axios error:", error.response?.status, error.response?.data);
            return { success: false, error: error.response?.data?.status || error.message };
        } else {
            console.error("Unexpected error:", error);
            return { success: false, error: error.message };
        }
    }
}

module.exports = { handleUpload };