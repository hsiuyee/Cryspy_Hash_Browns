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
    try {
      logger.info(`${apiBaseUrl}login`);
      // logger.info(`Password: ${password} / Password Hash: ${password_hash}`);
      const response = await axios.post(`${apiBaseUrl}login`, { email, password}, {
         headers: {'Content-Type': 'application/json'}
      });

      if (response.status==200){
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
    try {
      logger.info(`${apiBaseUrl}register`);
      // logger.info(`Password: ${password} / Password Hash: ${password_hash}`);
      const response = await axios.post(`${apiBaseUrl}register`, { email, password}, {
         headers: {'Content-Type': 'application/json'}
      });

      if (response.status==200){
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
  logger.info(`${apiBaseUrl}verify_login`);
  const response = await axios.post(`${apiBaseUrl}verify_login`, { email, otp }, {
    headers: {'Content-Type': 'application/json'}
  });
  if (response.data.code==200){
    logger.info(`${response.data.message} / SID=${response.data.sid}`);
    return {
      success: true, 
      sid: response.data.sid
    }
  }else{
    logger.info(`${response.data.message}`);
    return {
      success: false, 
      error: response.data.message
    }
  }
}

async function handleOTPRegister(event, { email, otp }) {
  logger.info(`OTP Register Attempt Username: ${email} OTP: ${otp}`);
  logger.info(`${apiBaseUrl}verify_register`);
  const response = await axios.post(`${apiBaseUrl}verify_register`, { email, otp }, {
    headers: {'Content-Type': 'application/json'}
  });
  if (response.data.code==200){
    logger.info(`${response.data.status}`);
    return {
      success: true, 
      sid: response.data.sid
    }
  }else{
    logger.info(`${response.data.message}`);
    return {
      success: false, 
      error: response.data.message
    }
  }
}



module.exports = { handleLogin, handleRegister, handleOTP, handleOTPRegister};
