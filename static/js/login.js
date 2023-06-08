document.addEventListener("DOMContentLoaded", function () {
  var loginForm = document.querySelector("#login-form");
  loginForm.addEventListener("submit", function (event) {
    event.preventDefault(); // 폼의 기본 동작 중지

    var usernameInput = document.querySelector("#username");
    var passwordInput = document.querySelector("#password");
    var username = usernameInput.value;
    var password = passwordInput.value;

    // TODO: 입력값 유효성 검사 및 서버로 로그인 요청 전송

    console.log("Username:", username);
    console.log("Password:", password);

    // TODO: 서버 응답에 따른 로그인 결과 처리
  });
});
