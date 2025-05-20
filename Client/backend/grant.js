const {logger} = require('../logger.js')

require('dotenv').config();
const apiBaseUrl = process.env.API_BASE_URL;
const axios = require('axios');

async function handleGrantAccess(event, { fileName, email, sid }) {
    logger.info(`Grant Access Attempt File: ${fileName} Email: ${email}`);
    try {
        logger.info(`${apiBaseUrl}grant_access`);
        const response = await axios.post(`${apiBaseUrl}grant_access`, { file_name: fileName, friend_email: email }, {
            headers: { 'Content-Type': 'application/json', 'sid': sid },
        });
        if (response.data.code == 200) {
            logger.info("Successfully grant access");
            return { success: true, message: response.data.message };
        } else {
            logger.error("Failed to grant access");
            return { success: false, error: response.data.message };
        }
    } catch (err) {
        logger.error(err);
        return { success: false, error: err.message };
    }
}

module.exports = {handleGrantAccess};