This is a program to scrape the WCCA (aka CCAP) website for files and then to download them as .mhtml files. 
It uses the selenium python library following a suggestion and some code sharing from Dan Fitch

This is currently set up for Windows OS and the chrome browser, I am sure making it work for mac would require only minimal tweaking to the save functions

This program will automatically save the court records as mhtml files with user input only for completing the occasional captcha.

It is set to receive date entries in MM-DD-YYYY format (change these dates in the main() command at the bottom of the code) and it will handle the rest, this includes entering the county and all the case tags

It should automatically enter new dates, it used to, but for now it might only do 30 days at a time (which is still like 90 cases sometimes) 

There is no stop right now, I usually just pause it when I’m done

Right now it takes about 8 seconds per file, idk if I’ll make this better, probably not worth 

Try not to touch your computer as much as possible since the only way I could get it to save the file was by using desktop commands which you can easily mess up by hitting the keyboard. 

Let me know what you think!
Quinn
