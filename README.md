The project made for CS50's final project.
This is a web-based messenger for gamers and which is called Mobiplay.

I considered implementing this project on the web, using a tech stack that I went through CS50 course, namely Python, Flask, Jinja2, Bootstrap, SQLite 3, HTML5, CSS 3, and a little bit of JavaScript. Unfortunately, Mobiplay is suited only for desktops, laptops and tablets, it's optimized very badly for phones. What about the code part?

I divided the project into 3 parts (static folder, templates, and application.py with other python files). The main technology which makes things works is Flask as I said before. The main page around which Messanger was built is chat which gives an opportunity for users to interact with each other. Also, users have a page named account in which they can enter their personal info, add a profile photo, change their password + page named games, there are games that are available in Messanger which users can add to their profiles. What about page profile, gamers can choose their location, first language, second language, the favorite game from added games to profile, status (online, idle or offline). Further, this information will be used on the search page where people can add new friends. All added friends transfer to the page "chat" and the page "mates" (list of added friends). Using this chat users can communicate with friends but it's only possible chatting if the user added these friends. If I remove some friend I lost chat history with him, and the opportunity to chat, but if I add him again, all is back. All data of the project are stored in SQlite3 on several tables. The main design of the site is built on Bootstrap.

Thanks for reading this!


