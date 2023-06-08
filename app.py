from flask import Flask, render_template, request, session, redirect, url_for
from pymongo import MongoClient
from flask_pymongo import PyMongo
from datetime import datetime


# app = Flask(__name__)


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/softwear"  # MongoDB 연결 URI
mongo = PyMongo(app)

app.secret_key = "mysecretkey"  # Set your own secret key
cluster = MongoClient(
    "mongodb+srv://2001dyddns:Z9QvQuFlMUzK2Ige@coinapp.h7x0xzm.mongodb.net/?retryWrites=true&w=majority"
)
db = cluster["coinmarket"]
usercol = db["user"]
coincol = db["coin"]
marketcol = db["marketplace"]
coin_inventory = 100
coin_firstprice = 100
if marketcol.count_documents({}) == 0:
    marketcol.insert_one(
        {"coin_inventory": coin_inventory, "coin_firstprice": coin_firstprice}
    )


@app.route("/")
def home():
    marketplace = marketcol.find_one({})
    coin_inventory = marketplace.get("coin_inventory", 0)
    coin_firstprice = marketplace.get("coin_firstprice", 0)
    if "username" in session:
        username = session["username"]
        user = usercol.find_one({"username": username})
        if user:
            name = user["name"]
            coins = user["coins"]
            seed_money = user["seed_money"]

            return render_template(
                "main.html",
                name=name,
                coins=coins,
                seed_money=seed_money,
                user=user,
                coin_inventory=coin_inventory,
                coin_price=coin_firstprice,
            )
        else:
            return "User not found"
    else:
        return redirect(url_for("login"))


# 회원가입 페이지
@app.route("/signup", methods=["GET", "POST"])
def signup():
    # username이 있다면
    if "username" in session:
        return redirect(url_for("home"))

    # DB에 저장
    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]

        # username이 이미 존재한다면
        if usercol.find_one({"username": username}):
            return "Username already exists"
        else:  # db 세팅
            new_user = {
                "name": name,
                "username": username,
                "password": password,
                "coins": 0,
                "seed_money": 0,
            }
            usercol.insert_one(new_user)

        # login으로 연결
        return redirect(url_for("login"))

    return render_template("signup.html")


# 로그인
@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("home"))

    # post to DB
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = usercol.find_one({"username": username})

        if user and user["password"] == password:
            session["username"] = username
            return redirect(url_for("home", user=user))
        else:
            return "Invalid username or password"
    return render_template("login.html")


# 로그아웃
@app.route("/logout")
def logout():
    # login 상태일 경우
    if "username" in session:
        session.pop("username", None)
    return redirect(url_for("login"))


# 마켓에서 코인을 구매
@app.route("/buy_coin", methods=["POST"])
def buy_coin():
    # login되어있는 상태일 경우
    if "username" not in session:
        return redirect(url_for("login"))

    # marketcol에서 문서 검색
    marketplace = marketcol.find_one()

    coin_inventory = marketplace.get("coin_inventory", 0)
    coin_quantity = int(request.form["coin_quantity"])
    if coin_quantity <= 0:
        return "Invalid coin quantity"
    if coin_quantity > coin_inventory:
        return "Insufficient coin inventory"

    # 전체 가격 계산
    total_price = coin_firstprice * coin_quantity

    username = session["username"]
    user = usercol.find_one({"username": username})

    if user:
        seed_money = user["seed_money"]
        if seed_money < total_price:
            return "Insufficient seed money"
        usercol.update_one(
            {"username": username}, {"$inc": {"seed_money": -total_price}}
        )
        usercol.update_one({"username": username}, {"$inc": {"coins": coin_quantity}})
        marketcol.update_one({}, {"$inc": {"coin_inventory": -coin_quantity}})
        sold_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        coincol.update_one(
            {},
            {
                "$push": {
                    "coins": {
                        "sold_time": sold_time,
                        "quantity": coin_quantity,
                        "price": coin_firstprice,
                        "who": username,
                    }
                }
            },
        )
        return "Coin purchase successful"

    return redirect(url_for("login"))


