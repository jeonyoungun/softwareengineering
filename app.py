from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "mysecretkey"  # 임의의 시크릿 키를 설정합니다.


class Coin:
    def __init__(self, sold_time, coin_type, quantity, price):
        self.sold_time = sold_time
        self.coin_type = coin_type
        self.quantity = quantity
        self.price = price

    def get_sold_time(self):
        return self.sold_time

    def get_coin_type(self):
        return self.coin_type

    def get_quantity(self):
        return self.quantity

    def get_price(self):
        return self.price


class User:
    def __init__(self, name, username, password):
        self.name = name
        self.username = username
        self.password = password
        self.coins = []  # 여러 개의 코인을 저장할 리스트
        self.seed_money = 0

    def get_username(self):
        return self.username

    def check_password(self, password):
        return self.password == password

    def add_coin(self, coin):
        self.coins.append(coin)

    def remove_coin(self, coin):
        self.coins.remove(coin)

    def get_seed_money(self):
        return self.seed_money

    def add_seed_money(self, new_seed_money):
        self.seed_money += new_seed_money

    def remove_seed_money(self, new_seed_money):
        self.seed_money -= new_seed_money


users = []
coin_inventory = 100
coin_firstprice = 100


@app.route("/")
def home():
    if "username" in session:
        username = session["username"]
        user = next((user for user in users if user.get_username() == username), None)
        return render_template("main.html", user=user)
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
        if any(user.username == username for user in users):
            return "Username already exists"
        new_user = User(name, username, password)
        users.append(new_user)

        return redirect(url_for("login"))


# 로그인
@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = next((user for user in users if user.get_username() == username), None)
        if user and user.check_password(password):
            session["username"] = username
            return redirect(url_for("home"))  # 로그인 성공 시 메인 화면으로 이동
        else:
            return "Invalid username or password"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)  # 세션에서 사용자 이름을 제거합니다.
    return redirect(url_for("login"))  # 로그인 페이지로 이동합니다.


# 마켓에서 코인을 구매
@app.route("/buy_coin", methods=["POST"])
def buy_coin():
    if "username" not in session:
        return redirect(url_for("login"))

    # 코인 개수 입력값 가져오기
    coin_quantity = int(request.form["coin_quantity"])

    # 코인 개수가 0 이하인 경우
    if coin_quantity <= 0:
        return "Invalid coin quantity"
    if coin_quantity > coin_inventory:
        return "Insufficient coin inventory"

    # 구매에 필요한 총 가격 계산
    total_price = coin_firstprice * coin_quantity

    # 사용자 정보 가져오기
    username = session["username"]
    user = next((user for user in users if user.get_username() == username), None)

    if user:
        # 사용자의 시드머니 확인
        seed_money = user.get_seed_money()

        # 시드머니가 구매에 필요한 가격보다 작거나 같은 경우
        if seed_money < total_price:
            return "Insufficient seed money"

        # 코인 개수 업데이트
        user.set_coin_quantity(user.get_coin_quantity() + coin_quantity)

        # 코인 재고 감소
        coin_inventory -= coin_quantity

        # 시드머니 감소
        user.set_seed_money(seed_money - total_price)

        return "Coin purchase successful"
    else:
        return redirect(url_for("login"))


# 입금
@app.route("/charge_money", methods=["POST"])
def charge_money():
    if "username" in session:
        username = session["username"]
        password = request.form["password"]

        # Get the user object from the list of users
        user = next(
            (
                user
                for user in users
                if user.get_username() == username and user.check_password(password)
            ),
            None,
        )

        if user:
            # Extract the seed money from the form data
            seed_money = float(request.form["seed_money"])

            # Update the user's seed money
            user.add_seed_money(seed_money)

            return redirect(url_for("home"))

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
