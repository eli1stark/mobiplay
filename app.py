import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session
import sqlite3
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, fix_apostrophe

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# config for image's upload 
app.config["IMAGE_UPLOADS"] = "static/avatar"


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Main user's page"""

    # get user's id
    user_id = session["user_id"]

    # Configure to use SQLite database
    conn = sqlite3.connect('mobi.db')
    c = conn.cursor()


    # GET USER'S INFORMATION
    c.execute(f"SELECT * FROM users WHERE id = {user_id}")
    conn.commit()
    # get data into the variable
    row = c.fetchone()

    outbox_username = row[1]
    outbox_photo = row[8]


    # GET MATES INFORMATION
    # query table (users) for data
    c.execute("SELECT * FROM users")
    conn.commit()
    # get data into the variable
    all_users = c.fetchall()

    # query table (mates) for data
    c.execute(f"SELECT * FROM mates WHERE userid = {user_id}")
    conn.commit()
    # get data into the variable
    all_mates = c.fetchall()

    # the variable to store only mates (without other users)
    all_users_update = []

    # remove accounts which wasn't added by the user
    for i in all_users[:]:
        for j in all_mates:
            if i[0] == j[1]:
                all_users_update.append(i)

    # query table (profile) for data
    c.execute("SELECT * FROM profile")
    conn.commit()
    # get data into the variable
    all_profiles = c.fetchall()

    # the variable to store only profiles of mates (without other users)
    all_profiles_update = []

    # remove profiles of mates which wasn't added by the user
    for i in all_profiles[:]:
        for j in all_mates:
            if i[0] == j[1]:
                all_profiles_update.append(i)


    # GET FAVORITE GAME
    # query table (games) for data
    c.execute("SELECT * FROM games")
    conn.commit()
    # get data into the variable
    all_games = c.fetchall()
    

    # GET MESSAGE DATA
    c.execute("SELECT * FROM chat")
    conn.commit()
    chat = c.fetchall()
    
    # close connection with database
    conn.close()

    # variable to change color of user's status
    online = "Online"

    # check whether message contains some data
    check = ""


    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Configure to use SQLite database
        conn = sqlite3.connect('mobi.db')
        c = conn.cursor()

        # query table (users) for data
        c.execute("SELECT * FROM users")
        conn.commit()
        all_users = c.fetchall()

        # variable to track number of users in database at all
        counter = 0
        for i in all_users:
            counter += 1
        counter += 1

        # check in waht chat message was sent
        for i in range(counter):
            if f"send_message_{user_id}_{i}" in request.form:
                # get mateid
                mateid = i
                
                # get sended message
                message_dirty = request.form.get("message")

                # if message is not empty, insert into table (chat)
                if message_dirty != check:
                
                    # fix apostrophe problem
                    message = fix_apostrophe(message_dirty)

                    # insert message into table (chat)
                    c.execute(f"INSERT INTO chat (userid, mateid, message) VALUES ({user_id}, {mateid}, '{message}')")
                    conn.commit()

                    # close connection with database
                    conn.close()

                    # Redirect user to chat page because if I reload twice, function inserts into table 2 times the same value
                    return redirect("/")


    return render_template("index.html", user_id=user_id, outbox_username=outbox_username, outbox_photo=outbox_photo, all_users_update=all_users_update, 
    all_profiles_update=all_profiles_update, all_games=all_games, chat=chat, online=online)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register page"""

    # declare variable for validating form
    valid = 0

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Configure to use SQLite database
        conn = sqlite3.connect('mobi.db')
        c = conn.cursor()

        # Ensure username was submitted
        if not request.form.get("username"):
            valid += 1
            return apology("Must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            valid += 1
            return apology("Must provide password", 400)

        # Ensure confirm password was submitted
        elif not request.form.get("confirmation"):
            valid += 1
            return apology("Must provide confirm password", 400)

        # get username from form
        username = request.form.get("username")

        # if username contains this symbols break
        forbidden_sym = r"!@#$%^&*()-=+';\/|{[}],.?`~№:"
        add_for_sym = '"'

        # for all symbols
        for sym in forbidden_sym:
            for letter in username:
                if letter == sym:
                    valid += 1
                    return apology(f"Forbidden symbol: {sym}", 400)

        # for problematic symbol: "
        for letter in username:
            if letter == add_for_sym:
                valid += 1
                return apology(f"Forbidden symbol: {add_for_sym}", 400)

        # compare passwords
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            valid += 1
            return apology("Passwords do not match", 400)

        # select info from database
        c.execute("SELECT * FROM users")
        conn.commit()
        # get this info into the variable
        rows = c.fetchall()

        # if username already exist
        if valid == 0:
            for row in rows:
                username_sql = row[1]
                if username == username_sql:
                    valid += 1
                    return apology("This username already exist!", 400)

        # insert into table (users) hash_password and username
        if valid == 0:
            hash_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            c.execute(f"INSERT INTO users (username, hash) VALUES ('{username}', '{hash_password}')")
            conn.commit()

        # user's id for table (profile)
        users_id_profile = 0

        # get user's id
        if valid == 0:
            c.execute(f"SELECT * FROM users WHERE username = '{username}'")
            conn.commit()
            # get data into the variable
            row = c.fetchone()
            users_id_profile = row[0]

        # insert into table (profile) user's id
        if valid == 0:
            c.execute(f"INSERT INTO profile (userid) VALUES ({users_id_profile})")
            conn.commit()


        # LOG IN directly

        # Forget any user_id
        session.clear()

        # Query database for username
        c.execute(f"SELECT * FROM users WHERE username = '{username}'")
        conn.commit()
        # get this info into the variable
        row = c.fetchone()

        # close database connection
        conn.close()

        # Remember which user has logged in
        session["user_id"] = row[0]
        session["user_name"] = row[1]

        flash("Registered!")

        # Redirect user to home page
        return redirect("/")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Configure to use SQLite database
        conn = sqlite3.connect('mobi.db')
        c = conn.cursor()
        
        username = request.form.get("username")

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # if username contains this symbols break
        forbidden_sym = r"!@#$%^&*()-=+';\/|{[}],.?`~№:"
        add_for_sym = '"'

        # for all symbols
        for sym in forbidden_sym:
            for letter in username:
                if letter == sym:
                    return apology(f"Forbidden symbol: {sym}", 400)

        # for problematic symbol: "
        for letter in username:
            if letter == add_for_sym:
                return apology(f"Forbidden symbol: {add_for_sym}", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        c.execute(f"SELECT * FROM users WHERE username = '{username}'")
        conn.commit()
        # get this info into the variable
        row = c.fetchone()

        # Ensure username exists and password is correct
        if not check_password_hash(row[2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = row[0]
        session["user_name"] = row[1]


        # STATUS SECTION
        # get user's id
        user_id = session["user_id"]

        # Query database for checkbox (remember)
        c.execute(f"SELECT * FROM profile WHERE userid = {user_id}")
        conn.commit()
        # get data into the variable
        row_status = c.fetchone()
        remember = row_status[7]

        # update user's status after login to default (Online) if checkbox remember wasn't checked
        if remember != 1:
            c.execute(f"UPDATE profile SET status = 'Online' WHERE userid = {user_id}")
            conn.commit()

        # close connection with database
        conn.close()

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    
    # Remember user's status after log out or not
    # get user's id
    user_id = session["user_id"]

    # Configure to use SQLite database
    conn = sqlite3.connect('mobi.db')
    c = conn.cursor()

    # Query database for checkbox (remember)
    c.execute(f"SELECT * FROM profile WHERE userid = {user_id}")
    conn.commit()

    # get data into the variable
    row = c.fetchone()
    remember = row[7]

    # update user's status to offline if logout and checkbox (remember) wasn't checked
    if remember != 1:
        c.execute(f"UPDATE profile SET status = 'Offline' WHERE userid = {user_id}")
        conn.commit()
    
    # close connection with database
    conn.close()
    
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/account", methods=["GET", "POST"])
def account():
    """User's account"""
    
    # get user's id
    user_id = session["user_id"]
   
    # Configure to use SQLite database
    conn = sqlite3.connect('mobi.db')
    c = conn.cursor()

    # Query database for data
    c.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
    conn.commit()
    # get data into the variable
    row_users = c.fetchone()
    
    # get data from row
    username = row_users[1]
    password = row_users[2]
    email = row_users[3]
    phone = row_users[4]
    firstname = row_users[5]
    lastname = row_users[6]
    dofb = row_users[7]

    # validator
    valid = 0

    # close connection with database
    conn.close()

    # variable for cheking input
    check = ""

    # variable for preventing empty image
    check_image = ""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure what button was submitted
        if "account" in request.form:
            form_firstname = request.form.get("firstnameinput")
            form_lastname = request.form.get("lastnameinput")
            form_email = request.form.get("emailinput")
            form_phone = request.form.get("phoneinput")
            form_username = request.form.get("usernameinput")
            form_dofb = request.form.get("dofbinput")
            form_confirm_password = request.form.get("confirmpassword")
            form_image = request.files["imageinput"]
            
            # preventing empty image
            check_image = form_image.filename

            # Ensure confirm password was submitted
            if form_confirm_password == check:
                return apology("must provide password", 403)

            if form_confirm_password != check:
                # Ensure password is correct
                a = check_password_hash(password, form_confirm_password)
                if a == False:
                    return apology("invalid password", 403)

            # Configure to use SQLite database
            conn = sqlite3.connect('mobi.db')
            c = conn.cursor()

            if form_firstname != check:
                c.execute(f"UPDATE users SET firstname = '{form_firstname}' WHERE id = {user_id}")
                conn.commit
                
                # Query database for data
                c.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
                conn.commit()
                # get data into the variable
                row = c.fetchone()
                firstname = row[5]
            
            if form_lastname != check:
                c.execute(f"UPDATE users SET lastname = '{form_lastname}' WHERE id = {user_id}")
                conn.commit
                
                # Query database for data
                c.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
                conn.commit()
                # get data into the variable
                row = c.fetchone()
                lastname = row[6]

            if form_email != check:
                c.execute(f"UPDATE users SET email = '{form_email}' WHERE id = {user_id}")
                conn.commit
                
                # Query database for data
                c.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
                conn.commit()
                # get data into the variable
                row = c.fetchone()
                email = row[3]

            if form_phone != check:
                c.execute(f"UPDATE users SET phone = '{form_phone}' WHERE id = {user_id}")
                conn.commit
                
                # Query database for data
                c.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
                conn.commit()
                # get data into the variable
                row = c.fetchone()
                phone = row[4]

            if form_username != check:
                # select info from database
                c.execute("SELECT * FROM users")
                conn.commit()
                # get this info into the variable
                rows = c.fetchall()

                # if username already exist
                for row in rows:
                    username_sql = row[1]
                    if form_username == username_sql:
                        valid = 1
                        return apology("This username already exist!", 400)
                
                if valid == 0:
                    c.execute(f"UPDATE users SET username = '{form_username}' WHERE id = {user_id}")
                    conn.commit
                    
                    # Query database for data
                    c.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
                    conn.commit()
                    # get data into the variable
                    row = c.fetchone()
                    username = row[1]   

                    # update username's session
                    session["user_name"] = row[1]     

            if form_dofb != check:
                # convert 2019-02-12 to 12/02/2019
                b = list(form_dofb)

                year = b[0] + b[1] + b[2] + b[3]
                month = b[5] + b[6]
                day = b[8] + b[9]

                dofb = month + "/" + day + "/" + year

                c.execute(f"UPDATE users SET dofb = '{dofb}' WHERE id = {user_id}")
                conn.commit
                
                # Query database for data
                c.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
                conn.commit()
                # get data into the variable
                row = c.fetchone()
                dofb = row[7]

            if check_image != check:
                # Prevent problem: 1.jpg and 1.png (together)
                # check whether image exists
                jpg = os.path.exists(f"static/avatar/{user_id}.jpg")
                png = os.path.exists(f"static/avatar/{user_id}.png")
                # remove image if its exists
                if jpg == True:
                    os.remove(f"static/avatar/{user_id}.jpg")
                if png == True:
                    os.remove(f"static/avatar/{user_id}.png")

                # get name of user's image
                old_name = form_image.filename

                # convert user's id to string
                string_id = str(user_id)

                # get format from user's image
                img_format = old_name[-4:]
                
                # making new name of image based on user's id
                new_name = string_id + img_format

                # save image to local storage 
                form_image.save(os.path.join(app.config["IMAGE_UPLOADS"], new_name))
                
                # insert image's name into database
                c.execute(f"UPDATE users SET image = '{new_name}' WHERE id = {user_id}")
                conn.commit
                
                # Query database for data
                c.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
                conn.commit()
 

            # close connection with database
            conn.close()

        # ensure what button was submitted
        if "changepassword" in request.form:
            form_current_password = request.form.get("currentpasswordinput")
            form_new_password = request.form.get("newpasswordinput")

            if form_current_password == check or form_new_password == check:
                return apology("must provide both passwords", 403)
                
            if form_current_password != check and form_new_password != check:
                # Ensure current password is correct
                a = check_password_hash(password, form_current_password)
                if a == False:
                    return apology("invalid current password", 403)

                # Configure to use SQLite database
                conn = sqlite3.connect('mobi.db')
                c = conn.cursor()

                hash_new = generate_password_hash(form_new_password, method='pbkdf2:sha256', salt_length=8)

                # update password(hash)
                c.execute(f"UPDATE users SET hash = '{hash_new}' WHERE id = {user_id}")
                conn.commit

                # Query database for data
                c.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
                conn.commit()

                # close connection with database
                conn.close()

    return render_template("account.html", username=username, email=email, phone=phone, firstname=firstname, 
    lastname=lastname, dofb=dofb)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    """User's profile"""
    # get user's id
    user_id = session["user_id"]

    # Configure to use SQLite database
    conn = sqlite3.connect('mobi.db')
    c = conn.cursor()


    # UPLOAD IMAGE FROM DATABASE
    # Query database for data
    c.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
    conn.commit()
    # get data into the variable
    row = c.fetchone()
    # get image from variable
    image = row[8]


    # UPLOAD USER'S STATUS
    # query database for status
    c.execute(f"SELECt * FROM profile WHERE userid = '{user_id}'")
    conn.commit
    # get data into the variable
    row_status = c.fetchone()
    
    # get status from the row
    user_status = row_status[1]

    # list ot store status
    list_status = ["Online", "Idle", "Do not disturb", "Offline"]

    # list of colors of selected box
    color_status = ["Online", "bg-success", "Idle", "bg-warning", "Do not disturb", "bg-danger", "Offline", "bg-secondary"]


    # UPLOAD USER'S DATA (LOCATION, LANGUAGE, LANGUAGE2, BIO, FAVORITE GAME)
    # Query database for data
    c.execute(f"SELECT * FROM profile WHERE userid = '{user_id}'")
    conn.commit()
    # get data into the variable
    row_profile = c.fetchone()
    
    location = row_profile[2]
    language = row_profile[3]
    language2 = row_profile[4]
    bio = row_profile[5]

    # list to store locations
    available_location = ["China", "India", "United States", "Indonesia", "Pakistan", "Brazil", "Russia", "Japan", "Philippines", "Egypt",
    "Germany", "Turkey", "Iran", "United Kingdom", "France", "Italy", "South Korea", "Spain", "Argentina", "Ukraine", "Poland", "Canada", 
    "Australia", "Greece", "Portugal"]

    # list to store available languages
    available_language = ["Mandarin Chinese", "English", "Hindi", "Spanish", "Arabic", "Malay", "Russian", "Bengali", "Portuguese", "French",
    "Indonesian", "Urdu", "German", "Japanese", "Turkish", "Korean", "Vietnamese", "Italian", "Egyptian Arabic", "Filipino", "Ukrainian", "Polish", 
    "Kannada", "Javanese", "Marathi"]


    # UPLOAD USER'S FAVORITE GAME
    # query database for favgame's id
    c.execute(f"SELECT * FROM profile WHERE userid = {user_id}")
    conn.commit()
    # get data into the variable
    row_favgame = c.fetchone()
    favgame_id = row_favgame[6]
    
    # declare variables for favorite game
    #gameid_favgame = 0
    photo_favgame = ""
    title_favgame = ""
    text_favgame = ""
    # the variable for select menu (selected game)
    checker_favgame = 0

    if favgame_id == None:
        photo_favgame = "favgame.jpg"
        title_favgame = "There can be your favorite game"
        
    else:
        checker_favgame = 1
        c.execute(f"SELECT * FROM games WHERE gameid = {favgame_id}")
        conn.commit()
        # get data into the variable
        row_favgame_candidate = c.fetchone()
        photo_favgame = row_favgame_candidate[1]
        title_favgame = row_favgame_candidate[2]
        text_favgame = row_favgame_candidate[3]
        

    # IMPLEMENT GAME SET
    # check global list of games
    c.execute("SELECT * FROM games")
    conn.commit()

    # get data into the variable
    games = c.fetchall()

    # check already added games by a user
    c.execute(f"SELECT * from gameset WHERE userid = {user_id}")
    conn.commit

    # get data into the variable
    added_games = c.fetchall()

    # close connection with database
    conn.close()

    gameset = []

    for i in games:
        for j in added_games:
            if i[0] == j[1]:
                gameset.append(i)

    # the variable to count how many games in a gameset at all
    counter = 0
    for i in gameset:
        counter += 1
    
    # how many rows
    a = counter // 3
    
    # how many games in last row
    b = counter % 3

    first_a = 0

    # case: 16,17 games
    if b != 0:
        first_a = a
        a += 1
    # case: 15 games
    else:
        first_a = a
        b = 3    


    # check empty input
    check = ""

    # checkbox (status)
    status_checkbox = ""
    checkout = []

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # GET USER'S STATUS
        if "update" in request.form:
            status_checkbox = request.form.getlist("status_checkbox")

            # Configure to use SQLite database
            conn = sqlite3.connect('mobi.db')
            c = conn.cursor()

            # condition to prevent out of range
            if status_checkbox != checkout:
                # if checkbox was checked
                if int(status_checkbox[0]) == 1:
                    c.execute(f"UPDATE profile SET remember = {status_checkbox[0]} WHERE userid = {user_id}")
                    conn.commit()
            #if checkbox wasn't checked
            else:
                c.execute(f"UPDATE profile SET remember = 0 WHERE userid = {user_id}")
                conn.commit()

            # get status value
            user_status_form = request.form.get("user_status")

            c.execute(f"UPDATE profile SET status = '{user_status_form}' WHERE userid = {user_id}")
            conn.commit()

            # Query database for data (for purpose to make changes in frontend without reloading page)
            c.execute(f"SELECT * FROM profile WHERE userid = '{user_id}'")
            conn.commit()
            # get data into the variable
            row_status_form = c.fetchone()
            user_status = row_status_form[1]

            # close connection with database
            conn.close()


        # FORM WITH USER'S INFO (LOCATION, LANGUAGE, LANGUAGE2, BIO)
        if "update_profile" in request.form:
            # get user's input
            location_form = request.form.get("location")
            language_form = request.form.get("language")
            language2_form = request.form.get("language2")
            bio_form = request.form.get("bio")

            # Configure to use SQLite database
            conn = sqlite3.connect('mobi.db')
            c = conn.cursor()

            if location_form != check:
                c.execute(f"UPDATE profile SET location = '{location_form}' WHERE userid = {user_id}")
                conn.commit
                
                # Query database for data
                c.execute(f"SELECT * FROM profile WHERE userid = '{user_id}'")
                conn.commit()
                # get data into the variable
                row_form = c.fetchone()
                location = row_form[2]

            if language_form != check:
                c.execute(f"UPDATE profile SET language = '{language_form}' WHERE userid = {user_id}")
                conn.commit
                
                # Query database for data
                c.execute(f"SELECT * FROM profile WHERE userid = '{user_id}'")
                conn.commit()
                # get data into the variable
                row_form = c.fetchone()
                language = row_form[3]

            if language2_form != check:
                c.execute(f"UPDATE profile SET language2 = '{language2_form}' WHERE userid = {user_id}")
                conn.commit
                
                # Query database for data
                c.execute(f"SELECT * FROM profile WHERE userid = '{user_id}'")
                conn.commit()
                # get data into the variable
                row_form = c.fetchone()
                language2 = row_form[4]

            if bio_form != check:
                c.execute(f"UPDATE profile SET bio = '{bio_form}' WHERE userid = {user_id}")
                conn.commit
                
                # Query database for data
                c.execute(f"SELECT * FROM profile WHERE userid = '{user_id}'")
                conn.commit()
                # get data into the variable
                row_form = c.fetchone()
                bio = row_form[5]

            # close connection with database
            conn.close()

        
        # GET USER'S FAVORITE GAME
        if "update_favgame" in request.form:
            # get user's input
            picked_game = request.form.get("select_menu")

            # Configure to use SQLite database
            conn = sqlite3.connect('mobi.db')
            c = conn.cursor()
            
            # get picked game from table (games)
            c.execute(f"SELECT * FROM games WHERE title = '{picked_game}'")
            conn.commit()
            # get data into the variable
            row_picked_game = c.fetchone()
            picked_game_id = row_picked_game[0]

            # update user's profile (favgame)
            c.execute(f"UPDATE profile SET favgame = {picked_game_id} WHERE userid = {user_id}")
            conn.commit

            # Query database for data
            c.execute(f"SELECT * FROM profile WHERE userid = '{user_id}'")
            conn.commit()

            # close connection with database
            conn.close()
            
            # reload page
            return redirect("/profile")


        # GAME SET
        # check what the game a user removed
        for i in range(22):
            if f"{i}" in request.form:
                gameid = i

                # Configure to use SQLite database
                conn = sqlite3.connect('mobi.db')
                c = conn.cursor()
                
                # remove game from table (gameset)
                c.execute(f"DELETE FROM gameset WHERE userid = {user_id} and gameid = {gameid}")
                conn.commit()

                # close connection with database
                conn.close()

                flash("Game removed!")

                # Redirect user to games page because if I reload twice, function removed from table 2 times the same value and after that profile page is crashing
                return redirect("/games")

    return render_template("profile.html", image=image, gameset=gameset, a=a, b=b, first_a=first_a, location=location, language=language,
    language2=language2, bio=bio, photo_favgame=photo_favgame, title_favgame=title_favgame, text_favgame=text_favgame, counter=counter,
    checker_favgame=checker_favgame, user_status=user_status, list_status=list_status, status_checkbox=status_checkbox, color_status=color_status,
    available_location=available_location, available_language=available_language)