# 사용자가 제시한 코인을 산다.
@app.route("/buy_user_coin", methods=["POST"])
def buy_user_coin():
    if "username" not in session:
        return redirect(url_for("login"))
    seller_username = request.form["seller_username"]
    coin_quantity = int(request.form["coin_quantity"])
    coin_price = float(request.form["coin_price"])
    username = session["username"]
    user = usercol.find_one({"username": username})

    if user:
        total_price = coin_firstprice * coin_quantity
        seed_money = user["seed_money"]
        if seed_money < total_price:
            return "Insufficient seed money"
        seller = marketcol.find_one(
            {"username": seller_username},
            {"name": 1, "coin_inventory": 1, "coin_firstprice": 1},
        )
        if not seller:
            return "Seller not found"
        seller_name = seller.get("name")
        seller_coin_inventory = seller.get("coin_inventory", 0)
        seller_coin_firstprice = seller.get("coin_firstprice", 0)
        if (
            seller_username == username
            and coin_quantity <= seller_coin_inventory
            and coin_price == seller_coin_firstprice
        ):
            usercol.update_one(
                {"username": username}, {"$inc": {"seed_money": -total_price}}
            )
            usercol.update_one(
                {"username": username}, {"$inc": {"coins": coin_quantity}}
            )
            del seller["name"]
            del seller["coin_inventory"]
            del seller["coin_firstprice"]
            sold_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            coincol.update_one(
                {},
                {
                    "$push": {
                        "coins": {
                            "sold_time": sold_time,
                            "quantity": coin_quantity,
                            "price": coin_firstprice,
                            "who": username,
                        }
                    }
                },
            )
            return f"Coin purchase successful. Bought {coin_quantity} coins from {seller_name} at {coin_price} each."
        return "Invalid seller information"
    return redirect(url_for("login"))


# 코인 판매
# 로그인 된 사용자만 사용 가능
@app.route("/sell_coin", methods=["POST"])
def sell_coin():
    # 세션에 username이 없을 경우 로그인 페이지로 리다이렉트
    if "username" not in session:
        return redirect(url_for("login"))

    coin_quantity = int(request.form["coin_quantity"])
    coin_price = float(request.form["coin_price"])

    # 수량 부족 시
    if coin_quantity <= 0:
        return "Invalid coin quantity"

    # db에서 user의 정보를 확인
    username = session["username"]
    user = usercol.find_one({"username": username})

    # user일 경우
    if user:
        coin_owned = user["coins"]
        if coin_quantity > coin_owned:
            return "Insufficient coin quantity"

        usercol.update_one({"username": username}, {"$inc": {"coins": -coin_quantity}})

        marketcol.insert_one(
            {"quantity": -coin_quantity, "price": coin_price, "who": username}
        )

        return "Coin sold successfully"

    return redirect(url_for("login"))


# 입금
@app.route("/charge_money", methods=["POST"])
def charge_money():
    if "username" in session:
        username = session["username"]
        user = usercol.find_one({"username": username})

        if user:
            seed_money = float(request.form["seed_money"])
            usercol.update_one(
                {"username": username}, {"$inc": {"seed_money": seed_money}}
            )
            return redirect(url_for("home"))

    return redirect(url_for("login"))


# 출금
@app.route("/convert_money", methods=["POST"])
def convert_money():
    if "username" not in session:
        return redirect(url_for("login"))

    amount = float(request.form["amount"])

    if amount <= 0:
        return "Invalid amount"

    username = session["username"]
    user = usercol.find_one({"username": username})

    if user:
        seed_money = user["seed_money"]
        if amount > seed_money:
            return "Insufficient seed money"

        usercol.update_one({"username": username}, {"$inc": {"seed_money": -amount}})
        usercol.update_one({"username": username}, {"$inc": {"cash_money": amount}})

        return "Money converted successfully"

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
