//login.js
document
  .getElementById("loginForm")
  .addEventListener("submit", function (event) {
    event.preventDefault(); // 기본 동작 방지

    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;

    fetch("/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        } else {
          throw new Error("Invalid response from server");
        }
      })
      .then((result) => {
        if (result.success) {
          alert("Login successful");
          console.log(result);
          // Redirect to a new page or perform any other action
        } else {
          alert("Invalid username or password");
        }
      })
      .catch(function (error) {
        console.error(error);
        alert("An error occurred during login");
      });
  });
