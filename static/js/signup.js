// signup.js
document
  .getElementById("registrationForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();

    var username = document.getElementById("username").value;
    var pasword = document.getElementById("pasword").value;
    var confirm_password = document.getElementById("confirm-password").value;

    var data = {
      username: username,
      pasword: pasword,
      confirm_password: confirm_password,
    };

    fetch("/register", {
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
