const {logger} = require('../logger.js')

require('dotenv').config();
const apiBaseUrl = process.env.API_BASE_URL;
const dataBaseUrl = process.env.DATA_BASE_URL;
const axios = require('axios');
const crypto = require('crypto');

const fs = require('fs');
const path = require('path');
const os = require('os');

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

async function handleListFile(event) {
    logger.info(`List File Attempt`);

    try {
        const response = await axios.get(`${dataBaseUrl}list_files`, {
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.data.code === 200) {
            logger.info("Successfully retrieved file list");
            console.log(response.data.files);
            return { success: true, files: response.data.files };
        } else {
            return { success: false, error: response.data.message };
        }
    } catch (error) {
        logger.error("Failed to retrieve file list");
        if (axios.isAxiosError(error)) {
            console.error("Axios error:", error.response?.status, error.response?.data);
            return { success: false, error: error.response?.data?.status || error.message };
        } else {
            console.error("Unexpected error:", error);
            return { success: false, error: error.message };
        }
    }

}

async function handleDownload(event, {fileName, sid, savePath}) {
    logger.info(`Download Attempt File: ${fileName} / SID: ${sid}`);

    try {
        // Part 1: Download from data server 
       const response = await axios.get(`${dataBaseUrl}download`, {
        params: { file_name: fileName },
        headers: { 'Content-Type': 'application/json' }
        });

        if (response.data.code != 200) {
           return { success: false, error: response.data.message };
        } 

        logger.info("Successfully download file from data server");
        const encryptedData = response.data.encrypted_data;
        const encryptedKey = response.data.encrypted_aes_key;
        const encryptedIV = response.data.encrypted_aes_initial_vector;
        
        // Part 2: Ask KMS Private Key and Decrypt AES key

        const response2 = await axios.post(`${apiBaseUrl}get_private_key`, { file_name: fileName }, {
            headers: { 'Content-Type': 'application/json', 'sid': sid }
        });

        if (response2.data.code != 200) {
            return { success: false, error: response2.data.message };
        }

        logger.info("Successfully ask KMS Private Key");
        let privKey = response2.data.kms_private_key;
        privKey = Buffer.from(privKey, 'base64').toString('utf-8');

        const decryptedKey = crypto.privateDecrypt(
            {
                key: privKey,
                padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
                oaepHash: "sha256",
            },
            Buffer.from(encryptedKey, 'base64')
        );

        const decryptedIV = crypto.privateDecrypt(
            {
                key: privKey,
                padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
                oaepHash: "sha256",
            },
            Buffer.from(encryptedIV, 'base64')
        );

        // Part 3: Decrypt data with AES key and IV 
        const decipher = crypto.createDecipheriv('aes-256-cbc', decryptedKey, decryptedIV);
        let decryptedData = decipher.update(encryptedData, 'hex', 'utf8');
        decryptedData += decipher.final('utf8');
        logger.info("Successfully decrypt data with AES key and IV");

        // Part 4: Save decrypted data to file
       
        // TODO: Modify the file path to save the file in a specific directory

        fs.writeFileSync(savePath, decryptedData);
        logger.info(`Successfully save file to ${savePath}`);
        

    } catch (error) {
        logger.error("Failed to download file");
        if (axios.isAxiosError(error)) {
            console.error("Axios error:", error.response?.status, error.response?.data);
            return { success: false, error: error.response?.data?.status || error.message };
        } else {
            console.error("Unexpected error:", error);
            return { success: false, error: error.message };
        }
    }
}

module.exports = { handleUpload, handleListFile, handleDownload };