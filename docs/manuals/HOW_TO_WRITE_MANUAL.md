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
1. Use the `qrencode` library in linux/wsl using these parameters: `qrencode {url} -o {filename}.svg -t SVG -s 50`
2. Use an image editor and add the QR code to the appropriate place on the qr-page.png file. If using Affinity Photo (an editor that we have a license for in onepass), make sure you combine all layers into one and then rasterize+trim that last layer before exporting as a png
