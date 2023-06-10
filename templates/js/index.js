function loadModule(modulePath) {
  var moduleContainer = document.getElementById("moduleContainer");
  var xhr = new XMLHttpRequest();
  xhr.open("GET", modulePath, true);
  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4 && xhr.status === 200) {
      moduleContainer.innerHTML += xhr.responseText;
    }
  };
  xhr.send();
}
