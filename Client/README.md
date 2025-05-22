# Final Project

## How to Run ?

```
$npm install 
// Change .env-template to .env (and add custom parameters)
$npm start 
```

## File structure

```
Client/
    |--- backend/
        |--- auth.js        # Deal with user login and register
        |--- file.js        # Deal with upload and download encrypt/decrypt
        |--- grant.js       # Deal with grant access to other users
    |--- renderer/          # This file for front-end logic 
        |--- upload.js
        |--- download.js
    |--- templates/ 
        |--- login.html
        |--- register.html
        |--- index.html
        |--- otp.html 
        |--- otp-register.html
        |--- download.html
        |--- grant.html
        |--- base.html
        |--- style.css
    |--- main.js 
    |--- preload.js 
    |--- package.json
    |--- package-lock.json
    |--- logger.js          # Output log to client.log 
    |--- README.md
    |--- .env-template 
```