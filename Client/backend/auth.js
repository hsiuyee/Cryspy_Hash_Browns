const {logger} = require('../logger.js')

require('dotenv').config();
const apiBaseUrl = process.env.API_BASE_URL;
const axios = require('axios');

const bcrypt = require('bcrypt');
const { session } = require('electron');

async function handleLogin(event, { email, password }) {
  logger.info(`Login Attempt Username: ${email} Password: ${password}`);
  
  const saltRounds = parseInt(process.env.SALT_ROUNDS || '10', 10);

  try {
    // const password_hash = await bcrypt.hash(password, saltRounds);
    const password_hash = password;
    try {
      logger.info(`${apiBaseUrl}login`);
      // logger.info(`Password: ${password} / Password Hash: ${password_hash}`);
      const response = await axios.post(`${apiBaseUrl}login`, { email, password_hash}, {
         headers: {'Content-Type': 'application/json'}
      });

      if (response.status==200){
        logger.info(response.data.status);
        return {
          success: true, 
          email: email,
          apiBaseUrl: apiBaseUrl
        }
      }
    } catch (err) {
      return { success: false, error: err.response?.data?.status || err.message };
    }
  } catch (err) {
    return { success: false, error: err.message };
  }
}

async function handleRegister(event, { email, password }) {
  logger.info(`Register Attempt Username: ${email} Password: ${password}`);
  
  const saltRounds = parseInt(process.env.SALT_ROUNDS || '10', 10);

  try {
    // const password_hash = await bcrypt.hash(password, saltRounds);
    const password_hash = password;
    try {
      logger.info(`${apiBaseUrl}register`);
      // logger.info(`Password: ${password} / Password Hash: ${password_hash}`);
      const response = await axios.post(`${apiBaseUrl}register`, { email, password_hash}, {
         headers: {'Content-Type': 'application/json'}
      });

      if (response.status==200){
        logger.info(response.data.status);
        return {
          success: true, 
          email: email,
          apiBaseUrl: apiBaseUrl
        }
      }
    } catch (err) {
      return { success: false, error: response.data.status };
    }
  } catch (err) {
    return { success: false, error: err.message };
  }
}

async function handleOTP(event, { email, otp }) {
  logger.info(`OTP Attempt Username: ${email} OTP: ${otp}`);
  try {
    logger.info(`${apiBaseUrl}verify_email`);
    const response = await axios.post(`${apiBaseUrl}verify_otp`, { email, otp }, {
      headers: {'Content-Type': 'application/json'}
    });
    if (response.status==200){
      logger.info(`${response.data.status} / SID=${response.data.sid}`);
      return {
        success: true, 
        sid: response.data.sid
      }
    }
  } catch (err) {
    return { success: false, error: err.message };
  }
}

async function handleOTPRegister(event, { email, otp }) {
  logger.info(`OTP Register Attempt Username: ${email} OTP: ${otp}`);
  try {
    logger.info(`${apiBaseUrl}verify_email`);
    const response = await axios.post(`${apiBaseUrl}verify_email`, { email, otp }, {
      headers: {'Content-Type': 'application/json'}
    });
    if (response.status==200){
      logger.info(`${response.data.status}`);
      return {
        success: true, 
      }
    }
  } catch (err) {
    return { success: false, error: err.message };
  }
}



module.exports = { handleLogin, handleRegister, handleOTP, handleOTPRegister};