@app.route("/games", methods=["GET", "POST"])
def games():
    """Available Games"""
    # get user's id
    user_id = session["user_id"]
    
    # Configure to use SQLite database
    conn = sqlite3.connect('mobi.db')
    c = conn.cursor()

    # Query table games for all games
    c.execute("SELECT * FROM games")
    conn.commit()

    # get data into the variable
    games = c.fetchall()

    # check already added games by a user
    c.execute(f"SELECT * from gameset WHERE userid = {user_id}")
    conn.commit

    # get data into the variable
    added_games = c.fetchall()

    # close connection with database
    conn.close()

    # remove games from global list if a user already had added them to game set
    for i in games[:]:
        for j in added_games: 
            if i[0] == j[1]:
                games.remove(i)

    # SHOW ALL AVAILABLE GAMES:
    # the variable to count how many games left in the global list 
    counter = 0
    for i in games:
        counter += 1
    
    # how many rows
    a = counter // 3
    
    # how many games in last row
    b = counter % 3

    first_a = 0

    # case: 16,17 games
    if b != 0:
        first_a = a
        a += 1
    # case: 15 games
    else:
        first_a = a
        b = 3

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # check what the game a user added
        for i in range(22):
            if f"{i}" in request.form:
                gameid = i

                # Configure to use SQLite database
                conn = sqlite3.connect('mobi.db')
                c = conn.cursor()
                
                # insert into table (gameset) added game
                c.execute(f"INSERT INTO gameset (userid, gameid) VALUES ({user_id}, {gameid})")
                conn.commit()
                
                # close connection with database
                conn.close

                flash("Game added!")

        # Redirect user to profile page because if I reload twice, function inserts into table 2 times the same value and after that games page is crashing
        return redirect("/profile")

    return render_template("games.html", games=games, first_a=first_a, a=a, b=b)


