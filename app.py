from flask import (
    flash,
    Flask,
    jsonify,
    render_template,
    request,
    session,
    redirect,
    url_for,
)
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)


app.secret_key = "mysecretkey"  # Set your own secret key
cluster = MongoClient(
    "mongodb+srv://2001dyddns:Z9QvQuFlMUzK2Ige@coinapp.h7x0xzm.mongodb.net/?retryWrites=true&w=majority"
)
db = cluster["coinmarket"]
usercol = db["user"]  # user info. include name,id, password,
coincol = db["coin"]  # coin info. include quantity, cost
marketcol = db["marketplace"]  # coin list
coin_inventory = 100  # coin max
coin_firstprice = 100

# coin initialize
if marketcol.count_documents({}) == 0:
    marketcol.insert_one(
        {"coin_inventory": coin_inventory, "coin_firstprice": coin_firstprice}
    )


@app.route("/")
def index():
    return render_template("index.html", title="Main")


@app.route("/home")
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
            market_data = marketcol.find({"quantity": {"$gt": 0}})
            data_list = list(market_data)

            coin_sell_data = coincol.find({"quantity": {"$gt": 0}})
            coin_sell_data_list = list(coin_sell_data)
            # sold_time과 price 데이터 추출
            sold_time_list = [data["sold_time"] for data in coin_sell_data_list]
            price_list = [data["price"] for data in coin_sell_data_list]

            # 그래프 생성
            plt.plot(sold_time_list, price_list)
            plt.xlabel("Sold Time")
            plt.ylabel("Price")
            plt.title("Coin Sell Data")
            plt.xticks(rotation=45)
            plt.tight_layout()
            img_stream = io.BytesIO()
            plt.savefig(img_stream, format="png")
            img_stream.seek(0)
            img_base64 = base64.b64encode(img_stream.getvalue()).decode("utf-8")
            return render_template(
                "main.html",
                name=name,
                coins=coins,
                seed_money=seed_money,
                user=user,
                coin_inventory=coin_inventory,
                coin_price=coin_firstprice,
                data_list=data_list,
                graph_data=img_base64,
            )
        else:
            return "User not found"
    else:
        return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "username" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]

        if usercol.find_one({"username": username}):
            return "Username already exists"
        else:
            new_user = {
                "name": name,
                "username": username,
                "password": password,
                "coins": 0,
                "seed_money": 0,
            }
            usercol.insert_one(new_user)

        return redirect(url_for("login"))

    return render_template("signup.html")


# 로그인
@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = usercol.find_one({"username": username})

        if user and user["password"] == password:
            session["username"] = username
            return redirect(url_for("home"))
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


@app.route("/coinlist")
def coinlist():
    return render_template("coinlist.html")


@app.route("/nav")
def nav():
    return render_template("nav.html")


# 코인의 주문목록 / 히스토리 확인
@app.route("/coin")
def coin():
    if "username" not in session:
        return redirect(url_for("login"))

    # marketplace의 정보를 가져온다.

    #

    return render_template("coin.html")


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
        coincol.insert_one(
            {
                "sold_time": sold_time,
                "quantity": coin_quantity,
                "price": coin_firstprice,
                "who": username,
            }
        )

        return "Coin purchase successful"

    return redirect(url_for("login"))


@app.route("/mypage")
def mypage():
    if "username" in session:
        username = session["username"]
        user = usercol.find_one({"username": username})
        if user:
            name = user["name"]
            coins = user["coins"]
            seed_money = user["seed_money"]

            return render_template(
                "mypage.html",
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
            {
                "who": seller_username,
                "quantity": {"$gte": coin_quantity},
                "price": coin_price,
            }
        )
        if not seller:
            return "Seller not found"
        else:
            usercol.update_one(
                {"username": username}, {"$inc": {"seed_money": -total_price}}
            )
            usercol.update_one(
                {"username": username}, {"$inc": {"coins": coin_quantity}}
            )
            marketcol.delete_many(
                {
                    "who": seller_username,
                    "quantity": {"$gte": coin_quantity},
                    "price": coin_price,
                }
            )
            sold_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            coincol.insert_one(
                {
                    "sold_time": sold_time,
                    "quantity": coin_quantity,
                    "price": coin_price,
                    "who": username,
                }
            )
            return f"Coin purchase successful. Bought {coin_quantity} coins from {seller_username} at {coin_price} each."
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
            {"quantity": coin_quantity, "price": coin_price, "who": username}
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
@app.route("/withdraw", methods=["POST"])
def withdraw():
    if "username" not in session:
        return redirect(url_for("login"))

    amount = float(request.form["amount"])

    # if amount <= 0:
    #     return "Invalid amount"

    username = session["username"]
    user = usercol.find_one({"username": username})

    if user:
        seed_money = user["seed_money"]
        if amount > seed_money:
            return "Insufficient seed money"

        usercol.update_one({"username": username}, {"$inc": {"seed_money": -amount}})

        return redirect(url_for("home"))

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
