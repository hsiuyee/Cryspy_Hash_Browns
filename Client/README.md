# Final Project

## How to Run ?

```
$npm install 
// Change .env-template to .env (and add custom parameters)
$npm start 
```

## File structure

```
Final/
    |--- backend/
        |--- auth.js        # Deal with user login and register
    |--- renderer/          # This file for front-end logic 
        |--- login.js
    |--- templates/ 
        |--- login.html
        |--- register.html
        |--- main.html
        |--- otp.html 
    |--- main.js 
    |--- preload.js 
    |--- package.json
    |--- package-lock.json
    |--- logger.js          # Output log to client.log 
    |--- README.md
    |--- .env-template 
```
## TODO 
* (Wait RegisterCreate and RegisterVerify API) Test handleRegister 
* Change handleLogin to api version 