@app.route("/search", methods=["GET", "POST"])
def search():
    """Search engine for adding friends"""
    # get user's id
    user_id = session["user_id"]

    # Configure to use SQLite database
    conn = sqlite3.connect('mobi.db')
    c = conn.cursor()

    # query table (users) for data
    c.execute("SELECT * FROM users")
    conn.commit()
    # get data into the variable
    all_users = c.fetchall()


    # query table (mates) for data
    c.execute(f"SELECT * FROM mates WHERE userid = {user_id}")
    conn.commit()
    # get data into the variable
    all_mates = c.fetchall()


    # remove accounts which was added by the user
    for i in all_users[:]:
        for j in all_mates:
            if i[0] == j[1]:
                all_users.remove(i)
    
    # remove current user from search
    for i in all_users[:]:
        if i[0] == user_id:
            all_users.remove(i)


    # query table (profile) for data
    c.execute("SELECT * FROM profile")
    conn.commit()
    # get data into the variable
    all_profiles = c.fetchall()

    # remove accounts which was added by the user
    for i in all_profiles[:]:
        for j in all_mates:
            if i[0] == j[1]:
                all_profiles.remove(i)

    # remove current user from search
    for i in all_profiles[:]:
        if i[0] == user_id:
            all_profiles.remove(i)

    
    # query table (games) for data
    c.execute("SELECT * FROM games")
    conn.commit()
    # get data into the variable
    all_games = c.fetchall()
    
    # close connection with database
    conn.close()

    # variable to change color of user's status
    online = "Online"


    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Configure to use SQLite database
        conn = sqlite3.connect('mobi.db')
        c = conn.cursor()

        # query table (users) for data
        c.execute("SELECT * FROM users")
        conn.commit()
        all_users = c.fetchall()

        # variable to track number of users in database at all
        counter = 0
        for i in all_users:
            counter += 1
        counter += 1
        
        # check what the mate the user choose
        for i in range(counter):
            if f"user_id_{i}" in request.form:
                mateid = i
                
                # insert into table (mates) added mate
                c.execute(f"INSERT INTO mates (userid, mateid) VALUES ({user_id}, {mateid})")
                conn.commit()

                # close connection with database
                conn.close()

                flash("Mate added!")

                # Redirect user to mates page because if I reload twice, function inserts into table 2 times the same value and after that search page is crashing
                return redirect("/mates")

    return render_template("search.html", all_users=all_users, all_profiles=all_profiles, online=online, all_games=all_games)


