			    		<<<----- Joynters's Object Rendering Tool ----->>>

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start by editing path in render to your downloaded at the very bottom, line 324

 base_path = "C:\\Your\\Path\\PSXGraphics"

Open windows cmd directory from your PSXGraphics Path and input:


 C:\ cd C:\ Path to\PSXGraphics\ > pip install pygame numpy


After this you will have the game emulator necessary for viewing in python

Now run the new command input:


 C:\> cd C:\Path to\PSXGraphics\

 C:\Path to\PSXGraphics> python render.py


Now enter you object base name


 Enter the base name (without extension): 


for example - Enter the base name (without extension): tv         which is a given object in c


This will open a viewer window and show your current object with a texture applied in the way your source will on the PSX


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For use of the blender model to c convertor copy and paste the script into blenders script menu and run the python

After this a new export option will pop up, rename your model (thing.c) and save into C:\ path to \ PSXGraphics \ cout \

Now you can render your own objects 