from flask import Flask, render_template, request, session, redirect, url_for
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'mysecretkey'  # Set your own secret key
cluster = MongoClient("mongodb+srv://2001dyddns:Z9QvQuFlMUzK2Ige@coinapp.h7x0xzm.mongodb.net/?retryWrites=true&w=majority")
db = cluster["coinmarket"]  
usercol = db["user"]
coincol = db["coin"]
marketcol = db["marketplace"]
coin_inventory = 100
coin_firstprice = 100
marketcol.insert_one({
    "coin_inventory": coin_inventory,
    "coin_firstprice": coin_firstprice
})
@app.route('/')
def home():
    marketplace = marketcol.find_one({})
    coin_inventory = marketplace.get("coin_inventory", 0)
    coin_firstprice = marketplace.get("coin_firstprice", 0)
    if 'username' in session:
        username = session['username']
        user = usercol.find_one({"username": username})
        if user:
            name = user['name']
            coins = user['coins']
            seed_money = user['seed_money']
            
            return render_template('main.html', name=name, coins=coins, seed_money=seed_money, user=user, coin_inventory =coin_inventory , coin_price=coin_firstprice)
        else:
            return "User not found"
    else:
        return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'username' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        
        if usercol.find_one({"username": username}):
            return "Username already exists"
        else:
            new_user = {
                'name': name,
                'username': username,
                'password': password,
                'coins': 0,
                'seed_money': 0
            }
            usercol.insert_one(new_user)
        
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = usercol.find_one({"username": username})

        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('home',user=user))
        else:
            return "Invalid username or password"
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'username' in session:
        username = session['username']
        session.pop('username', None)
        usercol.delete_one({"username": username})
    return redirect(url_for('login'))

@app.route('/buy_coin', methods=['POST'])
def buy_coin():
    if 'username' not in session:
        return redirect(url_for('login'))
    marketplace = marketcol.find_one()
    coin_inventory = marketplace.get("coin_inventory", 0)
    coin_quantity = int(request.form['coin_quantity'])
    if coin_quantity <= 0:
        return "Invalid coin quantity"
    if coin_quantity > coin_inventory:
        return "Insufficient coin inventory"
    total_price = coin_firstprice * coin_quantity
    username = session['username']
    user = usercol.find_one({"username": username})

    if user:
        seed_money = user['seed_money']
        if seed_money < total_price:
            return "Insufficient seed money"
        usercol.update_one({"username": username}, {"$inc": {"seed_money": -total_price}})
        usercol.update_one({"username": username}, {"$inc": {"coin": coin_quantity}})
        marketcol.update_one({}, {"$inc": {"coin_inventory": -coin_quantity}})
        sold_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        coincol.update_one({}, {"$push": {"coins": {
            "sold_time": sold_time,
            "quantity": coin_quantity,
            "price": coin_firstprice,
            "who": username
        }}})
        return "Coin purchase successful"

    return redirect(url_for('login'))

@app.route('/but_user_coin', methods=['POST'])
def buy_coin():
    if 'username' not in session:
        return redirect(url_for('login'))
    coin_quantity = int(request.form['coin_quantity'])
    username = session['username']
    user = usercol.find_one({"username": username})
    
    if user:
        total_price = coin_firstprice * coin_quantity
        seed_money = user['seed_money']
        if seed_money < total_price:
            return "Insufficient seed money"
        usercol.update_one({"username": username}, {"$inc": {"seed_money": -total_price}})
        usercol.update_one({"username": username}, {"$inc": {"coin": coin_quantity}})
        marketcol.update_one({}, {"$inc": {"coin_inventory": -coin_quantity}})
        sold_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        coincol.update_one({}, {"$push": {"coins": {
            "sold_time": sold_time,
            "quantity": coin_quantity,
            "price": coin_firstprice,
            "who": username
        }}})
        return "Coin purchase successful"

    return redirect(url_for('login'))


@app.route('/sell_coin', methods=['POST'])
def sell_coin():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    coin_quantity = int(request.form['coin_quantity'])
    coin_price = float(request.form['coin_price'])
    
    if coin_quantity <= 0:
        return "Invalid coin quantity"

    username = session['username']
    user = usercol.find_one({"username": username})

    if user:
        coin_owned = user['coin']
        if coin_quantity > coin_owned:
            return "Insufficient coin quantity"

        usercol.update_one({"username": username}, {"$inc": {"coin": -coin_quantity}})
  
        marketcol.insert_one({
            "quantity": -coin_quantity,
            "price": coin_price,
            "who": username
        })
        
        return "Coin sold successfully"

    return redirect(url_for('login'))


@app.route('/charge_money', methods=['POST'])
def charge_money():
    if 'username' in session:
        username = session['username']
        user = usercol.find_one({"username": username})

        if user:
            seed_money = float(request.form['seed_money'])
            usercol.update_one({"username": username}, {"$inc": {"seed_money": seed_money}})
            return redirect(url_for('home'))

    return redirect(url_for('login'))
@app.route('/convert_money', methods=['POST'])
def convert_money():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    amount = float(request.form['amount'])
    
    if amount <= 0:
        return "Invalid amount"
    
    username = session['username']
    user = usercol.find_one({"username": username})

    if user:
        seed_money = user['seed_money']
        if amount > seed_money:
            return "Insufficient seed money"

        usercol.update_one({"username": username}, {"$inc": {"seed_money": -amount}})
        usercol.update_one({"username": username}, {"$inc": {"cash_money": amount}})
        
        return "Money converted successfully"

    return redirect(url_for('login'))
if __name__ == '__main__':
    app.run(debug=True)