@app.route("/mates", methods=["GET", "POST"])
def mates():
    """User's teammates"""
    # get user's id
    user_id = session["user_id"]

    # Configure to use SQLite database
    conn = sqlite3.connect('mobi.db')
    c = conn.cursor()

    # query table (users) for data
    c.execute("SELECT * FROM users")
    conn.commit()
    # get data into the variable
    all_users = c.fetchall()


    # query table (mates) for data
    c.execute(f"SELECT * FROM mates WHERE userid = {user_id}")
    conn.commit()
    # get data into the variable
    all_mates = c.fetchall()


    # the variable to store only mates (without other users)
    all_users_update = []

    # remove accounts which wasn't added by the user
    for i in all_users[:]:
        for j in all_mates:
            if i[0] == j[1]:
                all_users_update.append(i)


    # query table (profile) for data
    c.execute("SELECT * FROM profile")
    conn.commit()
    # get data into the variable
    all_profiles = c.fetchall()

    # the variable to store only profiles of mates (without other users)
    all_profiles_update = []

    # remove profiles of mates which wasn't added by the user
    for i in all_profiles[:]:
        for j in all_mates:
            if i[0] == j[1]:
                all_profiles_update.append(i)

    
    # query table (games) for data
    c.execute("SELECT * FROM games")
    conn.commit()
    # get data into the variable
    all_games = c.fetchall()
    
    # close connection with database
    conn.close()

    # variable to change color of user's status
    online = "Online"


    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Configure to use SQLite database
        conn = sqlite3.connect('mobi.db')
        c = conn.cursor()

        # query table (users) for data
        c.execute("SELECT * FROM users")
        conn.commit()
        all_users = c.fetchall()

        # variable to track number of users in database at all
        counter = 0
        for i in all_users:
            counter += 1
        counter += 1
        
        # check what the mate the user choose
        for i in range(counter):
            if f"user_id_{i}" in request.form:
                mateid = f"{i}"
                
                # remove mate from table (mates)
                c.execute(f"DELETE FROM mates WHERE userid = {user_id} and mateid = {mateid}")
                conn.commit()

                # close connection with database
                conn.close()

                flash("Mate removed!")

                # Redirect user to search page because if I reload twice, function inserts into table 2 times the same value and after that mates page is crashing
                return redirect("/search")

    return render_template("mates.html", all_users_update=all_users_update, all_profiles_update=all_profiles_update, online=online, all_games=all_games)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Settings for chat"""
    # TO DO

    return render_template("settings.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


# Configure debug mode when use flask run
if __name__ == "__main__":
    app.run(debug=True)
