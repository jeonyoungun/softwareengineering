// signup.js
document
  .getElementById("registrationForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();

    var name = document.getElementById("name").value;
    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;

    var data = {
      name: name,
      username: username,
      password: password,
    };

    fetch("/signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })
      .then((response) => response.json())
      .then((result) => {
        alert("Registration successful!");
        console.log(result);
      })
      .catch((error) => {
        alert("Registration failed. Please try again.");
        console.error(error);
      });
  });
