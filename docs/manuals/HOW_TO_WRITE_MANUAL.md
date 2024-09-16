# HOW TO WRITE THE MANUAL

## COMPILING
In VSCode:
1. Make sure you have the docker extension installed
2. On Windows, you'll have to install and open docker desktop, and make sure you have the repo downloded in WSL
3. Right click on docker-compose.yaml, and select "Compose up"
4. Wait to see if the manual.pdf compiles. If you're unsure, delete manual.pdf and try again.

Some reasons why compilation might fail:
- You've used SVGs (the LaTex module that supported SVGs has seemingly been abandoned)
- Your files are routed wrong. In VSCode, right click and copy relative path of a given file to get an accurate pathing, then parse down to the proper relative path from where you're at. This is useful to avoid spelling errors, but also remove any differences between windows and linux in filenames.

## QR CODES
When collecting QR codes, follow these steps:
1. Use this free website: [https://new.express.adobe.com/tools/generate-qr-code](https://new.express.adobe.com/tools/generate-qr-code)
2. Use default settings, save as a PNG
3. Use an image editor and set the margins to 1500px wide, leave height alone unless you are adding other things to the QR code (such as appstore logos). The reason you set it so wide is because there's no way to format images in the LaTex compiler and they will always scale up to max width, increasing width makes it so that the height wont be changed (and you won't get half a page of QR code)
