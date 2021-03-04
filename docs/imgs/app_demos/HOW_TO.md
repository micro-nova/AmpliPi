# Gif creation process
1. Take screenshots using AmpliPi with iPhone, making sure to take one before and after any user action. Copy the files to your computer.
1. Open gimp, and click File->Open as Layers. Select the whole sequence of screenshots taken.
1. Organize the layers top down from last to first. It will probably be the opposite at first.
1. Add touches with the pencil tool using a circular tip with 30% opacity (use black or white to contrast with the touched background)
1. Add a set of layers for each click to emulate a click ie:
    * L1 - before click
    * L2 - before click + touch
    * L3 - before click copy
    * L4 - after click
1. click Filters->Animation->Optimize for GIF. This will make a duplicate project and remove repeated parts of the images to optize the gif.
1. Add extra transparent frames to show timing delays
  Simple recommendation: use 4fps (250ms period) and after every click add 4 transparent frames (1 sec)
    * L1 - before click
    * L2 - before click + touch
    * L3 - before click copy
    * L4 - after click
    * L5 - transparent
    * L6 - transparent
    * L7 - transparent
    * L8 - transparent
1. Add 3 seconds worth of delay at the end (to demonstrate this is the end since we will make this gif play in a loop)
1. Export to a gif using File->Export
    * set the filename to something.gif
    * Check the options: as animation, loop forever, and use delay entered. Set delay to 250ms.
1. View the gif and make sure it looks good
1. Use the create_smaller_sizes script to make smaller gifs
